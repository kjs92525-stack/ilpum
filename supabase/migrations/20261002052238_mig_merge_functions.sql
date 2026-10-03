create or replace function public.sch_mig_merge_items(p_rows jsonb, p_cutoff timestamptz) returns text
language plpgsql security definer set search_path to '' as $$
declare sid uuid := public.sch_anon_store();
begin
  if not public.sch_mig_is_open() then return 'closed'; end if;
  if jsonb_typeof(p_rows) <> 'array' or jsonb_array_length(p_rows) > 500 then return 'bad_rows'; end if;
  if exists (select 1 from jsonb_array_elements(p_rows) r
             where (r->>'kind') is null or (r->>'kind') not in ('cfg','staff','rule','dc','spot','aw','pay')
                or coalesce(r->>'id','') = '') then return 'bad_rows'; end if;
  insert into public.sch_items(store_id, kind, id, data, deleted)
  select distinct on (x.r->>'kind', x.r->>'id') sid, x.r->>'kind', x.r->>'id',
         case when coalesce((x.r->>'deleted')::boolean, false) then null else x.r->'data' end,
         coalesce((x.r->>'deleted')::boolean, false)
  from jsonb_array_elements(p_rows) with ordinality as x(r, n)
  order by x.r->>'kind', x.r->>'id', x.n desc
  on conflict (store_id, kind, id) do update set data = excluded.data, deleted = excluded.deleted
    where public.sch_items.updated_at <= p_cutoff;   -- 그 시각 이후 새 서버에서 직접 고친 줄은 건드리지 않음
  return 'ok';
end $$;

create or replace function public.sch_mig_merge_resdays(p_rows jsonb) returns text
language plpgsql security definer set search_path to '' as $$
declare sid uuid := public.sch_anon_store(); r jsonb; ex public.res_days%rowtype; merged jsonb;
begin
  if not public.sch_mig_is_open() then return 'closed'; end if;
  if jsonb_typeof(p_rows) <> 'array' or jsonb_array_length(p_rows) > 200 then return 'bad_rows'; end if;
  if exists (select 1 from jsonb_array_elements(p_rows) x where coalesce(x->>'id','') !~ '^\d{4}-\d{2}-\d{2}$' or jsonb_typeof(x->'data') <> 'object') then return 'bad_rows'; end if;
  for r in select * from jsonb_array_elements(p_rows) loop
    select * into ex from public.res_days where store_id = sid and id = r->>'id' for update;
    if not found then
      insert into public.res_days(store_id, id, data, rev) values (sid, r->>'id', r->'data', greatest(coalesce((r->>'rev')::int,0),1));
    else
      -- 같은 예약(id)이 양쪽에 있으면 더 늦게 고친 쪽(u)을 쓰고, 한쪽에만 있는 예약은 모두 남김
      select coalesce(jsonb_agg(d.item), '[]'::jsonb) into merged from (
        select distinct on (s.iid) s.item from (
          select e as item, coalesce(e->>'id', gen_random_uuid()::text) iid, case when (e->>'u') ~ '^\d+$' then (e->>'u')::numeric else 0 end u, 1 ord
            from jsonb_array_elements(coalesce(ex.data->'items','[]'::jsonb)) e
          union all
          select e, coalesce(e->>'id', gen_random_uuid()::text), case when (e->>'u') ~ '^\d+$' then (e->>'u')::numeric else 0 end, 2
            from jsonb_array_elements(coalesce(r->'data'->'items','[]'::jsonb)) e
        ) s order by s.iid, s.u desc, s.ord asc) d;
      update public.res_days set data = jsonb_set((r->'data') || ex.data, '{items}', merged),
        rev = greatest(ex.rev, coalesce((r->>'rev')::int,0)) + 1, updated_at = now()
      where store_id = sid and id = r->>'id';
    end if;
  end loop;
  return 'ok';
end $$;

revoke all on function public.sch_mig_merge_items(jsonb, timestamptz), public.sch_mig_merge_resdays(jsonb) from public;
grant execute on function public.sch_mig_merge_items(jsonb, timestamptz), public.sch_mig_merge_resdays(jsonb) to anon;
update public.sch_mig_window set until = now() + interval '2 hours' where id=1;