// naver-notify 서버 함수 시험 (Deno 없이 Node 로): 가짜 DB 로 새 예약·중복·5인 이상·취소·변경·토큰 확인
// 실행: node tests/t70_notify.mjs  (esbuild 필요: npm i -D esbuild 또는 ESBUILD 경로 지정)
const { build } = await import(process.env.ESBUILD || 'esbuild');
import fs from 'fs'; import path from 'path'; import os from 'os';
const HQ='0134d989-757a-4b60-9cb3-93245de2cac8', YC='ad2ffdae-f76b-44cd-a6c6-58514c4e4638';
const DB={ stores:[{id:HQ,name:'일품집 본점'},{id:YC,name:'유천점'}], res_days:[], sync_state:[] };
const mock=`export function createClient(){ const DB=globalThis.__DB;
  function q(t){ let rows=()=>DB[t]; const f=[]; let op='select', body=null, single=false;
    const run=()=>{ let r=DB[t].filter(x=>f.every(fn=>fn(x)));
      if(op==='update'){ r.forEach(x=>Object.assign(x,JSON.parse(JSON.stringify(body)))); return {data:r.map(x=>({rev:x.rev})),error:null}; }
      if(single) return {data:r[0]?JSON.parse(JSON.stringify(r[0])):null,error:null};
      return {data:JSON.parse(JSON.stringify(r)),error:null}; };
    const b={ select(){ return b; }, eq(k,v){ f.push(x=>x[k]===v); return b; }, gte(k,v){ f.push(x=>x[k]>=v); return b; },
      maybeSingle(){ single=true; return Promise.resolve(run()); }, update(o){ op='update'; body=o; return b; },
      insert(o){ if(DB[t].some(x=>x.store_id===o.store_id&&x.id===o.id)) return Promise.resolve({error:{message:'dup'}}); DB[t].push(JSON.parse(JSON.stringify(o))); return Promise.resolve({error:null}); },
      upsert(o){ const i=DB[t].findIndex(x=>x.key===o.key); if(i>=0) DB[t][i]=o; else DB[t].push(o); return Promise.resolve({error:null}); },
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
[s,j]=await call(NEWN); chk('새 예약 추가', j.ok&&day('2026-10-11').some(x=>x.name==='우상태'&&x.time==='17:30'&&x.pp==='4'&&x.auto==='new'&&x.tables.length===0), JSON.stringify(j));
[s,j]=await call(NEWN); chk('같은 알림 또 오면 중복 안 넣음', j.skip==='이미 있는 예약'&&day('2026-10-11').length===1, JSON.stringify(j));
[s,j]=await call('일품집 본점, 예약신청\n박단체님, 일품집 본점 예약, 2026.10.11.(일) 오후 6:00, 6명 (성인6), 새로운 예약이 접수되었습니다.'); chk('5인 이상은 안 넣음', /5인 이상/.test(j.skip)&&day('2026-10-11').length===1, JSON.stringify(j));
[s,j]=await call('일품집 본점\n리뷰가 등록되었습니다. AI가 답글을 준비하고 있어요!'); chk('리뷰 알림은 무시', j.skip==='예약 알림 아님');
[s,j]=await call('일품집 본점, 예약변경\n우상태님, 일품집 본점 예약, 2026.10.12.(월) 오후 7:00, 3명 (성인3), 예약이 변경되었습니다.');
chk('변경: 10/11 → 10/12 19:00 3명', j.ok&&!day('2026-10-11').some(x=>x.name==='우상태')&&day('2026-10-12').some(x=>x.name==='우상태'&&x.time==='19:00'&&x.pp==='3'&&x.auto==='chg'), JSON.stringify(j));
[s,j]=await call('일품집 본점, 예약취소\n우상태님, 일품집 본점 예약, 2026.10.12.(월) 오후 7:00, 3명 (성인3), 예약이 취소되었습니다.');
const w=day('2026-10-12').find(x=>x.name==='우상태'); chk('취소: 지우지 않고 테이블 칸에 네이버취소', j.ok&&w&&w.tnote==='네이버취소'&&w.auto==='cxl', JSON.stringify(j));
[s,j]=await call('일품집 본점, 예약취소\n우상태님, 일품집 본점 예약, 2026.10.12.(월) 오후 7:00, 3명 (성인3), 예약이 취소되었습니다.'); chk('또 취소 알림 → 이미 취소', j.cancel==='이미 취소돼 있음', JSON.stringify(j));
[s,j]=await call('유천점, 예약신청\n김유천님, 유천점 예약, 2026.10.13.(화) 오후 6:00, 2명 (성인2), 새로운 예약이 접수되었습니다.'); chk('유천점 알림은 유천점에', j.ok&&day('2026-10-13',YC).length===1&&day('2026-10-13',HQ).length===0, JSON.stringify(j));
chk('기록 남김', (DB.sync_state.find(x=>x.key==='naver_log')||{val:[]}).val.length>=8);
console.log(ok?'전체 OK':'실패 있음');
