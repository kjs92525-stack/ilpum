-- 공지사항(본사가 쓰고 모든 매장이 읽음) + 게시판(점주↔본사 1:1 상담: 점주 글은 본사와 그 매장 사람만 보임, 점주끼리는 서로 안 보임)
create or replace function public.has_any_role() returns boolean
 language sql stable security definer set search_path to '' as $$
  select exists(select 1 from public.profiles where user_id = auth.uid())
      or exists(select 1 from public.sch_members where user_id = auth.uid())
$$;

create table if not exists public.board_notices (
  id uuid primary key default gen_random_uuid(),
  title text not null check (length(btrim(title)) between 1 and 100),
  body text not null default '' check (length(body) <= 5000),
  pinned boolean not null default false,
  author_id uuid references auth.users(id) on delete set null default auth.uid(),
  created_at timestamptz not null default now()
);
alter table public.board_notices enable row level security;
create policy bn_sel on public.board_notices for select to authenticated using (public.has_any_role());
create policy bn_ins on public.board_notices for insert to authenticated with check (public.is_hq());
create policy bn_upd on public.board_notices for update to authenticated using (public.is_hq()) with check (public.is_hq());
create policy bn_del on public.board_notices for delete to authenticated using (public.is_hq());

create table if not exists public.board_msgs (
  id uuid primary key default gen_random_uuid(),
  store_id uuid not null references public.stores(id) on delete cascade,
  author_id uuid not null default auth.uid() references auth.users(id) on delete cascade,
  from_hq boolean not null default false,
  body text not null check (length(btrim(body)) between 1 and 2000),
  created_at timestamptz not null default now(),
  hq_read boolean not null default false,
  store_read boolean not null default false
);
create index if not exists board_msgs_store on public.board_msgs (store_id, created_at);
alter table public.board_msgs enable row level security;
-- 읽기: 본사(모든 매장) 또는 그 매장의 점주·매니저 (다른 매장 점주 글은 안 보임)
create policy bm_sel on public.board_msgs for select to authenticated using (public.is_hq() or public.sch_role(store_id) in ('owner','manager'));
-- 쓰기: 점주·매니저는 자기 매장에 "점주 글", 본사는 아무 매장에 "본사 답글"
create policy bm_ins on public.board_msgs for insert to authenticated with check (
  author_id = auth.uid() and (
    (from_hq = false and public.sch_role(store_id) in ('owner','manager'))
    or (from_hq = true and public.is_hq())));
-- 고치기·지우기 정책 없음: 읽음 표시는 함수로만

create or replace function public.board_mark_read(p_store uuid) returns void
 language plpgsql security definer set search_path to '' as $f$
begin
  if public.is_hq() then
    update public.board_msgs set hq_read = true where store_id = p_store and from_hq = false and not hq_read;
  elsif public.sch_role(p_store) in ('owner','manager') then
    update public.board_msgs set store_read = true where store_id = p_store and from_hq = true and not store_read;
  end if;
end $f$;
revoke all on function public.board_mark_read(uuid), public.has_any_role() from public, anon;
grant execute on function public.board_mark_read(uuid), public.has_any_role() to authenticated;
