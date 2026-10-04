/* ================= 앱 상태 ================= */
const QS=new URLSearchParams(location.search);
const VIEWS=['cards','week','day','staff','rules','me','hq','set','acct'];
const EMBED=QS.get('embed')==='1';                       // 통합관리 화면 안에 들어갈 때: 자기 왼쪽 메뉴는 숨김
if(EMBED) document.documentElement.classList.add('embed');
const APP={listMode:(()=>{ try{ return localStorage.getItem('ilpum-card-list')!=='0'; }catch(e){ return true; } })(),be:null,user:null,stores:[],sid:null,st:null,D:null,view:VIEWS.includes(QS.get('view'))?QS.get('view'):'cards',cardMode:'week7',anchor:new Date(),day:todayStr,sum:null,me:null,pf:'',q:''};
const role=()=>APP.st?APP.st.role:null;
const canEdit=()=>['hq','owner','manager','open'].includes(role());
const payAllowed=()=>!!(APP.st&&APP.st.pay);
const canPay=()=>payAllowed()&&sessionStorage.getItem('fr-pay')==='1';
const isHQ=()=>APP.stores.some(s=>s.role==='hq');
const posColor=name=>(APP.D.positions.find(p=>p.name===name)||{}).color||'#888888';

/* ---------- 체험용 예시 데이터 ---------- */
function seedDemo(){
  const mk=(name,pos,off,extra)=>Object.assign({id:uid(),name,pos,type:'regular',off,active:true},extra||{});
  const b=[mk('김지수','홀',[5]),mk('이과장','그릴',[2]),mk('매니저','카운터',[1]),mk('박민수','홀',[3]),mk('최영희','주방',[4]),
    mk('정화','주방',[1]),mk('상옥','주방',[3]),mk('홍주','홀',[3]),mk('신지은','홀',[4],{wk:{1:{sh:{k:'pm'}},2:{sh:{k:'pm'}},3:{sh:{k:'pm'}},4:{sh:{k:'pm'}},5:{sh:{k:'pm'}}}}),
    mk('배동영','홀',[2]),mk('신승엽','주차',[1,2,3,4],{wk:{6:{sh:{k:'t',s:'11:00',e:''}},0:{sh:{k:'t',s:'11:00',e:''}}}}),mk('김도윤','그릴',[1]),
    mk('준우','그릴',[],{type:'weekly'}),mk('서연','홀',[],{type:'weekly'})];
  b.forEach((s,i)=>s.order=i);
  const f=[mk('강점장','카운터',[1]),mk('윤하','홀',[2]),mk('도현','홀',[3]),mk('민재','그릴',[1]),mk('지호','그릴',[4]),mk('은서','주방',[2]),mk('수아','주방',[5]),mk('태민','홀',[],{type:'weekly'})];
  f.forEach((s,i)=>s.order=i);
  const ws=weekStart(new Date()), items1={staff:{},cfg:{store:Object.assign(defStore(),{name:'일품집 본점'})},pay:{},rule:{},spot:{},aw:{},dc:{},sales:{}};
  b.forEach(s=>{ items1.staff[s.id]=s; items1.pay['staff:'+s.id]= s.name==='매니저'?{k:'month',v:3300000}: s.type==='weekly'?{k:'hour',v:11000}: {k:'day',v:s.pos==='주방'?140000:130000}; });
  const wk=ds(ws); items1.aw[wk]={}; items1.aw[wk][b[12].id]={off:[0,1],pm:[2,3]}; items1.aw[wk][b[13].id]={off:[3],pm:[],t:{5:{s:'17:30'}}};
  const r1=uid(); items1.rule[r1]={id:r1,ids:[b[1].id],from:ds(addDays(ws,8)),to:ds(addDays(ws,10)),days:[],w:'off',memo:'휴가',at:1};
  const sp=uid(); items1.spot[sp]={id:sp,date:todayStr,name:'박알바',pos:'홀',sh:{k:'t',s:'17:00',e:''}}; items1.pay['spot:'+sp]={k:'day',v:60000,cash:true};
  for(let i=0;i<14;i++){ const d=addDays(ws,i-3), wd=d.getDay(); items1.sales[ds(d)]={v:(wd===0||wd===6)?5200000:wd===5?4300000:3200000}; }
  const items2={staff:{},cfg:{store:Object.assign(defStore(),{name:'수성점',fivePlus:true})},pay:{},aw:{}};
  f.forEach(s=>{ items2.staff[s.id]=s; items2.pay['staff:'+s.id]={k:'hour',v:11000}; });
  return {stores:[{id:'bonjum',name:'일품집 본점'},{id:'suseong',name:'수성점'}],items:{bonjum:items1,suseong:items2},sum:{},demoRole:'hq',demoMe:{}};
}

