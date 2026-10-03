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
    where (public.sch_items.data is distinct from excluded.data or public.sch_items.deleted)      -- 같은 내용이면 건드리지 않음(불필요한 실시간 알림 방지)
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
revoke all on function public.sync_merge_items(jsonb,boolean) from public, anon, authenticated;
grant execute on function public.sync_merge_items(jsonb,boolean) to service_role;