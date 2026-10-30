# 일품집 — 참고 자료 전문 (CLAUDE.md §1·§3~§10 에서 옮김)

> 2026-10-29 CLAUDE.md 를 줄이면서 **내용 그대로** 옮긴 파일이에요. 데이터 모양·권한·빌드·테스트·배포·남은 일·함정의 자세한 설명은 여기 있어요.

## 1. 시스템 지도

| 화면 | 파일 (dist/) | 데이터가 있는 곳 | 상태 |
|---|---|---|---|
| 통합관리 틀(왼쪽 메뉴, 오늘 현황) | `index.html` | 예약=**예전** 서버, 출근=**새** 서버 (읽기만) | 완성, 실서버 미확인 |
| 예약 관리 | `reserve.html` | **새** 서버 `res_days` (매장별, 로그인 필요) | 화면은 새 서버용으로 바꿈. **자료 이전은 아직**(이전 도구 실행 필요) |
| 근무 스케줄 (+직원·매장·설정 화면) | `ilpum-schedule.html` | **새** 서버 `sch_*` | 완성, 실서버 미확인 |
| 급여 관리 = 근무·급여 집계기 | `pay.html` | 구글 시트 "스케줄표" 탭(Apps Script 웹앱) 또는 엑셀 업로드 → 설정은 **새** 서버 `sch_items` kind `pay` id `calc:agg`(금액 권한 필요) | 2026-10-30 예전 급여 계산기를 통째로 교체(`src/payroll/pay.html`, 상세는 decisions.md 59) |
| 일회성 이전 도구 | `ilpum-migrate.html` | 예전 서버 → 새 서버 | 완성, **아직 실행 안 함** |
| 발주 관리 | `order.html` | **새** 서버 `wh_items`·`wh_orders` (매장별) | 화면 새로 만듦(추정 기반). 자료는 "가져오기" 버튼으로 이전 |
| 상권분석 (대구, 별도 프로그램) | `sangkwon.html` | **서버 없음** — 카카오 지도 JavaScript SDK 직접 호출, 기록은 그 브라우저 localStorage `ilpum-sk-v1` + 백업 파일 | 2026-10-05 1차. 통합관리 메뉴에 없음(주소로만 열기) |

**두 Supabase 프로젝트**
- **예전:** ref `fmzpmekypmjuydgxpnlu`. 예약(`reservations_day`: 날짜별 JSON 한 줄)과 예전 근무표(`schedule_state` id=`main` 한 줄 JSON)가 있음. 공개(anon) 키는 예전 HTML들 안에 박혀 있음(`keys.json`의 `old`). **Claude의 Supabase 도구로는 접근 불가**, 샌드박스에서도 접속 차단이었음. 사장님 컴퓨터에서만 읽을 수 있음.
- **새:** ref `bdqcrbnbuoujozlpttbe` (서울 리전), URL `https://bdqcrbnbuoujozlpttbe.supabase.co`, 프로젝트 이름 `ilpum-franchise`. 공개(anon) 키는 `keys.json`의 `new`와 `src/schedule/core.js`의 `DEF_SUPA`. **절대 `service_role` 키를 HTML·저장소에 넣지 말 것.**

**새 서버에는 다른 채팅에서 만든 프랜차이즈 기본 구조도 있어요** (내가 만든 게 아님. 함부로 바꾸지 말 것):
`stores`(본점·가맹점 1), `profiles`(계정↔매장↔역할 hq/franchise), `positions`, `staff`, `shifts`, `staff_rates`, `shift_pay`, `reservations`, `floors`, `dining_tables`, `orders`…, `app_settings`, `audit_log`. 적용된 마이그레이션 12개 중 앞 7개(`franchise_core_schema_rls` … `uploads_bucket_for_ticket_photos`)가 그쪽, 뒤 5개(`schedule_*`)가 내가 만든 근무표 모듈.
- 근무표 모듈은 `sch_` 접두사 표·함수만 쓰고, **기존 `stores`/`profiles`를 참조만** 함.
- 기존 `staff`/`shifts` 표는 지금 근무표가 **쓰지 않음**(비어 있음). 그 표의 RLS는 본사가 모든 매장 직원·근무를 볼 수 있게 돼 있음 → §8 참고.
- 매장 id: 본점 `0134d989-757a-4b60-9cb3-93245de2cac8`, 가맹점 1 `ad2ffdae-f76b-44cd-a6c6-58514c4e4638`.

