"""급여 계산기 빌드: 근무표 계산 엔진(core.js)을 그대로 끼워 넣고 공개 키를 채움
   실행: python3 src/payroll/build.py   ->  dist/일품집_급여.html"""
import os,json
here=os.path.dirname(os.path.abspath(__file__)); root=os.path.join(here,'..','..')
core=open(os.path.join(here,'..','schedule','core.js'),encoding='utf-8').read()
i=core.index('/* ================= 저장소'); j=core.index('/* ================= 매장 데이터')     # 저장소(Local/Remote) 부분은 제외
engine=core[:i]+'\n'+core[j:]
k=json.load(open(os.path.join(root,'keys.json')))
t=open(os.path.join(here,'pay.html'),encoding='utf-8').read()
out=t.replace('/*ENGINE*/',engine).replace('/*NEWKEY*/',k['new'])
os.makedirs(os.path.join(root,'dist'),exist_ok=True)
open(os.path.join(root,'dist','일품집_급여.html'),'w',encoding='utf-8').write(out); print('일품집_급여.html',len(out),'bytes')