/* ---------- 불러오기 · 저장 ---------- */
function setSync(t,k){ APP.sync=[t,k]; const el=$('#sync'); if(el){ el.textContent=t; el.dataset.k=k||''; } }
async function boot(){
  const remote=Conf.mode==='remote'&&Conf.url&&Conf.key;
  APP.be=remote?Remote:Local;
  try{ APP.user=await APP.be.init(); }
  catch(e){ APP.user=null; if(!e.auth){ renderOffline(e.message); return; } }          // 로그인 유지 토큰이 만료·취소됨 → 로그인 화면
  if(remote && !APP.user){ renderLogin(); return; }          // 로그인 없이 열기는 보안상 없앴어요 (2026-10-01)
  let netErr=null;
  try{ APP.stores=await APP.be.stores(); }catch(e){ netErr=e; setSync('연결 실패','err'); toast('불러오기 실패: '+e.message); APP.stores=[]; }
  if(remote && !APP.user && netErr){ renderOffline(netErr.message); return; }
  if(remote && !APP.user){                                                  // 로그인 없이 열기 (본점)
    if(!APP.stores.length){ renderOffline('열 수 있는 매장을 찾지 못했어요'); return; }
    APP.open=true; APP.user={email:''};
  }

  const mine=APP.stores.filter(s=>s.role);
  if(!mine.length){ renderShell(); $('#main').innerHTML=`<div class="card empty"><b>연결된 매장이 없어요</b>본사에 이 계정(${esc(APP.user&&APP.user.email||'')})을 매장에 연결해 달라고 요청하세요.</div>`; return; }
  const want=Conf.sid&&mine.find(s=>s.id===Conf.sid)?Conf.sid:mine[0].id;
  await openStore(want);
  if(APP.be===Local) await Promise.all(Local.db.stores.map(s=>summaryFor(s.id,true)));
  if(role()==='staff') APP.view='me';
  renderShell(); render();
  if(!pollStarted){ pollStarted=true; setInterval(()=>{ if(rtOk&&Date.now()-lastPollAt<300000) return; poll(); },60000);       // 실시간이면 5분마다 안전 확인, 아니면 1분마다 바뀐 것만 확인 (전송량 절약)
    ['pointerdown','keydown','touchstart'].forEach(ev=>document.addEventListener(ev,()=>{ const was=Date.now()-lastActive; lastActive=Date.now(); if(was>IDLE_MS) poll(); },{passive:true}));
    document.addEventListener('visibilitychange',()=>{ if(!document.hidden){ lastActive=Date.now(); poll(); } }); }
}
async function openStore(sid){
  APP.sid=sid; Conf.sid=sid; saveConf(); APP.st=APP.stores.find(s=>s.id===sid);
  setSync('불러오는 중…','busy');
  if(APP.be===Remote&&APP.st.role==='hq'){ try{ const o=await Remote.openInfo(); if(o&&o.id===APP.st.id) APP.st.hasPin=!!o.has_pin; }catch(e){} }
  try{ const it=await APP.be.items(sid); APP.D=buildD(it,APP.st.name); setSync(APP.be===Local?'이 기기에 저장 (체험)':'연결됨','ok'); }
  catch(e){ APP.D=buildD({},APP.st.name); setSync('불러오기 실패','err'); toast(e.message); }
  rtStart(sid);                                             // 이 매장의 변경을 실시간으로 받음
  if(!canEdit()&&!['me','cards','week'].includes(APP.view)) APP.view='me';
}
const pending=new Map(); let flushTimer=null, writing=false, flushFails=0, pollFails=0, pollNextAt=0, pollStarted=false;
const IDLE_MS=10*60*1000; let lastActive=Date.now();
function put(kind,id,data){
  const D=APP.D;
  if(kind==='cfg'){ if(id==='store') D.store=data; if(id==='positions') D.positions=cleanPositions(data); }
  else { const g=D[{staff:'staff',rule:'rules',dc:'dc',spot:'spot',aw:'aw',sales:'sales',pay:'pay'}[kind]]; if(data==null) delete g[id]; else g[id]=data; }
  pending.set(kind+'\u0001'+id,{sid:APP.sid,kind,id,data:data==null?null:JSON.parse(JSON.stringify(data))});
  clearTimeout(flushTimer); flushTimer=setTimeout(flush,350); schedSummary();
}
async function flush(){
  if(writing){ flushTimer=setTimeout(flush,300); return; } if(!pending.size) return;
  writing=true; setSync('저장 중…','busy'); const batch=[...pending.values()]; pending.clear();
  let denied=0;
  try{
    if(APP.be.putMany){ try{ await APP.be.putMany(batch); }
      catch(e){ if(e.code==='bad_pin'||e.code==='locked'){ APP.pinOk=false; Remote.pin=''; sessionStorage.removeItem('fr-pin'); localStorage.removeItem('fr-pin'); setSync('편집 잠김','err'); renderShell(); render(); toast(e.message+' · 저장하지 못했어요'); writing=false; return; }
        if(e.code||/row-level|permission|policy|42501|403/i.test(String(e.message))){ denied=batch.length; } else throw e; } }
    else for(let i=0;i<batch.length;i++){ const w=batch[i];
      try{ await APP.be.put(w.sid,w.kind,w.id,w.data); }
      catch(e){ if(/row-level|permission|policy|42501|403/i.test(String(e.message))){ denied++; continue; }   // 권한 없는 저장은 다시 시도하지 않음
        batch.slice(i).forEach(x=>{ const k=x.kind+'\u0001'+x.id; if(!pending.has(k)) pending.set(k,x); }); throw e; } }
    const t=new Date(); setSync(`${APP.be===Local?'이 기기에 저장':'저장됨'} ${pad(t.getHours())}:${pad(t.getMinutes())}`,'ok');
    flushFails=0; if(rtDirty){ rtDirty=false; setTimeout(()=>pollSoon(300),50); } if(denied) toast(`권한이 없어 저장하지 못한 항목이 ${denied}개 있어요`); }
  catch(e){ batch.forEach(x=>{ const k=x.kind+'\u0001'+x.id; if(!pending.has(k)) pending.set(k,x); }); flushFails++; setSync('저장 실패 — 다시 시도 중','err'); flushTimer=setTimeout(flush,Math.min(300000,4000*2**Math.min(flushFails-1,7))); }   // 실패하면 점점 천천히 (서버를 계속 두드리지 않도록)
  writing=false;
}
/* ---------- 실시간 알림: 다른 기기에서 근무표가 바뀌면 바로 반영 (Supabase Realtime) ---------- */
// 연결되어 있으면 서버가 "바뀌었어요" 하고 알려 줘서 계속 물어볼 필요가 없어요. 연결이 안 되면 예전처럼 60초마다 확인해요. (로그인 없이 보기는 실시간 없이 60초 확인)
let rtWs=null, rtOk=false, rtRef=0, rtBeat=null, rtTokT=null, rtWait=1000, rtSid='', rtTimer=null, rtDirty=false, lastPollAt=0;
function rtSet(v){ rtOk=!!v; const el=$('#sync'); if(el&&APP.sync&&APP.sync[1]==='ok'&&/^연결됨/.test(APP.sync[0])) setSync(rtOk?'연결됨 · 실시간':'연결됨','ok'); }
async function rtToken(){ const s=Remote.ses; if(s&&(s.expires_at||0)*1000>Date.now()+60000) return s.access_token; try{ await Remote.refresh(); }catch(e){} return Remote.ses&&Remote.ses.access_token; }
function rtStop(){ const w=rtWs; rtWs=null; clearInterval(rtBeat); clearInterval(rtTokT); clearTimeout(rtTimer); rtSet(false); if(w){ w.onclose=null; try{ w.close(); }catch(e){} } }
function rtStart(sid){
  rtStop(); rtSid=sid; if(APP.be!==Remote||!Remote.ses||!sid||!('WebSocket' in window)) return;
  let ws; try{ ws=new WebSocket(Remote.url.replace(/^http/,'ws')+'/realtime/v1/websocket?apikey='+encodeURIComponent(Remote.key)+'&vsn=1.0.0'); }catch(e){ return; }
  rtWs=ws; const topic='realtime:sch_'+sid;
  const send=(event,payload,t)=>{ try{ if(ws.readyState===1) ws.send(JSON.stringify({topic:t||topic,event,payload,ref:String(++rtRef)})); }catch(e){} };
  ws.onopen=async()=>{
    const tok=await rtToken(); if(!tok||rtWs!==ws){ try{ ws.close(); }catch(e){} return; }
    send('phx_join',{config:{broadcast:{ack:false,self:false},presence:{key:''},postgres_changes:[{event:'*',schema:'public',table:'sch_items',filter:'store_id=eq.'+sid}],private:false},access_token:tok});
    rtBeat=setInterval(()=>send('heartbeat',{},'phoenix'),25000);
    rtTokT=setInterval(async()=>{ const t=await rtToken(); if(t) send('access_token',{access_token:t}); },40*60*1000); };
  ws.onmessage=e=>{
    let m; try{ m=JSON.parse(e.data); }catch(x){ return; }
    if(m.event==='phx_reply'&&m.topic===topic){ rtSet(m.payload&&m.payload.status==='ok'); if(rtOk){ rtWait=1000; pollSoon(100); } return; }     // 연결되면 한 번 맞춰 봄
    if(m.event==='postgres_changes'){ pollSoon(400); return; }
    if(m.event==='phx_error'||m.event==='phx_close'||(m.event==='system'&&m.payload&&m.payload.status==='error')) rtSet(false); };
  ws.onclose=()=>{ rtSet(false); if(rtWs===ws){ rtWs=null; clearInterval(rtBeat); clearInterval(rtTokT); rtTimer=setTimeout(()=>rtStart(rtSid),rtWait); rtWait=Math.min(rtWait*2,300000); } };
  ws.onerror=()=>{ try{ ws.close(); }catch(e){} };
}
let pollTimer=null;
function pollSoon(ms){ if(pending.size||writing){ rtDirty=true; return; } clearTimeout(pollTimer); pollTimer=setTimeout(()=>poll(true),ms); }     // 연달아 오는 알림은 한 번에 처리
async function poll(force){
  if(APP.be!==Remote||!APP.sid||document.hidden||pending.size||writing||Date.now()<pollNextAt) return;
  try{ if(window.frameElement&&window.frameElement.hidden) return; }catch(e){}      // 통합 틀에서 가려진 창은 쉼
  if(!force&&!rtOk&&Date.now()-lastActive>IDLE_MS) return;                            // 실시간이 안 될 때만: 10분 동안 아무도 안 만졌으면 쉼
  try{ lastPollAt=Date.now(); const rows=await APP.be.since(APP.sid); pollFails=0; if(!rows||!rows.length) return;
    const D=APP.D; rows.forEach(r=>{ const data=r.deleted?null:r.data;
      if(r.kind==='cfg'){ if(r.id==='store'&&data) D.store=Object.assign(defStore(),data); if(r.id==='positions'&&data) D.positions=cleanPositions(data); return; }
      const g=D[{staff:'staff',rule:'rules',dc:'dc',spot:'spot',aw:'aw',sales:'sales',pay:'pay'}[r.kind]]; if(!g) return; if(data==null) delete g[r.id]; else g[r.id]=data; });
    render(); setSync('연결됨 · 방금 새로 받음','ok');
  }catch(e){ pollFails++; pollNextAt=Date.now()+Math.min(300000,15000*2**Math.min(pollFails,5)); setSync('연결 확인 실패','err'); }
}
let sumTimer=null;
function schedSummary(){ clearTimeout(sumTimer); sumTimer=setTimeout(()=>summaryFor(APP.sid),2500); }
async function summaryFor(sid,silent){
  // 본사에는 '집계'만 올림 (직원 이름·시급 없음)
  let D=APP.D, pay=payAllowed();
  if(sid!==APP.sid){ if(APP.be!==Local) return; D=buildD(await Local.items(sid)); pay=true; }
  const ws=weekStart(new Date());
  for(const w of [ws,addDays(ws,7)]){ const W=weekCalc(D,w,pay);
    const data={hours:Math.round(W.hours),staff:Object.keys(W.per).length,warn:W.W.filter(x=>x.lv==='bad'||x.lv==='warn').length,at:Date.now()};
    if(pay&&W.costKnown){ data.cost=Math.round(W.cost); if(W.sales) data.ratio=Math.round(W.cost/W.sales*1000)/10; }
    try{ await APP.be.putSummary(sid,ds(w),data); }catch(e){ if(!silent) console.warn(e); } }
}

