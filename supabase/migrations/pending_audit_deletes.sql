-- 발주·품목·공지를 지우면 지우기 전 내용을 audit_log 에 남김 (실수로 지워도 되살릴 수 있게). 지울 때만 기록해 용량은 거의 안 씀.
-- 기존 함수 public.audit() (20260929063759_franchise_ops_modules) 를 그대로 씀.
-- 되살리기: select old from public.audit_log where tbl='wh_orders' and action='DELETE' order by id desc;
drop trigger if exists audit_wh_orders_del on public.wh_orders;
drop trigger if exists audit_wh_items_del on public.wh_items;
drop trigger if exists audit_board_notices_del on public.board_notices;
create trigger audit_wh_orders_del after delete on public.wh_orders for each row execute function public.audit();
create trigger audit_wh_items_del after delete on public.wh_items for each row execute function public.audit();
create trigger audit_board_notices_del after delete on public.board_notices for each row execute function public.audit();
