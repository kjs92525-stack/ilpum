#!/bin/sh
# 전체 빌드 + 문법 검사 (Node 필요).  결과는 dist/ 폴더에 생김 -> 그 폴더를 배포
set -e
cd "$(dirname "$0")"
[ -f keys.json ] || { echo "keys.json 이 없어요 (공개 키 파일, 저장소에 안 올림). Supabase 대시보드 API 설정에서 anon 키를 복사해 {\"old\":\"…\",\"new\":\"…\"} 로 만드세요"; exit 1; }
mkdir -p dist dist-tools out
# 일회성 도구는 배포 폴더(dist)에 섞이지 않게 dist-tools/ 로 (인터넷에 올리지 말 것)
rm -f dist/site.html dist/yc-check.html dist/yucheon-import.html dist/ilpum-migrate.html
python3 src/schedule/build.py && node --check src/schedule/_all.js
python3 src/portal/build.py
python3 src/migrate/build.py
python3 - <<'PY'
# 키만 채워서 그대로 복사하는 화면들 (예약·발주)
import json
k=json.load(open('keys.json'))
for src,dst in [('src/reserve/reserve.html','dist/reserve.html'),('src/order/order.html','dist/order.html'),('src/notice/notice.html','dist/notice.html'),('src/board/board.html','dist/board.html'),('src/sangkwon/sangkwon.html','dist/sangkwon.html'),('src/inspect/yc-check.html','dist-tools/yc-check.html')]:
    s=open(src,encoding='utf-8').read()
    s=s.replace('/*OLDKEY*/',k.get('old','')).replace('/*NEWKEY*/',k['new']).replace('/*ORDKEY*/',k.get('ord','/*ORDKEY*/')).replace('/*YCKEY*/',k.get('yc',''))
    open(dst,'w',encoding='utf-8').write(s)
PY
python3 src/payroll/build.py
python3 - <<'PY'
import json
k=json.load(open('keys.json')); m=open('src/migrate/mig.js',encoding='utf-8').read().replace('if (typeof module','if (false && typeof module')
t=open('src/yucheon/import.html',encoding='utf-8').read()
open('dist-tools/yucheon-import.html','w',encoding='utf-8').write(t.replace('/*MIG*/',m).replace('/*NEWKEY*/',k['new']))
print('yucheon-import.html')
PY
mv dist/ilpum-migrate.html dist-tools/
# 상권분석은 따로 배포: 저장소에도 올려 두어 GitHub 에서 바로 받을 수 있게 (이름 index.html)
mkdir -p deploy/sangkwon out/sangkwon-upload && cp dist/sangkwon.html deploy/sangkwon/index.html && cp dist/sangkwon.html out/sangkwon-upload/index.html
rm -f out/ilpum-deploy.zip
(cd dist && zip -q ../out/ilpum-deploy.zip *.html)
echo "완료: dist/ 의 파일(또는 out/ilpum-deploy.zip)을 배포하세요. dist-tools/ 는 올리지 마세요"