## 3. 근무표 데이터 모델 (새 서버 `sch_items`)

한 표에 종류별로 한 줄씩: `(store_id, kind, id) → data jsonb`, `deleted`(삭제는 행 삭제가 아니라 표시), `updated_at`(폴링용). 화면은 15초마다 `updated_at` 이후 변경분만 받아옴.

| kind | id 모양 | data |
|---|---|---|
| `cfg` | `store` / `positions` | 영업시간·종일/오후 시간·목표율… / `[{name,color,req[7]}]` |
| `staff` | 직원 id | `{name,pos,type:'regular'|'weekly'|'spot',off:[일=0 기준 요일],wk?:{요일:{sh}},active,order,tel?}` |
| `rule` | 기간 설정 id | `{ids[],from,to,days[],w:'off'|'on',sh,pos,memo,at}` (나중 것이 우선) |
| `dc` | `YYYY-MM-DD|직원id` | 그날만: `{st:'off'|'annual'|'extra'|'paidoff',pos,sh,memo}` |
| `spot` | 알바 id | 단기·당일: `{date,name,pos,sh,memo}` |
| `aw` | 그 주 월요일 날짜 | 매주 변동 직원의 주간 입력 `{직원id:{off:[월=0 기준],pm:[],t:{}}}` |
| `pay` | `staff:id` / `pat:id:요일` / `rule:id` / `dc:날짜|id` / `spot:id` | `{k:'day'|'hour'|'bonus'|'month',v,cash?}` — **급여 권한자만 읽기/쓰기** |
| `sales` | 날짜 | `{v}` 매출(인건비율용) |

- 출근 시간 `sh`: `{k:'full'}` | `{k:'pm'}` | `{k:'t',s:'HH:MM',e:'HH:MM'|''}`(빈 e = 영업 마감). 근무시간은 **영업시간(기본 11–22) 안쪽만** 계산, 종일 10h·오후 5h가 기본.
- **적용 순서(`core.js`의 `resolve`)**: 요일 패턴 → 기간 설정(rule, `at` 오름차순) → 주간 입력(aw, 매주 변동 직원만) → 그날만(dc) → 단기알바(spot). 포지션이 기본과 다르면 태그 `chg`.
- **요일 번호 주의:** `off`·`days`·`wk` 는 **일요일=0**, `aw` 의 `off/pm/t` 인덱스는 **월요일=0**. 헷갈리기 쉬움.
- 직원 종류: `regular`(고정 근무, 쉬는 요일만 빼고 매주 자동) / `weekly`(매주 변동: 그 주 `aw` 입력이 있어야 출근, 없으면 "미입력") / `spot`(단기·당일, `spot` 행으로 넣은 날만). 예전 앱의 "고정알바"=`weekly`.

## 4. 인증·권한 (새 서버)

역할은 `sch_role(store_id)` 가 계산: `hq`(본사 계정이 **모든 매장에서**, 2026-10-01 변경 — `supabase/migrations/20261001_hq_manages_all_stores.sql`) / `owner`(`profiles.role='franchise'` 계정이 자기 매장) / `manager`·`staff`(`sch_members` 표) / 없음. 금액 권한 `sch_can_pay`: hq(+`finance` 권한, **본점에서만**) · owner · 허용된 manager.

