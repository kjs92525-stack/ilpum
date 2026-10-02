-- 예전 서버(예약·근무표) → 새 서버 자동 연동 (본점). 5분마다 pg_cron 이 edge function `sync-old` 를 부름.
-- 원칙: 새 서버에서 사람이 직접 고친 줄은 절대 덮어쓰지 않고, 예전 서버에서만 바뀐 것만 반영(예약은 id별로 더 늦게 고친 쪽).
create extension if not exists pg_net with schema extensions;
create extension if not exists pg_cron;

alter table public.sch_items add column if not exists synced_at timestamptz;
create table if not exists public.sync_state (key text primary key, val jsonb not null default '{}'::jsonb, updated_at timestamptz not null default now());
alter table public.sync_state enable row level security;     -- 정책 없음: 함수·서비스 키로만
revoke all on public.sync_state from anon, authenticated;

-- 근무표 합치기 (서비스 키 전용). p_prune: 예전에서 사라진 줄(사람이 안 고친 것만)을 지움 표시
-- "사람이 안 고친 줄" = 자동 연동이 쓴 뒤 그대로인 줄(synced_at) 또는 이전 도구가 쓴 줄(2026-10-02 02:26 이전, 05:28~05:29 의 두 번의 일괄 이전)
create or replace function public.sync_merge_items(p_rows jsonb, p_prune boolean default true) returns jsonb
language plpgsql security definer set search_path to '' as $$
declare sid uuid; n_up int := 0; n_pr int := 0; n_exist int;
begin
  select id into sid from public.stores where is_hq limit 1;
  if jsonb_typeof(p_rows) <> 'array' then return jsonb_build_object('error','bad_rows'); end if;
  if exists (select 1 from jsonb_array_elements(p_rows) r where (r->>'kind') is null or (r->>'kind') not in ('cfg','staff','rule','dc','spot','aw','pay') or coalesce(r->>'id','')='') then return jsonb_build_object('error','bad_rows'); end if;
  create temp table _inc on commit drop as
    select distinct on (r->>'kind', r->>'id') r->>'kind' kind, r->>'id' id, r->'data' data from jsonb_array_elements(p_rows) with ordinality x(r,n) order by r->>'kind', r->>'id', n desc;
  insert into public.sch_items(store_id,kind,id,data,deleted,synced_at)
    select sid, kind, id, data, false, now() from _inc
  on conflict (store_id,kind,id) do update set data = excluded.data, deleted = false, synced_at = now()
    where (public.sch_items.data is distinct from excluded.data or public.sch_items.deleted)
      and ((public.sch_items.synced_at is not null and public.sch_items.updated_at <= public.sch_items.synced_at)
        or (public.sch_items.synced_at is null and (public.sch_items.updated_at <= '2026-10-02 02:26:00+00' or public.sch_items.updated_at between '2026-10-02 05:28:00+00' and '2026-10-02 05:29:00+00')));
  get diagnostics n_up = row_count;
  if p_prune then
    select count(*) into n_exist from public.sch_items where store_id=sid and not deleted and kind in ('staff','rule','dc','spot','aw','pay');
    if (select count(*) from _inc where kind in ('staff','rule','dc','spot','aw','pay')) >= greatest(5, n_exist/5) then
      update public.sch_items s set deleted = true, data = null, synced_at = now()
        where s.store_id = sid and not s.deleted and s.kind in ('staff','rule','dc','spot','aw','pay')
          and ((s.synced_at is not null and s.updated_at <= s.synced_at) or (s.synced_at is null and (s.updated_at <= '2026-10-02 02:26:00+00' or s.updated_at between '2026-10-02 05:28:00+00' and '2026-10-02 05:29:00+00')))
          and not exists (select 1 from _inc i where i.kind = s.kind and i.id = s.id);
      get diagnostics n_pr = row_count;
    end if;
  end if;
  return jsonb_build_object('upserted', n_up, 'pruned', n_pr);
end $$;

