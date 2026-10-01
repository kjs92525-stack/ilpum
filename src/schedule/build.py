"""근무표 앱 빌드: core.js + app.js + img.js + events.js 를 이어 붙여 shell.html 에 끼워 넣음
   실행: python3 src/schedule/build.py   ->  dist/ilpum-schedule.html"""
import os,json
here=os.path.dirname(os.path.abspath(__file__)); dist=os.path.join(here,'..','..','dist')
rd=lambda n: open(os.path.join(here,n),encoding='utf-8').read()
js=rd('core.js')+'\n'+rd('app.js')+'\n'+rd('img.js')+'\n'+rd('events.js')
k=json.load(open(os.path.join(here,'..','..','keys.json')))     # 공개(anon) 키는 저장소에 안 올림 -> 빌드 때 채움
out=rd('shell.html').replace('/*CSS*/',rd('app.css')).replace('/*JS*/',js).replace('/*OLDKEY*/',k['old']).replace('/*NEWKEY*/',k['new'])
os.makedirs(dist,exist_ok=True)
open(os.path.join(dist,'ilpum-schedule.html'),'w',encoding='utf-8').write(out)
open(os.path.join(here,'_all.js'),'w',encoding='utf-8').write(js)     # 문법 검사용: node --check src/schedule/_all.js
print('ilpum-schedule.html', len(out),'bytes')