**RLS (표마다 켜짐)**
- `sch_items`: 로그인 사용자는 역할이 있는 매장만 읽기(금액 종류는 `sch_can_pay` 필요). 쓰기는 hq/owner/manager만. 삭제 정책 없음(표시로만 삭제).
- ~~`sch_items_anon_sel`~~ (로그인 없이 읽기)는 2026-10-01 삭제. anon 은 어떤 표도 못 읽고 쓰고, anon 이 부르던 `sch_open_store/put_many/put_summary/…pin/…mig_*` 함수는 전부 실행 권한 회수(`revoke … from public, anon, authenticated`). 새 함수·표도 기본적으로 anon 접근 없음(default privileges). 이전 도구(`ilpum-migrate.html`)는 이 때문에 더는 동작 안 함 — 다시 쓰려면 해당 함수에 grant 필요.
- `sch_summaries`: 본사는 모든 매장의 **집계**(근무시간·인건비율 등)만 읽음.
- `sch_members`: 자기 행만 읽기. `sch_pins`·`sch_pin_fail`·`sch_mig_window`: 정책 없음(함수로만 접근).

**RPC 함수 (실행 권한 주의)**
- 로그인 필요: `sch_my_stores`, `sch_create_store(name)`(본사만), `sch_add_member(email,store,role,pay)`(점주 연결은 본사만·가맹점에만 / 매니저·직원 연결은 그 매장의 본사(본점)·점주만 — 그래서 본사는 가맹점의 매니저·직원을 못 붙임. null 권한 검사 버그를 한 번 고쳤음), `sch_role`, `sch_can_pay`.
- (아래 anon 목록은 **옛 설명**, 지금은 모두 회수됨) 로그인 없이(anon) 호출 가능했던 것: `sch_open_store`, `sch_put_many(store,pin,rows)`(본점 쓰기, **금액·알 수 없는 종류는 거부**, PIN이 설정돼 있으면 확인), `sch_put_summary`, `sch_check_pin`, `sch_set_pin`, `sch_clear_pin`, `sch_anon_store`.
- **이전 창구 `sch_mig_*`**: `sch_mig_window.until` 시각 전까지만 동작(anon 가능, 본점만, 금액·예약 쓰기 가능). 시각이 지나면 전부 `closed`. 지금 값은 **2026‑10‑01 04:24 UTC** 에 닫히도록 돼 있음.
  - 다시 열기: `update public.sch_mig_window set until = now() + interval '12 hours' where id=1;`
  - 닫기: `update public.sch_mig_window set until = now() where id=1;`
  - **이전이 끝나면 닫을 것.** 예약 표(고객 이름·전화)에 쓰기가 가능한 창구이므로.
- 로그인 안 한 상태의 PIN 무차별 대입 방지: 8번 틀리면 15분 잠금(현재 PIN 0개라 비활성).

**계정 만들기(서버 함수):** `supabase/functions/create-account/index.ts` (Supabase Edge Function, verify_jwt). 호출자가 `profiles.role='hq'` 인지 확인 → `service_role` 로 `아이디@ilpum.invalid` 계정 생성 → `sch_add_member` 로 매장 연결(실패하면 계정 삭제). 서버 안에서만 service_role 사용. **실서버 호출은 미확인**(배포만 함, 화면 테스트는 가짜 서버). **Supabase 대시보드 Authentication → Sign In / Providers 에서 "Allow new users to sign up" 을 꺼야** 본사 말고는 계정을 못 만듦(꺼져 있는지 확인 못 함).

**아이디 로그인:** 입력 `ilpum` → `ilpum@ilpum.invalid` 로 바꿔 Supabase에 보냄(`core.js` `toLoginEmail`). `.invalid` 는 실제로 존재할 수 없는 주소라 "비밀번호 찾기" 메일이 남의 손에 가지 않음. 새 계정도 `아이디@ilpum.invalid` 로 만들 것. 계정이 있는 곳은 `auth.users`(현재 1개, 본점 hq 프로필 연결).

**알려진 보안 사항**
- 아이디가 누구나 짐작 가능한 `ilpum` 이라 **보안은 비밀번호 강도에만** 의존. 강한 비밀번호 권장함(사용자에게 안내했음).
- 대시보드의 Auth 설정 "유출된 비밀번호 검사"가 꺼져 있음(Supabase 경고, 이 프로젝트 기본 설정).
- `audit_log` 표에 RLS 켜져 있으나 정책 없음(기존 구조, Supabase 경고).

