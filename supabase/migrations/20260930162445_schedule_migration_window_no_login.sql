-- 로그인 없이 '예전 자료 옮기기'를 하기 위한 시간제한 창구.
--  · sch_mig_window.until 이 지나면 아래 함수들은 모두 'closed' 를 돌려주고 아무것도 하지 않음
--  · 쓰기는 본점(익명으로 열리는 매장)에만 가능
create table if not exists public.sch_mig_window (
  id    int primary key default 1 check (id = 1),
  until timestamptz not null default now()
);
alter table public.sch_mig_window enable row level security;
revoke all on public.sch_mig_window from anon, authenticated;

create or replace function public.sch_mig_is_open() returns boolean
language sql stable security definer set search_path = '' as $$
  select exists(select 1 from public.sch_mig_window where until > now())
$$;

create or replace function public.sch_mig_state()
returns table(is_open boolean, store_id uuid, store_name text, until timestamptz)
language sql stable security definer set search_path = '' as $$
  select public.sch_mig_is_open(), s.id, s.name, (select w.until from public.sch_mig_window w where w.id = 1)
  from public.stores s where s.id = public.sch_anon_store()
$$;

-- 새 서버에 이미 있는 근무표 항목 (금액은 내용 없이 id만)
create or replace function public.sch_mig_existing() returns jsonb
language plpgsql stable security definer set search_path = '' as $$
begin
  if not public.sch_mig_is_open() then return null; end if;
  return coalesce((select jsonb_agg(jsonb_build_object('kind', i.kind, 'id', i.id,
            'data', case when i.kind = 'pay' then null else i.data end, 'deleted', i.deleted))
          from public.sch_items i where i.store_id = public.sch_anon_store()), '[]'::jsonb);
end $$;

create or replace function public.sch_mig_put_items(p_rows jsonb) returns text
language plpgsql security definer set search_path = '' as $$
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
  on conflict (store_id, kind, id) do update set data = excluded.data, deleted = excluded.deleted;
  return 'ok';
end $$;

create or replace function public.sch_mig_put_reservations(p_rows jsonb) returns text
language plpgsql security definer set search_path = '' as $$
declare sid uuid := public.sch_anon_store();
begin
  if not public.sch_mig_is_open() then return 'closed'; end if;
  if jsonb_typeof(p_rows) <> 'array' or jsonb_array_length(p_rows) > 500 then return 'bad_rows'; end if;
  insert into public.reservations(id, store_id, rdate, rtime, name, phone, size, table_no, note, arrived)
  select x.id, sid, x.rdate, x.rtime, x.name, x.phone, greatest(coalesce(x.size,1),1), x.table_no, x.note, coalesce(x.arrived,false)
  from jsonb_to_recordset(p_rows) as x(id uuid, rdate date, rtime time, name text, phone text, size int, table_no text, note text, arrived boolean)
  on conflict (id) do update set rdate = excluded.rdate, rtime = excluded.rtime, name = excluded.name, phone = excluded.phone,
      size = excluded.size, table_no = excluded.table_no, note = excluded.note, arrived = excluded.arrived
    where public.reservations.store_id = excluded.store_id;      -- 다른 매장 예약은 건드리지 않음
  return 'ok';
end $$;

create or replace function public.sch_mig_counts() returns jsonb
language plpgsql stable security definer set search_path = '' as $$
declare sid uuid := public.sch_anon_store();
begin
  if not public.sch_mig_is_open() then return null; end if;
  return jsonb_build_object(
    'items', coalesce((select jsonb_object_agg(k, c) from (select kind k, count(*) c from public.sch_items where store_id = sid and not deleted group by kind) q), '{}'::jsonb),
    'reservations', (select count(*) from public.reservations where store_id = sid));
end $$;

revoke all on function public.sch_mig_is_open(), public.sch_mig_state(), public.sch_mig_existing(), public.sch_mig_put_items(jsonb),
  public.sch_mig_put_reservations(jsonb), public.sch_mig_counts() from public;
grant execute on function public.sch_mig_is_open(), public.sch_mig_state(), public.sch_mig_existing(), public.sch_mig_put_items(jsonb),
  public.sch_mig_put_reservations(jsonb), public.sch_mig_counts() to anon, authenticated;

-- 창구 열기: 지금부터 12시간
insert into public.sch_mig_window(id, until) values (1, now() + interval '12 hours')
  on conflict (id) do update set until = excluded.until;