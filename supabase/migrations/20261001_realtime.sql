-- 실시간 알림: 예약(res_days)·근무표(sch_items) 변경을 화면이 바로 받음 (권한(RLS)은 그대로 적용돼서 자기 매장 것만 받음)
alter publication supabase_realtime add table public.res_days;
alter publication supabase_realtime add table public.sch_items;
