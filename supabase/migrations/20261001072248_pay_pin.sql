create extension if not exists pgcrypto with schema extensions;
create table if not exists public.pay_pins (
  user_id uuid primary key references auth.users(id) on delete cascade,
  hash text not null,
  fails int not null default 0,
  locked_until timestamptz,
  updated_at timestamptz not null default now()
);
alter table public.pay_pins enable row level security;

create or replace function public.pay_pin_status() returns jsonb
 language plpgsql security definer set search_path to '' as $f$
declare r public.pay_pins;
begin
  if auth.uid() is null then return jsonb_build_object('has', false, 'locked', 0); end if;
  select * into r from public.pay_pins where user_id = auth.uid();
  return jsonb_build_object('has', r.user_id is not null, 'locked', coalesce(greatest(0, ceil(extract(epoch from (r.locked_until - now())))::int), 0));
end $f$;

create or replace function public.pay_pin_set(p_new text, p_old text default null) returns text
 language plpgsql security definer set search_path to '' as $f$
declare r public.pay_pins;
begin
  if auth.uid() is null then return 'auth'; end if;
  if length(btrim(coalesce(p_new,''))) < 4 or length(p_new) > 64 then return 'short'; end if;
  select * into r from public.pay_pins where user_id = auth.uid();
  if r.user_id is not null then
    if r.locked_until is not null and r.locked_until > now() then return 'locked'; end if;
    if p_old is null or extensions.crypt(p_old, r.hash) <> r.hash then
      update public.pay_pins set fails = fails + 1, locked_until = case when fails + 1 >= 5 then now() + interval '10 minutes' else locked_until end where user_id = auth.uid();
      return 'bad_old';
    end if;
  end if;
  insert into public.pay_pins(user_id, hash) values (auth.uid(), extensions.crypt(p_new, extensions.gen_salt('bf')))
    on conflict (user_id) do update set hash = excluded.hash, fails = 0, locked_until = null, updated_at = now();
  return 'ok';
end $f$;

create or replace function public.pay_pin_check(p_pin text) returns text
 language plpgsql security definer set search_path to '' as $f$
declare r public.pay_pins;
begin
  if auth.uid() is null then return 'auth'; end if;
  select * into r from public.pay_pins where user_id = auth.uid();
  if r.user_id is null then return 'none'; end if;
  if r.locked_until is not null and r.locked_until > now() then return 'locked'; end if;
  if extensions.crypt(coalesce(p_pin,''), r.hash) = r.hash then
    update public.pay_pins set fails = 0, locked_until = null where user_id = auth.uid(); return 'ok'; end if;
  update public.pay_pins set fails = case when fails + 1 >= 5 then 0 else fails + 1 end,
         locked_until = case when fails + 1 >= 5 then now() + interval '10 minutes' else locked_until end where user_id = auth.uid();
  return 'bad';
end $f$;

create or replace function public.pay_pin_reset(p_login text) returns text
 language plpgsql security definer set search_path to '' as $f$
declare u uuid;
begin
  if not public.is_hq() then return 'denied'; end if;
  select id into u from auth.users where lower(email) = lower(btrim(p_login)) || '@ilpum.invalid';
  if u is null then return 'none'; end if;
  delete from public.pay_pins where user_id = u; return 'ok';
end $f$;

revoke all on function public.pay_pin_status(), public.pay_pin_set(text,text), public.pay_pin_check(text), public.pay_pin_reset(text) from public, anon;
grant execute on function public.pay_pin_status(), public.pay_pin_set(text,text), public.pay_pin_check(text), public.pay_pin_reset(text) to authenticated;