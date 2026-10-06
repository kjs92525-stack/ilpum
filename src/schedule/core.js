/* ================= 기본 도구 ================= */
const $=(s,r=document)=>r.querySelector(s), $$=(s,r=document)=>[...r.querySelectorAll(s)];
const pad=n=>String(n).padStart(2,'0');
const ds=d=>`${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())}`;
const pd=k=>new Date(k+'T00:00');
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const uid=()=>Math.random().toString(36).slice(2,10);
const DOW=['일','월','화','수','목','금','토'], WD_MON=[1,2,3,4,5,6,0];
const addDays=(d,n)=>new Date(d.getFullYear(),d.getMonth(),d.getDate()+n);
const weekStart=d=>{ const x=new Date(d.getFullYear(),d.getMonth(),d.getDate()); x.setDate(x.getDate()-((x.getDay()+6)%7)); return x; };
const weekKey=d=>ds(weekStart(d));
const md=k=>{ const d=pd(k); return `${d.getMonth()+1}/${d.getDate()}`; };
const mdw=k=>{ const d=pd(k); return `${d.getMonth()+1}/${d.getDate()}(${DOW[d.getDay()]})`; };
const won=v=>Math.round(v||0).toLocaleString('ko-KR')+'원';
const todayStr=ds(new Date());
const MINWAGE=10320;   // 2026년 최저시급
function wonS(v){ if(v==null) return ''; if(v>=10000&&v%1000===0) return (v/10000).toLocaleString('ko-KR',{maximumFractionDigits:1})+'만'; return Math.round(v).toLocaleString('ko-KR')+'원'; }
function payLbl(p){ if(!p||p.v==null) return ''; return p.k==='hour'?'시급 '+wonS(p.v):p.k==='bonus'?'+'+wonS(p.v):p.k==='month'?'월 '+wonS(p.v):wonS(p.v); }
let _tt; function toast(m){ const el=$('#toast'); el.textContent=m; el.classList.add('on'); clearTimeout(_tt); _tt=setTimeout(()=>el.classList.remove('on'),2200); }

/* ---------- 시간 ---------- */
function tMin(t){ if(!t||typeof t!=='string') return null; const m=t.match(/^(\d{1,2}):(\d{2})$/); return m?(+m[1])*60+(+m[2]):null; }
function tLbl(t){ const x=tMin(t); if(x==null) return ''; const h=Math.floor(x/60), mi=x%60; const hh=h<10?'오전'+h:(h>12?h-12:h); return hh+'시'+(mi===30?'반':mi?mi+'분':''); }
function zen(s){ return String(s||'').replace(/[０-９．：]/g,c=>c==='．'?'.':c==='：'?':':String.fromCharCode(c.charCodeAt(0)-0xFEE0)); }
// "11" "5시반" "17:30" "1730" "오전 9시" → 'HH:MM' (출근 1~9시=오후, 퇴근 1~11시=오후)
function parseT(raw,isEnd){
  let s=zen(raw).trim().replace(/\s+/g,''); if(!s) return null;
  const am=/^오전/.test(s), pmf=/^오후/.test(s); s=s.replace(/^(오전|오후)/,'').replace(/(출근|퇴근|출|퇴)$/,'');
  let m,h,mi=0,lit=false;
  if((m=s.match(/^(\d{1,2}):(\d{2})$/))){ h=+m[1]; mi=+m[2]; lit=m[1].length===2&&(m[1][0]==='0'||h>=12); }
  else if((m=s.match(/^(\d{1,2})(\d{2})$/))){ h=+m[1]; mi=+m[2]; lit=true; }
  else if((m=s.match(/^(\d{1,2})시?(?:(반)|(\d{1,2})분?)?$/))){ h=+m[1]; mi=m[2]?30:(m[3]?+m[3]:0); }
  else return null;
  if(h>24||mi>59) return null;
  if(pmf&&h<12) h+=12; else if(!am&&!lit&&h<12&&(isEnd?h<=11:h<=9)) h+=12;
  if(h>=24) return null; return pad(h)+':'+pad(mi);
}
function parseWon(raw){ let s=zen(raw).trim().replace(/[,\s원]/g,''); if(!s) return null;
  const man=/만$/.test(s); s=s.replace(/만$/,''); if(!/^\d+(\.\d+)?$/.test(s)) return NaN;
  let v=parseFloat(s); if(man||v<1000) v*=10000; return Math.round(v); }
