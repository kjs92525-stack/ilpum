# 일품집 통합관리 — Claude Code 인수인계 (핵심)

> 매 작업마다 자동으로 읽히는 파일이라 **핵심만** 남겼어요(2026-10-29 사용자 요청: 사용량 절약).
> 자세한 내용은 그대로 옮겨 두었어요. 필요할 때만 검색해서 읽으세요.
> - `docs/claude/decisions.md` — 사용자 결정·작업 기록 전문(①~58, 기능별 날짜·테스트 번호·서버 함수 버전). **기능을 고치기 전에 그 기능 이름으로 검색**할 것.
> - `docs/claude/reference.md` — 시스템 지도·데이터 모델(`sch_items`)·인증/권한·빌드·테스트·배포·남은 일·함정 전문.
> **"미확인"** 은 실서버로 확인 못 한 부분. 사실과 추측을 구분해서 적을 것.

## 0. 한눈에

- **사용자:** 일품집(장어 프랜차이즈 본점) 운영자. 비개발자. 한국어. 직접적·실용적인 스타일을 좋아함.
- **소통 원칙:** ① 한국어로 답하고 UI 글자는 전부 한국어 ② 기존 코드를 살려서 고치기 ③ **어느 파일을 어디에 교체해야 하는지** 분명히 알려주기 ④ 모바일 화면에서 읽기 쉽게 짧게 ⑤ 모르는 건 묻기보다 합리적으로 정하고 이유를 한 줄로 알려주기 ⑥ 기능을 추가할 때 **다른 기능이 안 깨졌는지** 테스트로 확인하기.
- **제품:** 본점 + 가맹점(약 10곳 예정)이 함께 쓰는 통합 운영 프로그램. 예약 / 근무 스케줄 / 급여 / 발주 / 공지·게시판을 왼쪽 메뉴 하나로 묶음.
- **구조:** 빌드 도구 없는 정적 HTML + Supabase. Cloudflare Workers 에 폴더째 배포. React 전환은 안 함.
- **매장:** 본점 `0134d989-757a-4b60-9cb3-93245de2cac8`, 유천점(네이버 이름 "일품집달서직영점") `ad2ffdae-f76b-44cd-a6c6-58514c4e4638`.

## 1. 서버·파일 지도 (자세히는 reference.md)

- **Supabase 두 개 — 섞지 말 것.** 예전 `fmzpmekypmjuydgxpnlu`(예전 예약·근무표, Claude 도구로 접근 불가) / **새 `bdqcrbnbuoujozlpttbe`**(서울, `ilpum-franchise`, 지금 쓰는 것). 화면을 고칠 때 **어느 서버를 읽는지** 먼저 확인.
- **`service_role`·`sb_secret_` 키는 절대 HTML·저장소에 넣지 말 것.** 공개(anon) 키는 소스에 `/*OLDKEY*/`·`/*NEWKEY*/` 자리 표시, 빌드가 `keys.json`(gitignore)에서 채움. 키는 손으로 옮겨 적지 말고 JWT 를 디코드해 `ref`·`role` 확인.
- 새 서버의 `stores`/`profiles` 등 프랜차이즈 기본 구조는 다른 채팅에서 만든 것 → **참조만**. 근무표 모듈은 `sch_` 표·함수만 씀.
- 화면(src → dist): 통합 틀 `src/portal`→`index.html` · 근무표 `src/schedule`(core/app/img/events.js)→`ilpum-schedule.html` · 예약 `src/reserve/reserve.html` · 급여 `src/payroll/pay.html` · 발주 `src/order/order.html` · 공지 `src/notice` · 게시판 `src/board` · 손님용 현황판 `src/display/display.html` · 상권분석(별도 프로그램, 서버 없음) `src/sangkwon/sangkwon.html`.
- 서버 함수: `supabase/functions/`(create-account, manage-accounts, manage-stores, naver-notify, sync-old …). 마이그레이션 `supabase/migrations/`, 아직 안 적용된 건 `pending_*.sql`.
- 근무표 데이터는 `sch_items (store_id, kind, id) → data`, 삭제는 `deleted` 표시. **요일 번호: `off`·`days`·`wk` 는 일요일=0, `aw` 는 월요일=0.**

## 2. 작업·배포 순서 (반드시)

1. 조각 파일(`app.js` 등)을 고친 뒤 **반드시 `sh build_all.sh`** (dist 를 직접 고치면 사라짐).
2. 테스트: `sh tests/run.sh`(Playwright, Supabase 는 가짜 서버). 고친 기능의 테스트 + 관련 테스트를 돌릴 것.
3. **(2026-10-25 사용자 결정) 고친 건 기본으로 바로 운영 반영:** `sh build_all.sh && sh tools/release.sh` → 커밋 → **작업 브랜치와 `main` 둘 다 push**. `main` 에 올리기 전에 반드시 `git fetch origin main` 해서 합칠 것(다른 작업 창이 올렸을 수 있음). 사용자가 "테스트로"·"테스트 사이트에 올려줘" 할 때만 테스트 폴더(`deploy/main`)만.
4. **운영 반영 전 `git log` 로 테스트에만 올라간 맛보기(디자인 시험 등)가 섞였는지 확인**(2026-10-25 남색 테마가 실수로 운영에 나간 적 있음).
5. push 뒤 **check-runs 로 `ilpum`(운영) 빌드 성공 확인**: `curl api.github.com/repos/kjs92525-stack/ilpum/commits/<sha>/check-runs`. 실패면 사용자에게 Cloudflare **Retry build** 부탁(두 워커가 동시에 빌드하면 한쪽이 떨어지는 일이 잦음). `sangkwon`·`ilpum-data` 실패 표시는 무시.
- 운영 `https://ilpum.yoyo925.workers.dev`(워커 `ilpum`, 루트 `deploy/prod`) · 테스트 워커 `ilpum-test`(루트 `deploy/main`) · 상권분석 `https://sangkwon.yoyo925.workers.dev`(수동 배포, 통합관리와 별개).
- 서버 구조(DDL) 변경·데이터 삭제 SQL 은 이 환경에서 자주 취소됨 → `pending_*.sql` 로 남기고 사용자에게 알림.

