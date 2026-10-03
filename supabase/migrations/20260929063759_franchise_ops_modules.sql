-- ===== 본사 직원 권한 =====
alter table public.profiles add column perms text[] not null default '{}';

-- 비어 있으면 전체 관리자, 아니면 적힌 권한만 (order, finance, notice, ops, admin)
create function public.has_perm(p text) returns boolean
language sql stable security definer set search_path = ''
as $$
  select exists (
    select 1 from public.profiles
    where user_id = auth.uid() and role = 'hq'
      and (cardinality(perms) = 0 or 'admin' = any(perms) or p = any(perms))
  )
$$;
revoke execute on function public.has_perm(text) from public, anon;
grant execute on function public.has_perm(text) to authenticated;

-- ===== 품목 단가, 품절, 매장별 단가 =====
alter table public.products
  add column price int not null default 0 check (price >= 0),
  add column sold_out boolean not null default false,
  add column notice text;

create table public.product_price_log (
  id bigint generated always as identity primary key,
  product_id uuid not null references public.products(id) on delete cascade,
  price int not null,
  changed_at timestamptz not null default now(),
  changed_by uuid default auth.uid()
);
alter table public.product_price_log enable row level security;
revoke all on public.product_price_log from anon;
create policy product_price_log_hq on public.product_price_log for select to authenticated using ((select public.is_hq()));

create function public.log_product_price() returns trigger
language plpgsql security definer set search_path = ''
as $$
begin
  if tg_op = 'INSERT' or new.price is distinct from old.price then
    insert into public.product_price_log (product_id, price, changed_by) values (new.id, new.price, auth.uid());
  end if;
  return null;
end $$;
create trigger products_price_log after insert or update of price on public.products
  for each row execute function public.log_product_price();

create table public.store_prices (
  store_id uuid not null references public.stores(id) on delete cascade,
  product_id uuid not null references public.products(id) on delete cascade,
  price int not null check (price >= 0),
  primary key (store_id, product_id)
);
create index store_prices_product_idx on public.store_prices (product_id);
alter table public.store_prices enable row level security;
revoke all on public.store_prices from anon;
create policy store_prices_select on public.store_prices for select to authenticated
  using ((select public.is_hq()) or store_id = (select public.my_store_id()));
create policy store_prices_write on public.store_prices for all to authenticated
  using ((select public.has_perm('finance'))) with check ((select public.has_perm('finance')));

drop policy products_hq_write on public.products;
create policy products_write on public.products for all to authenticated
  using ((select public.has_perm('order')) or (select public.has_perm('finance')))
  with check ((select public.has_perm('order')) or (select public.has_perm('finance')));

-- 발주 품목에 그때의 단가와 금액 기록
alter table public.order_items
  add column unit_price int not null default 0 check (unit_price >= 0),
  add column amount bigint generated always as (round(qty * unit_price)::bigint) stored;

-- 발주 등록은 서버 함수로만 (단가를 서버가 정해서 조작 불가)
drop policy orders_insert_own on public.orders;
drop policy order_items_insert_own on public.order_items;
drop policy orders_hq_update on public.orders;
drop policy orders_hq_delete on public.orders;
create policy orders_update on public.orders for update to authenticated
  using ((select public.has_perm('order'))) with check ((select public.has_perm('order')));
create policy orders_delete on public.orders for delete to authenticated
  using ((select public.has_perm('order')));

create or replace function public.create_order(p_memo text, p_items jsonb) returns bigint
language plpgsql security definer set search_path = ''
as $$
declare v_id uuid; v_no bigint; v_store uuid; v_bad text;
begin
  v_store := public.my_store_id();
  if v_store is null then raise exception '매장이 연결되지 않은 계정이에요'; end if;
  if p_items is null or jsonb_typeof(p_items) <> 'array' or jsonb_array_length(p_items) = 0 then
    raise exception '품목이 없어요';
  end if;
  if exists (select 1 from jsonb_to_recordset(p_items) as x(product_id uuid, qty numeric) where x.qty is null or x.qty <= 0) then
    raise exception '수량을 확인해 주세요';
  end if;
  select string_agg(p.name, ', ') into v_bad
    from jsonb_to_recordset(p_items) as x(product_id uuid, qty numeric)
    join public.products p on p.id = x.product_id
    where p.sold_out or not p.active;
  if v_bad is not null then raise exception '품절이거나 판매하지 않는 품목이 있어요: %', v_bad; end if;
  insert into public.orders (store_id, memo, created_by)
    values (v_store, nullif(trim(coalesce(p_memo, '')), ''), auth.uid())
    returning id, no into v_id, v_no;
  insert into public.order_items (order_id, product_id, qty, unit_price)
    select v_id, x.product_id, x.qty, coalesce(sp.price, p.price)
    from jsonb_to_recordset(p_items) as x(product_id uuid, qty numeric)
    join public.products p on p.id = x.product_id
    left join public.store_prices sp on sp.store_id = v_store and sp.product_id = x.product_id;
  return v_no;
