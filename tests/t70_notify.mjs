// naver-notify 서버 함수 시험 (Deno 없이 Node 로): 가짜 DB 로 새 예약·중복·5인 이상·취소·변경·토큰 확인
// 실행: node tests/t70_notify.mjs  (esbuild 필요: npm i -D esbuild 또는 ESBUILD 경로 지정)
const { build } = await import(process.env.ESBUILD || 'esbuild');
import fs from 'fs'; import path from 'path'; import os from 'os';
const HQ='0134d989-757a-4b60-9cb3-93245de2cac8', YC='ad2ffdae-f76b-44cd-a6c6-58514c4e4638';
const DB={ stores:[{id:HQ,name:'일품집 본점'},{id:YC,name:'유천점'}], res_days:[], sync_state:[], sch_items:[{store_id:HQ,kind:'cfg',id:'tables',deleted:false,data:{floors:[{key:'1',name:'1층',groups:[{title:'홀',cols:[['1','2','3'],['6','7']]}]},{key:'r',name:'룸',groups:[{title:'룸',cols:[['R1-1','R1-2']]}]}],seats:{'6':6,'7':6}}}] };
const mock=`export function createClient(){ const DB=globalThis.__DB;
  function q(t){ let rows=()=>DB[t]; const f=[]; let op='select', body=null, single=false;
    const run=()=>{ let r=DB[t].filter(x=>f.every(fn=>fn(x)));
      if(op==='update'){ r.forEach(x=>Object.assign(x,JSON.parse(JSON.stringify(body)))); return {data:r.map(x=>({rev:x.rev})),error:null}; }
      if(single) return {data:r[0]?JSON.parse(JSON.stringify(r[0])):null,error:null};
      return {data:JSON.parse(JSON.stringify(r)),error:null}; };
    const b={ select(){ return b; }, eq(k,v){ f.push(x=>x[k]===v); return b; }, gte(k,v){ f.push(x=>x[k]>=v); return b; },
      maybeSingle(){ single=true; return Promise.resolve(run()); }, update(o){ op='update'; body=o; return b; },
      insert(o){ if(DB[t].some(x=>x.store_id===o.store_id&&x.id===o.id)) return Promise.resolve({error:{message:'dup'}}); DB[t].push(JSON.parse(JSON.stringify(o))); return Promise.resolve({error:null}); },
      upsert(o){ const i=DB[t].findIndex(x=>o.key!=null?x.key===o.key:(x.store_id===o.store_id&&x.kind===o.kind&&x.id===o.id)); if(i>=0) DB[t][i]=o; else DB[t].push(o); return Promise.resolve({error:null}); },
      then(res,rej){ return Promise.resolve(run()).then(res,rej); } };
    return b; }
  return { from:q }; }`;
