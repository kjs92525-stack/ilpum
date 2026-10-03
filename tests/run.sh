#!/bin/sh
# 화면 테스트 실행: sh tests/run.sh [t43 t45 ...]  (먼저 sh build_all.sh)
cd "$(dirname "$0")/.."
(cd dist && python3 -m http.server 8765 >/dev/null 2>&1) & A=$!
(cd dist-tools && python3 -m http.server 8766 >/dev/null 2>&1) & B=$!
trap 'kill $A $B 2>/dev/null' EXIT
sleep 1
if [ $# -gt 0 ]; then L="$*"; else L=$(ls tests/t*.py | sed 's#tests/##;s#\.py##'); fi
FAIL=""
for t in $L; do
  out=$(timeout 400 python3 tests/$t.py 2>&1); rc=$?
  if [ $rc -ne 0 ] || echo "$out" | grep -qE "FAIL|실패 있음|Traceback"; then FAIL="$FAIL $t"; echo "✗ $t"; else echo "✓ $t"; fi
done
[ -z "$FAIL" ] && echo "모두 통과" || { echo "확인 필요:$FAIL"; exit 1; }
