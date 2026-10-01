"""통합관리 틀(index.html) 빌드: 근무표 계산 엔진(core.js 의 유틸 + 매장 데이터 + 엔진 부분)을 그대로 가져와 끼워 넣음
   실행: python3 src/portal/build.py   ->  dist/index.html"""
import os,json
here=os.path.dirname(os.path.abspath(__file__)); root=os.path.join(here,'..','..')
core=open(os.path.join(here,'..','schedule','core.js'),encoding='utf-8').read()
i=core.index('/* ================= 저장소'); j=core.index('/* ================= 매장 데이터')     # 저장소(Local/Remote) 부분은 제외
engine=core[:i]+'\n'+core[j:]
k=json.load(open(os.path.join(root,'keys.json')))
t=open(os.path.join(here,'shell.html'),encoding='utf-8').read()
out=t.replace('/*ENGINE*/',engine).replace('/*OLDKEY*/',k['old']).replace('/*NEWKEY*/',k['new'])
os.makedirs(os.path.join(root,'dist'),exist_ok=True)
open(os.path.join(root,'dist','index.html'),'w',encoding='utf-8').write(out); print('index.html',len(out),'bytes')
