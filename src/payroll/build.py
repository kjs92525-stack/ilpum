"""근무·급여 집계기 빌드: 공개 키만 채움 (예전 급여 계산기의 근무표 엔진은 더 이상 쓰지 않음)
   실행: python3 src/payroll/build.py   ->  dist/pay.html"""
import os,json
here=os.path.dirname(os.path.abspath(__file__)); root=os.path.join(here,'..','..')
k=json.load(open(os.path.join(root,'keys.json')))
t=open(os.path.join(here,'pay.html'),encoding='utf-8').read()
out=t.replace('/*NEWKEY*/',k['new'])
os.makedirs(os.path.join(root,'dist'),exist_ok=True)
open(os.path.join(root,'dist','pay.html'),'w',encoding='utf-8').write(out); print('pay.html',len(out),'bytes')
