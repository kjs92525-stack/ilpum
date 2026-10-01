-- 발주(창고 발주): 예전 발주 사이트의 wh_items / wh_orders 를 새 서버로. 매장별로 나뉨, 로그인한 사람만.
create table if not exists public.wh_items (
  store_id uuid not null references public.stores(id) on delete cascade,
  id text not null,
  category text not null default '',
  name text not null default '',
  stock text not null default '',
  buy_url text,
  links jsonb not null default '[]'::jsonb,
  sort integer not null default 0,
  updated_at timestamptz not null default now(),
  primary key (store_id, id)
);
create table if not exists public.wh_orders (
  store_id uuid not null references public.stores(id) on delete cascade,
  code text not null,
  created_at timestamptz not null default now(),
  status text not null default 'open' check (status in ('open','done')),
  lines jsonb not null default '[]'::jsonb,
  updated_at timestamptz not null default now(),
  primary key (store_id, code)
);
create index if not exists wh_orders_created on public.wh_orders (store_id, created_at desc);
alter table public.wh_items enable row level security;
alter table public.wh_orders enable row level security;
-- 품목: 그 매장 사람은 읽기, 본사·점주·매니저만 고치기
create policy wh_items_sel on public.wh_items for select to authenticated using (public.sch_role(store_id) is not null);
create policy wh_items_ins on public.wh_items for insert to authenticated with check (public.sch_role(store_id) in ('hq','owner','manager'));
create policy wh_items_upd on public.wh_items for update to authenticated using (public.sch_role(store_id) in ('hq','owner','manager')) with check (public.sch_role(store_id) in ('hq','owner','manager'));
create policy wh_items_del on public.wh_items for delete to authenticated using (public.sch_role(store_id) in ('hq','owner','manager'));
-- 발주: 그 매장 사람은 모두 넣고·보고·체크 (지우기는 본사·점주·매니저)
create policy wh_orders_sel on public.wh_orders for select to authenticated using (public.sch_role(store_id) is not null);
create policy wh_orders_ins on public.wh_orders for insert to authenticated with check (public.sch_role(store_id) is not null);
create policy wh_orders_upd on public.wh_orders for update to authenticated using (public.sch_role(store_id) is not null) with check (public.sch_role(store_id) is not null);
create policy wh_orders_del on public.wh_orders for delete to authenticated using (public.sch_role(store_id) in ('hq','owner','manager'));
