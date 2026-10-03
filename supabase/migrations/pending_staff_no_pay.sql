-- 직원·발주 전용 계정에는 급여 보기 권한(can_pay)을 아예 못 붙이게 (지금도 sch_can_pay 가 직원엔 항상 false 라 못 보지만, 값 자체도 막아 둠)
update public.sch_members set can_pay = false where role <> 'manager' and can_pay;
alter table public.sch_members drop constraint if exists sch_members_pay_manager_only;
alter table public.sch_members add constraint sch_members_pay_manager_only check (role = 'manager' or not can_pay);
