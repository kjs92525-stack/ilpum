-- 근무자 기본 출근(종일/오후)
alter table public.staff
  add column default_part text not null default '' check (default_part in ('', '오후'));

-- 근무별 시간과 메모 (예: 11시 출근)
alter table public.shifts
  add column hours numeric check (hours is null or (hours > 0 and hours <= 24)),
  add column note text;

-- 시급 이력: 적용 시작일부터 새 시급으로 계산
create table public.staff_rates (
  id uuid primary key default gen_random_uuid(),
  store_id uuid not null references public.stores(id),
  staff_id uuid not null references public.staff(id) on delete cascade,
  from_date date not null,
  hourly int not null check (hourly >= 0),
  unique (staff_id, from_date)
);
create index staff_rates_store_idx on public.staff_rates (store_id);

-- 근무 하루치 급여를 직접 적은 금액 (당일알바 일당 등)
create table public.shift_pay (
  shift_id uuid primary key references public.shifts(id) on delete cascade,
  store_id uuid not null references public.stores(id),
  work_date date not null,
  day_pay int not null check (day_pay >= 0)
);
create index shift_pay_store_date_idx on public.shift_pay (store_id, work_date);

-- 급여 정보는 그 매장 계정만 볼 수 있어요 (본사 계정도 다른 매장 급여는 볼 수 없음)
alter table public.staff_rates enable row level security;
alter table public.shift_pay enable row level security;
revoke all on public.staff_rates, public.shift_pay from anon;
create policy staff_rates_own on public.staff_rates for all to authenticated
  using (store_id = (select public.my_store_id()))
  with check (store_id = (select public.my_store_id()));
create policy shift_pay_own on public.shift_pay for all to authenticated
  using (store_id = (select public.my_store_id()))
  with check (store_id = (select public.my_store_id()));