-- 편집 비밀번호가 '없으면' 로그인 없이도 본점 근무표를 바로 편집 (비밀번호를 켜면 다시 필요)
-- 급여(pay)는 어떤 경우에도 이 경로로 못 씀.
create or replace function public.sch_put_many(p_store uuid, p_pin text, p_rows jsonb) returns text
language plpgsql security definer set search_path = '' as $$
declare v text;
begin
  if p_store is distinct from public.sch_anon_store() then return 'denied'; end if;
  v := public.sch_verify_pin(p_store, p_pin);
  if v not in ('ok','nopin') then return v; end if;
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
  if v not in ('ok','nopin') then return v; end if;
  insert into public.sch_summaries(store_id, week, data) values (p_store, p_week, p_data)
    on conflict (store_id, week) do update set data = excluded.data;
  return 'ok';
end $$;

-- 비밀번호 끄기 (로그인한 본사·점주는 기존 비밀번호 없이도 가능)
create or replace function public.sch_clear_pin(p_store uuid, p_old text) returns text
language plpgsql security definer set search_path = '' as $$
declare authed boolean; v text;
begin
  authed := coalesce(public.sch_role(p_store), '') in ('hq','owner');
  if not authed and p_store is distinct from public.sch_anon_store() then return 'denied'; end if;
  if not authed then
    v := public.sch_verify_pin(p_store, p_old);
    if v not in ('ok','nopin') then return v; end if;
  end if;
  delete from public.sch_pins where store_id = p_store;
  delete from public.sch_pin_fail where store_id = p_store;
  return 'ok';
end $$;

revoke all on function public.sch_clear_pin(uuid,text) from public;
grant execute on function public.sch_clear_pin(uuid,text) to anon, authenticated;