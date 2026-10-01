-- 공지사항 사진·동영상: board_notices.media = [{path,type:'image'|'video',name}] / 비공개 저장소 notice-media (본사만 올리기·지우기, 역할 있는 계정이 보기)
alter table public.board_notices add column if not exists media jsonb not null default '[]'::jsonb;
insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values ('notice-media','notice-media',false,52428800,array['image/jpeg','image/png','image/webp','image/gif','video/mp4','video/quicktime','video/webm'])
on conflict (id) do update set file_size_limit=excluded.file_size_limit, allowed_mime_types=excluded.allowed_mime_types, public=false;
create policy notice_media_sel on storage.objects for select to authenticated using (bucket_id='notice-media' and public.has_any_role());
create policy notice_media_ins on storage.objects for insert to authenticated with check (bucket_id='notice-media' and public.is_hq());
create policy notice_media_del on storage.objects for delete to authenticated using (bucket_id='notice-media' and public.is_hq());