/* ================= 화면 틀 ================= */
const NAV=[['cards','▦','스케줄'],['week','▤','주간 표'],['day','◫','하루 타임라인'],['staff','◉','직원'],['rules','⟷','기간 설정'],['me','☺','내 스케줄'],['hq','◆','본사 현황'],['acct','⚿','계정 · 권한'],['set','⚙','설정']];
function navAllowed(v){ if(v==='hq') return isHQ(); if(v==='acct') return APP.be===Remote&&(isHQ()||role()==='owner'); if(!canEdit()) return v==='me'||((v==='cards'||v==='week')&&APP.D.store.vis==='week'); return true; }
function renderShell(){
  const st=APP.st, r=role();
  $('#app').innerHTML=`<aside class="side">
    <div class="brand"><div class="mk">일</div><div><b>일품집 근무표</b><small>본사·가맹점 통합</small></div></div>
    ${st?`<button class="store" data-a="stores"><span><b>${esc(APP.D.store.name||st.name)}</b><small>${roleName(r)}${APP.stores.filter(s=>s.role).length>1?' · 매장 바꾸기':''}</small></span><span>▾</span></button>`:''}
    <nav class="nav" id="nav">${st?NAV.filter(n=>navAllowed(n[0])).map(n=>(n[0]==='me'||n[0]==='hq'?'<div class="sep"></div>':'')+`<button data-a="view" data-v="${n[0]}"><span class="ic">${n[1]}</span>${n[2]}</button>`).join(''):''}</nav>
    <div class="foot"><span class="sync" id="sync"></span>
      <div class="who"><span>${APP.open?'':esc(showId(APP.user&&APP.user.email||''))}</span>${APP.be===Remote?(APP.open?'<button class="btn sm ghost" data-a="gologin">로그인</button>':'<button class="btn sm ghost" data-a="logout">로그아웃</button>'):''}</div></div>
  </aside><main class="main" id="main"></main>
  <nav class="mbar" id="mbar">${st?NAV.filter(n=>navAllowed(n[0])&&['cards','day','staff','me','set','hq'].includes(n[0])).map(n=>`<button data-a="view" data-v="${n[0]}"><span class="ic">${n[1]}</span>${n[2].replace(' 타임라인','').replace(' 보드','').replace(' 현황','')}</button>`).join(''):''}</nav>`;
}
function afterShell(){ if(APP.sync) setSync(APP.sync[0],APP.sync[1]); }
const roleName=r=>({hq:'본사 · 본점 관리',owner:'점주',manager:'매니저',staff:'직원',order:'발주 전용',open:'바로 저장'}[r]||'보기 전용');
function render(){
  if(!APP.st) return; afterShell();
  if(!navAllowed(APP.view)) APP.view=canEdit()?'cards':'me';
  $$('#nav button,#mbar button').forEach(b=>b.setAttribute('aria-current',b.dataset.v===APP.view?'page':'false'));
  const V={cards:vCards,week:vWeek,month:vMonth,day:vDay,staff:vStaff,rules:vRules,me:vMe,hq:vHQ,set:vSet,acct:vAcct}[APP.view]||vCards;
  $('#main').innerHTML=V();
  if(EMBED&&window.parent!==window){ try{ window.parent.postMessage({type:'fr-state',view:APP.view,hq:isHQ(),edit:canEdit(),role:role()},'*'); }catch(e){} }
  if(APP.view==='hq'&&!APP.sum) loadSum();
}
function payToggle(){ return payAllowed()?`<button class="btn ${canPay()?'ink':''}" data-a="paytog" title="금액은 권한 있는 사람만, 켰을 때만 보여요">${canPay()?'₩ 금액 숨기기':'₩ 금액 보기'}</button>`:''; }
function viewSeg(){ return `<div class="seg" role="group" aria-label="보기">${[['cards','카드'],['week','주간표'],['day','하루']].map(([v,t])=>`<button data-a="view" data-v="${v}" aria-pressed="${APP.view===v}">${t}</button>`).join('')}</div>`; }

/* ================= 스케줄 카드 (날짜마다 포지션 줄이 다 보이는 화면) ================= */
function vCards(){
  const D=APP.D, ed=canEdit(), cp=canPay(); const rules=rulesSorted(D); const mode=APP.cardMode||'month', a=APP.anchor;
  let start,end,title;
  if(mode==='month'){ start=new Date(a.getFullYear(),a.getMonth(),1); end=new Date(a.getFullYear(),a.getMonth()+1,0); title=`${a.getFullYear()}년 ${a.getMonth()+1}월`; }
  else { start=new Date(a.getFullYear(),a.getMonth(),a.getDate()); end=addDays(start,6); title=`${md(ds(start))} ~ ${md(ds(end))}`; }
  const ws=weekStart(new Date()); const hasWeekly=staffList(D).some(s=>s.type==='weekly');
  const missingAw=hasWeekly?staffList(D).filter(s=>s.type==='weekly'&&!(D.aw[ds(ws)]||{})[s.id]).length:0;
  let cards='', usedAny=new Set(), allPos=new Set();
  for(let d=new Date(start); d<=end; d=addDays(d,1)){
    const R=resolve(D,d,{rules}), key=R.key; if(cp) R.list.forEach(x=>{ x.cost=costOf(D,x,key,R.wd); });
    const by={}; D.positions.forEach(p=>by[p.name]=[]); R.list.forEach(x=>(by[x.pos]=by[x.pos]||[]).push(x)); D.positions.forEach(p=>{ allPos.add(p.name); if(by[p.name].length) usedAny.add(p.name); });
    let no=0; const LM=APP.listMode;
    const rows=D.positions.map(p=>`<div class="cr ${(!APP.showEmpty&&!by[p.name].length)?'empty':''}" style="--pc:${p.color}"><div class="cl">${esc(p.name)}${by[p.name].length?`<span class="cn">${by[p.name].length}명</span>`:''}</div><div class="bc" data-drop="${esc(p.name)}" data-k="${key}">${by[p.name].map(x=>LM?`<div class="lrow"><span class="lno">${++no}</span>${chipH(x,{key},cp,ed)}</div>`:chipH(x,{key},cp,ed)).join('')}${ed?`<button class="add" data-a="add" data-pos="${esc(p.name)}" data-k="${key}" aria-label="${esc(p.name)}에 사람 넣기">+</button>`:''}</div></div>`).join('');
    const offs=R.offs.filter(o=>!o.missing||key>=ds(ws)).map(o=>`<button data-a="${o.missing?'weekly':'edit'}" data-sid="${o.sid}" data-k="${key}" ${o.missing?`data-k2="${weekKey(d)}"`:''}>${esc(o.name)}${o.reason!=='고정휴무'&&o.reason!=='주간휴무'&&!o.missing?`<span class="rs">(${esc(o.reason)})</span>`:''}${o.missing?'<span class="rs">(미입력)</span>':''}</button>`).join('');
    const wd=R.wd;
    cards+=`<div class="dcard ${key===todayStr?'today':''} ${key<todayStr?'past':''}"><div class="ch"><button class="cdate ${wd===0?'sun':wd===6?'sat':''}" data-a="gday" data-k="${key}" title="하루 타임라인"><b>${d.getMonth()+1}/${d.getDate()}</b><span>${DOW[wd]}</span></button>${key===todayStr?'<span class="tag amber">오늘</span>':''}<span class="cn">총 <b>${R.list.length}</b>명</span><span class="sp"></span>${ed?`<button class="btn sm" data-a="add" data-pos="${esc(D.positions[0].name)}" data-k="${key}">+ 사람</button>`:''}<button class="btn sm" data-a="img" data-t="day" data-k="${key}" title="카톡용 사진">사진</button></div>
      ${R.list.length?'':'<div class="cr0">근무자가 없어요</div>'}${rows}${offs?`<div class="cf"><b>쉬는 사람</b>${offs}</div>`:''}</div>`; }
  const hiddenN=allPos.size-usedAny.size;
  return `<div class="vh"><div><h1>${title}</h1><div class="sub">이름을 누르면 시간·금액·휴무, 끌어서(폰은 꾹) 옮기기·복사</div></div>
    <div class="row"><button class="btn ic" data-a="cnav" data-n="-1" aria-label="이전">‹</button><button class="btn" data-a="cnav" data-n="0">${mode==='month'?'이번 달':'오늘'}</button><button class="btn ic" data-a="cnav" data-n="1" aria-label="다음">›</button></div>
    <div class="seg" role="group" aria-label="기간"><button data-a="cmode" data-v="week7" aria-pressed="${mode!=='month'}">오늘부터 7일</button><button data-a="cmode" data-v="month" aria-pressed="${mode==='month'}">한 달</button></div>${viewSeg()}<span class="sp"></span>
    <button class="btn" data-a="lmode">${APP.listMode?'번호 끄기':'번호 붙여 보기'}</button>
    ${hiddenN>0||APP.showEmpty?`<button class="btn" data-a="empty">${APP.showEmpty?'빈 포지션 숨기기':`빈 포지션 ${hiddenN}개 보기`}</button>`:''}
    ${ed?'<button class="btn" data-a="posmgr">포지션 관리</button>':''}
    ${ed&&hasWeekly?`<button class="btn ${missingAw?'pri':''}" data-a="weekly" data-k="${ds(ws)}">매주 변동 입력${missingAw?` (${missingAw}명 미입력)`:''}</button>`:''}
    ${payToggle()}${EMBED&&window.parent!==window?'<button class="btn" data-a="tores">예약 보기 ›</button>':''}<button class="btn" data-a="print">인쇄</button></div>
    <div class="cards${APP.listMode?' lst':''}">${cards}</div>
    <div class="legend"><span><span class="chip">이름</span> 기본</span><span><span class="chip g-add">이름</span> 추가 출근</span><span><span class="chip g-chg">이름</span> 포지션 변경</span><span><span class="chip t-spot">이름</span> 단기·당일</span><span><span class="chip t-weekly">이름</span> 매주 변동</span><span><span class="chip">이름<i class="pmb">오후</i></span><span class="chip">이름<i class="tm soft">11시</i></span> 출근 시간</span></div>`;
}