function shLbl(sh,st){ if(!sh||sh.k==='full') return ''; if(sh.k==='pm') return '오후'; if(sh.k==='am') return '오전';
  if(sh.k==='t') return tLbl(sh.s)+(sh.e&&sh.e!==(st?st.close:'22:00')?'~'+tLbl(sh.e):''); return ''; }
function shSame(a,b){ const n=x=>(!x||x.k==='full')?'full':x.k==='pm'?'pm':x.k==='am'?'am':'t'+x.s+'-'+(x.e||''); return n(a)===n(b); }
function shIsPm(sh,st){ return !!sh&&(sh.k==='pm'||(sh.k==='t'&&tMin(sh.s)>=12*60)); }
// 근무시간: 영업시간 안쪽만 (급여 계산기와 같은 규칙)
function hoursOf(st,sh){
  if(!sh||sh.k==='full') return +st.fullH||10; if(sh.k==='pm') return +st.pmH||5; if(sh.k==='am') return +st.amH||5;
  const o=tMin(st.open), c=tMin(st.close); let a=tMin(sh.s), b=tMin(sh.e||st.close); if(a==null||b==null) return +st.fullH||10;
  a=Math.max(o,Math.min(c,a)); b=Math.max(o,Math.min(c,b)); return Math.max(0,Math.round((b-a)/60*100)/100);
}
function spanOf(st,sh){ // 타임라인 막대용 [시작분, 끝분]
  const o=tMin(st.open), c=tMin(st.close);
  if(!sh||sh.k==='full') return [o,c];
  if(sh.k==='pm') return [tMin(st.pmStart)||c-300,c];
  if(sh.k==='am'){ const a=tMin(st.amStart)||720; return [a,Math.min(c,a+60*(+st.amH||5))]; }
  return [Math.max(o,tMin(sh.s)),Math.min(c,tMin(sh.e||st.close))];
}

/* ================= 저장소: 체험(이 기기) / Supabase ================= */
const CONF_KEY='ilpum-fr-conf', LOCAL_KEY='ilpum-fr-v1';
const Conf=(()=>{ try{ return JSON.parse(localStorage.getItem(CONF_KEY))||{}; }catch(e){ return {}; } })();
// 아이디만 쳐도 로그인: 'ilpum' → 'ilpum@ilpum.invalid' (.invalid 는 실제로 없는 주소라 비밀번호 찾기 메일이 새 나갈 일이 없음)
const ID_DOMAIN='ilpum.invalid';
const toLoginEmail=v=>{ v=String(v||'').trim(); return v.includes('@')?v:v.toLowerCase()+'@'+ID_DOMAIN; };
const showId=v=>String(v||'').replace('@'+ID_DOMAIN,'');
// 같은 주소의 다른 화면(예약·통합 틀)이 로그인 토큰을 갱신했으면 그걸 지우지 않음
function saveConf(){ try{ if(Conf.ses){ const cur=JSON.parse(localStorage.getItem(CONF_KEY)||'null'); if(cur&&cur.ses&&(cur.ses.expires_at||0)>(Conf.ses.expires_at||0)) Conf.ses=cur.ses; } localStorage.setItem(CONF_KEY,JSON.stringify(Conf)); }catch(e){} }
// ilpum-franchise 프로젝트 (anon 키는 공개용이며, 실제 접근은 로그인 + DB 권한 규칙으로 막힘)
const DEF_SUPA={url:'https://bdqcrbnbuoujozlpttbe.supabase.co',key:'/*NEWKEY*/'};
if(!Conf.url||!Conf.key){ Conf.url=DEF_SUPA.url; Conf.key=DEF_SUPA.key; }
if(!Conf.mode) Conf.mode='remote';

