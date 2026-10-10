# 예약 화면(reserve.html)의 문자 해석기를 서버 함수(naver-notify)로 그대로 복사 — 화면과 서버가 같은 규칙을 쓰게
import re
s=open('src/reserve/reserve.html',encoding='utf-8').read()
a=s.index('function parseResText('); b=s.index('// 빈 테이블 추천',a)
f=s.index('function fmtPhone('); g=s.index('\n}\n',f)+3
out='''// 자동 생성 파일 — 고치지 말 것. 원본: src/reserve/reserve.html (tools/gen_notify_parse.py 가 빌드 때 복사)
const pad=(n)=>String(n).padStart(2,'0');
const ds=(d)=>`${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())}`;
'''+s[f:g]+'\n'+s[a:b]+'\nexport { parseResText, fmtPhone, ds };\n'
open('supabase/functions/naver-notify/parse.js','w',encoding='utf-8').write(out)
print('naver-notify/parse.js')