/* ================= 주간 보드 ================= */
// 이름 옆 표기(직원 편집 창의 "이름 옆 표기"): 화면에만 보이는 꼬리표, 메모·급여와 무관
const nlH=x=>x&&x.nl?`<em class="nl2">${esc(x.nl)}</em>`:'';
function chipH(x,dd,cp,ed){
  const st=APP.D.store, l=shLbl(x.sh,st);
  const tb=l?`<i class="${x.sh.k==='pm'?'pmb':'tm'}${x.shSrc==='pat'?' soft':''}">${esc(l)}</i>`:'';
  const pb=cp&&x.cost&&(x.cost.ov||x.cost.base)&&x.cost.ov?`<i class="won">${esc(payLbl(x.cost.ov))}</i>`:'';
  const cls=['chip','t-'+x.type,x.tag?'g-'+x.tag:''].join(' ');
  const tip=[x.name,TYPES[x.type]||'',l?l+' 출근':'',x.memo].filter(Boolean).join(' · ');
  return `<button class="${cls}" data-a="edit" data-sid="${x.sid||''}" data-spot="${x.spotId||''}" data-k="${dd.key}" data-pos="${esc(x.pos)}" title="${esc(tip)}">${esc(x.name)}${nlH(x)}${tb}${pb}${x.memo?'<i class="mm">✎</i>':''}</button>`;
}
function vWeek(){
  const D=APP.D, st=D.store, ws=weekStart(APP.anchor), cp=canPay(), ed=canEdit();
  const W=weekCalc(D,ws,cp); const we=addDays(ws,6);
  const shownPos=D.positions.filter(p=>APP.showEmpty||W.days.some(dd=>(dd.by[p.name]||[]).length)); const hiddenN=D.positions.length-shownPos.length;
  const hasWeekly=staffList(D).some(s=>s.type==='weekly');
  const missingAw=hasWeekly&&staffList(D).filter(s=>s.type==='weekly'&&!(D.aw[ds(ws)]||{})[s.id]).length;
  const ratio=cp&&W.sales&&W.costKnown?W.cost/W.sales*100:null;
  let h=`<div class="vh"><div><h1>${ws.getMonth()+1}월 ${Math.ceil((ws.getDate()+((new Date(ws.getFullYear(),ws.getMonth(),1).getDay()+6)%7))/7)}주차</h1>
    <div class="sub num">${mdw(ds(ws))} ~ ${mdw(ds(we))} · ${esc(st.name)}</div></div>
    <div class="row"><button class="btn ic" data-a="wk" data-n="-1" aria-label="이전 주">‹</button><button class="btn" data-a="wk" data-n="0">이번 주</button><button class="btn ic" data-a="wk" data-n="1" aria-label="다음 주">›</button></div>
    ${viewSeg()}<span class="sp"></span>
    ${hiddenN||APP.showEmpty?`<button class="btn" data-a="empty">${APP.showEmpty?'빈 포지션 숨기기':`빈 포지션 ${hiddenN}개 보기`}</button>`:''}
    ${ed?'<button class="btn" data-a="posmgr">포지션 관리</button>':''}
    ${ed&&hasWeekly?`<button class="btn ${missingAw?'pri':''}" data-a="weekly" data-k="${ds(ws)}">매주 변동 입력${missingAw?` <span class="tag" style="background:rgba(255,255,255,.25);color:inherit">${missingAw}명 미입력</span>`:''}</button>`:''}
    ${payToggle()}<button class="btn pri" data-a="img" data-t="day" data-k="${(todayStr>=ds(ws)&&todayStr<=ds(we))?todayStr:ds(ws)}">하루 사진 보내기</button><button class="btn" data-a="print">인쇄</button></div>`;
  if(cp) h+=`<div class="kpis">
    <div class="kpi"><div class="k">예상 인건비${W.costKnown?'':' (급여 미입력 있음)'}</div><div class="v">${Math.round(W.cost/10000).toLocaleString('ko-KR')}<small>만원</small></div></div>
    <div class="kpi ${ratioCls(ratio,st.target)}"><div class="k">인건비율 (목표 ${st.target}%)</div><div class="v">${ratio==null?'—':fmtH(ratio)}<small>${ratio==null?'매출 입력 필요':'%'}</small></div></div></div>`;
  // 보드
  let g=`<div class="bh corner">포지션</div>`;
  W.days.forEach(dd=>{ const d=dd.d; const cls=['bh',dd.wd===0?'sun':'',dd.wd===6?'sat':'',dd.key===todayStr?'today':''].join(' ');
    g+=`<div class="${cls}"><button class="dt" data-a="gday" data-k="${dd.key}" title="하루 타임라인"><b>${d.getDate()}</b><span>${DOW[dd.wd]}</span></button><button class="dimg" data-a="img" data-t="day" data-k="${dd.key}" title="${mdw(dd.key)} 근무표를 카톡용 사진으로">사진</button></div>`; });
  D.positions.forEach(p=>{ const hide=(!APP.showEmpty&&!W.days.some(dd=>(dd.by[p.name]||[]).length))?' empty':'';
    g+=`<div class="bl${hide}" style="--pc:${p.color}"><b>${esc(p.name)}</b></div>`;
    W.days.forEach(dd=>{ const list=dd.by[p.name]||[];
      g+=`<div class="bc${hide} ${dd.key<todayStr?'past':''}" data-drop="${esc(p.name)}" data-k="${dd.key}">${list.map(x=>chipH(x,dd,cp,ed)).join('')}${ed?`<button class="add" data-a="add" data-pos="${esc(p.name)}" data-k="${dd.key}" aria-label="${esc(p.name)}에 사람 넣기">+</button>`:''}</div>`; });
  });
  g+=`<div class="bl off"><b>휴무</b><small>누르면 출근으로</small></div>`;
  W.days.forEach(dd=>{ g+=`<div class="offs">${dd.R.offs.filter(o=>!o.missing||dd.key>=ds(weekStart(new Date()))).map(o=>`<button data-a="${o.missing?'weekly':'edit'}" data-sid="${o.sid}" data-k="${dd.key}" ${o.missing?`data-k2="${ds(ws)}"`:''}>${esc(o.name)}${o.reason!=='고정휴무'&&o.reason!=='주간휴무'?`<span class="rs">(${esc(o.reason)})</span>`:''}</button>`).join('')}</div>`; });
  if(cp){ g+=`<div class="bl foot"><b>인건비</b><small>매출 · 비율</small></div>`;
    W.days.forEach(dd=>{ const r=dd.sales&&!dd.costMissing?dd.cost/dd.sales*100:null;
      g+=`<div class="bf"><b>${dd.costMissing?`${Math.round(dd.cost/10000)}만+`:`${Math.round(dd.cost/10000)}만`}</b>${dd.costMissing?` <span class="r">미입력 ${dd.costMissing}명</span>`:''}
        <button class="sales" data-a="sales" data-k="${dd.key}">${dd.sales?'매출 '+Math.round(dd.sales/10000)+'만':'매출 입력'}</button>
        ${r!=null?`<span class="r">비율 <span class="ratio ${ratioCls(r,st.target)}">${fmtH(r)}%</span></span>`:''}</div>`; }); }
  h+=`<div class="boardwrap"><div class="board">${g}</div></div>
    <div class="legend"><span><span class="chip">이름</span> 기본</span><span><span class="chip g-add">이름</span> 추가 출근</span><span><span class="chip g-chg">이름</span> 포지션 변경</span><span><span class="chip t-spot">이름</span> 단기·당일</span><span><span class="chip t-weekly">이름</span> 매주 변동</span>
      <span><span class="chip">이름<i class="pmb">오후</i></span><span class="chip">이름<i class="tm soft">11시</i></span> 출근 시간 (테두리만 = 요일 패턴)</span>${ed?'<span>이름을 끌어서(폰은 꾹 누른 채) <b>같은 날 다른 포지션</b>에 놓으면 그 날만 포지션 변경, <b>다른 날</b>에 놓으면 복사돼요</span>':''}</div>`;
    return h;
}

/* ================= 월간 (전체 이름) ================= */
function vMonth(){
  const D=APP.D, st=D.store, a=APP.anchor, y=a.getFullYear(), m=a.getMonth(); const first=new Date(y,m,1), last=new Date(y,m+1,0).getDate(), lead=(first.getDay()+6)%7;
  const rules=rulesSorted(D), order=D.positions.map(p=>p.name); const used=new Set(); let cells='';
  for(let i=0;i<lead;i++) cells+='<div class="cd out"></div>';
  for(let day=1;day<=last;day++){ const d=new Date(y,m,day); const R=resolve(D,d,{rules,quiet:true}); const key=R.key;
    const list=R.list.slice().sort((p,q)=>order.indexOf(p.pos)-order.indexOf(q.pos)); list.forEach(x=>used.add(x.pos));
    const offs=R.offs.filter(o=>!o.missing);
    cells+=`<button class="cd ${key===todayStr?'today':''}" data-a="gweek" data-k="${key}"><span class="n ${R.wd===0?'sun':R.wd===6?'sat':''}">${day}</span>
      <span class="nl">${list.map(x=>{ const t=shLbl(x.sh,st); return `<i class="${x.type==='spot'?'sp':''}" style="--pc:${posColor(x.pos)}">${esc(x.name)}${nlH(x)}${t?`<u>${esc(t)}</u>`:''}</i>`; }).join('')}</span>
      ${offs.length?`<span class="of"><b>휴</b> ${esc(offs.map(o=>o.name).join(' '))}</span>`:''}</button>`; }
  const ym=`${y}-${pad(m+1)}`;
  return `<div class="vh"><div><h1>${y}년 ${m+1}월</h1><div class="sub">날짜를 누르면 그 주 보드로 가요</div></div>
    <div class="row"><button class="btn ic" data-a="mon" data-n="-1">‹</button><button class="btn" data-a="mon" data-n="0">이번 달</button><button class="btn ic" data-a="mon" data-n="1">›</button></div>${viewSeg()}<span class="sp"></span>
    <button class="btn pri" data-a="img" data-t="day" data-k="${todayStr.startsWith(ym)?todayStr:ym+'-01'}">하루 사진 보내기</button></div>
    <div class="legend" style="margin:0 2px 10px">${[...used].map(n=>`<span><i class="sw" style="background:${posColor(n)}"></i>${esc(n)}</span>`).join('')}<span><span class="muted">표시된 시간은 오후·시간 지정 출근이에요</span></span></div>
    <div class="cal">${['월','화','수','목','금','토','일'].map(n=>`<div class="h">${n}</div>`).join('')}${cells}</div>`;
}