const Local={
  db:null, name:'local',
  load(){ try{ this.db=JSON.parse(localStorage.getItem(LOCAL_KEY)); }catch(e){} if(!this.db||!this.db.stores) this.db=seedDemo(); },
  persist(){ try{ localStorage.setItem(LOCAL_KEY,JSON.stringify(this.db)); }catch(e){ toast('이 기기 저장 공간이 부족해요'); } },
  async init(){ this.load(); return {uid:'demo', email:'체험 모드'}; },
  async stores(){ const r=this.db.demoRole||'hq';
    return this.db.stores.map(s=>{ const hqOwned=s.id===this.db.stores[0].id;
      const role = r;                                           // 본사는 모든 매장을 관리 (실서버와 같은 규칙)
      return {id:s.id,name:s.name,role,pay: (role==='hq'&&hqOwned)||role==='owner'||(role==='manager'&&!!this.db.managerPay), staffId:(this.db.demoMe||{})[s.id]||null}; }); },
  async items(sid){ const it=this.db.items[sid]||{}; const out={}; Object.keys(it).forEach(k=>out[k]=JSON.parse(JSON.stringify(it[k]))); return out; },
  async put(sid,kind,id,data){ const it=this.db.items[sid]=this.db.items[sid]||{}; const g=it[kind]=it[kind]||{};
    if(data==null) delete g[id]; else g[id]=JSON.parse(JSON.stringify(data)); this.persist(); },
  async since(){ return null; },
  async summaries(){ return JSON.parse(JSON.stringify(this.db.sum||{})); },
  async putSummary(sid,week,data){ this.db.sum=this.db.sum||{}; (this.db.sum[sid]=this.db.sum[sid]||{})[week]=data; this.persist(); },
  async createStore(id,name){ if(this.db.stores.some(s=>s.id===id)) throw new Error('이미 있는 매장 코드예요'); this.db.stores.push({id,name}); this.db.items[id]={}; this.persist(); },
  async addMember(){ throw new Error('체험 모드에서는 계정을 연결할 수 없어요. Supabase에 연결한 뒤 사용하세요'); },
  async createAccount(){ throw new Error('체험 모드에서는 계정을 만들 수 없어요. Supabase에 연결한 뒤 사용하세요'); },
  async rpcText(){ throw new Error('체험 모드에서는 쓸 수 없어요'); }, async backupAll(){ throw new Error('체험 모드에서는 백업할 수 없어요'); }, async restoreAll(){ throw new Error('체험 모드에서는 복원할 수 없어요'); }
};