end $$;
revoke execute on function public.create_order(text, jsonb) from public, anon;
grant execute on function public.create_order(text, jsonb) to authenticated;

-- ===== 정산: 입금·조정 =====
create table public.payments (
  id uuid primary key default gen_random_uuid(),
  store_id uuid not null references public.stores(id),
  paid_on date not null default current_date,
  amount bigint not null check (amount <> 0),
  method text,
  memo text,
  created_by uuid default auth.uid(),
  created_at timestamptz not null default now()
);
create index payments_store_idx on public.payments (store_id, paid_on);
alter table public.payments enable row level security;
revoke all on public.payments from anon;
create policy payments_select on public.payments for select to authenticated
  using ((select public.is_hq()) or store_id = (select public.my_store_id()));
create policy payments_write on public.payments for all to authenticated
  using ((select public.has_perm('finance'))) with check ((select public.has_perm('finance')));

-- 매장별 미수금 요약 (출고·완료된 발주를 청구로 봄, 입금은 먼저 생긴 청구부터 갚는 것으로 계산)
create function public.store_balances()
returns table (store_id uuid, store_name text, is_hq boolean, charged bigint, paid bigint, balance bigint,
               month_charged bigint, last_order timestamptz, last_paid date, oldest_unpaid timestamptz)
language sql stable security invoker set search_path = ''
as $$
  with ch as (
    select o.store_id, o.id, o.created_at, coalesce(sum(i.amount), 0)::bigint as amt
    from public.orders o left join public.order_items i on i.order_id = o.id
    where o.status in ('출고', '완료')
    group by o.store_id, o.id, o.created_at
  ), pay as (
    select p.store_id, sum(p.amount)::bigint as paid, max(p.paid_on) filter (where p.amount > 0) as last_paid
    from public.payments p group by p.store_id
  ), cum as (
    select ch.*, sum(ch.amt) over (partition by ch.store_id order by ch.created_at, ch.id) as c from ch
  ), tot as (
    select ch.store_id, sum(ch.amt)::bigint as charged,
      coalesce(sum(ch.amt) filter (where ch.created_at >= (date_trunc('month', now() at time zone 'Asia/Seoul') at time zone 'Asia/Seoul')), 0)::bigint as month_charged
    from ch group by ch.store_id
  )
  select s.id, s.name, s.is_hq,
    coalesce(tot.charged, 0), coalesce(pay.paid, 0), coalesce(tot.charged, 0) - coalesce(pay.paid, 0),
    coalesce(tot.month_charged, 0),
    (select max(o.created_at) from public.orders o where o.store_id = s.id and o.status <> '취소'),
    pay.last_paid,
    (select min(cum.created_at) from cum where cum.store_id = s.id and cum.c > coalesce(pay.paid, 0))
  from public.stores s
  left join tot on tot.store_id = s.id
  left join pay on pay.store_id = s.id
  order by s.is_hq desc, s.name
$$;

create function public.store_balance_before(p_store uuid, p_date date) returns bigint
language sql stable security invoker set search_path = ''
as $$
  select (
    coalesce((select sum(i.amount) from public.orders o join public.order_items i on i.order_id = o.id
              where o.store_id = p_store and o.status in ('출고', '완료')
                and o.created_at < (p_date::timestamp at time zone 'Asia/Seoul')), 0)
    - coalesce((select sum(p.amount) from public.payments p where p.store_id = p_store and p.paid_on < p_date), 0)
  )::bigint
$$;