/* ================= 하루 타임라인 ================= */
function vDay(){
  const D=APP.D, st=D.store, key=APP.day, R=resolve(D,pd(key)); const o=tMin(st.open), c=tMin(st.close); const hrs=Math.max(1,Math.round((c-o)/60));
  const ed=canEdit();
  const rows=D.positions.map(p=>R.list.filter(x=>x.pos===p.name).map(x=>{ const [a,b]=spanOf(st,x.sh); const L=(a-o)/(c-o)*100, Wd=Math.max(2,(b-a)/(c-o)*100);
    return `<div class="nm" style="--pc:${p.color}"><span>${esc(x.name)}${nlH(x)}</span><small>${esc(p.name)}</small></div>
      <div class="lane" style="--hrs:${hrs}"><button class="blk ${x.type==='spot'?'spot':''}" style="--pc:${p.color};left:${L}%;width:${Wd}%;border:0" data-a="edit" data-sid="${x.sid||''}" data-spot="${x.spotId||''}" data-k="${key}" data-pos="${esc(x.pos)}">${esc(shLbl(x.sh,st)||(x.sh&&x.sh.k==='full'?'종일':'종일'))} · ${fmtH(hoursOf(st,x.sh))}h</button></div>`; }).join('')).join('');
  const cnt=[]; for(let i=0;i<hrs;i++){ const t=o+i*60+30; cnt.push(R.list.filter(x=>{ const [a,b]=spanOf(st,x.sh); return a<=t&&t<b; }).length); }
  const d=pd(key);
  return `<div class="vh"><div><h1>${d.getMonth()+1}월 ${d.getDate()}일 (${DOW[d.getDay()]})</h1><div class="sub">시간대별 인원 · 총 ${R.list.length}명 · 휴무 ${R.offs.filter(x=>!x.missing).map(x=>x.name).join(', ')||'없음'}</div></div>
    <div class="row"><button class="btn ic" data-a="dayn" data-n="-1">‹</button><button class="btn" data-a="dayn" data-n="0">오늘</button><button class="btn ic" data-a="dayn" data-n="1">›</button></div>${viewSeg()}<span class="sp"></span>
    <button class="btn pri" data-a="img" data-t="day" data-k="${key}">하루 사진 보내기</button>${ed?`<button class="btn" data-a="add" data-pos="${esc(D.positions[0].name)}" data-k="${key}">+ 사람 넣기</button>`:''}</div>
    <div class="tl"><div class="nm" style="border-left-color:transparent"><small>시간대별 인원</small></div><div><div class="axis">${Array.from({length:hrs},(_,i)=>`<span>${(Math.floor((o+i*60)/60)%12)||12}시</span>`).join('')}</div><div class="cnt">${cnt.map(n=>`<span>${n}</span>`).join('')}</div></div>
    ${rows||'<div class="nm">근무자 없음</div><div></div>'}</div>`;
}
function dayText(key){
  const D=APP.D, R=resolve(D,pd(key)), d=pd(key);
  const lines=[`[${D.store.name}] ${d.getMonth()+1}/${d.getDate()}(${DOW[d.getDay()]}) 근무`];
  D.positions.forEach(p=>{ const l=R.list.filter(x=>x.pos===p.name); if(l.length) lines.push(`${p.name}: ${l.map(x=>x.name+(shLbl(x.sh,D.store)?'('+shLbl(x.sh,D.store)+')':'')).join(', ')}`); });
  const off=R.offs.filter(x=>!x.missing); if(off.length) lines.push(`휴무: ${off.map(x=>x.name).join(', ')}`);
  return lines.join('\n');
}

/* ================= 직원 ================= */
function pat7(s){ return `<span class="pat7">${WD_MON.map(wd=>{ const off=s.type==='regular'&&(s.off||[]).includes(wd); const c=(s.wk||{})[wd]; const k=off?'off':c&&c.sh?(c.sh.k==='pm'?'pm':c.sh.k==='am'?'pm':c.sh.k==='t'?'t':''):(s.type!=='regular'?'wk':'');
  return `<i class="${k}" title="${DOW[wd]}">${off?'휴':DOW[wd]}</i>`; }).join('')}</span>`; }
function vStaff(){
  const D=APP.D, ed=canEdit(), cp=canPay(); const all=staffList(D,true); const ws=weekStart(APP.anchor); const W=weekCalc(D,ws,cp);
  const q=APP.q.trim(); const list=all.filter(s=>(!APP.pf||s.pos===APP.pf)&&(!q||s.name.includes(q)));
  return `<div class="vh"><div><h1>직원</h1><div class="sub">${all.filter(s=>s.active!==false).length}명 · 이름을 누르면 요일 패턴·급여를 바꿀 수 있어요</div></div><span class="sp"></span>${payToggle()}${ed?'<button class="btn pri" data-a="staffnew">+ 직원 추가</button>':''}</div>
    <div class="row" style="margin-bottom:12px"><div class="seg" style="overflow-x:auto;max-width:100%">${['',...D.positions.map(p=>p.name)].map(p=>`<button data-a="pf" data-v="${esc(p)}" aria-pressed="${APP.pf===p}">${esc(p||'전체')}</button>`).join('')}</div>
      <input type="text" id="staffQ" placeholder="이름 찾기" value="${esc(APP.q)}" style="width:140px"></div>
    <div class="card" style="padding:6px 8px"><div class="scroll"><table class="t"><thead><tr><th>이름</th><th>종류</th><th>포지션</th><th>요일 패턴 (월~일)</th><th>이번 주</th>${cp?'<th>기본 급여</th>':''}</tr></thead><tbody>
    ${list.map(s=>{ const p=W.per[s.id]; const b=(D.pay||{})['staff:'+s.id];
      return `<tr class="click" data-a="staff" data-sid="${s.id}" style="${s.active===false||(s.last&&s.last<todayStr)?'opacity:.45':''}"><td><b>${esc(s.name)}</b>${s.note?` <em class="nl2">${esc(s.note)}</em>`:''}${s.active===false?' <span class="tag">그만둠</span>':''}${s.last?` <span class="tag ${s.last<todayStr?'':'amber'}">${md(s.last)}까지</span>`:''}</td><td><span class="tag ${s.type==='weekly'?'amber':s.type==='spot'?'warn':''}">${TYPES[s.type]}</span></td>
        <td><span style="color:${posColor(s.pos)};font-weight:700">${esc(s.pos)}</span></td><td>${pat7(s)}</td><td class="num">${p?fmtH(p.h)+'시간 · '+p.days.length+'일':'-'}${p&&p.h>=13&&p.h<15?' <span class="tag warn">주휴 경계</span>':''}</td>
        ${cp?`<td class="num">${b?esc(payLbl(b)):'<span class="muted">미입력</span>'}</td>`:''}</tr>`; }).join('')||`<tr><td colspan="6" class="empty">조건에 맞는 직원이 없어요</td></tr>`}
    </tbody></table></div></div>`;
}

/* ================= 기간 설정 ================= */
function effTags(r){ const o=[]; const st=APP.D.store;
  if(r.w==='off') o.push('<span class="tag bad">쉬게 하기</span>'); if(r.w==='on') o.push('<span class="tag ok">출근</span>');
  if(r.sh) o.push(`<span class="tag">${esc(shLbl(r.sh,st)||'종일')} 출근</span>`); if(r.pos) o.push(`<span class="tag">${esc(r.pos)}</span>`);
  const p=(APP.D.pay||{})['rule:'+r.id]; if(p) o.push(canPay()?`<span class="tag ok">${esc(payLbl(p))}${p.cash?' 현금':''}</span>`:'<span class="tag ok">금액 🔒</span>');
  return o.join(''); }