const PINMSG={bad_pin:'편집 비밀번호가 달라요',locked:'여러 번 틀려서 15분 동안 잠겼어요',denied:'권한이 없어요',short:'비밀번호는 6자 이상으로 정해주세요',bad_rows:'저장할 수 없는 항목이 있어요',nopin:''};
const Remote={
  name:'remote', url:'', key:'', ses:null, pin:'',
  H(auth=true){ const h={apikey:this.key,'Content-Type':'application/json'}; h.Authorization='Bearer '+((auth&&this.ses&&this.ses.access_token)||this.key); return h; },
  async fetchJ(path,opt={},retry=true){
    const r=await fetch(this.url+path,{...opt,headers:{...this.H(),...(opt.headers||{})},cache:'no-store'});
    if(r.status===401&&retry&&this.ses&&this.ses.refresh_token){ await this.refresh(); return this.fetchJ(path,opt,false); }
    if(!r.ok){ let m='HTTP '+r.status; try{ const j=await r.json(); m=j.message||j.msg||j.error_description||(typeof j.error==='string'&&j.error)||m; }catch(e){} throw new Error(m); }
    const t=await r.text(); return t?JSON.parse(t):null;
  },
  // 자동 로그인: 비밀번호는 저장하지 않고, 서버가 준 '로그인 유지 토큰'만 이 기기에 저장 (만료되면 알아서 갱신)
  persist(){ if(this.keep){ Conf.ses=this.ses; saveConf(); try{ sessionStorage.removeItem('fr-ses'); }catch(e){} }
             else { Conf.ses=null; saveConf(); try{ sessionStorage.setItem('fr-ses',JSON.stringify(this.ses)); }catch(e){} } },
  forget(){ this.ses=null; Conf.ses=null; saveConf(); try{ sessionStorage.removeItem('fr-ses'); }catch(e){} },
  async login(email,pw,keep){
    const r=await fetch(this.url+'/auth/v1/token?grant_type=password',{method:'POST',headers:this.H(false),body:JSON.stringify({email,password:pw})});
    const j=await r.json().catch(()=>({})); if(!r.ok) throw new Error(/invalid/i.test(j.error_description||j.msg||'')?'이메일이나 비밀번호가 달라요':(j.error_description||j.msg||'로그인 실패'));
    this.ses=j; this.keep=!!keep; this.persist(); return j.user;
  },
  async refresh(){
    // 여러 화면이 동시에 갱신하면 서로의 토큰을 무효로 만들 수 있어서, 한 번에 한 화면만 갱신 (다른 화면이 방금 갱신했으면 그걸 씀)
    const run=async()=>{
      let latest=null; try{ const c=JSON.parse(localStorage.getItem(CONF_KEY)||'null'); latest=(c&&c.ses)||null; if(!latest){ const t=sessionStorage.getItem('fr-ses'); if(t) latest=JSON.parse(t); } }catch(e){}
      if(latest && this.ses && latest.access_token!==this.ses.access_token && (latest.expires_at||0)*1000>Date.now()+60000){ this.ses=latest; return; }
      const rt=(latest&&latest.refresh_token)||this.ses.refresh_token;
      const r=await fetch(this.url+'/auth/v1/token?grant_type=refresh_token',{method:'POST',headers:this.H(false),body:JSON.stringify({refresh_token:rt})});
      const j=await r.json().catch(()=>({})); if(!r.ok){ this.forget(); throw Object.assign(new Error('다시 로그인해 주세요'),{auth:true}); }
      this.ses=j; this.persist();
    };
    return navigator.locks?navigator.locks.request('ilpum-refresh',run):run();
  },
  async init(){ this.url=(Conf.url||'').replace(/\/$/,''); this.key=Conf.key||''; this.ses=Conf.ses||null; this.keep=!!this.ses;
    if(!this.ses){ try{ const s=sessionStorage.getItem('fr-ses'); if(s){ this.ses=JSON.parse(s); this.keep=false; } }catch(e){} }
    if(!this.ses) return null;
    if(this.ses.expires_at && this.ses.expires_at*1000<Date.now()+60000) await this.refresh();
    return this.ses.user; },
  // 로그인 없이 열리는 본점 (급여 제외 · 편집 비밀번호가 켜져 있으면 그때만 비밀번호)
  async openInfo(){ const r=await fetch(this.url+'/rest/v1/rpc/sch_open_store',{method:'POST',headers:this.H(false),body:'{}'}); if(!r.ok) return null; const j=await r.json(); return (j&&j[0])||null; },   // 네트워크 오류는 그대로 던짐
  async rpcText(fn,body){ const r=await this.fetchJ('/rest/v1/rpc/'+fn,{method:'POST',body:JSON.stringify(body)}); return r; },
  async stores(){
    if(!this.ses){ const o=await this.openInfo(); return o?[{id:o.id,name:o.name,isHq:true,role:'open',pay:false,staffId:null,hasPin:!!o.has_pin}]:[]; }
    const rows=await this.fetchJ('/rest/v1/rpc/sch_my_stores',{method:'POST',body:'{}'});
    return rows.map(r=>({id:r.id,name:r.name,isHq:!!r.is_hq,role:r.role||null,pay:!!r.can_pay,staffId:r.staff_id||null}));
  },
  async items(sid){ const rows=await this.fetchJ(`/rest/v1/sch_items?select=kind,id,data,deleted,updated_at&store_id=eq.${encodeURIComponent(sid)}&deleted=eq.false&id=not.like.calc:*&kind=neq.site`);
    const out={}; let last=''; rows.forEach(r=>{ (out[r.kind]=out[r.kind]||{})[r.id]=r.data; if(r.updated_at>last) last=r.updated_at; }); this.last=last||new Date(0).toISOString(); return out; },
  async since(sid){ const rows=await this.fetchJ(`/rest/v1/sch_items?select=kind,id,data,deleted,updated_at&store_id=eq.${encodeURIComponent(sid)}&id=not.like.calc:*&kind=neq.site&updated_at=gt.${encodeURIComponent(this.last)}&order=updated_at`);
    rows.forEach(r=>{ if(r.updated_at>this.last) this.last=r.updated_at; }); return rows; },
  async putMany(batch){
    const by={}; batch.forEach(w=>(by[w.sid]=by[w.sid]||[]).push(w));
    for(const sid of Object.keys(by)){ const list=by[sid];
      if(!this.ses){   // 로그인 없이: 서버 함수로 저장 (급여는 못 씀)
        const r=await this.rpcText('sch_put_many',{p_store:sid,p_pin:this.pin||'',p_rows:list.map(w=>({kind:w.kind,id:w.id,data:w.data,deleted:w.data==null}))});
        if(r!=='ok') throw Object.assign(new Error(PINMSG[r]||('저장 실패: '+r)),{code:r||'fail'});
      } else {
        await this.fetchJ('/rest/v1/sch_items?on_conflict=store_id,kind,id',{method:'POST',headers:{Prefer:'resolution=merge-duplicates,return=minimal'},
          body:JSON.stringify(list.map(w=>({store_id:w.sid,kind:w.kind,id:w.id,data:w.data==null?null:w.data,deleted:w.data==null})))});
      } } },
  async put(sid,kind,id,data){ await this.fetchJ('/rest/v1/sch_items?on_conflict=store_id,kind,id',{method:'POST',headers:{Prefer:'resolution=merge-duplicates,return=minimal'},
    body:JSON.stringify({store_id:sid,kind,id,data:data==null?null:data,deleted:data==null})}); },
  async summaries(){ const rows=await this.fetchJ('/rest/v1/sch_summaries?select=store_id,week,data,updated_at'); const o={};
    rows.forEach(r=>{ (o[r.store_id]=o[r.store_id]||{})[r.week]=Object.assign({},r.data,{at:Date.parse(r.updated_at)}); }); return o; },
  async putSummary(sid,week,data){
    if(!this.ses){ const r=await this.rpcText('sch_put_summary',{p_store:sid,p_pin:this.pin||'',p_week:week,p_data:data}); if(r!=='ok') throw Object.assign(new Error(PINMSG[r]||r),{code:r}); return; }
    await this.fetchJ('/rest/v1/sch_summaries?on_conflict=store_id,week',{method:'POST',headers:{Prefer:'resolution=merge-duplicates,return=minimal'},body:JSON.stringify({store_id:sid,week,data})}); },
  async createStore(id,name){ await this.fetchJ('/rest/v1/rpc/sch_create_store',{method:'POST',body:JSON.stringify({p_name:name})}); },
  async addMember(email,sid,role,pay){ await this.fetchJ('/rest/v1/rpc/sch_add_member',{method:'POST',body:JSON.stringify({p_email:email,p_store:sid,p_role:role,p_pay:!!pay})}); },
  // 계정 만들기: 본사만 (서버 함수가 본사인지 확인하고 만들어요)
  async createAccount(o){ return this.fetchJ('/functions/v1/create-account',{method:'POST',body:JSON.stringify(o)}); },
  // 계정 관리(목록·비밀번호 바꾸기·정지·삭제): 본사만
  // 내 비밀번호 바꾸기 (로그인한 본인). pw_self_at 은 "본사가 바꾼 뒤 내가 다시 바꿨는지" 판단용
  async changeMyPassword(pw){ const j=await this.fetchJ('/auth/v1/user',{method:'PUT',body:JSON.stringify({password:pw,data:{pw_self_at:new Date().toISOString()}})}); if(j&&j.id&&this.ses){ this.ses.user=j; this.persist(); } return j; },
  async manageStores(o){ return this.fetchJ('/functions/v1/manage-stores',{method:'POST',body:JSON.stringify(o)}); },
  async manageAccounts(o){ return this.fetchJ('/functions/v1/manage-accounts',{method:'POST',body:JSON.stringify(o)}); },
  // 전체 백업 / 복원 (본사만 — 서버 규칙이 본사 계정 말고는 모든 매장 자료를 주지 않아요)
  BK_TABLES:[['sch_items','store_id,kind,id'],['res_days','store_id,id'],['wh_items','store_id,id'],['wh_orders','store_id,code'],['board_notices','id'],['board_msgs','id']],
  async backupAll(prog){
    const out={app:'ilpum',version:1,createdAt:new Date().toISOString(),tables:{}};
    out.stores=await this.fetchJ('/rest/v1/rpc/sch_my_stores',{method:'POST',body:'{}'});
    for(const [t,ord] of this.BK_TABLES){ if(prog) prog(t); let all=[],from=0;
      for(;;){ const rows=await this.fetchJ(`/rest/v1/${t}?select=*&order=${ord}&limit=1000&offset=${from}`)||[]; all=all.concat(rows); if(rows.length<1000) break; from+=1000; }
      out.tables[t]=all; }
    try{ out.noticeMedia=(out.tables.board_notices||[]).flatMap(n=>n.media||[]).map(m=>m.path); }catch(e){}
    return out;
  },
  // 복원 = 덮어쓰기(upsert)만 해요. 파일에 없는 자료를 지우지는 않아요. 게시판 글은 서버 규칙상 다시 넣을 수 없어 건너뛰어요.
  async restoreAll(o,prog){
    if(!o||o.app!=='ilpum'||!o.tables) throw new Error('일품집 백업 파일이 아니에요');
    const done={};
    for(const [t,ord] of this.BK_TABLES){ if(t==='board_msgs') continue; const rows=o.tables[t]||[]; if(!rows.length){ done[t]=0; continue; }
      for(let i=0;i<rows.length;i+=200){ if(prog) prog(t,Math.min(i+200,rows.length),rows.length);
        await this.fetchJ(`/rest/v1/${t}?on_conflict=${ord}`,{method:'POST',headers:{Prefer:'resolution=merge-duplicates,return=minimal'},body:JSON.stringify(rows.slice(i,i+200))}); }
      done[t]=rows.length; }
    return done;
  }
};

