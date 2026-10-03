-- 역할별 권한(RLS) 확인. Supabase SQL Editor 에서 통째로 실행.
-- 가짜 매장·계정을 만들어 확인한 뒤, 맨 끝에서 일부러 오류를 내서 "전부 취소"됨 → 실자료에 흔적이 안 남음.
-- 결과는 오류 메시지 안에 줄별로 나와요. 줄 앞이 FAIL 이면 권한 구멍.
do $$
declare
  hq_store uuid := (select id from public.stores where is_hq limit 1);
  sa uuid := gen_random_uuid(); sb uuid := gen_random_uuid();
  u_hq uuid := gen_random_uuid(); u_oa uuid := gen_random_uuid(); u_ob uuid := gen_random_uuid();
  u_ma uuid := gen_random_uuid(); u_sa uuid := gen_random_uuid(); u_xa uuid := gen_random_uuid();
  res text := ''; n int; t text; ok boolean;
begin
  insert into public.stores(id,name,is_hq) values (sa,'__test_A',false),(sb,'__test_B',false);
  insert into auth.users(id,email) values (u_hq,'__t_hq@ilpum.invalid'),(u_oa,'__t_oa@ilpum.invalid'),(u_ob,'__t_ob@ilpum.invalid'),
    (u_ma,'__t_ma@ilpum.invalid'),(u_sa,'__t_sa@ilpum.invalid'),(u_xa,'__t_xa@ilpum.invalid');
  insert into public.profiles(user_id,store_id,role,perms) values (u_hq,hq_store,'hq','{}'),(u_oa,sa,'franchise','{}'),(u_ob,sb,'franchise','{}');
  insert into public.sch_members(user_id,store_id,role,can_pay) values (u_ma,sa,'manager',false),(u_sa,sa,'staff',false),(u_xa,sa,'order',false);
  insert into public.sch_items(store_id,kind,id,data) values (sa,'staff','x1','{"name":"갑"}'),(sa,'pay','staff:x1','{"k":"hour","v":10000}');
  insert into public.res_days(store_id,id,data) values (sa,'2099-01-01','{"items":[]}');
  insert into public.wh_items(store_id,id,name) values (sa,'w1','장어');
  insert into public.board_msgs(store_id,author_id,body) values (sa,u_oa,'테스트');

  -- 사람별로: 근무표(급여 제외)·급여·예약·발주·게시판을 몇 줄 보는지, 근무표 쓰기가 되는지
  for t, n in select * from (values ('hq',0),('owner_A',1),('owner_B',2),('manager_A',3),('staff_A',4),('order_A',5)) v(a,b) loop
    perform set_config('request.jwt.claims', json_build_object('sub', (array[u_hq,u_oa,u_ob,u_ma,u_sa,u_xa])[n+1], 'role','authenticated')::text, true);
    execute 'set local role authenticated';
    declare c_s int; c_p int; c_r int; c_w int; c_b int; can_write boolean := true; begin
      select count(*) into c_s from public.sch_items where store_id=sa and kind<>'pay' and id='x1';
      select count(*) into c_p from public.sch_items where store_id=sa and kind='pay';
      select count(*) into c_r from public.res_days where store_id=sa;
      select count(*) into c_w from public.wh_items where store_id=sa;
      select count(*) into c_b from public.board_msgs where store_id=sa;
      begin insert into public.sch_items(store_id,kind,id,data) values (sa,'staff','w_'||t,'{}'); exception when others then can_write := false; end;
      res := res || format(E'%s: 근무표 %s · 급여 %s · 예약 %s · 발주 %s · 게시판 %s · 근무표쓰기 %s\n', t, c_s, c_p, c_r, c_w, c_b, can_write);
      -- 기대값
      ok := case t
        when 'hq'        then c_s=1 and c_p=0 and c_r=1 and c_w=1 and c_b=1 and can_write
        when 'owner_A'   then c_s=1 and c_p=1 and c_r=1 and c_w=1 and c_b=1 and can_write
        when 'owner_B'   then c_s=0 and c_p=0 and c_r=0 and c_w=0 and c_b=0 and not can_write
        when 'manager_A' then c_s=1 and c_p=0 and c_r=1 and c_w=1 and c_b=1 and can_write
        when 'staff_A'   then c_s=1 and c_p=0 and c_r=1 and c_w=1 and c_b=0 and not can_write
        when 'order_A'   then c_s=0 and c_p=0 and c_r=0 and c_w=1 and c_b=0 and not can_write end;
      res := res || case when ok then '  OK' else '  FAIL' end || E'\n';
    end;
    execute 'reset role';
  end loop;

  -- 점주 B 가 A 매장에 계정 연결 시도 → 거부돼야 함
  perform set_config('request.jwt.claims', json_build_object('sub', u_ob, 'role','authenticated')::text, true);
  execute 'set local role authenticated';
  begin perform public.sch_add_member('__t_sa@ilpum.invalid', sa, 'manager', true); res := res || E'FAIL 점주B가 A매장에 계정 연결함\n';
  exception when others then res := res || E'OK   점주B → A매장 계정 연결 거부\n'; end;
  execute 'reset role';

  -- 로그인 안 한 사람(anon)
  execute 'set local role anon';
  begin select count(*) into n from public.sch_items; res := res || format(E'FAIL anon 이 근무표 %s줄 읽음\n', n);
  exception when others then res := res || E'OK   anon 근무표 읽기 거부\n'; end;
  begin select count(*) into n from public.res_days; res := res || format(E'FAIL anon 이 예약 %s줄 읽음\n', n);
  exception when others then res := res || E'OK   anon 예약 읽기 거부\n'; end;
  execute 'reset role';

  raise exception E'[결과 — 모두 취소됨]\n%', res;
end $$;