function daysTxt(days){ if(!days||!days.length||days.length===7) return '매일'; const s=[...days].sort().join(','); if(s==='1,2,3,4,5') return '평일'; if(s==='0,6') return '주말'; return WD_MON.filter(w=>days.includes(w)).map(w=>DOW[w]).join('·'); }
function rangeTxt(r){ const to=r.to||r.from; return to===r.from?mdw(r.from):`${mdw(r.from)} ~ ${mdw(to)}`; }
function vRules(){
  const D=APP.D; const all=Object.values(D.rules).sort((a,b)=>b.from.localeCompare(a.from));
  const cur=all.filter(r=>(r.to||r.from)>=todayStr), past=all.filter(r=>(r.to||r.from)<todayStr);
  const item=r=>{ const names=r.ids.map(id=>(D.staff[id]||{}).name).filter(Boolean);
    return `<div class="ri ${(r.to||r.from)<todayStr?'past':''}"><div><div class="wn">${esc(rangeTxt(r))}<small>${esc(daysTxt(r.days))}</small>${r.from<=todayStr&&(r.to||r.from)>=todayStr?' <span class="tag ok">적용 중</span>':''}</div>
      <div class="wh">${esc(names.length>5?names.slice(0,5).join(', ')+` 외 ${names.length-5}명`:names.join(', '))}${r.memo?' · '+esc(r.memo):''}</div></div>
      <div class="row"><button class="btn sm" data-a="rule" data-id="${r.id}">고치기</button><button class="btn sm" data-a="rulecopy" data-id="${r.id}">복사</button></div><div class="eff">${effTags(r)}</div></div>`; };
  return `<div class="vh"><div><h1>기간 설정</h1><div class="sub">휴가, 단기 근무, 기간별 출근시간·금액을 한 번에. 겹치면 <b>이 날만 &gt; 기간(나중 것) &gt; 요일 패턴</b></div></div><span class="sp"></span>${payToggle()}<button class="btn pri" data-a="rule">+ 기간 설정</button></div>
    ${cur.length?`<div class="rl">${cur.map(item).join('')}</div>`:`<div class="card empty"><b>진행 중이거나 앞으로의 기간 설정이 없어요</b>예: 김지수 10/14~16 휴가, 추석 연휴 전원 11시 출근, 단기 알바 3일 13만원</div>`}
    ${past.length?`<h2 style="font-size:15px;margin:22px 2px 8px;color:var(--sub)">지난 설정 ${past.length}</h2><div class="rl">${past.slice(0,30).map(item).join('')}</div>`:''}`;
}

/* ================= 내 스케줄 ================= */
function vMe(){
  const D=APP.D, st=D.store; const mine=APP.st.staffId&&D.staff[APP.st.staffId]?APP.st.staffId:null;
  const sid=role()==='staff'?mine:(APP.me&&D.staff[APP.me]?APP.me:(mine||(staffList(D)[0]||{}).id));
  const pick=role()==='staff'?'':`<select data-a="mepick" id="mePick">${staffList(D).map(s=>`<option value="${s.id}" ${s.id===sid?'selected':''}>${esc(s.name)}</option>`).join('')}</select>`;
  if(!sid) return `<div class="card empty"><b>내 이름이 연결되지 않았어요</b>점주나 매니저에게 계정과 직원 이름을 연결해 달라고 하세요.</div>`;
  const ws=weekStart(new Date()); let tot=0; let out='';
  for(let w=0;w<2;w++){ out+=`<h2 style="font-size:15px;margin:16px 2px 8px">${w?'다음 주':'이번 주'}</h2>`; let wh=0;
    for(let i=0;i<7;i++){ const d=addDays(ws,w*7+i), key=ds(d); const R=resolve(D,d); const x=R.list.find(z=>z.sid===sid); const o=R.offs.find(z=>z.sid===sid);
      const mates=x&&st.vis!=='none'?R.list.filter(z=>z.pos===x.pos&&z.sid!==sid).map(z=>z.name):[];
      if(x){ const h=hoursOf(st,x.sh); wh+=h; const [a,b]=spanOf(st,x.sh);
        out+=`<div class="mday ${key===todayStr?'today':''}"><div class="d"><b>${d.getDate()}</b><span>${DOW[d.getDay()]}요일</span></div><div class="mw"><b>${pad(Math.floor(a/60))}:${pad(a%60)} – ${pad(Math.floor(b/60))}:${pad(b%60)}</b> <span class="tag" style="color:${posColor(x.pos)}">${esc(x.pos)}</span><small>${fmtH(h)}시간${h>=4?` · 휴게 ${h>=8?'1시간':'30분'}`:''}${mates.length?' · 함께: '+esc(mates.join(', ')):''}</small></div></div>`; }
      else out+=`<div class="mday off ${key===todayStr?'today':''}"><div class="d"><b>${d.getDate()}</b><span>${DOW[d.getDay()]}요일</span></div><div class="mw"><b class="muted">${o?esc(o.reason==='고정휴무'||o.reason==='주간휴무'?'휴무':o.reason):'휴무'}</b></div></div>`; }
    out+=`<div class="muted" style="font-size:13px;margin:0 4px 6px">${w?'다음 주':'이번 주'} ${fmtH(wh)}시간${wh>=15?' · 주휴수당 대상':''}</div>`; if(!w) tot=wh; }
  return `<div class="me"><div class="vh"><div><h1>${esc((D.staff[sid]||{}).name||'')}님 근무</h1><div class="sub">${esc(st.name)} · 이번 주 ${fmtH(tot)}시간</div></div><span class="sp"></span>${pick}</div>${out}
    <button class="btn pri" data-a="img" data-t="me" data-k="${sid}" style="width:100%;margin-top:8px">카톡으로 보낼 사진</button></div>`;
}

/* ================= 본사 현황 ================= */
async function loadSum(){ try{ APP.sum=await APP.be.summaries(); }catch(e){ APP.sum={}; toast('본사 현황을 못 불러왔어요: '+e.message); } if(APP.view==='hq') render(); }
function vHQ(){
  const S=APP.sum; const wk=ds(weekStart(new Date())), nk=ds(addDays(weekStart(new Date()),7));
  const stores=APP.be===Local?Local.db.stores:APP.stores;
  const card=s=>{ const a=(S&&S[s.id]||{})[wk], b=(S&&S[s.id]||{})[nk]; const mine=APP.stores.find(x=>x.id===s.id&&x.role);
    const closed=isClosedName(s.name);
    return `<div class="sc"${closed?' style="opacity:.62"':''}><div class="t"><b>${esc(s.name)}</b>${a?'':'<span class="tag">자료 없음</span>'}</div>
      <div class="m"><div><small>이번 주 근무시간</small><b>${a?a.hours.toLocaleString('ko-KR'):'-'}h</b></div><div><small>근무 인원</small><b>${a?a.staff:'-'}명</b></div>
      <div><small>인건비율</small><b>${a&&a.ratio!=null?a.ratio+'%':'—'}</b></div><div><small>다음 주 근무시간</small><b>${b?b.hours.toLocaleString('ko-KR')+'h':'-'}</b></div></div>
      <div class="row" style="justify-content:space-between"><span class="muted" style="font-size:12px">${a&&a.at?'갱신 '+new Date(a.at).toLocaleString('ko-KR',{month:'numeric',day:'numeric',hour:'2-digit',minute:'2-digit'}):'아직 근무표 입력 전'}</span>
      <span>${isHQ()&&APP.be===Remote?`<button class="btn sm" data-a="storerename" data-id="${s.id}" data-name="${esc(s.name)}">이름 바꾸기</button> ${s.isHq?'':`<button class="btn sm ${closed?'':'bad'}" data-a="storeactive" data-id="${s.id}" data-name="${esc(s.name)}" data-on="${closed?1:0}">${closed?'다시 사용':'사용 중지'}</button> ${closed?`<button class="btn sm bad" data-a="storedel" data-id="${s.id}" data-name="${esc(s.name)}">삭제</button> `:''}`}`:''}${mine?`<button class="btn sm" data-a="gostore" data-id="${s.id}">열기</button>`:''}</span></div></div>`; };
  return `<div class="vh"><div><h1>본사 현황</h1><div class="sub">이번 주 매장별 요약 · <b>열기</b>를 누르면 그 매장의 스케줄을 보고 고칠 수 있어요</div></div><span class="sp"></span><button class="btn" data-a="sumreload">새로고침</button><button class="btn pri" data-a="storenew">+ 매장 추가</button></div>
    ${S?`<div class="stores">${stores.map(card).join('')}</div>`:'<div class="card empty">불러오는 중…</div>'}
    <div class="card" style="margin-top:14px"><h2>본사 권한</h2><p class="help" style="margin:0">본사 계정은 모든 매장의 스케줄을 볼 수 있고 고칠 수 있어요. 가맹점 급여 금액은 점주(허용한 매니저)만 보여요. 가맹점은 자기 매장만 보여요.</p></div>`;
}

/* ================= 설정 ================= */
// 급여 보기 권한 버튼: 점주 → 우리 매장 매니저 / 본사 → 본점 매니저 (직원에게는 없음)
function payBtn(a){ const hqName=(APP.stores.find(s=>s.isHq)||{}).name; const L=a.links.find(l=>l.role==='manager'&&(role()==='owner'||(isHQ()&&l.store===hqName))); if(!L) return '';
  return `<button class="btn" data-a="acctpay" data-id="${esc(a.id)}" data-on="${L.pay?0:1}">${L.pay?'급여 보기 끄기':'급여 보기 켜기'}</button>`; }