create function public.store_ledger(p_store uuid, p_from date, p_to date)
returns table (at timestamptz, kind text, ref text, charge bigint, paid bigint, memo text, pay_id uuid)
language sql stable security invoker set search_path = ''
as $$
  select * from (
    select o.created_at, '발주'::text,
      o.no::text || '번  ' || coalesce(string_agg(pr.name || ' ' || rtrim(to_char(i.qty, 'FM999999990.99'), '.'), ', ' order by pr.sort_order), ''),
      coalesce(sum(i.amount), 0)::bigint, 0::bigint, o.status, null::uuid
    from public.orders o
    left join public.order_items i on i.order_id = o.id
    left join public.products pr on pr.id = i.product_id
    where o.store_id = p_store and o.status in ('출고', '완료')
      and o.created_at >= (p_from::timestamp at time zone 'Asia/Seoul')
      and o.created_at < ((p_to + 1)::timestamp at time zone 'Asia/Seoul')
    group by o.id
    union all
    select (p.paid_on::timestamp at time zone 'Asia/Seoul') + interval '23 hours 59 minutes',
      case when p.amount > 0 then '입금' else '추가 청구' end, coalesce(p.method, ''), 0::bigint, p.amount, p.memo, p.id
    from public.payments p
    where p.store_id = p_store and p.paid_on between p_from and p_to
  ) t order by 1
$$;
revoke execute on function public.store_balances() from public, anon;
revoke execute on function public.store_balance_before(uuid, date) from public, anon;
revoke execute on function public.store_ledger(uuid, date, date) from public, anon;
grant execute on function public.store_balances() to authenticated;
grant execute on function public.store_balance_before(uuid, date) to authenticated;
grant execute on function public.store_ledger(uuid, date, date) to authenticated;

-- ===== 설정 (발주 마감 안내, 점검 항목, 오픈 기본 할 일) =====
create table public.app_settings (
  key text primary key,
  value jsonb not null,
  updated_at timestamptz not null default now()
);
alter table public.app_settings enable row level security;
revoke all on public.app_settings from anon;
create policy app_settings_select on public.app_settings for select to authenticated using (true);
create policy app_settings_write on public.app_settings for all to authenticated
  using ((select public.is_hq())) with check ((select public.is_hq()));