/* ================= 매장 데이터 ================= */
const DEF_POS=[['카운터','#3C5A86',1,1],['홀','#2F6B3F',3,4],['그릴','#B8621B',2,3],['주방','#8A2E2E',3,4],['장치','#5B3F86',0,0],['장잡','#1F6F78',0,0],['배송','#8A6A12',0,0],['주차','#55605A',0,1]];
const defStore=()=>({name:'',open:'11:00',close:'22:00',fullH:10,pmH:5,pmStart:'17:00',amH:5,amStart:'12:00',fivePlus:true,vis:'week',target:25});
const defPositions=()=>DEF_POS.map(([name,color,wd,we])=>({name,color,req:[we,wd,wd,wd,wd,wd,we]}));
const safeColor=c=>/^#[0-9a-fA-F]{3,8}$/.test(String(c||''))?c:'#888888';
const cleanPositions=a=>Array.isArray(a)? a.filter(p=>p&&typeof p.name==='string').map(p=>Object.assign({},p,{color:safeColor(p.color)})) : [];
// 본사가 이 계정 비밀번호를 바꾼 뒤 본인이 아직 다시 안 바꿨으면 그 시각(문자열), 아니면 ''
const pwByHqAt=u=>{ const h=u&&u.app_metadata&&u.app_metadata.pw_by_hq, m=u&&u.user_metadata&&u.user_metadata.pw_self_at; return h&&(!m||m<h)?h:''; };
const CLOSED_MARK=' (사용 중지)', isClosedName=n=>String(n||'').endsWith(CLOSED_MARK);
const TYPES={regular:'고정 근무',weekly:'매주 변동',spot:'단기·당일'};
// 보건증(건강진단결과서): 발급일 hcIss · 만료일 hcExp (만료일을 비우면 발급일 + 1년). 만료 30일 전부터 알림
// 입사 1년 되는 날 (같은 날짜 다음 해, 2/29 입사는 3/1)
function oneYear(k){ const m=String(k||'').match(/^(\d{4})-(\d{2})-(\d{2})$/); if(!m) return ''; return ds(new Date(+m[1]+1,+m[2]-1,+m[3])); }
function hcExpOf(s){ if(!s) return ''; if(s.hcExp) return s.hcExp; if(!s.hcIss) return ''; const m=s.hcIss.match(/^(\d{4})-(\d{2})-(\d{2})$/); if(!m) return ''; const d=new Date(+m[1]+1,+m[2]-1,+m[3]); d.setDate(d.getDate()-1); return ds(d); }
function hcState(s,today){ const exp=hcExpOf(s); if(!exp) return {exp:'',days:null,lv:'none'};
  const t=today||ds(new Date()); const days=Math.round((new Date(exp+'T00:00')-new Date(t+'T00:00'))/86400000);
  return {exp,days,lv:days<0?'over':days<=30?'soon':'ok'}; }