const fmtAt=t=>{ const d=new Date(t); return isNaN(d)?'':`${d.getMonth()+1}/${d.getDate()} ${String(d.getHours()).padStart(2,'0')}:${String(d.getMinutes()).padStart(2,'0')}`; };
async function acctLoad(){ try{ const r=await APP.be.manageAccounts({action:'list'}); APP.accts=r.rows||[]; APP.acctErr=''; }catch(e){ APP.accts=[]; APP.acctErr=e.message; } if(APP.view==='set'||APP.view==='acct') render(); }
function acctCard(){
  if(APP.accts===undefined){ APP.accts=null; acctLoad(); }
  const A=APP.accts, ago=t=>{ if(!t) return '아직 로그인 안 함'; const d=Math.floor((Date.now()-new Date(t))/864e5); return d<=0?'오늘 로그인':d+'일 전 로그인'; };
  const body=APP.acctErr?`<p class="help" style="color:#C0392B">${esc(APP.acctErr)}</p>`:!A?'<p class="help">불러오는 중…</p>':A.length?A.map(a=>`<div class="row" style="align-items:center;border-top:1px solid var(--line,#E5E8EB);padding:8px 0"><div class="grow"><b>${esc(a.id)}</b>${a.hq?' <span class="muted">· 본사</span>':''}${a.pwByHq?` <span class="muted">· ${esc(fmtAt(a.pwByHq))} 본사가 비밀번호 바꿈</span>`:''}${a.banned?' <span style="color:#C0392B">· 정지됨</span>':''}<br><span class="muted" style="font-size:12px">${a.links.length?a.links.map(l=>esc(l.store)+' '+esc(roleName(l.role).split(' ')[0])+(l.role==='manager'&&l.pay?' (급여 보기)':'')).join(', '):(a.hq?'모든 매장':'연결된 매장 없음')} · ${ago(a.last)}</span></div>${a.hq||a.me?'':`${payBtn(a)}<button class="btn" data-a="acctpw" data-id="${esc(a.id)}">비밀번호 바꾸기</button><button class="btn" data-a="acctban" data-id="${esc(a.id)}" data-on="${a.banned?0:1}">${a.banned?'정지 풀기':'정지'}</button><button class="btn bad" data-a="acctdel" data-id="${esc(a.id)}">삭제</button>`}</div>`).join(''):'<p class="help">계정이 없어요</p>';
  return `<div class="card"><h2>계정 목록 · 관리${isHQ()?' (본사만)':''}</h2><p class="help">만든 아이디를 보고, 비밀번호를 새로 정하거나 정지·삭제할 수 있어요. 지금 비밀번호는 누구도 볼 수 없어요.${isHQ()?' 본사 계정은 여기서 바꾸지 못해요.':''}</p>${body}<div class="row" style="margin-top:8px"><button class="btn" data-a="acctreload">새로고침</button></div></div>`;
}
async function syncLoad(){ try{ APP.syncSt=await APP.be.rpcText('sync_status',{}); }catch(e){ APP.syncSt={err:e.message,last:{error:e.message}}; } if(APP.view==='set') render(); }
// 매장·계정이 바뀌었음을 통합 틀에 알림 → 예약·발주 같은 다른 화면이 다음에 열 때 매장 목록을 새로 불러옴
function notifyStores(){ if(EMBED&&window.parent!==window){ try{ window.parent.postMessage({type:'fr-stores'},'*'); }catch(e){} } }
function acctPage(r){ return `
  ${(r==='hq'||r==='owner')&&APP.be===Remote?`<div class="card"><h2>계정 만들기${r==='hq'?' (본사만)':''}</h2><p class="help">${r==='hq'?'가맹점·매니저·직원 계정은 본사에서만 만들 수 있어요.':'우리 매장 직원·매니저·발주 전용 계정을 만들 수 있어요.'} 아이디와 비밀번호를 정해 알려 주세요. 비밀번호는 8자 이상이고, 만든 뒤에는 본사도 다시 볼 수 없어요.</p>
    ${APP.mkNote?`<p class="help" style="background:#E6F4EA;color:#14532D;padding:10px 12px;border-radius:10px;font-weight:600">${esc(APP.mkNote)}</p>`:''}
    <form id="mkForm" autocomplete="off"><div class="row" style="align-items:flex-end">
    <label class="f">아이디<input type="text" id="mkId" style="width:150px" placeholder="예: suseong" autocapitalize="none" autocomplete="off"></label>
    <label class="f">비밀번호<input type="password" id="mkPw" style="width:150px" placeholder="8자 이상" autocomplete="new-password"></label>
    <label class="f">매장<select id="mkStore">${APP.stores.map(s=>`<option value="${s.id}">${esc(s.name)}</option>`).join('')}</select></label>
    <label class="f">역할<select id="mkRole">${r==='hq'?'<option value="owner">점주</option>':''}<option value="manager">매니저</option><option value="staff">직원</option><option value="order">발주 전용 (발주 화면만)</option></select></label>
    <label class="ck" style="margin-bottom:8px"><input type="checkbox" id="mkPay"> 급여 보기 <span class="muted">(매니저만 · 직원은 불가)</span></label><button type="button" class="btn pri" data-a="mkaccount">계정 만들기</button></div></form>
    ${r!=='hq'?'':`<div class="row" style="align-items:flex-end;margin-top:12px"><label class="f">급여 비밀번호 잊은 계정<input type="text" id="rpId" style="width:150px" placeholder="아이디" autocapitalize="none" autocomplete="off"></label><button type="button" class="btn" data-a="pinreset">급여 비밀번호 초기화</button></div><p class="help">초기화하면 그 계정이 급여 계산기를 열 때 새 비밀번호를 다시 정해요.</p>`}</div>`:''}
    ${(r==='hq'||r==='owner')&&APP.be===Remote?acctCard():''}
`; }
function vAcct(){ const r=role();
  return `<div class="vh"><div><h1>계정 · 권한</h1><div class="sub">${esc(APP.st.name)} · 계정 만들기, 비밀번호, 급여 보기 권한</div></div></div>${APP.be===Remote?acctPage(r):'<div class="card empty"><b>연결된 서버가 없어요</b>설정에서 먼저 연결해 주세요</div>'}`; }
