# supabase/

- `migrations/<버전>_<이름>.sql` — 실서버(`ilpum-franchise`)에 **실제로 적용된 원본 그대로**예요 (2026-10-03 서버의 `supabase_migrations.schema_migrations` 에서 받아 md5 로 대조). 순서대로 전부 적용하면 빈 프로젝트에 같은 구조가 만들어져요.
- `migrations/pending_*.sql` — 아직 **적용 안 된** 것. 적용하면 `<버전>_<이름>.sql` 로 이름을 바꿔 두세요.
- 같은 함수가 여러 파일에서 다시 정의되면 **나중 파일이 이긴 것**이 지금 서버 상태예요 (예: `has_any_role` 은 `order_role` 판 = 발주 전용 계정 제외).
- 마이그레이션 밖에 있는 것: `bak_20261002_*` 표(자동 연동 시작 전 복사본), `sync_state` 의 토큰 값, pg_cron 예약(설정 화면 버튼으로 켬). 비밀 값이라 저장소에 없어요.
- `functions/` — Edge Function. `sync-old` 의 `__OLD_KEY__`·`__SYNC_TOKEN__` 은 배포할 때만 채워요.
- 권한(RLS) 확인: `tests/rls_check.sql` (끝에서 일부러 오류를 내서 전부 취소되므로 실자료에 흔적이 안 남아요).