const dir=fs.mkdtempSync(path.join(os.tmpdir(),'nt-')); fs.writeFileSync(path.join(dir,'mock.js'),mock);
const src=fs.readFileSync('supabase/functions/naver-notify/index.ts','utf8').replace('__NOTIFY_TOKEN__','TESTTOKEN');
fs.writeFileSync('supabase/functions/naver-notify/_test_index.ts',src);
let handler; globalThis.Deno={ serve:(h)=>{ handler=h; }, env:{ get:()=> 'x' } }; globalThis.__DB=DB;
try{ await build({ entryPoints:['supabase/functions/naver-notify/_test_index.ts'], bundle:true, format:'esm', platform:'node', outfile:path.join(dir,'fn.mjs'), alias:{'npm:@supabase/supabase-js@2':path.join(dir,'mock.js')}, logLevel:'error' }); }
finally{ fs.unlinkSync('supabase/functions/naver-notify/_test_index.ts'); }
await import(path.join(dir,'fn.mjs'));
const RealDate=Date; const T=new RealDate('2026-10-10T06:00:00Z').getTime();   // 한국 15:00
const call=async(text,tok='TESTTOKEN')=>{ const r=await handler(new Request('https://x/functions/v1/naver-notify?t='+tok,{method:'POST',body:JSON.stringify({title:text.split('\n')[0],text:text.split('\n').slice(1).join('\n')})})); return [r.status, await r.json()]; };
let ok=true; const chk=(n,c,x='')=>{ ok&&=!!c; console.log((c?'OK  ':'FAIL'),n,x); };
const day=(d,s=HQ)=>(DB.res_days.find(x=>x.store_id===s&&x.id===d)||{data:{items:[]}}).data.items.filter(x=>!x.deleted);
// Date 고정
globalThis.Date=class extends RealDate{ constructor(...a){ if(!a.length) super(T+(RealDate.now()-st0)); else super(...a); } static now(){ return T+(RealDate.now()-st0); } }; const st0=RealDate.now();
const NEWN='일품집 본점, 예약신청\n우상태님, 일품집 본점 예약, 2026.10.11.(일) 오후 5:30, 4명 (성인4), 새로운 예약이 접수되었습니다.';
let [s,j]=await call(NEWN,'wrong'); chk('토큰 틀리면 거절', s===401);
[s,j]=await call(NEWN); chk('새 예약 추가', j.ok&&day('2026-10-11').some(x=>x.name==='우상태'&&x.time==='17:30'&&x.pp==='4'&&x.auto==='new'&&x.tables.join()==='2'), JSON.stringify(j));
[s,j]=await call(NEWN); chk('같은 알림 또 오면 중복 안 넣음', j.skip==='이미 있는 예약'&&day('2026-10-11').length===1, JSON.stringify(j));
[s,j]=await call('일품집 본점, 예약신청\n박단체님, 일품집 본점 예약, 2026.10.11.(일) 오후 6:00, 6명 (성인6), 새로운 예약이 접수되었습니다.'); chk('6명 → 6인석 자동 지정', j.ok&&day('2026-10-11').some(x=>x.name==='박단체'&&x.tables.join()==='6'), JSON.stringify(day('2026-10-11')));
[s,j]=await call('일품집 본점, 예약신청\n이팔명님, 일품집 본점 예약, 2026.10.11.(일) 오후 6:00, 8명 (성인8), 새로운 예약이 접수되었습니다.'); chk('8명 → (8인석이 없는 배치라) 룸1 통째', j.ok&&day('2026-10-11').some(x=>x.name==='이팔명'&&x.tables.join()==='R1-1,R1-2'), JSON.stringify(day('2026-10-11')));
[s,j]=await call('일품집 본점, 예약신청\n구단체님, 일품집 본점 예약, 2026.10.11.(일) 오후 6:00, 9명 (성인9), 새로운 예약이 접수되었습니다.'); chk('9인 이상도 넣되 테이블은 비움', j.ok&&day('2026-10-11').some(x=>x.name==='구단체'&&x.pp==='9'&&x.tables.length===0), JSON.stringify(j));
for(const nm of ['박단체','이팔명','구단체']){ const r=DB.res_days.find(x=>x.store_id===HQ&&x.id==='2026-10-11'); r.data.items=r.data.items.filter(x=>x.name!==nm); }
[s,j]=await call('일품집 본점\n리뷰가 등록되었습니다. AI가 답글을 준비하고 있어요!'); chk('리뷰 알림은 무시', j.skip==='예약 알림 아님');
[s,j]=await call('일품집 본점, 예약변경\n우상태님, 일품집 본점 예약, 2026.10.12.(월) 오후 7:00, 3명 (성인3), 예약이 변경되었습니다.');
chk('변경: 10/11 → 10/12 19:00 3명', j.ok&&!day('2026-10-11').some(x=>x.name==='우상태')&&day('2026-10-12').some(x=>x.name==='우상태'&&x.time==='19:00'&&x.pp==='3'&&x.auto==='chg'), JSON.stringify(j));
[s,j]=await call('일품집 본점, 예약취소\n우상태님, 일품집 본점 예약, 2026.10.12.(월) 오후 7:00, 3명 (성인3), 예약이 취소되었습니다.');
const w=day('2026-10-12').find(x=>x.name==='우상태'); chk('취소: 지우지 않고 테이블 칸에 네이버취소', j.ok&&w&&w.tnote==='네이버취소'&&w.auto==='cxl', JSON.stringify(j));
[s,j]=await call('일품집 본점, 예약취소\n우상태님, 일품집 본점 예약, 2026.10.12.(월) 오후 7:00, 3명 (성인3), 예약이 취소되었습니다.'); chk('또 취소 알림 → 이미 취소', j.cancel==='이미 취소돼 있음', JSON.stringify(j));
[s,j]=await call('유천점, 예약신청\n김유천님, 유천점 예약, 2026.10.13.(화) 오후 6:00, 2명 (성인2), 새로운 예약이 접수되었습니다.'); chk('유천점 알림 → 유천점 칸에 들어감(본점엔 없음)', j.ok&&j.store==='유천점'&&day('2026-10-13',YC).some(x=>x.name==='김유천'&&x.auto==='new')&&day('2026-10-13',HQ).length===0, JSON.stringify(j));
{ await call('일품집 본점, 예약신청\n김준현님, 일품집 본점 예약, 2026.10.20.(화) 오후 6:00, 3명 (성인3), 새로운 예약이 접수되었습니다.');
  const it=day('2026-10-20').find(x=>x.name==='김준현'); if(it) it.time='17:30';   // 매장에서 시간을 고침
  const [s2,j2]=await call('일품집 본점, 예약확정\n김준현님, 일품집 본점 예약, 2026.10.20.(화) 오후 6:00, 3명 (성인3), 새로운 예약이 확정되었습니다.');
  chk('신청으로 넣은 예약을 매장이 시간 고친 뒤 확정 알림 → 또 넣지 않음', j2.skip==='이미 있는 예약'&&day('2026-10-20').filter(x=>x.name==='김준현').length===1, JSON.stringify(j2)+JSON.stringify(day('2026-10-20'))); }
