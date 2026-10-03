-- =====================================================================
-- 일품집 근무표 모듈 (기존 stores / profiles 에 붙임)
--  - 본점(hq)  : is_hq 매장의 근무표만 열람·편집 (가맹점 근무표는 집계만)
--  - 점주(franchise 계정) : 자기 매장 근무표 편집·급여 열람
--  - 매니저/직원 : sch_members 로 연결 (근무표만, 다른 업무 화면 접근 없음)
-- =====================================================================

create table public.sch_items (
  store_id   uuid not null references public.stores(id) on delete cascade,
  kind       text not null,
  id         text not null,
  data       jsonb,
  deleted    boolean not null default false,
  updated_at timestamptz not null default now(),
  updated_by uuid default auth.uid(),
  primary key (store_id, kind, id)
);
create index sch_items_store_upd on public.sch_items (store_id, updated_at);

create table public.sch_summaries (
  store_id   uuid not null references public.stores(id) on delete cascade,
  week       text not null,
  data       jsonb not null,
  updated_at timestamptz not null default now(),
  primary key (store_id, week)
);

create table public.sch_members (
  user_id  uuid not null references auth.users(id) on delete cascade,
  store_id uuid not null references public.stores(id) on delete cascade,
  role     text not null check (role in ('manager','staff')),
  can_pay  boolean not null default false,
  staff_id text,
  primary key (user_id, store_id)
);

create or replace function public.sch_touch() returns trigger
language plpgsql set search_path = '' as $$
begin new.updated_at := now(); new.updated_by := auth.uid(); return new; end $$;
create or replace function public.sch_touch2() returns trigger
language plpgsql set search_path = '' as $$
begin new.updated_at := now(); return new; end $$;
create trigger sch_items_touch before insert or update on public.sch_items
  for each row execute function public.sch_touch();
create trigger sch_sum_touch before insert or update on public.sch_summaries
  for each row execute function public.sch_touch2();

-- 이 사람이 그 매장에서 맡은 역할: hq | owner | manager | staff | null
create or replace function public.sch_role(sid uuid) returns text
language sql stable security definer set search_path = '' as $$
  select coalesce(
    (select 'hq'::text from public.profiles p join public.stores s on s.id = sid
       where p.user_id = auth.uid() and p.role = 'hq' and s.is_hq limit 1),
    (select 'owner'::text from public.profiles p
       where p.user_id = auth.uid() and p.role = 'franchise' and p.store_id = sid limit 1),
    (select m.role from public.sch_members m where m.user_id = auth.uid() and m.store_id = sid limit 1)
  )
$$;

-- 급여 금액을 볼 수 있는 사람: 본사(finance 권한) · 점주 · 허용된 매니저
create or replace function public.sch_can_pay(sid uuid) returns boolean
language sql stable security definer set search_path = '' as $$
  select case public.sch_role(sid)
    when 'hq' then public.has_perm('finance')
    when 'owner' then true
    when 'manager' then coalesce((select m.can_pay from public.sch_members m where m.user_id = auth.uid() and m.store_id = sid), false)
    else false end
$$;

alter table public.sch_items     enable row level security;
alter table public.sch_summaries enable row level security;
alter table public.sch_members   enable row level security;

create policy sch_items_sel on public.sch_items for select to authenticated
  using (public.sch_role(store_id) is not null and (kind <> 'pay' or public.sch_can_pay(store_id)));
create policy sch_items_ins on public.sch_items for insert to authenticated
  with check (public.sch_role(store_id) in ('hq','owner','manager') and (kind <> 'pay' or public.sch_can_pay(store_id)));
create policy sch_items_upd on public.sch_items for update to authenticated
  using      (public.sch_role(store_id) in ('hq','owner','manager') and (kind <> 'pay' or public.sch_can_pay(store_id)))
  with check (public.sch_role(store_id) in ('hq','owner','manager') and (kind <> 'pay' or public.sch_can_pay(store_id)));

-- 본사는 모든 매장의 '집계'만 읽음. 쓰기는 그 매장 편집자만.
create policy sch_sum_sel on public.sch_summaries for select to authenticated
  using (public.is_hq() or public.sch_role(store_id) is not null);
create policy sch_sum_ins on public.sch_summaries for insert to authenticated
  with check (public.sch_role(store_id) in ('hq','owner','manager'));
create policy sch_sum_upd on public.sch_summaries for update to authenticated
  using (public.sch_role(store_id) in ('hq','owner','manager'))
  with check (public.sch_role(store_id) in ('hq','owner','manager'));

create policy sch_members_sel on public.sch_members for select to authenticated
  using (user_id = (select auth.uid()));

