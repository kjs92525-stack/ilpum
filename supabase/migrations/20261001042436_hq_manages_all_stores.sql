create or replace function public.sch_role(sid uuid)
 returns text language sql stable security definer set search_path to ''
as $function$
  select coalesce(
    (select 'hq'::text from public.profiles p
       where p.user_id = auth.uid() and p.role = 'hq'
         and exists (select 1 from public.stores s where s.id = sid) limit 1),
    (select 'owner'::text from public.profiles p
       where p.user_id = auth.uid() and p.role = 'franchise' and p.store_id = sid limit 1),
    (select m.role from public.sch_members m where m.user_id = auth.uid() and m.store_id = sid limit 1)
  )
$function$;

create or replace function public.sch_can_pay(sid uuid)
 returns boolean language sql stable security definer set search_path to ''
as $function$
  select case public.sch_role(sid)
    when 'hq' then public.has_perm('finance') and coalesce((select s.is_hq from public.stores s where s.id = sid), false)
    when 'owner' then true
    when 'manager' then coalesce((select m.can_pay from public.sch_members m where m.user_id = auth.uid() and m.store_id = sid), false)
    else false end
$function$;