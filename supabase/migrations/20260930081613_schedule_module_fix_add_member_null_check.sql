create or replace function public.sch_add_member(p_email text, p_store uuid, p_role text, p_pay boolean default false) returns void
language plpgsql security definer set search_path = '' as $$
declare u uuid; ps uuid; isq boolean;
begin
  if p_role not in ('owner','manager','staff') then raise exception '역할이 올바르지 않아요'; end if;
  select s.is_hq into isq from public.stores s where s.id = p_store;
  if isq is null then raise exception '없는 매장이에요'; end if;
  -- 이 매장에서 본사/점주가 아니면 누구도 계정을 연결할 수 없음 (권한 없음=null 도 막음)
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
    insert into public.sch_members(user_id, store_id, role, can_pay) values (u, p_store, p_role, coalesce(p_pay,false))
      on conflict (user_id, store_id) do update set role = excluded.role, can_pay = excluded.can_pay;
  end if;
end $$;

revoke all on function public.sch_add_member(text,uuid,text,boolean) from public, anon;
grant execute on function public.sch_add_member(text,uuid,text,boolean) to authenticated;