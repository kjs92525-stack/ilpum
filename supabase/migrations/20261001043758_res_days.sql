create table if not exists public.res_days (
  store_id uuid not null references public.stores(id) on delete cascade,
  id text not null check (id ~ '^\d{4}-\d{2}-\d{2}$'),
  data jsonb not null default '{"items":[]}'::jsonb,
  rev integer not null default 0,
  updated_at timestamptz not null default now(),
  primary key (store_id, id)
);
alter table public.res_days enable row level security;
create policy res_days_sel on public.res_days for select to authenticated using (public.sch_role(store_id) is not null);
create policy res_days_ins on public.res_days for insert to authenticated with check (public.sch_role(store_id) is not null);
create policy res_days_upd on public.res_days for update to authenticated using (public.sch_role(store_id) is not null) with check (public.sch_role(store_id) is not null);

create or replace function public.sch_mig_put_resdays(p_rows jsonb) returns text
 language plpgsql security definer set search_path to ''
as $function$
declare sid uuid := public.sch_anon_store();
begin
  if not public.sch_mig_is_open() then return 'closed'; end if;
  if jsonb_typeof(p_rows) <> 'array' or jsonb_array_length(p_rows) > 200 then return 'bad_rows'; end if;
  if exists (select 1 from jsonb_array_elements(p_rows) r where coalesce(r->>'id','') !~ '^\d{4}-\d{2}-\d{2}$' or jsonb_typeof(r->'data') <> 'object') then return 'bad_rows'; end if;
  insert into public.res_days(store_id, id, data, rev)
  select sid, x.r->>'id', x.r->'data', greatest(coalesce((x.r->>'rev')::int, 0), 1)
  from jsonb_array_elements(p_rows) as x(r)
  on conflict (store_id, id) do update set data = excluded.data, rev = greatest(public.res_days.rev, excluded.rev) + 1, updated_at = now();
  return 'ok';
end $function$;

create or replace function public.sch_mig_counts() returns jsonb
 language plpgsql stable security definer set search_path to ''
as $function$
declare sid uuid := public.sch_anon_store();
begin
  if not public.sch_mig_is_open() then return null; end if;
  return jsonb_build_object(
    'items', coalesce((select jsonb_object_agg(k, c) from (select kind k, count(*) c from public.sch_items where store_id = sid and not deleted group by kind) q), '{}'::jsonb),
    'reservations', (select count(*) from public.reservations where store_id = sid),
    'res_days', (select count(*) from public.res_days where store_id = sid));
end $function$;