[s,j]=await call('주식회사 일품집달서직영점, 예약확정김민정님, 주식회사 일품집달서직영점, 2026.10.25.(일) 오후 7:30, 5명 (성인5), 새로운 예약이 확정되었습니다.'); chk('달서직영점(=유천점 네이버 이름) 알림 → 유천점', j.ok&&j.store==='유천점'&&day('2026-10-25',YC).some(x=>x.name==='김민정'), JSON.stringify(j));
[s,j]=await call('일품집 동성로점, 예약신청홍길동님, 일품집 동성로점 예약, 2026.10.25.(일) 오후 7:30, 2명 (성인2), 새로운 예약이 접수되었습니다.'); chk('다른 매장 알림은 무시', j.skip==='본점·유천점 알림 아님', JSON.stringify(j));
chk('기록 남김', (DB.sync_state.find(x=>x.key==='naver_log')||{val:[]}).val.length>=8);
{ const r=await call('일품집 본점, 예약신청김지수님, 일품집 본점 예약, 2026.10.14.(수) 오후 3:30, 2명 (성인2), 새로운 예약이 접수되었습니다.일품집 본점, 예약신청\n김지수님, 일품집 본점 예약, 2026.10.14.(수) 오후 3:30, 2명 (성인2), 새로운 예약이 접수되었습니다.');
  chk('제목·내용이 붙어 와도 이름 김지수', day('2026-10-14').some(x=>x.name==='김지수'&&x.time==='15:30'), JSON.stringify(r[1])); }
{ const r1=await call('일품집 본점, 예약신청\n박일번님, 일품집 본점 예약, 2026.10.15.(목) 오후 6:00, 2명 (성인2), 새로운 예약이 접수되었습니다.');
  const r2=await call('일품집 본점, 예약신청\n최이번님, 일품집 본점 예약, 2026.10.15.(목) 오후 7:00, 4명 (성인4), 새로운 예약이 접수되었습니다.');
  const r3=await call('일품집 본점, 예약신청\n정삼번님, 일품집 본점 예약, 2026.10.15.(목) 오후 9:30, 2명 (성인2), 새로운 예약이 접수되었습니다.');
  const g=n=>day('2026-10-15').find(x=>x.name===n).tables.join();
  chk('2시간 안 겹치는 자리로(주로 쓰는 순서): 18시 2번, 19시 3번, 21:30 다시 2번', g('박일번')==='2'&&g('최이번')==='3'&&g('정삼번')==='2', [g('박일번'),g('최이번'),g('정삼번')].join('/')); 
  await call('일품집 본점, 예약신청\n가나님, 일품집 본점 예약, 2026.10.15.(목) 오후 6:30, 2명 (성인2), 새로운 예약이 접수되었습니다.');
  await call('일품집 본점, 예약신청\n다라님, 일품집 본점 예약, 2026.10.15.(목) 오후 6:40, 2명 (성인2), 새로운 예약이 접수되었습니다.');
  chk('작은 자리가 다 차면 큰 자리·룸 대신 미정', g('가나')==='1'&&g('다라')==='', g('가나')+'/'+g('다라')); }
{ DB.sch_items=[]; await call('일품집 본점, 예약신청\n홍길순님, 일품집 본점 예약, 2026.10.16.(금) 오후 6:00, 2명 (성인2), 새로운 예약이 접수되었습니다.');
  await call('일품집 본점, 예약신청\n이영자님, 일품집 본점 예약, 2026.10.16.(금) 오후 6:00, 2명 (성인2), 새로운 예약이 접수되었습니다.\n요청사항 : 창가 자리 부탁해요');
  const g=n=>day('2026-10-16').find(x=>x.name===n).tables.join();
  chk('배치 저장 안 한 본점: 주로 쓰는 12번부터, 창가 요청은 2번(창가 중 주로 쓰는 자리)', g('홍길순')==='12'&&g('이영자')==='2', g('홍길순')+'/'+g('이영자'));
  const names=['가','나','다','라','마','바','사','아','자','차','카','타','파','하','거'].map(c=>c+'순자');
  for(const nm of names) await call(`일품집 본점, 예약신청\n${nm}님, 일품집 본점 예약, 2026.10.17.(토) 오후 6:00, 2명 (성인2), 새로운 예약이 접수되었습니다.`);
  const order=names.map(n=>day('2026-10-17').find(x=>x.name===n).tables.join()).join(',');
  chk('순서: 12,13,14,16,17,18,2,3,4,21,22,25,26,27 다음 나머지 1층(11)', order==='12,13,14,16,17,18,2,3,4,21,22,25,26,27,11', order); }
{ await call('일품집 본점, 예약신청박서연님, 일품집 본점 예약, 2026.10.18.(일) 오후 6:00, 2명 (성인2), 10% 할인쿠폰 사용, 새로운 예약이 접수되었습니다.');
  const x=day('2026-10-18').find(x=>x.name==='박서연'); chk('쿠폰 예약 → 메모에 10%', x&&x.req==='10%'&&x.time==='18:00', JSON.stringify(x&&[x.name,x.time,x.req])); }
{ // 확정 대기 안내: 재촉 알림엔 매장 이름이 없음 → 신청만 오고 확정 안 된 매장에만 켬 (2026-10-25 달서 예약 때문에 본점에 뜸)
  DB.sch_items=[]; const W=s=>(DB.sch_items.find(x=>x.store_id===s&&x.id==='naver_wait')||{data:{}}).data;
  const NAG='확정이 필요한 예약건이 있습니다.\n확정이 필요한 예약건이 있습니다. 빠른 확정 부탁드립니다.';
  await call('주식회사 일품집달서직영점, 예약신청박경숙님, 주식회사 일품집달서직영점, 2026.10.10.(토) 오후 7:30, 5명 (성인5), 새로운 예약이 접수되었습니다.');
  await call(NAG);
  chk('유천점(달서) 신청만 남음 → 재촉 알림은 유천점에만, 본점엔 안 켬', W(YC).at&&!W(HQ).at, JSON.stringify([W(HQ),W(YC)]));
  await call('주식회사 일품집달서직영점, 예약확정박경숙님, 주식회사 일품집달서직영점, 2026.10.10.(토) 오후 7:30, 5명 (성인5), 새로운 예약이 확정되었습니다.');
  chk('확정 알림 → 유천점 안내 끔·남은 이름 없음', W(YC).done>=W(YC).at&&!(W(YC).pend||[]).length, JSON.stringify(W(YC)));
  await call('일품집 본점, 예약신청\n본점손님님, 일품집 본점 예약, 2026.10.10.(토) 오후 6:00, 2명 (성인2), 새로운 예약이 접수되었습니다.');
  await call(NAG);
  chk('본점 신청이 남으면 본점에 켬', W(HQ).at&&(W(HQ).pend||[]).some(p=>p.n==='본점손님'), JSON.stringify(W(HQ)));
  DB.sch_items=[]; await call(NAG); chk('어느 매장도 모르면 예전처럼 본점', W(HQ).at&&!W(YC).at);
  // 당일 예약일 때만 켬 (2026-10-25 사용자: 급한 건 당일). 이 시험에서 오늘 = 10/10
  DB.sch_items=[]; await call('일품집 본점, 예약신청\n다른날님, 일품집 본점 예약, 2026.10.20.(화) 오후 6:00, 2명 (성인2), 새로운 예약이 접수되었습니다.'); await call(NAG);
  chk('다른 날 예약만 확정 대기 → 안내 안 켬', !W(HQ).at, JSON.stringify(W(HQ)));
  await call('일품집 본점, 예약신청\n김당일님, 일품집 본점 예약, 2026.10.10.(토) 오후 7:00, 2명 (성인2), 새로운 예약이 접수되었습니다.'); await call(NAG);
  chk('당일 예약이 확정 대기 → 안내 켬', W(HQ).at&&(W(HQ).pend||[]).some(p=>p.n==="김당일"&&p.d==='2026-10-10'), JSON.stringify(W(HQ)));
  await call('일품집 본점, 예약확정\n김당일님, 일품집 본점 예약, 2026.10.10.(토) 오후 7:00, 2명 (성인2), 새로운 예약이 확정되었습니다.'); const at0=W(HQ).at; await call(NAG);
  chk('당일 건 확정 뒤엔 (다른 날 대기만 남아) 안내 다시 안 켬', W(HQ).done>=at0&&W(HQ).at===at0, JSON.stringify(W(HQ))); }
console.log(ok?'전체 OK':'실패 있음');
