create or replace function public.sync_status() returns jsonb language plpgsql security definer set search_path to '' as $$
begin
  if not public.is_hq() then raise exception '본사만 볼 수 있어요'; end if;
  return jsonb_build_object(
    'enabled', coalesce((select (val->>'v')::boolean from public.sync_state where key='enabled'), true),
    'auto', exists(select 1 from cron.job where jobname = 'sync-old' and active),
    'last', (select val from public.sync_state where key='last_run'),
    'at', (select updated_at from public.sync_state where key='last_run'));
end $$;

-- 지금 한 번 실행 (p_full=true 면 처음부터 다시 훑음)
create or replace function public.sync_run_now(p_full boolean default false) returns void language plpgsql security definer set search_path to '' as $$
declare tok text;
begin
  if not public.is_hq() then raise exception '본사만 실행할 수 있어요'; end if;
  select val->>'v' into tok from public.sync_state where key='token';
  if tok is null then raise exception '연동 설정이 아직 없어요'; end if;
  if p_full then delete from public.sync_state where key='revs'; end if;
  insert into public.sync_state(key,val) values ('enabled', jsonb_build_object('v',true)) on conflict (key) do update set val = excluded.val, updated_at = now();
  perform net.http_post(url := 'https://bdqcrbnbuoujozlpttbe.supabase.co/functions/v1/sync-old',
    headers := jsonb_build_object('Content-Type','application/json','x-sync-token',tok), body := '{}'::jsonb, timeout_milliseconds := 55000);
end $$;

-- 5분마다 자동 실행 켜기/끄기
create or replace function public.sync_auto_set(p_on boolean) returns void language plpgsql security definer set search_path to '' as $$
begin
  if not public.is_hq() then raise exception '본사만 바꿀 수 있어요'; end if;
  if exists(select 1 from cron.job where jobname='sync-old') then perform cron.unschedule('sync-old'); end if;
  if p_on then
    perform cron.schedule('sync-old', '*/5 * * * *', $c$ select net.http_post(url := 'https://bdqcrbnbuoujozlpttbe.supabase.co/functions/v1/sync-old', headers := jsonb_build_object('Content-Type','application/json','x-sync-token',(select val->>'v' from public.sync_state where key='token')), body := '{}'::jsonb, timeout_milliseconds := 55000) $c$);
  end if;
  insert into public.sync_state(key,val) values ('enabled', jsonb_build_object('v',p_on)) on conflict (key) do update set val = excluded.val, updated_at = now();
end $$;

revoke all on function public.sync_status(), public.sync_run_now(boolean), public.sync_auto_set(boolean) from public, anon;
grant execute on function public.sync_status(), public.sync_run_now(boolean), public.sync_auto_set(boolean) to authenticated;