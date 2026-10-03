-- 발주 번호 (1001번부터)
alter table public.orders add column no bigint generated always as identity (start with 1001);
create unique index orders_no_key on public.orders (no);

-- 발주 등록: 발주와 품목을 한 번에 저장 (권한 규칙은 그대로 적용)
create function public.create_order(p_memo text, p_items jsonb) returns bigint
language plpgsql security invoker set search_path = ''
as $$
declare v_id uuid; v_no bigint;
begin
  if p_items is null or jsonb_typeof(p_items) <> 'array' or jsonb_array_length(p_items) = 0 then
    raise exception '품목이 없어요';
  end if;
  insert into public.orders (store_id, memo)
    values ((select public.my_store_id()), nullif(trim(coalesce(p_memo, '')), ''))
    returning id, no into v_id, v_no;
  insert into public.order_items (order_id, product_id, qty)
    select v_id, x.product_id, x.qty
    from jsonb_to_recordset(p_items) as x(product_id uuid, qty numeric);
  return v_no;
end $$;

revoke execute on function public.create_order(text, jsonb) from public, anon;
grant execute on function public.create_order(text, jsonb) to authenticated;

-- 실시간 반영
alter publication supabase_realtime add table public.orders;