**백업·복원(2026-10-01):** 설정 → "백업 · 복원 (본사만)"(`Remote.backupAll/restoreAll` in `core.js`). 본사 로그인 상태로 `sch_items·res_days·wh_items·wh_orders·board_notices·board_msgs` 와 매장 목록을 JSON 한 파일로 내려받음(RLS 가 본사 말고는 모든 매장 자료를 주지 않으므로 별도 서버 권한 불필요). 복원은 upsert(덮어쓰기, 삭제 없음), 게시판 글은 서버 규칙(작성자=본인)상 되돌릴 수 없어 건너뜀, 공지 사진·동영상 파일 자체는 백업에 없음(경로 목록만). 다른 Supabase 프로젝트로 통째로 옮기려면: 마이그레이션 전부 적용 → `stores` 를 같은 id 로 만들기 → 계정 다시 만들기 → 복원. 급여(`pay`) 줄은 본사 계정이 `can_pay` 인 매장(본점)만 들어감. 테스트 `tests/t32.py`. 마지막 백업 시각은 이 기기 localStorage `ilpum-last-backup`, 7일 넘으면 붉게 표시.

## 5. 프론트 코드 구조 · 빌드

**빌드:** `sh build_all.sh` → `dist/`(배포용 7개) + `dist-tools/`(일회성 도구, 올리지 말 것) + `out/ilpum-deploy.zip` (Python3 + Node 필요).

**키와 저장소(git):** 공개(anon) 키는 저장소에 올리지 않아요. 소스에는 `/*OLDKEY*/`·`/*NEWKEY*/` 자리 표시만 있고, 빌드가 `keys.json` 에서 채워 넣어요. `keys.json`·`dist/`·`legacy/` 는 `.gitignore` 로 빠져 있어서 **새 환경에서는 사용자에게 받은 zip(또는 Supabase 대시보드의 anon 키)으로 `keys.json` 과 `legacy/` 를 다시 놓아야** 빌드가 돼요(급여 화면이 `legacy/patched/` 에서 복사되기 때문). 소스에서 다시 만든 결과가 채팅에서 전달한 파일과 **해시까지 동일**함을 확인해 둠.

```
src/schedule/   근무표 앱 (→ dist/ilpum-schedule.html)
  core.js       유틸·시간/금액 해석 · 저장소(Local 체험 / Remote Supabase) · 근무 계산 엔진(resolve)
  app.js        상태(APP) · 화면들(카드/주간표/하루/직원/기간 설정/내 스케줄/본사 현황/설정) · 로그인 화면
  img.js        카톡용 사진 — 캔버스로 직접 그림(하루/주간/월간/내 근무). 화면에는 하루·내 근무만 노출
  events.js     서랍(편집 창) · 클릭/입력 처리 · 끌어서 옮기기/복사 · 기존 근무표 가져오기
  app.css / shell.html   스타일 / HTML 뼈대
src/portal/     통합관리 틀 (→ dist/index.html). 근무표 core.js 의 엔진 부분을 빌드 때 그대로 가져와 씀
src/migrate/    이전 도구 (→ dist/ilpum-migrate.html). mig.js = 예전→새 형식 변환(순수 함수)
src/reserve/    reserve.html — 예전 예약 화면 + "목록·현황 너비 조절" 추가본. 빌드 없이 그대로 dist로 복사
legacy/original 사용자가 처음 올린 예전 운영 파일 4개(원본)
legacy/patched  예전 근무표(schedule.html)·급여 계산기 패치본 (예전 서버용, 참고만 — 급여 계산기는 `src/payroll/pay.html` 로 옮김)
tools/import-oct 엑셀(예전 근무표 10월 내보내기)을 새 서버 형식으로 바꾸고 검증한 일회성 스크립트 (이미 DB에 반영 완료)
```

**근무표 앱의 저장소 추상화:** `Local`(체험, localStorage)과 `Remote`(Supabase REST/RPC)가 같은 인터페이스(`init, stores, items, since, put, putMany, summaries, putSummary, createStore, addMember`). 화면 코드는 `APP.be` 만 봄.