## 3. 바꾸기 전에 꼭 물어볼 결정 (요약 — 전문은 decisions.md)

- **금액(급여)은 로그인해야만 보이고 인쇄·카톡 사진·엑셀에는 절대 안 나감.** 카톡 공유는 **사진**(기본 하루치).
- 근무표: 필요 인원 부족·총 근무시간·"확인할 것" 경고는 **화면에 안 띄움**. 기본 화면은 **날짜별 카드(포지션 줄·이름 전부) "오늘부터 7일"**, Toss풍 디자인 유지, 이름 끌어서 옮기기(같은 날=포지션 변경, 다른 날=복사, 폰은 꾹 눌러 끌기). 조건 3단계: 요일 패턴 → 기간 설정 → 그날만.
- 로그인: 아이디 `ilpum`(내부 `ilpum@ilpum.invalid`), **자동 로그인 토큰**만 저장, **비밀번호는 localStorage 에 저장 안 함**. **로그인 없이 보기 없음.**
- 가맹점끼리는 서로 자료를 못 봄. **본사는 모든 매장 스케줄·예약을 보고 고침**(법률 자문 미확인). 가맹점 **급여 금액은 본사도 못 봄**. 급여는 점주·점주가 허락한 매니저·본점 한정 본사(finance)만, 직원·발주 전용은 절대 못 봄.
- 현황판 배치는 **"배치 수정" → "저장"** 해야만 바뀜(점주·매니저·본사만).
- 네이버 스마트플레이스 알림 → `naver-notify` 서버 함수가 예약 자동 입력(본점·유천점, 테이블 자동 지정은 8명까지). 세부 규칙은 decisions.md ㊹.
- **다시 꺼내지 말 것:** 예약 화면 디자인 바꾸기(4번 시도 모두 "원래가 가시성이 좋다"로 되돌림, ㊽·㊿·51·52), 근무표 카드 화면 가독성 개편(⑳, "쓰던 걸로 쓸게").
- 남색 테마는 **선택형**(기본은 원래 색, 통합관리 "테마" 버튼).

## 4. 남은 일 · 미적용

- **미적용 DDL**(사용자가 SQL Editor 에서 직접 실행하거나 허용 필요): `pending_staff_no_pay.sql`, `pending_pay_pin_reset_owner.sql`, `pending_audit_deletes.sql`.
- 실서버 미확인 항목·예전 서버 이전·보안 정리 등 목록은 reference.md §8.
- 매장 3D 배치도(새 매장 1층 판매장 + 2층 식당, 2026-10-25~30): **원본 `src/store3d/store3d.html` → `dist/store3d.html`**(운영 `https://ilpum.yoyo925.workers.dev/store3d.html`, 통합관리 로그인 토큰 `ilpum-fr-conf` 이 있어야 보임, Three.js 0.160 jsdelivr). 1층 도면 21,862×22,639mm·2층 39,890×22,119mm, 도면 좌표(px)→미터 변환 `X/Z`. 사람 걷기·그릴/화구 라인은 사용자 요청으로 뺌. 같은 내용의 아티팩트 https://claude.ai/artifact/NbKEDF1BW18uSveaaccNkw 는 이전 미리보기용(저장소 파일이 기준).

## 5. 함정 (꼭 지킬 것 — 나머지는 reference.md §9)

- **재시도는 반드시 점점 느리게.** 즉시 재시도는 무료 한도를 며칠 만에 넘김(실제로 예전 서버 전송량 202%). `tests/t19.py`·`tests/t22.py` 로 요청 수 확인.
- **전송량 규칙:** 자동 확인 근무표 60초·예약 30초·오늘 현황 60초, 10분 방치 시 멈춤, 가려진 창은 확인 안 함. 예약·근무표는 Supabase Realtime 으로 바뀐 것만 받음.
- 권한 검사에서 `null not in (…)` 은 통과됨 → `coalesce(x,'') not in (…)`. RLS 표에 익명 쓰기를 열지 말고 검증하는 RPC 로만.
- Supabase REST 기본 1000행 → `Range` 로 페이지 넘김.
- 전역 CSS 클래스는 접두사(`.ghost` 충돌 사례). `const APP` 는 `window.APP` 가 아님.
- 날짜는 한국 날짜(`ds(new Date())`).
- DB 권한 검증은 `do $$ … raise exception $$` 패턴으로(끝에서 취소돼 흔적 없음).
