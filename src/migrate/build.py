"""이전 도구 빌드: mig.js(변환 로직) + tool.html + 공개 키
   실행: python3 src/migrate/build.py   ->  dist/ilpum-migrate.html"""
import os,json
here=os.path.dirname(os.path.abspath(__file__)); root=os.path.join(here,'..','..')
k=json.load(open(os.path.join(root,'keys.json')))
m=open(os.path.join(here,'mig.js'),encoding='utf-8').read().replace('if (typeof module','if (false && typeof module')
t=open(os.path.join(here,'tool.html'),encoding='utf-8').read()
out=t.replace('/*MIG*/',m).replace('/*OLDKEY*/',k['old']).replace('/*NEWKEY*/',k['new'])
os.makedirs(os.path.join(root,'dist'),exist_ok=True)
open(os.path.join(root,'dist','ilpum-migrate.html'),'w',encoding='utf-8').write(out); print('ilpum-migrate.html',len(out),'bytes')