function vSet(){
  const D=APP.D, st=D.store, ed=canEdit(), r=role();
  const posRows=D.positions.map((p,i)=>`<tr><td><input type="color" value="${p.color}" data-a="posf" data-i="${i}" data-f="color" style="width:34px;height:30px;padding:0;border:0;background:none" aria-label="색"></td>
    <td><input type="text" value="${esc(p.name)}" data-a="posf" data-i="${i}" data-f="name" style="width:90px"></td>
    <td class="row" style="flex-wrap:nowrap"><button class="btn sm" data-a="posmv" data-i="${i}" data-n="-1" aria-label="위로">↑</button><button class="btn sm" data-a="posmv" data-i="${i}" data-n="1" aria-label="아래로">↓</button><button class="btn sm bad" data-a="posdel" data-i="${i}">삭제</button></td></tr>`).join('');
  return `<div class="vh"><div><h1>설정</h1><div class="sub">${esc(st.name)} · ${roleName(r)}</div></div></div>
  ${ed?`<div class="card"><h2>매장 정보</h2><p class="help">근무시간 계산 기준이에요. 영업시간 밖은 근무시간에 안 들어가요.</p>
    <div class="row" style="align-items:flex-end">
      <label class="f">매장 이름<input type="text" data-a="stf" data-f="name" value="${esc(st.name)}" style="width:160px"></label>
      <label class="f">영업 시작<input type="text" data-a="stf" data-f="open" value="${st.open}" style="width:80px"></label>
      <label class="f">영업 끝<input type="text" data-a="stf" data-f="close" value="${st.close}" style="width:80px"></label>
      <label class="f">종일 근무(시간)<input type="number" step="0.5" data-a="stf" data-f="fullH" value="${st.fullH}" style="width:80px"></label>
      <label class="f">오후 근무(시간)<input type="number" step="0.5" data-a="stf" data-f="pmH" value="${st.pmH}" style="width:80px"></label>
      <label class="f">오후 출근 시각<input type="text" data-a="stf" data-f="pmStart" value="${st.pmStart}" style="width:80px"></label>
      <label class="f">오전 근무(시간)<input type="number" step="0.5" data-a="stf" data-f="amH" value="${st.amH||5}" style="width:80px"></label>
      <label class="f">오전 출근 시각<input type="text" data-a="stf" data-f="amStart" value="${st.amStart||'12:00'}" style="width:80px"></label>
      <label class="f">목표 인건비율(%)<input type="number" data-a="stf" data-f="target" value="${st.target}" style="width:80px"></label>
    </div>
    <div class="row" style="margin-top:12px;gap:18px">
      <label class="ck"><input type="checkbox" data-a="stf" data-f="fivePlus" ${st.fivePlus?'checked':''}> 상시 5인 이상 매장 (연장·야간 가산 경고)</label>
      <label class="ck">직원끼리 보기 <select data-a="stf" data-f="vis"><option value="week" ${st.vis==='week'?'selected':''}>주간 보드까지</option><option value="day" ${st.vis==='day'?'selected':''}>같은 날 동료만</option><option value="none" ${st.vis==='none'?'selected':''}>자기 근무만</option></select></label></div></div>
  <div class="card"><h2>포지션</h2><p class="help">보드에 나오는 줄이에요. 이름·색·순서를 바꿀 수 있어요.</p>
    <div class="scroll"><table class="t"><thead><tr><th></th><th>포지션</th><th></th></tr></thead><tbody>${posRows}</tbody></table></div>
    <div class="row" style="margin-top:10px"><button class="btn pri" data-a="posmgr">포지션 관리 (추가·삭제·순서)</button><button class="btn" data-a="posadd">+ 포지션 추가</button>${isHQ()?'':'<button class="btn" data-a="postpl">기본 포지션으로 되돌리기</button>'}</div></div>`:''}
  ${pwByHqAt(APP.user)?`<div class="card" style="border-color:#E5533D"><h2>⚠ 본사가 비밀번호를 바꿨어요</h2><p class="help">${esc(fmtAt(pwByHqAt(APP.user)))}에 본사가 이 계정의 비밀번호를 새로 정했어요. 직접 부탁한 게 아니라면 아래 <b>내 비밀번호 바꾸기</b>로 새로 정하세요. 바꾸면 이 알림이 사라져요.</p></div>`:''}
  <div class="card"><h2>연결 · 계정</h2>
    ${APP.be===Local?`<p class="help">지금은 <b>체험 모드</b>예요. 데이터가 이 기기에만 저장돼요. 아래 <b>연결하기</b>를 누르고 로그인하면 ilpum-franchise의 실제 데이터로 쓰고, 가맹점과도 같이 쓸 수 있어요.</p>
      <div class="row"><label class="f grow">Supabase 주소<input type="text" id="cfUrl" placeholder="https://xxxx.supabase.co" value="${esc(Conf.url||'')}"></label><label class="f grow">anon public 키<input type="text" id="cfKey" placeholder="eyJ..." value="${esc(Conf.key||'')}"></label><button class="btn pri" data-a="connect" style="align-self:flex-end">연결하기</button></div>
      <div class="row" style="margin-top:14px"><span class="muted" style="font-size:13px">체험용 역할 바꿔보기:</span><div class="seg">${['hq','owner','manager','staff'].map(x=>`<button data-a="demorole" data-v="${x}" aria-pressed="${(Local.db.demoRole||'hq')===x}">${roleName(x).split(' ')[0]}</button>`).join('')}</div></div>`
    :APP.open?`<p class="help">로그인하지 않고 <b>본점 근무표</b>만 열고 있어요. 금액(급여)과 가맹점 자료는 로그인해야 보여요.</p><div class="row"><button class="btn pri" data-a="gologin">로그인</button><button class="btn" data-a="disconnect">체험 모드로 돌아가기</button></div>`
    :`<p class="help">로그인: <b>${esc(showId(APP.user&&APP.user.email||''))}</b> · 이 기기에서는 다시 묻지 않고 자동으로 들어와요.${Remote.keep?'':' (자동 로그인을 끄고 들어와서, 브라우저를 닫으면 다시 로그인해야 해요)'}</p><div class="row"><button class="btn" data-a="logout">로그아웃</button><button class="btn" data-a="mypw">내 비밀번호 바꾸기</button><button class="btn" data-a="disconnect">체험 모드로 돌아가기</button></div>`}</div>
  ${(r==='hq'||r==='owner')&&APP.be===Remote?'<div class="card"><h2>계정 · 권한</h2><p class="help">계정 만들기 · 비밀번호 바꾸기 · <b>급여 보기 권한 주기</b>는 왼쪽 메뉴 <b>계정 · 권한</b>으로 옮겼어요.</p><div class="row"><button class="btn pri" data-a="view" data-v="acct">계정 · 권한 열기</button></div></div>':''}
    ${r==='hq'&&APP.be===Remote?(()=>{ if(APP.syncSt===undefined){ APP.syncSt=null; syncLoad(); } const S=APP.syncSt; const L=S&&S.last||{}; const ago=S&&S.at?Math.max(0,Math.round((Date.now()-new Date(S.at))/60000)):null;
      const msg=!S?'불러오는 중…':L.error?`<span style="color:#C0392B">마지막 실행에 문제가 있었어요: ${esc(String(L.error).slice(0,160))}</span>`:L.ok?`마지막 실행 ${ago<1?'방금':ago+'분 전'} · 예약 ${L.daysChanged||0}일 확인${L.sched&&(L.sched.upserted||L.sched.pruned)?` · 근무표 ${L.sched.upserted||0}줄 바뀜${L.sched.pruned?` · ${L.sched.pruned}줄 정리`:''}`:''}`:'아직 실행한 적이 없어요';
      return `<div class="card"><h2>예전 서버 자동 연동 (본사만)</h2><p class="help">예전 사이트에서 입력한 예약·근무표가 새 시스템으로 <b>자동으로 따라와요</b>(5분마다, 바뀐 것만). 새 시스템에서 직접 고친 내용은 덮어쓰지 않아요. 새 시스템만 쓰게 되면 끄세요.</p>
      <p class="help"><b>${S?(S.auto?'● 자동 연동 켜짐':'○ 자동 연동 꺼짐'):''}</b> · ${msg}</p>
      <div class="row"><button class="btn pri" data-a="syncrun">지금 한 번 가져오기</button>${S&&S.auto?'<button class="btn" data-a="syncoff">자동 끄기</button>':'<button class="btn pri" data-a="syncon">자동 켜기</button>'}</div></div>`; })():''}
    ${r==='hq'&&APP.be===Remote?(()=>{ let last=''; try{ last=localStorage.getItem('ilpum-last-backup')||''; }catch(e){} const days=last?Math.floor((Date.now()-new Date(last))/864e5):null;
      return `<div class="card"><h2>백업 · 복원 (본사만)</h2><p class="help">모든 매장의 예약·근무표·발주·공지·게시판을 파일 하나로 PC에 받아요. <b>일주일에 한 번</b> 받아 두세요. 급여 금액이 들어 있으니 파일은 아무에게도 보내지 말고 안전한 곳에 보관하세요.</p>
      <p class="help" style="color:${days===null||days>7?'#C0392B':'inherit'}">${days===null?'아직 이 기기에서 백업한 적이 없어요':`마지막 백업: ${days===0?'오늘':days+'일 전'}`}</p>
      <div class="row"><button class="btn pri" data-a="bkdl">전체 백업 받기</button><button class="btn" data-a="bkpick">백업 파일로 복원…</button><input type="file" id="bkFile" accept=".json" hidden></div>
      <p class="help">복원은 파일 내용으로 덮어써요(파일에 없는 자료를 지우지는 않아요). 게시판 글과 공지 사진·동영상 파일은 복원되지 않고 백업 파일에만 남아요.</p></div>`; })():''}
    ${ed&&(APP.be===Local||(APP.st&&APP.st.isHq))?`<div class="card"><h2>데이터</h2><p class="help">지금 쓰는 근무표(schedule.html) 데이터를 이 매장으로 옮길 수 있어요. 직원·요일 패턴·기간 설정·이 날만·고정알바 주간 입력·금액까지 옮겨져요.</p>
    <div class="row"><button class="btn pri" data-a="importold">기존 근무표 서버에서 가져오기</button><label class="btn" style="cursor:pointer">기존 백업 파일(.json)로 가져오기<input type="file" id="impFile" accept=".json" hidden></label>
    <button class="btn" data-a="backup">이 매장 백업 받기</button>${APP.be===Local?'<button class="btn bad" data-a="resetdemo">체험 데이터 초기화</button>':''}</div></div>`:''}`;
}

/* ================= 로그인 (자동 로그인) ================= */
function renderLogin(){
  $('#app').innerHTML=`<div style="min-height:100vh;display:grid;place-items:center;padding:20px"><div class="card" style="width:min(380px,100%)">
    <div class="brand" style="padding:0;margin-bottom:14px"><div class="mk">일</div><div><b>일품집 근무표</b><small>본사·가맹점 통합</small></div></div>
    <form id="lgForm" method="post" autocomplete="on">
      <label class="f">아이디<input type="text" name="username" id="lgEmail" autocomplete="username" autocapitalize="none" autocorrect="off" spellcheck="false" value="${esc(showId(Conf.email||''))}" required></label><div style="height:10px"></div>
      <label class="f">비밀번호<input type="password" name="password" id="lgPw" autocomplete="current-password" required></label><div style="height:10px"></div>
      <label class="ck"><input type="checkbox" id="lgKeep" checked> 자동 로그인 <span class="muted" style="font-size:12px">(이 기기에서 다시 묻지 않아요)</span></label><div style="height:12px"></div>
      <button class="btn pri" type="submit" style="width:100%">로그인</button></form>
    <button class="btn ghost" data-a="disconnect" style="width:100%;margin-top:4px">체험 모드로 보기</button></div></div>`;
  setTimeout(()=>{ const f=$(Conf.email?'#lgPw':'#lgEmail'); if(f) f.focus(); },50);
}

/* ================= 접속 실패 안내 ================= */
function renderOffline(msg){
  $('#app').innerHTML=`<div style="min-height:100vh;display:grid;place-items:center;padding:20px"><div class="card" style="width:min(420px,100%)">
    <div class="brand" style="padding:0;margin-bottom:12px"><div class="mk">일</div><div><b>일품집 근무표</b><small>본사·가맹점 통합</small></div></div>
    <h2>서버에 연결하지 못했어요</h2>
    <p class="help">${esc(msg||'')}<br>인터넷이 끊겼거나, Claude 앱 안의 미리보기처럼 외부 접속을 막는 화면에서 열었을 수 있어요. 실제 사이트 주소(Netlify·Cloudflare)로 열면 돼요.</p>
    <button class="btn pri" data-a="retry" style="width:100%">다시 시도</button>
    <button class="btn" data-a="disconnect" style="width:100%;margin-top:8px">체험 모드로 보기</button></div></div>`;
}

/* ---------- 통합관리 화면과 주고받기 ---------- */
window.addEventListener('message',e=>{
  const m=e.data; if(!m||e.source!==window.parent||m.type!=='fr-goto'||!VIEWS.includes(m.view)||!APP.st) return;
  try{ closeDrawer(); }catch(_){} APP.view=m.view; render(); window.scrollTo(0,0);
});
window.pullNow=()=>{ try{ poll(); }catch(e){} };      // 탭을 다시 열 때 최신으로 (기존 index.html 방식)
