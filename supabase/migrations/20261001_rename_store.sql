-- 매장 이름 바꾸기: 본사만 (앱의 매장 관리 화면에서 사용)
create or replace function public.sch_rename_store(p_store uuid, p_name text) returns text
 language plpgsql security definer set search_path to '' as $f$
begin
  if not public.is_hq() then return 'denied'; end if;
  if length(btrim(coalesce(p_name,''))) < 1 or length(btrim(p_name)) > 40 then return 'bad_name'; end if;
  update public.stores set name = btrim(p_name) where id = p_store;
  if not found then return 'none'; end if;
  return 'ok';
end $f$;
revoke all on function public.sch_rename_store(uuid,text) from public, anon;
grant execute on function public.sch_rename_store(uuid,text) to authenticated;
