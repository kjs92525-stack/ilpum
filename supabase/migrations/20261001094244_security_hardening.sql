drop policy if exists sch_items_anon_sel on public.sch_items;
revoke all on function public.sch_anon_store(), public.sch_open_store(),
  public.sch_check_pin(uuid,text), public.sch_set_pin(uuid,text,text), public.sch_clear_pin(uuid,text),
  public.sch_put_many(uuid,text,jsonb), public.sch_put_summary(uuid,text,text,jsonb),
  public.sch_mig_counts(), public.sch_mig_existing(), public.sch_mig_is_open(), public.sch_mig_state(),
  public.sch_mig_put_items(jsonb), public.sch_mig_put_resdays(jsonb), public.sch_mig_put_reservations(jsonb)
  from public, anon, authenticated;
revoke all on all tables in schema public from anon;
revoke truncate, references, trigger on all tables in schema public from authenticated;
revoke all on public.pay_pins from authenticated;
alter default privileges for role postgres in schema public revoke execute on functions from public, anon;
alter default privileges for role postgres in schema public revoke all on tables from anon;