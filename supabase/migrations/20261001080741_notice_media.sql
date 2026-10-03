alter table public.board_notices add column if not exists media jsonb not null default '[]'::jsonb;

insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values ('notice-media','notice-media',false,52428800,array['image/jpeg','image/png','image/webp','image/gif','video/mp4','video/quicktime','video/webm'])
on conflict (id) do update set file_size_limit=excluded.file_size_limit, allowed_mime_types=excluded.allowed_mime_types, public=false;

drop policy if exists notice_media_sel on storage.objects;
drop policy if exists notice_media_ins on storage.objects;
drop policy if exists notice_media_del on storage.objects;
create policy notice_media_sel on storage.objects for select to authenticated using (bucket_id='notice-media' and public.has_any_role());
create policy notice_media_ins on storage.objects for insert to authenticated with check (bucket_id='notice-media' and public.is_hq());
create policy notice_media_del on storage.objects for delete to authenticated using (bucket_id='notice-media' and public.is_hq());