**통합 틀 ↔ 근무표 iframe:** `?embed=1&view=…` 이면 근무표가 자기 왼쪽 메뉴를 숨기고 초록 강조색을 씀. 틀이 `postMessage({type:'fr-goto',view})` 로 화면을 바꾸고, 근무표는 `{type:'fr-state',view,hq,edit}` 로 현재 화면·권한을 알려 메뉴 강조·숨김을 맞춤. 탭을 다시 열 때 `window.pullNow()` 를 부름(예전 index.html 방식 유지). iframe은 한 번 띄우면 계속 살려 둠(입력 내용 유지).

**localStorage 키:** `ilpum-fr-conf`(접속 설정·로그인 토큰·마지막 아이디·`openOnly`), `ilpum-fr-v1`(체험 모드 데이터), `ilpum-nav`·`ilpum-page`(통합 틀), `ilpum-res-listw`(예약 목록 너비). sessionStorage `fr-pay`(금액 보기 켬), `fr-ses`(자동 로그인 끈 경우의 세션).

## 6. 테스트

`tests/` 의 Playwright(Python) 스크립트. **Supabase를 가짜 서버로 흉내**(`page.route`)내서 화면 동작을 확인하는 방식이라 "로직"은 검증되지만 **실서버와의 연동은 검증하지 못함.**
- 하드코딩된 것: `/home/claude/...` 경로, `chromium` 실행 파일 경로(`/opt/pw-browsers/...`), 가짜 날짜. → 새 환경에서는 경로를 고치고 `p.chromium.launch()` 기본값을 쓰면 됨(`playwright install chromium`).
- 주요 테스트: `t9/t10`(카드 화면·끌어서 복사·포지션 관리, 체험 모드), `t14`(로그인 없이 열기), `t16`(자동 로그인 전 과정 + 아이디 변환), `t_shell`·`t_mob`(통합 틀, **`file://` 이 아니라 `http://` 로 띄워야 iframe 내부 접근 가능**), `t_mig2`(이전 도구), `test_conv.js`(변환기를 엑셀 10월 스케줄 279칸과 대조), `tools/import-oct/verify.js`.
- DB 권한 검증 패턴: `do $$ … set local role authenticated/anon; select set_config('request.jwt.claims', …); … raise exception E'결과…' $$;` — 마지막에 예외를 던져 **전체가 취소**되므로 실데이터에 흔적이 안 남음. 권한을 바꾸면 이 방식으로 역할별(본사/점주/매니저/직원/익명) 검증을 다시 할 것. (이 패턴으로 점주가 다른 매장에 계정을 연결할 수 있던 구멍을 한 번 찾아 고쳤음.)

## 7. 배포

- 정적 호스팅(Netlify 등)에 **`dist/` 안의 파일을 한 폴더에** 올림: `index.html`, `reserve.html`, `ilpum-schedule.html`, `order.html`, `pay.html`(+ 일회성 `ilpum-migrate.html`). 파일 이름은 한글 없이 영문으로(배포 도구가 한글 이름에서 실패하는 일을 피함).
- 같은 주소 아래여야 iframe/postMessage/localStorage 공유(자동 로그인)가 동작. 파일 이름을 바꾸면 `src/portal/shell.html` 의 `FILES` 만 고치면 됨.
- 사용자가 지금 운영하는 사이트(예전 세트: `index.html` 탭 + `reserve.html` + `schedule.html`)를 덮어쓰면 예전 화면이 새 틀로 바뀜. 예전 것을 유지하고 싶으면 별도 경로에 올릴 것.
- 운영 사이트 주소: **`https://ilpum.yoyo925.workers.dev`** (Cloudflare Workers, 2026-10-05 사용자가 카카오 앱 등록 화면에서 알려 줌). 카카오 앱 회사명 `일품수산`.

## 8. 남은 일 (우선순위)

