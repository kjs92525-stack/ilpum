create extension if not exists pg_net with schema extensions;
create extension if not exists pg_cron;

alter table public.sch_items add column if not exists synced_at timestamptz;
create table if not exists public.sync_state (key text primary key, val jsonb not null default '{}'::jsonb, updated_at timestamptz not null default now());
alter table public.sync_state enable row level security;
revoke all on public.sync_state from anon, authenticated;

create or replace function public.sync_merge_items(p_rows jsonb, p_prune boolean default true) returns jsonb
language plpgsql security definer set search_path to '' as $$
declare sid uuid; n_up int := 0; n_pr int := 0; n_exist int;
  cutoff constant timestamptz := '2026-10-02 02:26:00+00';
begin
  select id into sid from public.stores where is_hq limit 1;
  if jsonb_typeof(p_rows) <> 'array' then return jsonb_build_object('error','bad_rows'); end if;
  if exists (select 1 from jsonb_array_elements(p_rows) r where (r->>'kind') is null or (r->>'kind') not in ('cfg','staff','rule','dc','spot','aw','pay') or coalesce(r->>'id','')='') then return jsonb_build_object('error','bad_rows'); end if;
  create temp table _inc on commit drop as
    select distinct on (r->>'kind', r->>'id') r->>'kind' kind, r->>'id' id, r->'data' data from jsonb_array_elements(p_rows) with ordinality x(r,n) order by r->>'kind', r->>'id', n desc;
  insert into public.sch_items(store_id,kind,id,data,deleted,synced_at)
    select sid, kind, id, data, false, now() from _inc
  on conflict (store_id,kind,id) do update set data = excluded.data, deleted = false, synced_at = now()
    where (public.sch_items.synced_at is not null and public.sch_items.updated_at <= public.sch_items.synced_at)
       or (public.sch_items.synced_at is null and public.sch_items.updated_at <= cutoff);
  get diagnostics n_up = row_count;
  if p_prune then
    select count(*) into n_exist from public.sch_items where store_id=sid and not deleted and kind in ('staff','rule','dc','spot','aw','pay');
    if (select count(*) from _inc where kind in ('staff','rule','dc','spot','aw','pay')) >= greatest(5, n_exist/5) then
      update public.sch_items s set deleted = true, data = null, synced_at = now()
        where s.store_id = sid and not s.deleted and s.kind in ('staff','rule','dc','spot','aw','pay')
          and ((s.synced_at is not null and s.updated_at <= s.synced_at) or (s.synced_at is null and s.updated_at <= cutoff))
          and not exists (select 1 from _inc i where i.kind = s.kind and i.id = s.id);
      get diagnostics n_pr = row_count;
    end if;
  end if;
  return jsonb_build_object('upserted', n_up, 'pruned', n_pr);
end $$;

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
      if merged is distinct from coalesce(ex.data->'items','[]'::jsonb) then
        update public.res_days set data = jsonb_set((r->'data') || ex.data, '{items}', merged), rev = ex.rev + 1, updated_at = now() where store_id = sid and id = r->>'id';
      end if;
    end if;
    n := n + 1;
  end loop;
  return n;
end $$;
revoke all on function public.sync_merge_items(jsonb,boolean), public.sync_merge_resdays(jsonb) from public, anon, authenticated;
grant execute on function public.sync_merge_items(jsonb,boolean), public.sync_merge_resdays(jsonb) to service_role;

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