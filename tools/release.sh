#!/bin/sh
# 운영 반영: 테스트 사이트(deploy/main/public)에서 확인한 완성본을 운영 폴더(deploy/prod/public)로 복사.
# 먼저 `sh build_all.sh` 로 deploy/main/public 이 최신인지 확인하고, 복사 뒤 git commit·push 하면 Cloudflare 가 운영(ilpum)을 자동 배포함.
set -e
cd "$(dirname "$0")/.."
[ -d deploy/main/public ] || { echo "deploy/main/public 이 없어요. 먼저 sh build_all.sh"; exit 1; }
rm -rf deploy/prod/public && mkdir -p deploy/prod/public && cp deploy/main/public/*.html deploy/prod/public/
# 공개(anon) 키 외의 비밀이 섞였는지 마지막 확인
if grep -l "service_role\|sb_secret_" deploy/prod/public/*.html >/dev/null 2>&1; then echo "비밀 키가 들어 있어요. 중단"; rm -rf deploy/prod/public; exit 1; fi
echo "운영 폴더 갱신 완료: $(ls deploy/prod/public | wc -l)개 파일"
