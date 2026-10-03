insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values ('uploads', 'uploads', false, 5242880, array['image/jpeg', 'image/png', 'image/webp'])
on conflict (id) do nothing;

create policy uploads_read on storage.objects for select to authenticated
  using (bucket_id = 'uploads' and ((storage.foldername(name))[1] = (select public.my_store_id())::text or (select public.is_hq())));
create policy uploads_insert on storage.objects for insert to authenticated
  with check (bucket_id = 'uploads' and (storage.foldername(name))[1] = (select public.my_store_id())::text);
create policy uploads_delete on storage.objects for delete to authenticated
  using (bucket_id = 'uploads' and (select public.is_hq()));