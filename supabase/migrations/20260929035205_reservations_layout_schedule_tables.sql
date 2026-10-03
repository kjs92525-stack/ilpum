-- 예약: 앱 구조에 맞게 다시 만들기 (아직 데이터 없음)
drop table public.reservations;
create table public.reservations (
  id uuid primary key default gen_random_uuid(),
  store_id uuid not null references public.stores(id),
  rdate date not null,
  rtime time not null,
  name text not null,
  phone text,
  size int not null check (size > 0),
  table_no text,
  note text,
  arrived boolean not null default false,
  created_by uuid default auth.uid() references auth.users(id),
  created_at timestamptz not null default now()
);
create index reservations_store_date_idx on public.reservations (store_id, rdate);

-- 테이블 배치 (층, 테이블)
create table public.floors (
  id uuid primary key default gen_random_uuid(),
  store_id uuid not null references public.stores(id),
  name text not null,
  sort_order int not null default 0
);
create index floors_store_idx on public.floors (store_id, sort_order);

create table public.dining_tables (
  id uuid primary key default gen_random_uuid(),
  store_id uuid not null references public.stores(id),
  floor_id uuid not null references public.floors(id) on delete cascade,
  no text not null,
  seats int not null default 4 check (seats > 0),
  x numeric not null default 4,
  y numeric not null default 4,
  unique (store_id, no)
);
create index dining_tables_floor_idx on public.dining_tables (floor_id);

-- 스케줄 (포지션, 근무자, 날짜별 근무)
create table public.positions (
  id uuid primary key default gen_random_uuid(),
  store_id uuid not null references public.stores(id),
  name text not null,
  sort_order int not null default 0,
  unique (store_id, name)
);

create table public.staff (
  id uuid primary key default gen_random_uuid(),
  store_id uuid not null references public.stores(id),
  name text not null,
  fixed_off smallint[] not null default '{}',
  active boolean not null default true,
  sort_order int not null default 0,
  unique (store_id, name)
);

create table public.shifts (
  id uuid primary key default gen_random_uuid(),
  store_id uuid not null references public.stores(id),
  work_date date not null,
  position text not null,
  staff_id uuid references public.staff(id) on delete set null,
  name text not null,
  part text not null default '' check (part in ('', '오후')),
  day_hire boolean not null default false,
  created_at timestamptz not null default now(),
  unique (store_id, work_date, name)
);
create index shifts_store_date_idx on public.shifts (store_id, work_date);

-- 권한 규칙: 본점은 전체, 가맹점은 자기 매장만
do $$
declare t text;
begin
  foreach t in array array['reservations','floors','dining_tables','positions','staff','shifts'] loop
    execute format('alter table public.%I enable row level security', t);
    execute format('revoke all on public.%I from anon', t);
    execute format($p$create policy %I on public.%I for all to authenticated
      using ((select public.is_hq()) or store_id = (select public.my_store_id()))
      with check ((select public.is_hq()) or store_id = (select public.my_store_id()))$p$, t || '_all', t);
  end loop;
end $$;

-- 실시간 반영
alter publication supabase_realtime add table public.reservations, public.shifts;

-- 시작용 포지션
insert into public.positions (store_id, name, sort_order)
select s.id, p.name, p.ord from public.stores s
join (values ('카운터',1),('홀',2),('그릴',3),('주방',4),('장치',5),('주차',6),('장잡',7),('배송',8)) as p(name, ord) on true
where s.is_hq;
insert into public.positions (store_id, name, sort_order)
select s.id, p.name, p.ord from public.stores s
join (values ('카운터',1),('홀',2),('그릴',3),('주방',4)) as p(name, ord) on true
where not s.is_hq;

-- 시작용 테이블 배치 (앱에서 자유롭게 옮기고 고칠 수 있어요)
do $$
declare hq uuid; fr uuid; f1 uuid; f2 uuid; f3 uuid; ff uuid; i int; n int;
  fseats int[] := array[4,4,4,6,6,2,4,4,4,4];
begin
  select id into hq from public.stores where is_hq limit 1;
  select id into fr from public.stores where not is_hq order by created_at limit 1;
  insert into public.floors (store_id, name, sort_order) values (hq, '1층', 1) returning id into f1;
  insert into public.floors (store_id, name, sort_order) values (hq, '2층', 2) returning id into f2;
  insert into public.floors (store_id, name, sort_order) values (hq, '룸', 3) returning id into f3;
  for i in 0..23 loop
    n := i + 1;
    insert into public.dining_tables (store_id, floor_id, no, seats, x, y)
    values (hq, f1, n::text, case when n between 6 and 10 then 6 else 4 end, 5 + (i % 6) * 15.5, 8 + (i / 6) * 22);
  end loop;
  for i in 0..11 loop
    n := 42 + i;
    insert into public.dining_tables (store_id, floor_id, no, seats, x, y)
    values (hq, f2, n::text, case when n <= 45 or n >= 51 then 6 else 4 end, 5 + (i % 6) * 15.5, 14 + (i / 6) * 30);
  end loop;
  for i in 0..3 loop
    insert into public.dining_tables (store_id, floor_id, no, seats, x, y)
    values (hq, f3, 'R' || (i + 1), 10, 10 + (i % 2) * 42, 16 + (i / 2) * 40);
  end loop;
  if fr is not null then
    insert into public.floors (store_id, name, sort_order) values (fr, '홀', 1) returning id into ff;
    for i in 0..9 loop
      insert into public.dining_tables (store_id, floor_id, no, seats, x, y)
      values (fr, ff, (i + 1)::text, fseats[i + 1], 6 + (i % 5) * 18, 16 + (i / 5) * 32);
    end loop;
  end if;
end $$;