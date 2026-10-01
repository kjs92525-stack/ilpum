-- 발주 전용 계정(role 'order'): 발주 화면(wh_*)만 쓰고, 예약·근무표·공지·게시판은 못 봄.
alter table public.sch_members drop constraint if exists sch_members_role_check;
alter table public.sch_members add constraint sch_members_role_check check (role = any (array['manager','staff','order']));

drop policy if exists sch_items_sel on public.sch_items;
create policy sch_items_sel on public.sch_items for select to authenticated
  using (sch_role(store_id) = any (array['hq','owner','manager','staff']) and (kind <> 'pay' or sch_can_pay(store_id)));

drop policy if exists sch_sum_sel on public.sch_summaries;
create policy sch_sum_sel on public.sch_summaries for select to authenticated
  using (is_hq() or sch_role(store_id) = any (array['hq','owner','manager','staff']));

drop policy if exists res_days_sel on public.res_days;
drop policy if exists res_days_ins on public.res_days;
drop policy if exists res_days_upd on public.res_days;
create policy res_days_sel on public.res_days for select to authenticated using (sch_role(store_id) = any (array['hq','owner','manager','staff']));
create policy res_days_ins on public.res_days for insert to authenticated with check (sch_role(store_id) = any (array['hq','owner','manager','staff']));
create policy res_days_upd on public.res_days for update to authenticated using (sch_role(store_id) = any (array['hq','owner','manager','staff'])) with check (sch_role(store_id) = any (array['hq','owner','manager','staff']));

create or replace function public.has_any_role() returns boolean language sql stable security definer set search_path to '' as $$
  select exists(select 1 from public.profiles where user_id = auth.uid())
      or exists(select 1 from public.sch_members where user_id = auth.uid() and role <> 'order')
$$;

create or replace function public.sch_add_member(p_email text, p_store uuid, p_role text, p_pay boolean default false)
returns void language plpgsql security definer set search_path to '' as $$
declare u uuid; ps uuid; isq boolean;
begin
  if p_role not in ('owner','manager','staff','order') then raise exception '역할이 올바르지 않아요'; end if;
  select s.is_hq into isq from public.stores s where s.id = p_store;
  if isq is null then raise exception '없는 매장이에요'; end if;
  if p_role = 'owner' then
    if not public.is_hq() then raise exception '점주 연결은 본사만 할 수 있어요'; end if;
  else
    if coalesce(public.sch_role(p_store), '') not in ('hq','owner') then raise exception '이 매장에 계정을 연결할 권한이 없어요'; end if;
  end if;
  select id into u from auth.users where lower(email) = lower(trim(p_email));
  if u is null then raise exception '먼저 Supabase Authentication에서 % 계정을 만들어 주세요', p_email; end if;
  if p_role = 'owner' then
    if isq then raise exception '본점은 본사 계정을 써요. 가맹점에만 점주를 연결할 수 있어요'; end if;
    insert into public.profiles(user_id, store_id, role, display_name) values (u, p_store, 'franchise', split_part(trim(p_email),'@',1))
      on conflict (user_id) do nothing;
    select store_id into ps from public.profiles where user_id = u;
    if ps is distinct from p_store then raise exception '이 계정은 이미 다른 매장에 연결돼 있어요'; end if;
  else
    insert into public.sch_members(user_id, store_id, role, can_pay) values (u, p_store, p_role, case when p_role='order' then false else coalesce(p_pay,false) end)
      on conflict (user_id, store_id) do update set role = excluded.role, can_pay = excluded.can_pay;
  end if;
end $$;
