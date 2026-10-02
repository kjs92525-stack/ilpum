-- 급여 비밀번호 초기화: 본사는 모든 계정, 점주는 자기 매장에 연결된 매니저·직원 계정만
create or replace function public.pay_pin_reset(p_login text) returns text
language plpgsql security definer set search_path = '' as $$
declare u uuid;
begin
  select id into u from auth.users where lower(email) = lower(btrim(p_login)) || '@ilpum.invalid';
  if public.is_hq() then
    if u is null then return 'none'; end if;
  else
    if u is null then return 'none'; end if;
    -- 점주: 내 매장 소속(매니저·직원)인 계정만, 점주·본사 계정은 안 됨
    if not exists (select 1 from public.sch_members m where m.user_id = u and coalesce(public.sch_role(m.store_id),'') = 'owner')
       or exists (select 1 from public.sch_members m where m.user_id = u and coalesce(public.sch_role(m.store_id),'') <> 'owner')
       or exists (select 1 from public.profiles p where p.user_id = u)
    then return 'denied'; end if;
  end if;
  delete from public.pay_pins where user_id = u; return 'ok';
end $$;