-- 예약 합치기 (서비스 키 전용): 같은 예약 id 는 더 늦게 고친 쪽(u), 한쪽에만 있는 예약은 모두 남김
create or replace function public.sync_merge_resdays(p_rows jsonb) returns int
language plpgsql security definer set search_path to '' as $$
declare sid uuid; r jsonb; ex public.res_days%rowtype; merged jsonb; n int := 0;
begin
  select id into sid from public.stores where is_hq limit 1;
  for r in select * from jsonb_array_elements(p_rows) loop
    if coalesce(r->>'id','') !~ '^\d{4}-\d{2}-\d{2}$' or jsonb_typeof(r->'data') <> 'object' then continue; end if;
    select * into ex from public.res_days where store_id = sid and id = r->>'id' for update;
    if not found then
      insert into public.res_days(store_id,id,data,rev) values (sid, r->>'id', r->'data', greatest(coalesce((r->>'rev')::int,0),1));
    else
      select coalesce(jsonb_agg(d.item), '[]'::jsonb) into merged from (
        select distinct on (s.iid) s.item from (
          select e as item, coalesce(e->>'id', gen_random_uuid()::text) iid, case when (e->>'u') ~ '^\d+$' then (e->>'u')::numeric else 0 end u, 1 ord from jsonb_array_elements(coalesce(ex.data->'items','[]'::jsonb)) e
          union all
          select e, coalesce(e->>'id', gen_random_uuid()::text), case when (e->>'u') ~ '^\d+$' then (e->>'u')::numeric else 0 end, 2 from jsonb_array_elements(coalesce(r->'data'->'items','[]'::jsonb)) e
        ) s order by s.iid, s.u desc, s.ord asc) d;
      if merged is distinct from coalesce(ex.data->'items','[]'::jsonb) then      -- 바뀐 게 있을 때만 저장 (불필요한 실시간 알림 방지)
        update public.res_days set data = jsonb_set((r->'data') || ex.data, '{items}', merged), rev = ex.rev + 1, updated_at = now() where store_id = sid and id = r->>'id';
      end if;
    end if;
    n := n + 1;
  end loop;
  return n;
end $$;
revoke all on function public.sync_merge_items(jsonb,boolean), public.sync_merge_resdays(jsonb) from public, anon, authenticated;
grant execute on function public.sync_merge_items(jsonb,boolean), public.sync_merge_resdays(jsonb) to service_role;

-- 본사 화면용: 상태 보기 / 켜고 끄기
create or replace function public.sync_status() returns jsonb language plpgsql security definer set search_path to '' as $$
begin
  if not public.is_hq() then raise exception '본사만 볼 수 있어요'; end if;
  return jsonb_build_object('enabled', coalesce((select (val->>'v')::boolean from public.sync_state where key='enabled'), true),
    'last', (select val from public.sync_state where key='last_run'), 'at', (select updated_at from public.sync_state where key='last_run'));
end $$;
create or replace function public.sync_set_enabled(p_on boolean) returns void language plpgsql security definer set search_path to '' as $$
begin
  if not public.is_hq() then raise exception '본사만 바꿀 수 있어요'; end if;
  insert into public.sync_state(key,val) values ('enabled', jsonb_build_object('v',p_on)) on conflict (key) do update set val = excluded.val, updated_at = now();
end $$;
revoke all on function public.sync_status(), public.sync_set_enabled(boolean) from public, anon;
grant execute on function public.sync_status(), public.sync_set_enabled(boolean) to authenticated;

-- 5분마다 실행 (아직 켜지 않음 — 사용자 확인 후): 
-- select cron.schedule('sync-old','*/5 * * * *',$$ select net.http_post(url:='https://bdqcrbnbuoujozlpttbe.supabase.co/functions/v1/sync-old', headers:=jsonb_build_object('Content-Type','application/json','x-sync-token',(select val->>'v' from public.sync_state where key='token')), body:='{}'::jsonb, timeout_milliseconds:=55000) $$);
-- 끄기: select cron.unschedule('sync-old');

-- 설정 화면 버튼용 함수 (본사만): sync_status(켜짐 여부·마지막 결과), sync_run_now(처음부터 한 번 실행), sync_auto_set(5분마다 자동 켜기/끄기)
-- 본문은 DB 마이그레이션 auto_sync_buttons 에 적용돼 있음.