-- ===== 공지·매뉴얼 =====
create table public.notices (
  id uuid primary key default gen_random_uuid(),
  kind text not null default '공지' check (kind in ('공지', '매뉴얼')),
  category text,
  title text not null,
  body text not null default '',
  pinned boolean not null default false,
  created_by uuid default auth.uid(),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
alter table public.notices enable row level security;
revoke all on public.notices from anon;
create policy notices_select on public.notices for select to authenticated using (true);
create policy notices_write on public.notices for all to authenticated
  using ((select public.has_perm('notice'))) with check ((select public.has_perm('notice')));

create table public.notice_reads (
  notice_id uuid not null references public.notices(id) on delete cascade,
  user_id uuid not null default auth.uid() references auth.users(id) on delete cascade,
  store_id uuid not null references public.stores(id),
  read_at timestamptz not null default now(),
  primary key (notice_id, user_id)
);
create index notice_reads_store_idx on public.notice_reads (store_id);
alter table public.notice_reads enable row level security;
revoke all on public.notice_reads from anon;
create policy notice_reads_select on public.notice_reads for select to authenticated
  using (user_id = (select auth.uid()) or (select public.is_hq()));
create policy notice_reads_insert on public.notice_reads for insert to authenticated
  with check (user_id = (select auth.uid()) and store_id = (select public.my_store_id()));

-- ===== 문의·AS =====
create table public.tickets (
  id uuid primary key default gen_random_uuid(),
  no bigint generated always as identity (start with 1),
  store_id uuid not null references public.stores(id),
  category text not null default '기타',
  title text not null,
  body text not null default '',
  photos text[] not null default '{}',
  status text not null default '접수' check (status in ('접수', '처리중', '완료')),
  reply text,
  created_by uuid default auth.uid(),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index tickets_store_idx on public.tickets (store_id, created_at desc);
alter table public.tickets enable row level security;
revoke all on public.tickets from anon;
create policy tickets_select on public.tickets for select to authenticated
  using ((select public.is_hq()) or store_id = (select public.my_store_id()));
create policy tickets_insert on public.tickets for insert to authenticated
  with check (store_id = (select public.my_store_id()) and status = '접수' and reply is null);
create policy tickets_update on public.tickets for update to authenticated
  using ((select public.has_perm('notice'))) with check ((select public.has_perm('notice')));
create policy tickets_delete on public.tickets for delete to authenticated
  using ((select public.has_perm('notice')));

-- ===== 일 매출 보고 =====
create table public.sales_reports (
  store_id uuid not null references public.stores(id),
  sale_date date not null,
  amount bigint not null check (amount >= 0),
  customers int check (customers is null or customers >= 0),
  memo text,
  updated_at timestamptz not null default now(),
  primary key (store_id, sale_date)
);
alter table public.sales_reports enable row level security;
revoke all on public.sales_reports from anon;
create policy sales_reports_all on public.sales_reports for all to authenticated
  using ((select public.is_hq()) or store_id = (select public.my_store_id()))
  with check ((select public.is_hq()) or store_id = (select public.my_store_id()));

-- ===== 매장 점검 =====
create table public.inspections (
  id uuid primary key default gen_random_uuid(),
  store_id uuid not null references public.stores(id),
  visit_date date not null default current_date,
  inspector text,
  items jsonb not null default '[]',
  score int check (score between 0 and 100),
  memo text,
  created_by uuid default auth.uid(),
  created_at timestamptz not null default now()
);
create index inspections_store_idx on public.inspections (store_id, visit_date desc);
alter table public.inspections enable row level security;
revoke all on public.inspections from anon;
create policy inspections_select on public.inspections for select to authenticated
  using ((select public.is_hq()) or store_id = (select public.my_store_id()));
create policy inspections_write on public.inspections for all to authenticated
  using ((select public.has_perm('ops'))) with check ((select public.has_perm('ops')));

-- ===== 신규 오픈 준비 =====
create table public.openings (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  target_date date not null,
  status text not null default '준비중' check (status in ('준비중', '오픈', '보류')),
  memo text,
  created_at timestamptz not null default now()
);
create table public.opening_tasks (
  id uuid primary key default gen_random_uuid(),
  opening_id uuid not null references public.openings(id) on delete cascade,
  title text not null,
  due_date date,
  done boolean not null default false,
  sort_order int not null default 0
);
create index opening_tasks_opening_idx on public.opening_tasks (opening_id);
alter table public.openings enable row level security;
alter table public.opening_tasks enable row level security;
revoke all on public.openings, public.opening_tasks from anon;
create policy openings_select on public.openings for select to authenticated using ((select public.is_hq()));
create policy openings_write on public.openings for all to authenticated
  using ((select public.has_perm('ops'))) with check ((select public.has_perm('ops')));
create policy opening_tasks_select on public.opening_tasks for select to authenticated using ((select public.is_hq()));
create policy opening_tasks_write on public.opening_tasks for all to authenticated
  using ((select public.has_perm('ops'))) with check ((select public.has_perm('ops')));

-- ===== 협력업체 계약 =====
create table public.contracts (
  id uuid primary key default gen_random_uuid(),
  partner text not null,
  title text,
  store_id uuid references public.stores(id) on delete set null,
  start_date date,
  end_date date,
  monthly_fee bigint check (monthly_fee is null or monthly_fee >= 0),
  memo text,
  created_at timestamptz not null default now()
);
alter table public.contracts enable row level security;
revoke all on public.contracts from anon;
create policy contracts_select on public.contracts for select to authenticated using ((select public.is_hq()));
create policy contracts_write on public.contracts for all to authenticated
  using ((select public.has_perm('ops'))) with check ((select public.has_perm('ops')));

-- ===== 변경 기록 =====
create table public.audit_log (
  id bigint generated always as identity primary key,
  at timestamptz not null default now(),
  actor uuid,
  tbl text not null,
  row_id text,
  action text not null,
  old jsonb,
  new jsonb
);
create index audit_log_at_idx on public.audit_log (id desc);
alter table public.audit_log enable row level security;
revoke all on public.audit_log from anon, authenticated;

create function public.audit() returns trigger
language plpgsql security definer set search_path = ''
as $$
declare r jsonb := coalesce(to_jsonb(new), to_jsonb(old));
begin
  insert into public.audit_log (actor, tbl, row_id, action, old, new)
  values (auth.uid(), tg_table_name,
          coalesce(r ->> 'id', (r ->> 'store_id') || ':' || coalesce(r ->> 'product_id', '')),
          tg_op,
          case when tg_op <> 'INSERT' then to_jsonb(old) end,
          case when tg_op <> 'DELETE' then to_jsonb(new) end);
  return null;
end $$;
create trigger audit_orders after insert or update or delete on public.orders for each row execute function public.audit();
create trigger audit_products after insert or update or delete on public.products for each row execute function public.audit();
create trigger audit_store_prices after insert or update or delete on public.store_prices for each row execute function public.audit();
create trigger audit_payments after insert or update or delete on public.payments for each row execute function public.audit();
create trigger audit_contracts after insert or update or delete on public.contracts for each row execute function public.audit();
create trigger audit_notices after insert or update or delete on public.notices for each row execute function public.audit();
create trigger audit_tickets after update or delete on public.tickets for each row execute function public.audit();
create trigger audit_profiles after update on public.profiles for each row execute function public.audit();

create function public.audit_list(p_limit int default 200)
returns table (at timestamptz, email text, tbl text, action text, old jsonb, new jsonb)
language plpgsql stable security definer set search_path = ''
as $$
begin
  if not public.has_perm('admin') then raise exception '권한이 없어요'; end if;
  return query
    select a.at, u.email::text, a.tbl, a.action, a.old, a.new
    from public.audit_log a left join auth.users u on u.id = a.actor
    order by a.id desc limit least(greatest(coalesce(p_limit, 200), 1), 500);
end $$;

-- 직원 목록과 권한 바꾸기 (관리자만)
create function public.list_staff()
returns table (user_id uuid, email text, role text, store_name text, perms text[], display_name text)
language plpgsql stable security definer set search_path = ''
as $$
begin
  if not public.has_perm('admin') then raise exception '권한이 없어요'; end if;
  return query
    select p.user_id, u.email::text, p.role, s.name, p.perms, p.display_name
    from public.profiles p join auth.users u on u.id = p.user_id join public.stores s on s.id = p.store_id
    order by p.role, s.name, u.email;
end $$;

create function public.set_perms(p_user uuid, p_perms text[]) returns void
language plpgsql security definer set search_path = ''
as $$
begin
  if not public.has_perm('admin') then raise exception '권한이 없어요'; end if;
  if exists (select 1 from unnest(coalesce(p_perms, '{}')) x where x not in ('order', 'finance', 'notice', 'ops', 'admin')) then
    raise exception '알 수 없는 권한이에요';
  end if;
  update public.profiles set perms = coalesce(p_perms, '{}') where user_id = p_user and role = 'hq';
  if not exists (select 1 from public.profiles where role = 'hq' and (cardinality(perms) = 0 or 'admin' = any(perms))) then
    raise exception '관리자가 최소 한 명은 있어야 해요';
  end if;
end $$;

revoke execute on function public.audit_list(int) from public, anon;
revoke execute on function public.list_staff() from public, anon;
revoke execute on function public.set_perms(uuid, text[]) from public, anon;
grant execute on function public.audit_list(int) to authenticated;
grant execute on function public.list_staff() to authenticated;
grant execute on function public.set_perms(uuid, text[]) to authenticated;
revoke execute on function public.audit() from public, anon, authenticated;
revoke execute on function public.log_product_price() from public, anon, authenticated;

-- 실시간 반영
alter publication supabase_realtime add table public.notices, public.tickets, public.payments;

-- 기본 설정값
insert into public.app_settings (key, value) values
 ('order_cutoff', to_jsonb('매일 오후 3시까지 발주하면 다음 날 오전에 도착해요'::text)),
 ('inspect_items', '["홀·테이블 청결","주방 위생 (조리대·바닥·후드)","식자재 보관과 유통기한","개인 위생 (복장·위생모·장갑)","장어 손질과 굽기 기준","소스 보관과 사용 기준","손님 응대와 서비스","화장실 청결","소방·안전 설비"]'::jsonb),
 ('open_tasks', '[[90,"상권 분석과 입지 확정"],[75,"가맹계약 체결"],[70,"임대차 계약"],[60,"인테리어 설계 확정"],[45,"인테리어 공사 시작"],[40,"영업신고·사업자등록 준비"],[30,"주방 설비·집기 발주"],[21,"POS·카드단말기 설치"],[21,"직원 채용"],[14,"본사 교육 (조리·서비스)"],[10,"간판·홍보물 설치"],[7,"첫 발주 (장어·소스)"],[5,"보건증·위생 교육 확인"],[3,"시식과 리허설 영업"],[0,"오픈"]]'::jsonb);