function buildD(items,storeName){
  const g=k=>items[k]||{}; const cfg=g('cfg');
  const store=Object.assign(defStore(),cfg.store||{}); if(!store.name) store.name=storeName||'';
  return {store, positions:(cleanPositions(cfg.positions).length)?cleanPositions(cfg.positions):defPositions(),
    staff:g('staff'),rules:g('rule'),dc:g('dc'),spot:g('spot'),aw:g('aw'),sales:g('sales'),pay:g('pay')};
}
const KIND_OF={staff:'staff',rules:'rule',dc:'dc',spot:'spot',aw:'aw',sales:'sales',pay:'pay'};
function staffList(D,all){ return Object.values(D.staff).filter(s=>all||s.active!==false).sort((a,b)=>(a.order||0)-(b.order||0)||a.name.localeCompare(b.name,'ko')); }

/* ================= 근무 계산 엔진: 요일 패턴 → 기간 설정 → 주간 입력 → 그날만 ================= */
function rulesSorted(D){ return Object.values(D.rules).filter(r=>r&&r.from&&Array.isArray(r.ids)).sort((a,b)=>(a.at||0)-(b.at||0)); }
function ruleHit(r,sid,key,wd){ return r.ids.includes(sid)&&key>=r.from&&key<=(r.to||r.from)&&(!r.days||!r.days.length||r.days.includes(wd)); }
function resolve(D,d,opt={}){
  const rules=opt.rules||rulesSorted(D);
  const key=ds(d), wd=d.getDay(), di=(wd+6)%7, wk=weekKey(d);
  const list=[], offs=[]; const pnames=D.positions.map(p=>p.name);
  staffList(D).forEach(s=>{
    if(s.last&&key>s.last) return;            // 마지막 근무일이 지난 사람은 그 다음 날부터 근무표에서 빠져요 (지난 기록은 그대로)
    let working=false, reason=null, pos=s.pos, tag=null, sh=null, shSrc='', ruleIds=[], payoff=false, awSh=null, awMissing=false;
    if(s.type==='weekly'){ const en=(D.aw[wk]||{})[s.id];
      if(en){ working=!(en.off||[]).includes(di); if(!working) reason='주간휴무';
        else { const tt=(en.t||{})[di]; if(tt&&tt.s) awSh={k:'t',s:tt.s,e:tt.e||''}; else if((en.pm||[]).includes(di)) awSh={k:'pm'}; } }
      else awMissing=true; }
    else if(s.type==='spot'){ working=false; }
    else { working=!(s.off||[]).includes(wd); if(!working) reason='고정휴무'; }
    const pat=(s.wk||{})[wd]; if(pat&&pat.sh){ sh=pat.sh; shSrc='pat'; }
    rules.forEach(r=>{ if(!ruleHit(r,s.id,key,wd)) return; ruleIds.push(r.id);
      if(r.w==='off'){ working=false; reason=(r.memo&&r.memo.length<=8)?r.memo:'기간휴무'; }
      else if(r.w==='on'&&!working){ working=true; reason=null; tag='add'; }
      if(r.pos) pos=r.pos; if(r.sh){ sh=r.sh; shSrc='rule'; } });
    if(awSh){ sh=awSh; shSrc='week'; }
    const dc=opt.noDc&&opt.noDc===s.id? null : D.dc[key+'|'+s.id];
    if(dc){
      if(dc.st==='off'||dc.st==='annual'){ working=false; reason=dc.st==='annual'?'월차':'휴무'; }
      else if(dc.st==='extra'){ if(!working) tag='add'; working=true; reason=null; }
      else if(dc.st==='paidoff'){ working=true; payoff=true; tag='payoff'; reason=null; }
      if(dc.pos) pos=dc.pos; if(dc.sh){ sh=dc.sh; shSrc='day'; } }
    if(!pnames.includes(pos)) pos=pnames[0];
    if(!tag&&pos!==s.pos) tag='chg';
    if(working) list.push({sid:s.id,name:s.name,nl:s.note||'',type:s.type,pos,tag,sh,shSrc,ruleIds,payoff,memo:(dc&&dc.memo)||''});
    else if(reason||(awMissing&&!opt.quiet)) offs.push({sid:s.id,name:s.name,reason:reason||'미입력',ruleIds,missing:!reason&&awMissing});
  });
  Object.values(D.spot).filter(x=>x&&x.date===key).forEach(x=>{
    list.push({spotId:x.id,name:x.name,type:'spot',pos:pnames.includes(x.pos)?x.pos:pnames[0],tag:'spot',sh:x.sh||null,shSrc:x.sh?'day':'',ruleIds:[],memo:x.memo||'',nl:x.note||''}); });
  return {key,wd,list,offs};
}
function findItem(D,key,sid,opt={}){ return resolve(D,pd(key),opt).list.find(x=>x.sid===sid)||null; }

