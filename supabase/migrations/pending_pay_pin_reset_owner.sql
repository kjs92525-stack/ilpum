-- 급여 비밀번호 초기화: 본사는 모든 계정, 점주는 "급여 보기 권한이 있는 우리 매장 매니저"만 (직원·발주 전용은 급여 비밀번호 자체가 없음)
create or replace function public.pay_pin_reset(p_login text) returns text
language plpgsql security definer set search_path = '' as $$
declare u uuid;
begin
  select id into u from auth.users where lower(email) = lower(btrim(p_login)) || '@ilpum.invalid';
  if u is null then return 'none'; end if;
  if not public.is_hq() then
    -- 점주: 내 매장에만 연결된, 급여 권한이 있는 매니저만. 점주·본사 계정은 안 됨
    if coalesce((select p.role from public.profiles p where p.user_id = auth.uid()), '') <> 'franchise'
       or not exists (select 1 from public.sch_members m where m.user_id = u and m.role = 'manager' and m.can_pay
                        and m.store_id = (select p.store_id from public.profiles p where p.user_id = auth.uid()))
       or exists (select 1 from public.sch_members m where m.user_id = u and m.store_id <> (select p.store_id from public.profiles p where p.user_id = auth.uid()))
       or exists (select 1 from public.profiles p where p.user_id = u)
    then return 'denied'; end if;
  end if;
  delete from public.pay_pins where user_id = u; return 'ok';
end $$;
