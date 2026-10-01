#!/bin/sh
# 전체 빌드 + 문법 검사 (Node 필요).  결과는 dist/ 폴더에 생김 -> 그 폴더를 배포
set -e
cd "$(dirname "$0")"
[ -f keys.json ] || { echo "keys.json 이 없어요 (공개 키 파일, 저장소에 안 올림). Supabase 대시보드 API 설정에서 anon 키를 복사해 {\"old\":\"…\",\"new\":\"…\"} 로 만드세요"; exit 1; }
python3 src/schedule/build.py && node --check src/schedule/_all.js
python3 src/portal/build.py
python3 src/migrate/build.py
python3 - <<'PY'
# 키만 채워서 그대로 복사하는 화면들 (예약·발주)
import json
k=json.load(open('keys.json'))
for src,dst in [('src/reserve/reserve.html','dist/reserve.html'),('src/order/order.html','dist/order.html'),('src/notice/notice.html','dist/notice.html'),('src/board/board.html','dist/board.html'),('src/inspect/yc-check.html','dist/yc-check.html')]:
    s=open(src,encoding='utf-8').read()
    s=s.replace('/*OLDKEY*/',k.get('old','')).replace('/*NEWKEY*/',k['new']).replace('/*ORDKEY*/',k.get('ord','/*ORDKEY*/')).replace('/*YCKEY*/',k.get('yc',''))
    open(dst,'w',encoding='utf-8').write(s)
PY
python3 src/payroll/build.py
echo "완료: dist/ 폴더를 배포하세요"