/* ---------- 금액 (권한 있는 사람만 D.pay가 채워짐) ---------- */
function payOf(D,x,key,wd){
  const P=D.pay||{}; let ov=null, src='';
  if(x.spotId){ ov=P['spot:'+x.spotId]||null; if(ov) src='day'; return {ov,src,base:null}; }
  const pat=P['pat:'+x.sid+':'+wd]; if(pat){ ov=pat; src='pat'; }
  x.ruleIds.forEach(id=>{ const p=P['rule:'+id]; if(p){ ov=p; src='rule'; } });
  const dp=P['dc:'+key+'|'+x.sid]; if(dp){ ov=dp; src='day'; }
  return {ov,src,base:P['staff:'+x.sid]||null};
}
function costOf(D,x,key,wd){
  const st=D.store; const h=x.payoff?0:hoursOf(st,x.sh); const {ov,src,base}=payOf(D,x,key,wd);
  let bc=null; if(base){ if(base.k==='hour') bc=base.v*h; else if(base.k==='day') bc=Math.round(base.v*h/(+st.fullH||10)); else if(base.k==='month') bc=Math.round(base.v/30); }
  let c=bc; if(ov){ if(ov.k==='day') c=ov.v; else if(ov.k==='hour') c=ov.v*h; else if(ov.k==='bonus') c=(bc||0)+ov.v; }
  const rate = h>0&&c!=null&&(ov?ov.k!=='bonus':base&&base.k!=='month')? c/h : null;
  return {h,c,ov,src,base,rate,cash:!!(ov&&ov.cash)};
}