-- 화면에서 쓰는 함수들
create or replace function public.sch_my_stores()
returns table(id uuid, name text, is_hq boolean, role text, can_pay boolean, staff_id text)
language sql stable security definer set search_path = '' as $$
  select s.id, s.name, s.is_hq, public.sch_role(s.id), coalesce(public.sch_can_pay(s.id), false),
         (select m.staff_id from public.sch_members m where m.user_id = auth.uid() and m.store_id = s.id)
  from public.stores s
  where public.is_hq() or public.sch_role(s.id) is not null
  order by s.is_hq desc, s.created_at, s.name
$$;

create or replace function public.sch_create_store(p_name text) returns uuid
language plpgsql security definer set search_path = '' as $$
declare v uuid;
begin
  if not public.is_hq() then raise exception '본사 계정만 매장을 만들 수 있어요'; end if;
  if nullif(trim(coalesce(p_name,'')),'') is null then raise exception '매장 이름을 넣어주세요'; end if;
  insert into public.stores(name, is_hq) values (trim(p_name), false) returning id into v;
  return v;
end $$;

create or replace function public.sch_add_member(p_email text, p_store uuid, p_role text, p_pay boolean default false) returns void
language plpgsql security definer set search_path = '' as $$
declare u uuid; ps uuid; isq boolean;
begin
  if p_role not in ('owner','manager','staff') then raise exception '역할이 올바르지 않아요'; end if;
  select s.is_hq into isq from public.stores s where s.id = p_store;
  if isq is null then raise exception '없는 매장이에요'; end if;
  select id into u from auth.users where lower(email) = lower(trim(p_email));
  if u is null then raise exception '먼저 Supabase Authentication에서 % 계정을 만들어 주세요', p_email; end if;
  if p_role = 'owner' then
    if not public.is_hq() then raise exception '점주 연결은 본사만 할 수 있어요'; end if;
    if isq then raise exception '본점은 본사 계정을 써요. 가맹점에만 점주를 연결할 수 있어요'; end if;
    insert into public.profiles(user_id, store_id, role, display_name) values (u, p_store, 'franchise', split_part(trim(p_email),'@',1))
      on conflict (user_id) do nothing;
    select store_id into ps from public.profiles where user_id = u;
    if ps is distinct from p_store then raise exception '이 계정은 이미 다른 매장에 연결돼 있어요'; end if;
  else
    if public.sch_role(p_store) not in ('hq','owner') then raise exception '이 매장에 계정을 연결할 권한이 없어요'; end if;
    insert into public.sch_members(user_id, store_id, role, can_pay) values (u, p_store, p_role, coalesce(p_pay,false))
      on conflict (user_id, store_id) do update set role = excluded.role, can_pay = excluded.can_pay;
  end if;
end $$;

-- 함수 실행 권한: 로그인한 사람만 (익명 접근 차단)
revoke all on function public.sch_role(uuid), public.sch_can_pay(uuid), public.sch_my_stores(),
  public.sch_create_store(text), public.sch_add_member(text,uuid,text,boolean) from public, anon;
grant execute on function public.sch_role(uuid), public.sch_can_pay(uuid), public.sch_my_stores(),
  public.sch_create_store(text), public.sch_add_member(text,uuid,text,boolean) to authenticated;
revoke all on function public.sch_touch(), public.sch_touch2() from public, anon, authenticated;
revoke all on public.sch_items, public.sch_summaries, public.sch_members from anon;

-- 기존 매장·포지션을 근무표 설정으로 가져오기 (본점 8개, 가맹점 4개 등 그대로)
insert into public.sch_items(store_id, kind, id, data)
select s.id, 'cfg', 'store',
       jsonb_build_object('name', s.name, 'open','11:00','close','22:00','fullH',10,'pmH',5,'pmStart','17:00','fivePlus',true,'vis','week','target',25)
from public.stores s
on conflict do nothing;

insert into public.sch_items(store_id, kind, id, data)
select s.id, 'cfg', 'positions',
       (select jsonb_agg(jsonb_build_object('name', p.name,
                 'color', coalesce(c.color, '#6B7A8F'), 'req', jsonb_build_array(0,0,0,0,0,0,0)) order by p.sort_order)
        from public.positions p
        left join (values ('카운터','#3C5A86'),('홀','#2F6B3F'),('그릴','#B8621B'),('주방','#8A2E2E'),
                          ('장치','#5B3F86'),('장잡','#1F6F78'),('배송','#8A6A12'),('주차','#55605A')) c(n, color) on c.n = p.name
        where p.store_id = s.id)
from public.stores s
where exists (select 1 from public.positions p where p.store_id = s.id)
on conflict do nothing;