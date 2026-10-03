-- 로그인 없이 '본점 근무표'를 보고, 편집 비밀번호로만 고치는 방식
--  · 읽기: 본점의 급여 제외 항목만 (익명 허용)
--  · 쓰기: 표를 직접 열지 않고, 비밀번호를 서버에서 확인하는 함수로만 (급여는 불가)
--  · 비밀번호 무차별 대입 방지: 8번 틀리면 15분 잠금

create table public.sch_pins (
  store_id   uuid primary key references public.stores(id) on delete cascade,
  pin_hash   text not null,
  updated_at timestamptz not null default now()
);
create table public.sch_pin_fail (
  store_id uuid primary key references public.stores(id) on delete cascade,
  fails    int not null default 0,
  first_at timestamptz not null default now()
);
alter table public.sch_pins     enable row level security;
alter table public.sch_pin_fail enable row level security;
revoke all on public.sch_pins, public.sch_pin_fail from anon, authenticated;

-- 로그인 없이 열리는 매장 = 본사 소유 매장 중 가장 먼저 만든 것(본점)
create or replace function public.sch_anon_store() returns uuid
language sql stable security definer set search_path = '' as $$
  select id from public.stores where is_hq order by created_at, id limit 1
$$;

create or replace function public.sch_pin_hash(sid uuid, pin text) returns text
language sql immutable set search_path = '' as $$
  select encode(sha256(convert_to(sid::text || ':' || coalesce(pin,''), 'UTF8')), 'hex')
$$;

-- 결과: ok | bad_pin | locked | nopin   (틀린 횟수를 남기려고 오류를 던지지 않고 값으로 돌려줌)
create or replace function public.sch_verify_pin(sid uuid, pin text) returns text
language plpgsql security definer set search_path = '' as $$
declare cur text; f int; t timestamptz;
begin
  select p.pin_hash into cur from public.sch_pins p where p.store_id = sid;
  if cur is null then return 'nopin'; end if;
  select x.fails, x.first_at into f, t from public.sch_pin_fail x where x.store_id = sid;
  if t is not null and now() - t < interval '15 minutes' and f >= 8 then return 'locked'; end if;
  if t is null or now() - t >= interval '15 minutes' then f := 0; t := now(); end if;
  if cur = public.sch_pin_hash(sid, pin) then
    delete from public.sch_pin_fail where store_id = sid;
    return 'ok';
  end if;
  insert into public.sch_pin_fail(store_id, fails, first_at) values (sid, f + 1, t)
    on conflict (store_id) do update set fails = excluded.fails, first_at = excluded.first_at;
  return 'bad_pin';
end $$;

create or replace function public.sch_open_store()
returns table(id uuid, name text, has_pin boolean)
language sql stable security definer set search_path = '' as $$
  select s.id, s.name, exists(select 1 from public.sch_pins p where p.store_id = s.id)
  from public.stores s where s.id = public.sch_anon_store()
$$;

create or replace function public.sch_check_pin(p_store uuid, p_pin text) returns text
language plpgsql security definer set search_path = '' as $$
begin
  if p_store is distinct from public.sch_anon_store() then return 'denied'; end if;
  return public.sch_verify_pin(p_store, p_pin);
end $$;

-- 비밀번호 정하기/바꾸기: 처음엔 그냥 정함, 이미 있으면 기존 비밀번호 필요(본사·점주 로그인 상태면 초기화 가능)
create or replace function public.sch_set_pin(p_store uuid, p_old text, p_new text) returns text
language plpgsql security definer set search_path = '' as $$
declare authed boolean; has boolean; v text;
begin
  if length(coalesce(p_new,'')) < 6 then return 'short'; end if;
  authed := coalesce(public.sch_role(p_store), '') in ('hq','owner');
  if not authed and p_store is distinct from public.sch_anon_store() then return 'denied'; end if;
  if not authed then
    select exists(select 1 from public.sch_pins where store_id = p_store) into has;
    if has then
      v := public.sch_verify_pin(p_store, p_old);
      if v <> 'ok' then return v; end if;
    end if;
  end if;
  insert into public.sch_pins(store_id, pin_hash) values (p_store, public.sch_pin_hash(p_store, p_new))
    on conflict (store_id) do update set pin_hash = excluded.pin_hash, updated_at = now();
  delete from public.sch_pin_fail where store_id = p_store;
  return 'ok';
end $$;

-- 근무표 저장 (급여 항목 'pay' 는 이 경로로 절대 못 씀)
create or replace function public.sch_put_many(p_store uuid, p_pin text, p_rows jsonb) returns text
language plpgsql security definer set search_path = '' as $$
declare v text;
begin
  if p_store is distinct from public.sch_anon_store() then return 'denied'; end if;
  v := public.sch_verify_pin(p_store, p_pin);
  if v <> 'ok' then return v; end if;
  if jsonb_typeof(p_rows) <> 'array' or jsonb_array_length(p_rows) > 1000 then return 'bad_rows'; end if;
  if exists (select 1 from jsonb_array_elements(p_rows) r
             where (r->>'kind') is null or (r->>'kind') not in ('cfg','staff','rule','dc','spot','aw','sales')
                or coalesce(r->>'id','') = '') then return 'bad_rows'; end if;
  insert into public.sch_items(store_id, kind, id, data, deleted)
  select distinct on (x.r->>'kind', x.r->>'id') p_store, x.r->>'kind', x.r->>'id',
         case when coalesce((x.r->>'deleted')::boolean, false) then null else x.r->'data' end,
         coalesce((x.r->>'deleted')::boolean, false)
  from jsonb_array_elements(p_rows) with ordinality as x(r, n)
  order by x.r->>'kind', x.r->>'id', x.n desc
  on conflict (store_id, kind, id) do update set data = excluded.data, deleted = excluded.deleted;
  return 'ok';
end $$;

create or replace function public.sch_put_summary(p_store uuid, p_pin text, p_week text, p_data jsonb) returns text
language plpgsql security definer set search_path = '' as $$
declare v text;
begin
  if p_store is distinct from public.sch_anon_store() then return 'denied'; end if;
  v := public.sch_verify_pin(p_store, p_pin);
  if v <> 'ok' then return v; end if;
  insert into public.sch_summaries(store_id, week, data) values (p_store, p_week, p_data)
    on conflict (store_id, week) do update set data = excluded.data;
  return 'ok';
end $$;

-- 익명 읽기: 본점의 급여 제외 항목만
grant select on public.sch_items to anon;
create policy sch_items_anon_sel on public.sch_items for select to anon
  using (store_id = public.sch_anon_store() and kind <> 'pay');

revoke all on function public.sch_pin_hash(uuid,text), public.sch_verify_pin(uuid,text) from public, anon, authenticated;
revoke all on function public.sch_anon_store(), public.sch_open_store(), public.sch_check_pin(uuid,text),
  public.sch_set_pin(uuid,text,text), public.sch_put_many(uuid,text,jsonb), public.sch_put_summary(uuid,text,text,jsonb) from public;
grant execute on function public.sch_anon_store(), public.sch_open_store(), public.sch_check_pin(uuid,text),
  public.sch_set_pin(uuid,text,text), public.sch_put_many(uuid,text,jsonb), public.sch_put_summary(uuid,text,text,jsonb) to anon, authenticated;