0. **(긴급) 예전 서버 무료 한도 초과** (전송량 202%, 로그 1,988%). 원인으로 보이는 것: 예전 `reserve.html` 의 저장 실패 시 **무한 즉시 재시도**(`catch` 에서 `dirty=true` → 바로 `pushDay` 재호출) — 테스트에서 14초에 3,500건 요청. 새 화면은 고침(점점 느리게 재시도, 로그인 오류는 반복 안 함). **새 `dist/` 를 배포하고 예전 화면을 닫아야** 멈춤. 근무표 앱도 저장·확인 실패 시 점점 느리게 재시도하도록 고침.
0-1. **예약 이전(진행 중):** 예약은 새 서버의 `res_days`(예전 `reservations_day` 와 같은 모양: 매장·날짜·JSON·rev, RLS=그 매장 사람만)로 **그대로** 옮김(평평한 `reservations` 표로 바꾸는 계획은 접음 — 화면 로직 보존·무손실이 빨라서). 이전 도구(`ilpum-migrate.html`)가 `sch_mig_put_resdays` 로 넣음. 창구는 닫혀 있음 → 사용자가 PC에서 실행할 때 다시 열 것(§4). 급여(`일품집_급여.html`)는 아직 예전 서버 → 가맹점에는 메뉴 숨김. 예전 화면은 새 배포 후 쓰지 말 것.
1. **실서버 확인(최우선, 미확인):** 배포 후 폰·PC에서 ① `ilpum` 로그인과 자동 로그인 ② 오늘 현황(예약·출근) ③ 사진 공유/복사/저장 ④ 스케줄 저장이 Supabase에 들어가는지. 문제가 나오면 브라우저 콘솔 오류부터.
2. **예전 → 새 서버 이전 실행:** `ilpum-migrate.html` 을 사장님 PC에서 실행(창구 재오픈 필요 — §4). 근무표는 "통째로 바꾸기"가 기본값(지금 들어 있는 10월 엑셀 임시 자료를 지움, 바꾸기 전 백업 파일 자동 저장). 끝나면 **창구 닫기.** 예약은 삭제·취소 제외, 시간 없는 것은 `00:00`+메모.
3. **예약 화면을 새 서버로 전환:** `reserve.html` 을 새 `reservations`/`dining_tables` 로 옮기고, 오늘 현황의 예약 출처(`OLD`)도 함께 바꿀 것. 새 `dining_tables` 는 본점 40개(1층 1–24, 2층 42–53, 룸 R1–R4)로 예전 배치(1–53 + 룸 세부)와 **달라서** 테이블 번호가 안 맞을 수 있음 → 배치도를 사용자와 확인해 맞출 것. (`reservations.table_no` 는 자유 텍스트라 이전 자료는 예전 번호 그대로 들어감.)
4. **급여 계산기를 새 근무표에 연결:** 지금은 예전 서버 `schedule_state` 를 읽음. 새 `sch_items`(특히 `pay`)를 읽도록 바꾸고 `workersOn` 을 `core.js` 의 `resolve` 기반으로 교체. `legacy/patched/일품집_급여.html` 에 `applyCond`(출근시간·금액 반영) 구현이 이미 있음(예전 서버용). 금액은 로그인한 본사 계정에서만 읽을 수 있음.
4-1-a. **유천점 이전 도구(2026-10-02):** `src/yucheon/import.html` → `dist/yucheon-import.html`(배포 폴더에 올리지 말고 가게 PC에서 파일로 열기). 본사 계정으로 새 서버에 로그인(RLS 로 유천점 칸에 직접 씀, 이전 창구 불필요) → 사용자가 붙여 넣은 유천점 URL·키(로그인 있으면 이메일·비번)로 `schedule_state`/`reservations_day`(본점 예전 사이트와 같은 모양이라고 가정)를 읽어 → `MIG.convertSchedule` 로 변환해 유천점 칸에 "없는 줄만 추가", 예약은 id별 더 늦게 고친 쪽(`u`) 합침. 읽은 내용은 JSON 백업 파일로 자동 저장. 테스트 `tests/t41.py`(가짜 서버). 유천점 서버 구조가 다르면 표 이름부터 확인해야 함.
4-1. **(보류, 2026-10-01 사용자 결정) 유천점 기존 사이트(`yucheonjeom.netlify.app`, Supabase `vijisdwfbhggnmshlmcl`) 자료 이전:** 그 서버는 이 Supabase 계정 밖(다른 계정)이고, 사용자가 가진 `config.js` 의 anon 키로는 모든 요청이 401(키 오타·정지·교체 추정, 표가 있어서 막힌 게 아님). 대시보드 접근 불가. 사용자가 "일단 하지 말고 두자"고 함 → **먼저 건드리지 말 것.** 재개하려면 ① 그 사이트가 지금 실제로 도는지 ② 가입 메일함에서 supabase 계정 주인 찾기 ③ 대시보드 Table Editor CSV 또는 앱의 백업/엑셀 받기. `src/inspect/yc-check.html`(읽기 전용 확인 페이지, 빌드가 `keys.json` 의 `yc` 로 키를 채움, 배포 폴더에 올리지 말 것)가 있음. 새 시스템에는 유천점 매장 칸이 이미 있고 점주 계정(`yucheon`)만 만들면 됨.
5. **가맹점 켜기:** 가맹점 계정은 Supabase Authentication에서 `아이디@ilpum.invalid` 로 만든 뒤 설정 → 계정 연결(또는 `sch_add_member`). 매장 추가는 본사 현황 화면(`sch_create_store`). 가맹점 초기 설정(포지션)은 본점 것을 복사하는 기능이 **없음**.
6. **정리할 보안 사항:** 기존 `staff`/`shifts` RLS(본사가 모든 매장을 봄) 재검토 · 강한 비밀번호 · 유출 비밀번호 검사 켜기 · `audit_log` 정책 · 가맹사업법/개인정보 관련 변호사 확인.
7. **예전 근무표에 있던 기능 중 새 앱에 없는 것:** 엑셀로 받기, 인쇄용 월간 A4 2쪽. 필요하면 다시 만들 것(엑셀 표기 `xlTime` 은 `legacy/patched/schedule.html` 참고).
8. **통합 틀 보강 아이디어:** 전체 매장 선택(본사), 오늘 현황의 예약금·인건비 카드(예약금 자료 구조 미확인), 발주 관리 자체 화면.

