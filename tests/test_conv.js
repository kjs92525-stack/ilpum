const fs=require('fs'), vm=require('vm'); const MIG=require('./mig.js');
const old=JSON.parse(fs.readFileSync('old_state.json','utf8'));
const posNames=['카운터','홀','그릴','주방','장치','주차','장잡','배송'];
const existing=posNames.map(n=>({name:n,color:'#000',req:[0,0,0,0,0,0,0]}));
const r=MIG.convertSchedule(old,existing);
console.log('변환:', Object.fromEntries(Object.entries(r.items).map(([k,v])=>[k,Object.keys(v).length])), '| 추가된 포지션', r.added);
// 새 앱 엔진으로 10월 전체를 돌려 엑셀 스케줄과 비교
const ctx={console,localStorage:{getItem(){return null},setItem(){}},sessionStorage:{getItem(){return null}},document:{querySelector(){return null}},navigator:{},window:{},setTimeout,clearTimeout,Date,Math,JSON,Object,Array,Set,Map};
vm.createContext(ctx); vm.runInContext(fs.readFileSync('/home/claude/fr/core.js','utf8')+';globalThis.__api={buildD,resolve,pd};',ctx);
const {buildD,resolve,pd}=ctx.__api; const expected=JSON.parse(fs.readFileSync('/home/claude/imp/expected.json','utf8'));
const D=buildD({cfg:{store:{name:'x'},positions:r.positions},staff:r.items.staff,dc:r.items.dc,spot:r.items.spot,aw:r.items.aw,pay:r.items.pay,rule:r.items.rule,sales:{}},'x');
let bad=0,total=0;
for(const date of Object.keys(expected).sort()){
  const R=resolve(D,pd(date)); const got={}; posNames.forEach(p=>got[p]=[]);
  R.list.forEach(x=>{ (got[x.pos]=got[x.pos]||[]).push(x.name+((x.sh&&x.sh.k==='pm')?'(오후)':'')); });
  const offAll=R.offs.filter(o=>!o.missing).map(o=>(o.reason==='고정휴무'||o.reason==='주간휴무')?o.name:o.name+'(휴무)');
  const E=expected[date];
  posNames.forEach(p=>{ total++; if(JSON.stringify([...(E.pos[p]||[])].sort())!==JSON.stringify([...(got[p]||[])].sort())){ bad++; console.log('다름',date,p,E.pos[p],got[p]); } });
  total++; if(JSON.stringify([...E.off].sort())!==JSON.stringify([...offAll].sort())){ bad++; console.log('휴무 다름',date,E.off,offAll); }
}
console.log('엑셀과 비교:', total,'칸 중 다른 칸', bad);
// 메모 해석
for(const m of ['일급110,000','13','6.5','일당백6.5','11-19시','직원지원 / 11시 출근','']) console.log(JSON.stringify(m),'→',JSON.stringify(MIG.parseAlbaMemo(m,false)));
// 예약 변환
const rows=[{id:'2026-10-01',data:{items:[
 {id:'a1',name:'홍길동',phone:'010-1111-2222',time:'18:30',pp:'5+1',tables:['33','34'],req:'창가',tnote:'',done:true,u:1},
 {id:'a2',name:'김철수',phone:'',time:'',pp:'',tables:['R1-1','R1-2'],req:'',tnote:'취소 (노쇼)',done:false,u:1},
 {id:'a3',name:'',phone:'01033334444',time:'19:00',pp:'4',tables:[],req:'',tnote:'룸 문의',done:false,u:1},
 {id:'a4',name:'삭제된',time:'12:00',pp:'2',tables:['1'],deleted:true,u:1}]}},
 {id:'2026-10-02',data:{items:[{id:'a1',name:'홍길동',time:'18:30',pp:'2',tables:['5'],u:1}]}}];
const rr=MIG.convertReservations(rows,'STORE');
console.log('예약 변환', JSON.stringify(rr.stat)); rr.rows.forEach(x=>console.log(JSON.stringify(x)));
const again=MIG.convertReservations(rows,'STORE'); console.log('같은 입력 → 같은 id:', JSON.stringify(again.rows.map(x=>x.id))===JSON.stringify(rr.rows.map(x=>x.id)), '| 날짜만 다른 같은 원본 id는 다른 uuid:', rr.rows[0].id!==rr.rows[rr.rows.length-1].id);
console.log('uuid 형식:', rr.rows.every(x=>/^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/.test(x.id)));
