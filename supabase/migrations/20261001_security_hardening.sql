-- 보안 강화 (2026-10-01): 가맹점이 늘어도 로그인 없이는 아무것도 읽거나 쓸 수 없게 한다.
-- 1) 로그인 없이(anon) 쓰던 길 전부 닫기: 본점 근무표 공개 읽기·쓰기, PIN 함수, 이전 창구
drop policy if exists sch_items_anon_sel on public.sch_items;
revoke all on function public.sch_anon_store(), public.sch_open_store(),
  public.sch_check_pin(uuid,text), public.sch_set_pin(uuid,text,text), public.sch_clear_pin(uuid,text),
  public.sch_put_many(uuid,text,jsonb), public.sch_put_summary(uuid,text,text,jsonb),
  public.sch_mig_counts(), public.sch_mig_existing(), public.sch_mig_is_open(), public.sch_mig_state(),
  public.sch_mig_put_items(jsonb), public.sch_mig_put_resdays(jsonb), public.sch_mig_put_reservations(jsonb)
  from public, anon, authenticated;
-- sch_anon_store 는 정책 안에서 쓰일 수 있어 서버 내부(postgres)만 남김
-- 2) 표 권한: anon 은 아무 표도 못 건듦, 로그인 사용자도 TRUNCATE 등 위험 권한 제거 (RLS 가 막지 못하는 권한)
revoke all on all tables in schema public from anon;
revoke truncate, references, trigger on all tables in schema public from authenticated;
-- 급여 비밀번호 표는 함수로만 접근
revoke all on public.pay_pins from authenticated;
-- 3) 앞으로 만드는 함수·표도 기본으로 anon 이 못 쓰게
alter default privileges for role postgres in schema public revoke execute on functions from public, anon;
alter default privileges for role postgres in schema public revoke all on tables from anon;