## 9. 함정 · 교훈 (실제로 겪은 것)

- **예전 파일 ↔ 새 파일 혼동:** 사용자가 "원래 쓰던 내용이 안 보인다"고 했던 원인이 서로 다른 Supabase였음. 화면을 고칠 때 **어느 서버를 읽는지** 항상 확인.
- **공개 키는 손으로 옮겨 적지 말 것.** 한 글자 틀려 로그인이 안 됨 → 파일에서 프로그램으로 복사하고 JWT를 디코드해 `ref`·`role` 을 확인(`eyJ…` 의 가운데 부분).
- **CSS 클래스 이름 충돌:** 끌 때 따라다니는 칩 이름을 `.ghost` 로 했다가 `.btn.ghost` 버튼이 화면 밖으로 튀어나감 → `.dghost`. 전역 클래스는 접두사를 붙일 것.
- `const APP=…` 는 `window.APP` 가 아님. 바깥에서 읽을 땐 `frame.contentWindow.eval('APP.view')`.
- Supabase REST: 기본 1000행 제한 → `Range` 헤더로 페이지 넘김(`pagedGet`). 업서트는 `?on_conflict=컬럼&Prefer: resolution=merge-duplicates`. 브라우저에서 `Content-Range` 는 CORS로 안 읽힐 수 있어 **개수는 직접 세는 대체 수단**을 둠.
- 권한 검사에서 `null not in (…)` 은 `null` → 통과해 버림. `coalesce(role,'') not in (…)` 로 쓸 것.
- RLS가 켜진 표에 익명 쓰기를 열지 말고 **검증하는 RPC 함수**를 통해서만 쓰게 했음(쓰기 범위·종류·시간 제한을 함수 안에서 강제).
- 채팅 환경의 미리보기(iframe 샌드박스)는 `blob:` 이미지·클립보드·공유가 막히고 외부 접속도 안 됨 → 사진 미리보기는 `data:` URL + 캔버스 대체로 구현. **사용자가 미리보기 화면에서 열어 보고 "안 된다"고 하는 경우가 잦았으니**, 증상이 접속 문제인지 코드 문제인지 먼저 구분할 것(접속 막힘은 "서버에 연결하지 못했어요" 화면이 뜸).
- **재시도는 반드시 점점 느리게.** 실패한 저장·확인을 곧바로 다시 부르면(`finally`/`dirty` 재호출 포함) 기기 하나가 초당 수 건씩 영원히 서버를 두드려 무료 한도를 며칠 만에 넘김. 테스트(`tests/t19.py` 4번)로 "서버가 500을 줄 때 요청 수"를 확인할 것.
- **전송량 규칙(무료 한도: 전송량 5GB·로그 1GB):** 자동 확인은 근무표 60초·예약 30초·오늘 현황 60초(예약은 rev만 먼저, 근무표는 30분 캐시), **10분 동안 아무도 안 만지면 멈추고** 다시 만지면 바로 확인. 가려진 창(통합 틀의 다른 탭)은 확인 안 함. 발주 화면은 자동 확인 없음. 새 화면을 만들 때 같은 규칙을 지키고 `tests/t22.py`(가짜 시계로 몇 시간 돌려 요청 수 세기)로 확인할 것.
- **예약 화면은 실시간(Supabase Realtime)**: `res_days` 를 `supabase_realtime` 발행에 넣었고(마이그레이션 `res_days_realtime`), 화면이 웹소켓(`/realtime/v1/websocket?vsn=1.0.0`, Phoenix 프로토콜 직접 구현)으로 자기 매장의 `res_days` 변경을 받아 바뀐 날짜만 다시 받음. 헤더에 `● 실시간` / `○ 30초마다 확인` 표시. 연결되면 5분마다 안전 확인만, 안 되면 30초 확인(30분 방치 시 쉼). **실서버에서 `● 실시간` 표시가 뜨는 것을 사용자가 확인함(2026-10-01)** — 연결·가입은 됨. 다른 기기에서 추가한 예약이 바로 뜨는지는 사용자 확인 대기(프로토콜은 기억·가짜 웹소켓 테스트 `tests/t23.py` 기준). 안 되면 콘솔 오류부터.
- **근무표도 실시간(2026-10-01):** `sch_items` 도 `supabase_realtime` 발행에 넣음(`supabase/migrations/20261001_realtime.sql`). `src/schedule/app.js` 의 `rtStart(sid)` 가 매장을 열 때마다 연결(매장 바꾸면 새로), 변경 알림이 오면 `since` 로 바뀐 줄만 받음. 사이드 상태 글자가 `연결됨 · 실시간`. 연결되면 5분마다 안전 확인, 안 되면 60초 확인(10분 방치 시 쉼). 로그인 없이 보기(anon)는 실시간 없이 60초 확인. 테스트 `tests/t24.py`. **실서버 동작은 배포 후 확인 필요**(예약 쪽 `● 실시간` 표시는 확인됨).
- 로그인 토큰 갱신은 여러 화면(통합 틀·근무표·예약)이 동시에 하면 서로의 토큰을 무효로 만들 수 있어 `navigator.locks` 로 한 번에 한 화면만 함, 설정 저장(`saveConf`)은 다른 화면이 갱신한 토큰을 지우지 않게 병합.
- 날짜는 한국 시간 기준 로컬 날짜(`ds(new Date())`). 테스트에서 고정 날짜가 필요하면 `Date` 를 덮어씀.
- 파일을 고칠 때 `app.js` 같은 조각 파일을 고친 뒤 **반드시 `sh build_all.sh`** 로 dist를 다시 만들 것(dist 파일을 직접 고치면 다음 빌드에서 사라짐).

## 10. 첫 작업 제안

1. `git init && git add -A && git commit -m "채팅에서 인수인계"` (이 시점을 되돌릴 기준점으로).
2. `sh build_all.sh` 가 되는지, `dist/` 가 사용자에게 전달된 것과 같은지 확인.
3. Supabase MCP/CLI가 연결돼 있으면 `sch_*` 표·함수·정책을 실제로 조회해 §4와 일치하는지 확인.
4. §8-1 실서버 확인부터. 결과를 사용자에게 짧게 보고.
