-- 매장
create table public.stores (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  is_hq boolean not null default false,
  created_at timestamptz not null default now()
);
create unique index stores_one_hq on public.stores (is_hq) where is_hq;

-- 사용자-매장 연결
create table public.profiles (
  user_id uuid primary key references auth.users(id) on delete cascade,
  store_id uuid not null references public.stores(id),
  role text not null check (role in ('hq','franchise')),
  display_name text,
  created_at timestamptz not null default now()
);
create index profiles_store_id_idx on public.profiles (store_id);

-- 권한 확인 함수
create function public.my_store_id() returns uuid
language sql stable security definer set search_path = ''
as $$ select store_id from public.profiles where user_id = auth.uid() $$;

create function public.is_hq() returns boolean
language sql stable security definer set search_path = ''
as $$ select exists (select 1 from public.profiles where user_id = auth.uid() and role = 'hq') $$;

revoke execute on function public.my_store_id() from public, anon;
revoke execute on function public.is_hq() from public, anon;
grant execute on function public.my_store_id() to authenticated;
grant execute on function public.is_hq() to authenticated;

-- 발주 품목
create table public.products (
  id uuid primary key default gen_random_uuid(),
  name text not null unique,
  unit text,
  sort_order int not null default 0,
  active boolean not null default true
);

-- 발주
create table public.orders (
  id uuid primary key default gen_random_uuid(),
  store_id uuid not null references public.stores(id),
  status text not null default '접수' check (status in ('접수','확인','출고','완료','취소')),
  memo text,
  created_by uuid default auth.uid() references auth.users(id),
  created_at timestamptz not null default now()
);
create index orders_store_id_idx on public.orders (store_id, created_at desc);

create table public.order_items (
  id uuid primary key default gen_random_uuid(),
  order_id uuid not null references public.orders(id) on delete cascade,
  product_id uuid not null references public.products(id),
  qty numeric not null check (qty > 0)
);
create index order_items_order_id_idx on public.order_items (order_id);

-- 예약 (2단계용 기본 틀)
create table public.reservations (
  id uuid primary key default gen_random_uuid(),
  store_id uuid not null references public.stores(id),
  customer_name text not null,
  phone text,
  party_size int,
  reserved_at timestamptz not null,
  memo text,
  status text not null default '예약',
  created_at timestamptz not null default now()
);
create index reservations_store_id_idx on public.reservations (store_id, reserved_at);

-- RLS 활성화
alter table public.stores enable row level security;
alter table public.profiles enable row level security;
alter table public.products enable row level security;
alter table public.orders enable row level security;
alter table public.order_items enable row level security;
alter table public.reservations enable row level security;

-- 익명 접근 차단
revoke all on all tables in schema public from anon;

-- stores: 본사는 전체, 가맹점은 자기 매장만 (쓰기는 관리자 SQL로만)
create policy stores_select on public.stores for select to authenticated
  using ((select public.is_hq()) or id = (select public.my_store_id()));

-- profiles: 본인 또는 본사만 조회 (권한 상승 방지를 위해 클라이언트 쓰기 없음)
create policy profiles_select on public.profiles for select to authenticated
  using (user_id = (select auth.uid()) or (select public.is_hq()));

-- products: 로그인 사용자 조회, 본사만 관리
create policy products_select on public.products for select to authenticated using (true);
create policy products_hq_write on public.products for all to authenticated
  using ((select public.is_hq())) with check ((select public.is_hq()));

-- orders: 가맹점은 자기 매장 조회 + '접수' 상태로만 등록, 본사는 전체 관리
create policy orders_select on public.orders for select to authenticated
  using ((select public.is_hq()) or store_id = (select public.my_store_id()));
create policy orders_insert_own on public.orders for insert to authenticated
  with check (store_id = (select public.my_store_id()) and status = '접수');
create policy orders_hq_update on public.orders for update to authenticated
  using ((select public.is_hq())) with check ((select public.is_hq()));
create policy orders_hq_delete on public.orders for delete to authenticated
  using ((select public.is_hq()));

-- order_items: 부모 발주의 매장 기준
create policy order_items_select on public.order_items for select to authenticated
  using (exists (select 1 from public.orders o where o.id = order_id
    and ((select public.is_hq()) or o.store_id = (select public.my_store_id()))));
create policy order_items_insert_own on public.order_items for insert to authenticated
  with check (exists (select 1 from public.orders o where o.id = order_id
    and o.store_id = (select public.my_store_id()) and o.status = '접수'));
create policy order_items_hq_write on public.order_items for all to authenticated
  using ((select public.is_hq())) with check ((select public.is_hq()));

-- reservations: 본사 전체, 가맹점은 자기 매장만
create policy reservations_all on public.reservations for all to authenticated
  using ((select public.is_hq()) or store_id = (select public.my_store_id()))
  with check ((select public.is_hq()) or store_id = (select public.my_store_id()));

-- 초기 데이터
insert into public.stores (name, is_hq) values ('일품집 본점', true), ('가맹점 1', false);
insert into public.products (name, sort_order) values
  ('장어', 1), ('간장소스', 2), ('고추장소스', 3), ('장어탕', 4);