/* ---------- 한 주 계산 + 노동법 경고 ---------- */
function reqOf(D,pos,wd){ const p=D.positions.find(x=>x.name===pos); return p&&p.req? (+p.req[wd]||0) : 0; }
function weekCalc(D,ws,canPay){
  const rules=rulesSorted(D); const st=D.store; const days=[]; const per={};
  let reqCells=0, filled=0, shortCells=0, hours=0, cost=0, costKnown=true, sales=0;
  for(let i=0;i<7;i++){ const d=addDays(ws,i); const R=resolve(D,d,{rules});
    const by={}; D.positions.forEach(p=>by[p.name]=[]); R.list.forEach(x=>(by[x.pos]=by[x.pos]||[]).push(x));
    let dh=0, dc=0, dMissing=0, need=0, have=0; const short={};
    D.positions.forEach(p=>{ const rq=reqOf(D,p.name,R.wd), n=by[p.name].length; need+=rq; have+=Math.min(n,rq); if(rq&&n<rq){ short[p.name]=rq-n; shortCells+=rq-n; } });
    reqCells+=need; filled+=have;
    R.list.forEach(x=>{ const k=costOf(D,x,R.key,R.wd); x.h=k.h; x.cost=k; dh+=k.h;
      if(canPay){ if(k.c==null) dMissing++; else dc+=k.c; }
      if(x.sid){ const p=per[x.sid]=per[x.sid]||{name:x.name,h:0,days:[]}; p.h+=k.h; p.days.push({key:R.key,h:k.h,rate:k.rate,sh:x.sh}); } });
    const sv=(D.sales[R.key]||{}).v||0; sales+=sv; hours+=dh; cost+=dc; if(dMissing) costKnown=false;
    days.push({d,key:R.key,wd:R.wd,R,by,short,hours:dh,cost:dc,costMissing:dMissing,sales:sv,need,have,count:R.list.length});
  }
  // 경고
  const W=[];
  const P=Object.values(per), nm=l=>l.slice(0,6).join(', ')+(l.length>6?` 외 ${l.length-6}명`:'');
  const o52=P.filter(p=>p.h>52); if(o52.length) W.push({lv:'bad',t:`주 52시간 넘는 사람 ${o52.length}명`,s:nm(o52.map(p=>`${p.name} ${fmtH(p.h)}h`))+' — 연장근로는 주 12시간까지예요'+(st.fivePlus?'':' (5인 미만 매장은 적용 안 됨)')});
  P.filter(p=>p.h>=13&&p.h<15).forEach(p=>W.push({lv:'warn',t:`${p.name} 주 ${fmtH(p.h)}시간 — 주휴수당 경계`,s:'주 15시간 이상이면 주휴수당이 생겨요. 의도한 시간인지 확인하세요'}));
  if(canPay){ const low=[]; P.forEach(p=>{ const d=p.days.filter(x=>x.rate!=null&&x.rate<MINWAGE); if(d.length) low.push(`${p.name} ${won(Math.min(...d.map(x=>x.rate)))}(${d.map(x=>md(x.key)).join(',')})`); });
    if(low.length) W.push({lv:'bad',t:`시간당 금액이 최저시급(${won(MINWAGE)})보다 낮은 사람 ${low.length}명`,s:low.join(' / ')}); }
  if(st.fivePlus){ const o8=P.filter(p=>p.days.some(x=>x.h>8)); if(o8.length){ const extra=P.reduce((a,p)=>a+p.days.reduce((b,x)=>b+Math.max(0,x.h-8),0),0);
    W.push({lv:'info',t:`하루 8시간 넘는 근무 ${o8.length}명 · 연장 합계 ${fmtH(extra)}시간 (가산 50%)`,s:nm(o8.map(p=>p.name))}); } }
  return {days,per,W,reqCells,filled,shortCells,hours,cost,costKnown,sales,fill:reqCells?filled/reqCells:1};
}
const fmtH=h=>(Math.round(h*10)/10).toLocaleString('ko-KR');
function ratioCls(r,t){ if(r==null) return ''; return r<=t?'ok':r<=t+5?'warn':'bad'; }
