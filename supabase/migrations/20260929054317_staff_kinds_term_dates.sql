-- 근무자 종류: regular(직원·고정알바), flex(매주 스케줄이 바뀌는 알바), term(기간을 정해 일하는 알바)
alter table public.staff
  add column kind text not null default 'regular' check (kind in ('regular', 'flex', 'term')),
  add column start_date date,
  add column end_date date,
  add constraint staff_term_dates_ok check (kind <> 'term' or (start_date is not null and end_date is not null and end_date >= start_date));