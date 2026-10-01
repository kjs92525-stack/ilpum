const fs=require('fs'), vm=require('vm');
const ctx={console,localStorage:{getItem(){return null},setItem(){}},sessionStorage:{getItem(){return null}},document:{querySelector(){return null}},navigator:{},window:{},setTimeout,clearTimeout,Date,Math,JSON,Object,Array,Set,Map};
vm.createContext(ctx);
vm.runInContext(fs.readFileSync('/home/claude/fr/core.js','utf8')+`
;globalThis.__api={buildD,resolve,pd,shLbl,rulesSorted};`,ctx);
const {buildD,resolve,pd,shLbl}=ctx.__api;
const items=JSON.parse(fs.readFileSync('items.json','utf8')), expected=JSON.parse(fs.readFileSync('expected.json','utf8'));
const posNames=['카운터','홀','그릴','주방','장치','주차','장잡','배송'];
const cfg={store:{name:'일품집 본점'},positions:posNames.map(n=>({name:n,color:'#000',req:[0,0,0,0,0,0,0]}))};
const D=buildD({cfg,staff:items.staff,dc:items.dc,spot:items.spot,aw:items.aw,pay:items.pay,rule:{},sales:{}},'일품집 본점');
let bad=0, total=0; const report=[];
const sortk=a=>[...a].sort();
for(const date of Object.keys(expected).sort()){
  const R=resolve(D,pd(date)); const got={}; posNames.forEach(p=>got[p]=[]);
  R.list.forEach(x=>{ const t=x.name+((x.sh&&x.sh.k==='pm')?'(오후)':''); (got[x.pos]=got[x.pos]||[]).push(t); });
  const offs=R.offs.filter(o=>!o.missing).map(o=>o.reason==='고정휴무'||o.reason==='주간휴무'?null:o.name+'('+(o.reason==='월차'?'월차':'휴무')+')').filter(Boolean);
  // 엑셀의 휴무 줄: 고정휴무자 이름 + 예외 휴무자(휴무) 표시
  const offAll=R.offs.filter(o=>!o.missing).map(o=>(o.reason==='고정휴무'||o.reason==='주간휴무')?o.name:o.name+'(휴무)');
  const E=expected[date];
  posNames.forEach(p=>{ total++; const e=sortk(E.pos[p]||[]), g=sortk(got[p]||[]); if(JSON.stringify(e)!==JSON.stringify(g)){ bad++; report.push({date,pos:p,엑셀:e,앱:g,엑셀에만:e.filter(x=>!g.includes(x)),앱에만:g.filter(x=>!e.includes(x))}); } });
  const eo=sortk(E.off), go=sortk(offAll);
  total++; if(JSON.stringify(eo)!==JSON.stringify(go)){ bad++; report.push({date,pos:'휴무',엑셀에만:eo.filter(x=>!go.includes(x)),앱에만:go.filter(x=>!eo.includes(x))}); }
}
console.log('비교 칸',total,'| 다른 칸',bad);
report.slice(0,40).forEach(r=>console.log(JSON.stringify(r)));
// ---- 제목의 총 인원 / 오후 인원
const titles=JSON.parse(fs.readFileSync('titles.json','utf8')); let tb=0;
for(const date of Object.keys(titles).sort()){
  const R=resolve(D,pd(date)); const tot=R.list.length, pm=R.list.filter(x=>x.sh&&x.sh.k==='pm').length;
  if(tot!==titles[date][0]||pm!==titles[date][1]){ tb++; console.log('제목 불일치',date,'엑셀',titles[date],'앱',[tot,pm]); }
}
console.log('제목(총 인원·오후 인원) 비교', Object.keys(titles).length,'일 | 다른 날',tb);
