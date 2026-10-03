/* ================= 오른쪽 서랍 ================= */
function openDrawer(title,sub,body,foot,wide){
  $('#dTitle').textContent=title; $('#dSub').innerHTML=sub||''; $('#dBody').innerHTML=body; $('#dFoot').innerHTML=foot||'';
  $('#drawer').classList.toggle('wide',!!wide); $('#drawer').classList.add('on'); $('#scrim').classList.add('on'); $('#drawer').setAttribute('aria-hidden','false');
  setTimeout(()=>{ const f=$('#dBody input:not([type=hidden]):not([type=checkbox]),#dBody select'); if(f&&window.innerWidth>860) f.focus(); ['c','p','s','a'].forEach(updHints); },60);
}
function closeDrawer(){ $('#drawer').classList.remove('on'); $('#scrim').classList.remove('on'); $('#drawer').setAttribute('aria-hidden','true'); }

/* ---------- 출근 시간 · 금액 입력 ---------- */
function timeW(p,cur,baseTxt){
  const k=cur?cur.k:(baseTxt!=null?'base':'full'); const st=APP.D.store;
  const opts=[...(baseTxt!=null?[['base','기본대로']]:[]),['full','종일'],['pm','오후'],['t','시간 지정']];
  return `<div class="sect"><div class="lb"><span>출근 시간</span>${baseTxt!=null?`<span class="bt">기본: ${esc(baseTxt)}</span>`:''}</div>
    <input type="hidden" id="${p}K" value="${k}">
    <div class="seg4">${opts.map(([v,t])=>`<button type="button" data-a="shk" data-p="${p}" data-v="${v}" aria-pressed="${v===k}">${t}</button>`).join('')}</div>
    <div class="row" id="${p}T" ${k==='t'?'':'hidden'}><input type="text" id="${p}S" class="grow" value="${k==='t'?esc(tLbl(cur.s)):''}" placeholder="출근 예: 11, 5시반" autocomplete="off"><span>~</span><input type="text" id="${p}E" class="grow" value="${k==='t'&&cur.e?esc(tLbl(cur.e)):''}" placeholder="퇴근 (비우면 ${tLbl(st.close)})" autocomplete="off"></div>
    <div class="qt" id="${p}Q" ${k==='t'?'':'hidden'}>${['10','11','12','3','4','5','6'].map(h=>`<button type="button" data-a="qt" data-p="${p}" data-v="${h}">${h}시</button>`).join('')}</div>
    <div class="hint" id="${p}H"></div></div>`;
}
function payW(p,cur,baseTxt,none){
  const k=cur?cur.k:'';
  return `<div class="sect"><div class="lb"><span>금액 ₩</span>${baseTxt?`<span class="bt">기본: ${esc(baseTxt)}</span>`:''}</div>
    <div class="row"><select id="${p}Pk" style="flex:0 0 auto"><option value="">${none||'기본대로'}</option><option value="day" ${k==='day'?'selected':''}>그날 금액</option><option value="hour" ${k==='hour'?'selected':''}>시급</option><option value="bonus" ${k==='bonus'?'selected':''}>추가금</option></select>
    <input type="text" id="${p}Pv" class="grow" inputmode="decimal" value="${cur?cur.v:''}" placeholder="예: 13 → 13만원"></div>
    <label class="ck"><input type="checkbox" id="${p}Pc" ${cur&&cur.cash?'checked':''}> 그날 현금으로 지급</label><div class="hint" id="${p}PH"></div></div>`;
}
function readTime(p){ const k=($('#'+p+'K')||{}).value; if(!k||k==='base') return {ok:true,sh:null}; if(k==='full'||k==='pm') return {ok:true,sh:{k}};
  const s=parseT($('#'+p+'S').value,false), er=$('#'+p+'E').value.trim(), e=er?parseT(er,true):'';
  if(!s) return {ok:false,msg:'출근 시간을 알아보지 못했어요 (예: 11, 5시반, 17:30)'}; if(er&&!e) return {ok:false,msg:'퇴근 시간을 알아보지 못했어요'};
  if(e&&tMin(e)<=tMin(s)) return {ok:false,msg:'퇴근이 출근보다 빨라요'};
  return {ok:true,sh:{k:'t',s,e:(e&&e!==APP.D.store.close)?e:''}}; }
function readPay(p){ const el=$('#'+p+'Pk'); if(!el) return {ok:true,skip:true}; if(!el.value) return {ok:true,pay:null};
  const v=parseWon($('#'+p+'Pv').value); if(!v||isNaN(v)) return {ok:false,msg:'금액을 알아보지 못했어요 (예: 13, 13만, 130000)'};
  const o={k:el.value,v}; if($('#'+p+'Pc').checked) o.cash=true; return {ok:true,pay:o}; }
function updHints(p){
  const h=$('#'+p+'H'); if(h){ const k=($('#'+p+'K')||{}).value; if(k==='t'){ const t=readTime(p); const sv=$('#'+p+'S').value.trim();
    h.classList.toggle('bad',!!sv&&!t.ok); h.textContent=!sv?'출근 시간을 넣어주세요':t.ok?`${t.sh.s} ~ ${t.sh.e||APP.D.store.close} · ${fmtH(hoursOf(APP.D.store,t.sh))}시간`:t.msg; } else h.textContent=''; }
  const ph=$('#'+p+'PH'); if(ph){ const k=$('#'+p+'Pk').value, raw=$('#'+p+'Pv').value; if(!k||!raw.trim()) ph.textContent='';
    else { const v=parseWon(raw); ph.classList.toggle('bad',!v||isNaN(v)); ph.textContent=v&&!isNaN(v)?`= ${v.toLocaleString('ko-KR')}원${k==='hour'?' (시급)':k==='bonus'?' 더 줌':' (그날 전체)'}`:'금액을 알아보지 못했어요'; } }
}
function setShk(p,v){ $('#'+p+'K').value=v; $$(`[data-a="shk"][data-p="${p}"]`).forEach(b=>b.setAttribute('aria-pressed',b.dataset.v===v));
  ['T','Q'].forEach(x=>{ const el=$('#'+p+x); if(el) el.hidden=v!=='t'; }); if(v==='t') setTimeout(()=>$('#'+p+'S').focus(),20); updHints(p); }
function putPay(key,pay){ if(!payAllowed()) return; put('pay',key,pay||null); }
function srcTxt(s){ return {pat:'요일 패턴',rule:'기간 설정',week:'주간 입력',day:'이 날만'}[s]||'기본'; }

/* ---------- 직원 하루 편집 ---------- */
function dStaffDay(sid,key){
  const D=APP.D, s=D.staff[sid]; if(!s) return; const cp=canPay(), st=D.store;
  const x=findItem(D,key,sid), b=findItem(D,key,sid,{noDc:sid}); const dc=D.dc[key+'|'+sid]||{};
  const status=x?(dc.st==='paidoff'?'paidoff':'work'):(dc.st==='annual'?'annual':'off');
  const bp=b?b.pos:s.pos; const k=x?costOf(D,x,key,pd(key).getDay()):null;
  const why=[]; if(x){ why.push(`출근 <b>${esc(shLbl(x.sh,st)||'종일')}</b> ← ${srcTxt(x.shSrc)}`); if(cp&&k) why.push(`금액 <b>${k.c!=null?won(k.c):'미정'}</b> · ${fmtH(k.h)}시간${k.ov?' ← '+srcTxt(k.src):k.base?' ← 기본 급여':''}`); }
  x&&x.ruleIds.forEach(id=>{ const r=D.rules[id]; if(r) why.push(`<button class="lnk" data-a="rule" data-id="${id}">${esc(rangeTxt(r))}${r.memo?' '+esc(r.memo):''} 기간 설정 보기</button>`); });
  const bTxt=b?(shLbl(b.sh,st)||'종일')+' · '+srcTxt(b.shSrc):'쉬는 날';
  openDrawer(s.name,`${mdw(key)} · ${esc(TYPES[s.type])} · 기본 ${esc(s.pos)}`,
    `${why.length?`<div class="why">${why.join('<br>')}</div>`:''}
    <div class="sect"><div class="lb"><span>이 날</span></div><input type="hidden" id="stK" value="${status}">
      <div class="seg4 st">${[['work','근무'],['off','휴무'],['annual','월차'],['paidoff','휴무지급']].map(([v,t])=>`<button type="button" data-a="stk" data-v="${v}" aria-pressed="${status===v}">${t}</button>`).join('')}</div></div>
    ${timeW('c',dc.sh||null,bTxt)}
    <div class="sect"><div class="lb"><span>포지션</span></div><select id="cPos"><option value="">기본대로 (${esc(bp)})</option>${D.positions.map(p=>`<option ${dc.pos===p.name?'selected':''}>${esc(p.name)}</option>`).join('')}</select></div>
    ${cp?payW('c',(D.pay||{})['dc:'+key+'|'+sid]||null,k&&(k.ov&&k.src!=='day'?payLbl(k.ov)+' · '+srcTxt(k.src):k.base?payLbl(k.base):'')||'미입력'):''}
    <div class="sect"><div class="lb"><span>메모</span></div><textarea id="cMemo" placeholder="예: 30분 늦게 옴, 대타(홍주)">${esc(dc.memo||'')}</textarea></div>
    <div class="row"><button class="btn sm" data-a="toRule" data-sid="${sid}" data-k="${key}">여러 날 한 번에 (기간 설정)</button><button class="btn sm" data-a="staff" data-sid="${sid}">요일 패턴·기본 급여</button></div>`,
    `<button class="btn pri grow" data-a="dcsave" data-sid="${sid}" data-k="${key}">이 날 저장</button>${Object.keys(dc).length||(D.pay||{})['dc:'+key+'|'+sid]?`<button class="btn" data-a="dcclear" data-sid="${sid}" data-k="${key}">원래대로</button>`:''}`);
}
function saveStaffDay(sid,key){
  const D=APP.D; const t=readTime('c'); if(!t.ok){ updHints('c'); return toast(t.msg); } const pr=readPay('c'); if(!pr.ok) return toast(pr.msg);
  const b=findItem(D,key,sid,{noDc:sid}); const want=$('#stK').value; const o={};
  if(want==='work'){ if(!b) o.st='extra'; } else if(want==='off'){ if(b) o.st='off'; } else o.st=want;
  if(t.sh&&!shSame(t.sh,b?b.sh:null)) o.sh=t.sh;
  const pos=$('#cPos').value; if(pos&&pos!==(b?b.pos:D.staff[sid].pos)) o.pos=pos;
  const memo=$('#cMemo').value.trim(); if(memo) o.memo=memo;
  put('dc',key+'|'+sid,Object.keys(o).length?o:null);
  if(!pr.skip) putPay('dc:'+key+'|'+sid,pr.pay);
  closeDrawer(); render(); toast('저장했어요');
}

/* ---------- 단기·당일 알바 편집 ---------- */
function dSpot(id){
  const D=APP.D, x=D.spot[id]; if(!x) return; const cp=canPay();
  openDrawer(x.name,`${mdw(x.date)} · 단기·당일`,
    `<div class="sect"><div class="lb"><span>이름</span></div><input type="text" id="spName" value="${esc(x.name)}"></div>
    <div class="sect"><div class="lb"><span>포지션</span></div><select id="spPos">${D.positions.map(p=>`<option ${x.pos===p.name?'selected':''}>${esc(p.name)}</option>`).join('')}</select></div>
    ${timeW('s',x.sh||null,null)}${cp?payW('s',(D.pay||{})['spot:'+id]||null,'','안 정함'):''}
    <div class="sect"><div class="lb"><span>메모</span></div><textarea id="spMemo" placeholder="연락처, 알바몬 등">${esc(x.memo||'')}</textarea></div>`,
    `<button class="btn pri grow" data-a="spotsave" data-id="${id}">저장</button><button class="btn bad" data-a="spotdel" data-id="${id}">이 날 빼기</button>`);
}

/* ---------- 사람 넣기 ---------- */
function dAdd(pos,key){
  const D=APP.D, R=resolve(D,pd(key)); const on=new Set(R.list.map(x=>x.sid).filter(Boolean)); const cand=staffList(D).filter(s=>!on.has(s.id)); const cp=canPay();
  openDrawer('사람 넣기',mdw(key),
    `<div class="sect"><div class="lb"><span>포지션</span></div><select id="aPos">${D.positions.map(p=>`<option ${p.name===pos?'selected':''}>${esc(p.name)}</option>`).join('')}</select></div>
    ${timeW('a',null,null)}${cp?payW('a',null,'','안 정함'):''}
    <div class="sect"><div class="lb"><span>쉬는 직원 불러오기</span><span class="bt">${cand.length}명</span></div>
      ${cand.length?`<div class="pick">${cand.map(s=>`<label><input type="checkbox" data-add="${s.id}"> ${esc(s.name)} <small class="muted">${esc(s.pos)}</small></label>`).join('')}</div>
      <button class="btn" data-a="addstaff" data-k="${key}">고른 직원 출근시키기</button>`:'<span class="muted" style="font-size:13px">모두 출근해요</span>'}</div>
    <div class="sect"><div class="lb"><span>새 단기·당일 알바</span></div>
      <div class="row"><input type="text" id="aName" class="grow" placeholder="이름 (예: 박알바)"><input type="text" id="aMemo" class="grow" placeholder="메모 (선택)"></div>
      <div class="row"><span class="muted" style="font-size:13px">마지막 날</span><input type="date" id="aTo" value="${key}" min="${key}"><span class="hint">며칠 연속이면 바꾸세요</span></div>
      <button class="btn pri" data-a="addspot" data-k="${key}">알바 넣기</button></div>`,'');
}

/* ---------- 매주 변동 입력 ---------- */
let WD=null;
function dWeekly(wk){
  const D=APP.D, ws=pd(wk); const list=staffList(D).filter(s=>s.type==='weekly');
  if(!WD||WD.wk!==wk){ WD={wk,mode:(WD&&WD.mode)||'st',map:{}}; list.forEach(s=>{ const en=(D.aw[wk]||{})[s.id]; WD.map[s.id]=en?JSON.parse(JSON.stringify({off:en.off||[],pm:en.pm||[],t:en.t||{},saved:true})):{off:[],pm:[],t:{},saved:false}; }); }
  const cell=(sid,i)=>{ const m=WD.map[sid]; const st=m.off.includes(i)?'off':m.pm.includes(i)?'pm':'on'; const tt=m.t[i];
    if(WD.mode==='time'){ if(st==='off') return '<span class="tag bad" style="width:100%;justify-content:center;padding:7px 0">휴무</span>';
      return `<input type="text" data-wt="${sid}" data-i="${i}" value="${tt?esc(tLbl(tt.s)):''}" placeholder="${st==='pm'?'오후':'기본'}" style="width:100%;text-align:center;padding:6px 2px">`; }
    const lbl=st==='off'?'휴무':tt?tLbl(tt.s):st==='pm'?'오후':'근무';
    return `<button class="btn sm" style="width:100%;${st==='off'?'background:var(--bad-soft);color:var(--bad);border-color:var(--bad)':st==='pm'||tt?'background:var(--tm);color:#fff;border-color:var(--tm)':''}" data-a="wcell" data-sid="${sid}" data-i="${i}">${esc(lbl)}</button>`; };
  openDrawer('매주 변동 입력',`${mdw(wk)} ~ ${mdw(ds(addDays(ws,6)))} · 매주 스케줄이 바뀌는 사람`,
    `<div class="row"><button class="btn sm" data-a="wnav" data-n="-7">‹ 지난주</button><button class="btn sm" data-a="wnav" data-n="7">다음 주 ›</button><span class="grow"></span>
      <div class="seg"><button data-a="wmode" data-v="st" aria-pressed="${WD.mode!=='time'}">근무·휴무·오후</button><button data-a="wmode" data-v="time" aria-pressed="${WD.mode==='time'}">출근 시간</button></div></div>
    <p class="hint" style="margin:0">${WD.mode==='time'?'칸에 출근 시간을 적으세요 (예: 11, 5, 5시반). 비우면 요일 패턴대로.':'칸을 누를 때마다 근무 → 휴무 → 오후로 바뀌어요.'}</p>
    ${list.length?`<div class="scroll"><table class="t"><thead><tr><th>이름</th>${WD_MON.map((w,i)=>`<th style="text-align:center">${DOW[w]}<br><span class="muted" style="font-weight:500">${addDays(ws,i).getDate()}</span></th>`).join('')}</tr></thead><tbody>
    ${list.map(s=>`<tr><td style="white-space:nowrap"><b>${esc(s.name)}</b>${WD.map[s.id].saved?'':'<br><span class="tag warn">미입력</span>'}</td>${[0,1,2,3,4,5,6].map(i=>`<td style="padding:4px 2px;min-width:52px">${cell(s.id,i)}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`
      :'<div class="empty">‘매주 변동’ 직원이 없어요. 직원 화면에서 종류를 바꾸세요.</div>'}`,
    `<button class="btn" data-a="wcopy">지난주와 같게</button><span class="grow"></span><button class="btn pri" data-a="wsave">이번 주 저장</button>`,true);
}

/* ---------- 직원 정보 ---------- */
function dStaff(sid){
  const D=APP.D, s=sid?D.staff[sid]:{name:'',pos:D.positions[0].name,type:'regular',off:[],wk:{}}; const cp=canPay(), ed=canEdit(); const b=sid?(D.pay||{})['staff:'+sid]:null;
  const pr=wd=>{ const off=(s.off||[]).includes(wd), c=(s.wk||{})[wd]; const v=off?'off':c&&c.sh?c.sh.k:'full'; const pay=cp&&sid?(D.pay||{})['pat:'+sid+':'+wd]:null;
    return `<div class="patrow"><b style="color:${wd===0?'var(--bad)':wd===6?'var(--pm)':'inherit'}">${DOW[wd]}</b>
      <select data-pat="${wd}">${[['full','종일'],['pm','오후'],['t','시간 지정'],['off','휴무']].map(([k,t])=>`<option value="${k}" ${v===k?'selected':''}>${t}</option>`).join('')}</select>
      <input type="text" data-patt="${wd}" value="${v==='t'?esc(tLbl(c.sh.s)+(c.sh.e?'~'+tLbl(c.sh.e):'')):''}" placeholder="${v==='t'?'예: 11 또는 11~9':''}" ${v==='t'?'':'hidden'}>
      ${cp&&sid?`<input type="text" data-patp="${wd}" value="${pay?pay.v:''}" placeholder="그날 금액 (선택)" inputmode="decimal" style="grid-column:2/-1;${pay?'':'display:none'}">`:''}</div>`; };
  openDrawer(sid?s.name:'직원 추가',sid?`${TYPES[s.type]} · ${esc(s.pos)}`:'',
    `<div class="row"><label class="f grow">이름<input type="text" id="sfName" value="${esc(s.name)}"></label><label class="f">연락처<input type="tel" id="sfTel" value="${esc(s.tel||'')}" style="width:140px"></label></div>
    <div class="row"><label class="f grow">종류<select id="sfType">${Object.entries(TYPES).map(([k,t])=>`<option value="${k}" ${s.type===k?'selected':''}>${t}</option>`).join('')}</select></label>
      <label class="f grow">기본 포지션<select id="sfPos">${D.positions.map(p=>`<option ${s.pos===p.name?'selected':''}>${esc(p.name)}</option>`).join('')}</select></label></div>
    <div class="row"><label class="f grow">마지막 근무일 <small class="muted">(그만두는 날 · 이 날까지만 근무로 나와요 · 비우면 계속)</small><input type="date" id="sfLast" value="${esc(s.last||'')}"></label></div>
    <p class="hint" style="margin:-6px 0 0">고정 근무: 쉬는 요일만 빼고 매주 자동 · 매주 변동: 주마다 입력 · 단기·당일: 넣은 날만</p>
    <div class="sect"><div class="lb"><span>요일 패턴 (매주 기본)</span>${cp&&sid?'<button class="lnk" data-a="patpay">요일별 금액도 정하기</button>':''}</div>${WD_MON.map(pr).join('')}
      <span class="hint">‘매주 변동’·‘단기’는 휴무 칸이 무시되고, 출근할 때의 기본 시간으로만 쓰여요.</span></div>
    ${cp?`<div class="sect"><div class="lb"><span>기본 급여 ₩</span><span class="bt">급여 보기 권한자만</span></div>
      <div class="row"><select id="sfPk"><option value="">미입력</option><option value="hour" ${b&&b.k==='hour'?'selected':''}>시급</option><option value="day" ${b&&b.k==='day'?'selected':''}>일급(종일 기준)</option><option value="month" ${b&&b.k==='month'?'selected':''}>월급</option></select>
      <input type="text" id="sfPv" class="grow" value="${b?b.v:''}" placeholder="예: 1.1 → 11,000 / 13 → 13만" inputmode="decimal"></div></div>`:''}`,
    ed?`<button class="btn pri grow" data-a="staffsave" data-sid="${sid||''}">${sid?'저장':'추가'}</button>${sid?`<button class="btn" data-a="staffact" data-sid="${sid}">${s.active===false?'다시 근무':'그만둠'}</button><button class="btn bad" data-a="staffdel" data-sid="${sid}">삭제</button>`:''}`:'');
}
function saveStaff(sid){
  const D=APP.D; const name=$('#sfName').value.trim(); if(!name) return toast('이름을 넣어주세요');
  const id=sid||uid(); const s=Object.assign({},D.staff[id]||{id,active:true,order:Object.keys(D.staff).length});
  s.name=name; s.tel=$('#sfTel').value.trim(); { const lv=($('#sfLast').value||'').trim(); if(lv) s.last=lv; else delete s.last; } s.type=$('#sfType').value; s.pos=$('#sfPos').value; s.off=[]; s.wk={};
  for(const sel of $$('[data-pat]')){ const wd=+sel.dataset.pat, v=sel.value;
    if(v==='off') s.off.push(wd); else if(v==='pm') s.wk[wd]={sh:{k:'pm'}};
    else if(v==='t'){ const raw=$(`[data-patt="${wd}"]`).value.trim(); const [a,b]=raw.split(/[~\-]/); const st=parseT(a,false), en=b?parseT(b,true):'';
      if(!st||(b&&!en)) return toast(`${DOW[wd]}요일 시간을 알아보지 못했어요 (예: 11 또는 11~9)`); s.wk[wd]={sh:{k:'t',s:st,e:en&&en!==D.store.close?en:''}}; } }
  s.off.sort(); if(!Object.keys(s.wk).length) delete s.wk;
  put('staff',id,s);
  if($('#sfPk')){ const k=$('#sfPk').value, v=parseWon($('#sfPv').value); if(k&&(!v||isNaN(v))) return toast('기본 급여를 알아보지 못했어요'); putPay('staff:'+id,k?{k,v}:null);
    $$('[data-patp]').forEach(i=>{ const wd=i.dataset.patp, v2=parseWon(i.value); putPay('pat:'+id+':'+wd,v2&&!isNaN(v2)?{k:'day',v:v2}:null); }); }
  closeDrawer(); render(); toast(sid?'저장했어요':`${name} 님을 추가했어요`);
}

/* ---------- 기간 설정 ---------- */
function dRule(id,preset){
  const D=APP.D, r=id?D.rules[id]:Object.assign({ids:[],from:todayStr,to:todayStr,days:[]},preset||{}); const cp=canPay(); const pay=id?(D.pay||{})['rule:'+id]:null; const sel=new Set(r.ids);
  const pick=D.positions.map(p=>{ const l=staffList(D).filter(s=>s.pos===p.name); if(!l.length) return ''; return `<div class="pg" style="--pc:${p.color}">${esc(p.name)}</div>`+l.map(s=>`<label data-rn="${esc(s.name)}"><input type="checkbox" data-rid="${s.id}" ${sel.has(s.id)?'checked':''}>${esc(s.name)}</label>`).join(''); }).join('');
  openDrawer(id?'기간 설정 고치기':'기간 설정','여러 사람·여러 날을 한 번에',
    `<div class="sect"><div class="lb"><span>누구</span><span class="bt" id="rCnt">${r.ids.length}명</span></div><div class="row"><input type="text" id="rQ" placeholder="이름 찾기" class="grow"><button class="btn sm" data-a="rsel" data-v="1">보이는 사람 모두</button><button class="btn sm" data-a="rsel" data-v="0">해제</button></div><div class="pick" id="rPick">${pick}</div></div>
    <div class="sect"><div class="lb"><span>기간</span></div><div class="row"><input type="date" id="rFrom" value="${r.from}" class="grow"><span>~</span><input type="date" id="rTo" value="${r.to||r.from}" class="grow"></div>
      <div class="row"><span class="days7">${WD_MON.map(w=>`<button type="button" data-a="rday" data-v="${w}" aria-pressed="${(r.days||[]).includes(w)}">${DOW[w]}</button>`).join('')}</span><button class="btn sm" data-a="rdp" data-v="all">매일</button><button class="btn sm" data-a="rdp" data-v="wd">평일</button><button class="btn sm" data-a="rdp" data-v="we">주말</button></div></div>
    <div class="sect"><div class="lb"><span>근무</span></div><select id="rW"><option value="">그대로</option><option value="off" ${r.w==='off'?'selected':''}>쉬게 하기 (휴가·휴무)</option><option value="on" ${r.w==='on'?'selected':''}>출근하게 하기</option></select></div>
    ${timeW('r',r.sh||null,'그대로')}
    <div class="sect"><div class="lb"><span>포지션</span></div><select id="rPos"><option value="">그대로</option>${D.positions.map(p=>`<option ${r.pos===p.name?'selected':''}>${esc(p.name)}</option>`).join('')}</select></div>
    ${cp?payW('r',pay,'','그대로'):''}
    <div class="sect"><div class="lb"><span>메모</span></div><input type="text" id="rMemo" value="${esc(r.memo||'')}" placeholder="예: 휴가, 추석, 단기 알바 (8자 이하면 휴무 이유로 보여요)"></div>
    <div class="prev" id="rPrev"></div>`,
    `<button class="btn pri grow" data-a="rulesave" data-id="${id||''}">${id?'저장':'추가'}</button>${id?`<button class="btn bad" data-a="ruledel" data-id="${id}">삭제</button>`:''}`);
  setTimeout(rulePrev,70);
}
function ruleRead(){ const ids=$$('[data-rid]').filter(x=>x.checked).map(x=>x.dataset.rid); const days=$$('[data-a="rday"][aria-pressed="true"]').map(b=>+b.dataset.v);
  return {ids,from:$('#rFrom').value,to:$('#rTo').value,days,w:$('#rW').value,pos:$('#rPos').value,memo:$('#rMemo').value.trim(),t:readTime('r'),p:readPay('r')}; }
function ruleDates(f,t,days){ const o=[]; if(!f||!t||t<f) return o; let d=pd(f); const e=pd(t); for(let i=0;i<400&&d<=e;i++){ if(!days.length||days.includes(d.getDay())) o.push(ds(d)); d=addDays(d,1); } return o; }
function rulePrev(){ const el=$('#rPrev'); if(!el) return; const r=ruleRead(); $('#rCnt').textContent=r.ids.length+'명'; updHints('r');
  const dates=ruleDates(r.from,r.to,r.days); const eff=[]; if(r.w) eff.push(r.w==='off'?'쉬게 하기':'출근'); if(r.t.ok&&r.t.sh) eff.push((shLbl(r.t.sh,APP.D.store)||'종일')+' 출근'); if(r.pos) eff.push(r.pos); if(r.p.ok&&r.p.pay) eff.push(payLbl(r.p.pay));
  if(!r.ids.length&&!eff.length){ el.innerHTML='<span class="muted">사람·기간·바꿀 것을 고르면 적용되는 날짜가 보여요</span>'; return; }
  const bad=[]; if(!r.ids.length) bad.push('사람을 고르세요'); if(!dates.length) bad.push('기간·요일을 확인하세요'); if(!eff.length) bad.push('바꿀 것을 하나 이상 고르세요'); if(!r.t.ok) bad.push(r.t.msg); if(!r.p.ok) bad.push(r.p.msg);
  el.innerHTML=bad.length?`<span style="color:var(--bad);font-weight:600">${bad.map(esc).join(' · ')}</span>`:`<b>${r.ids.length}명 × ${dates.length}일</b> → ${esc(eff.join(' · '))}<br><span class="muted">${dates.slice(0,10).map(mdw).join(', ')}${dates.length>10?` 외 ${dates.length-10}일`:''}</span>`; }
function saveRule(id){
  const r=ruleRead(); if(!r.t.ok) return toast(r.t.msg); if(!r.p.ok) return toast(r.p.msg);
  if(!r.ids.length) return toast('누구에게 적용할지 고르세요'); if(!ruleDates(r.from,r.to,r.days).length) return toast('기간·요일을 확인하세요');
  const pay=r.p.skip?(id?(APP.D.pay||{})['rule:'+id]:null):r.p.pay;
  if(!r.w&&!r.t.sh&&!r.pos&&!pay) return toast('바꿀 것을 하나 이상 고르세요');
  const rid=id||uid(); const o={id:rid,ids:r.ids,from:r.from,to:r.to,days:r.days.sort(),at:Date.now()}; if(r.w) o.w=r.w; if(r.t.sh) o.sh=r.t.sh; if(r.pos) o.pos=r.pos; if(r.memo) o.memo=r.memo;
  put('rule',rid,o); if(!r.p.skip) putPay('rule:'+rid,pay);
  const cf=Object.keys(APP.D.dc).filter(k=>{ const [d,s]=k.split('|'); return o.ids.includes(s)&&d>=o.from&&d<=o.to&&(!o.days.length||o.days.includes(pd(d).getDay()))&&((o.sh&&APP.D.dc[k].sh)||(o.pos&&APP.D.dc[k].pos)); });
  closeDrawer(); render(); toast(cf.length?`저장했어요 · 이 날만 따로 정한 ${cf.length}일은 그대로 우선해요`:'기간 설정을 저장했어요');
}

/* ---------- 포지션 관리 (추가·이름/색 바꾸기·순서·삭제) ---------- */
function posUsers(name){ const D=APP.D; return Object.values(D.staff).filter(s=>s.pos===name&&s.active!==false); }
function renamePos(oldN,newN){ const D=APP.D;
  Object.values(D.staff).forEach(s=>{ if(s.pos===oldN) put('staff',s.id,{...s,pos:newN}); });
  Object.values(D.spot).forEach(x=>{ if(x.pos===oldN) put('spot',x.id,{...x,pos:newN}); });
  Object.values(D.rules).forEach(r=>{ if(r.pos===oldN) put('rule',r.id,{...r,pos:newN}); });
  Object.keys(D.dc).forEach(k=>{ const v=D.dc[k]; if(v.pos===oldN) put('dc',k,{...v,pos:newN}); }); }
function dPositions(delIdx){
  const D=APP.D; const del=(delIdx==null||delIdx==='')?null:+delIdx;
  const rows=D.positions.map((p,i)=>{ const n=posUsers(p.name).length;
    return `<div class="ri" style="grid-template-columns:auto minmax(0,1fr) auto;align-items:center;padding:8px 10px;${del===i?'border-color:var(--bad)':''}">
      <input type="color" value="${p.color}" data-a="pmf" data-i="${i}" data-f="color" style="width:34px;height:32px;padding:0;border:0;background:none" aria-label="색">
      <input type="text" value="${esc(p.name)}" data-a="pmf" data-i="${i}" data-f="name" aria-label="포지션 이름">
      <div class="row" style="flex-wrap:nowrap;gap:4px"><span class="muted" style="font-size:12px;white-space:nowrap">${n}명</span>
        <button class="btn sm" data-a="pmmv" data-i="${i}" data-n="-1" aria-label="위로" ${i===0?'disabled':''}>↑</button><button class="btn sm" data-a="pmmv" data-i="${i}" data-n="1" aria-label="아래로" ${i===D.positions.length-1?'disabled':''}>↓</button>
        <button class="btn sm bad" data-a="pmdel" data-i="${i}">삭제</button></div></div>`; }).join('');
  let panel='';
  if(del!=null&&D.positions[del]){ const p=D.positions[del], users=posUsers(p.name), others=D.positions.filter((_,i)=>i!==del);
    panel=`<div class="why" style="border:1px solid var(--bad)"><b>‘${esc(p.name)}’ 포지션을 삭제할까요?</b><br>${users.length?`여기 있는 ${users.length}명(${esc(users.slice(0,6).map(s=>s.name).join(', '))}${users.length>6?' 외':''})은 다른 포지션으로 옮겨요.`:'이 포지션에는 기본으로 배정된 사람이 없어요.'}
      <div class="row" style="margin-top:8px;flex-wrap:nowrap">${users.length?`<select id="pmTo" class="grow">${others.map(o=>`<option>${esc(o.name)}</option>`).join('')}</select>`:''}<button class="btn bad" data-a="pmdel2" data-i="${del}">${users.length?'옮기고 삭제':'삭제'}</button><button class="btn" data-a="pmmgr">취소</button></div></div>`; }
  const keep=$('#dBody')?$('#dBody').scrollTop:0;
  openDrawer('포지션 관리','스케줄 화면에 나오는 줄이에요 · 이름·색은 바로 저장돼요',
    `${D.positions.length<=1?'':''}${panel}<div class="rl">${rows}</div>
     <div class="sect"><div class="lb"><span>새 포지션 추가</span></div><div class="row" style="flex-wrap:nowrap"><input type="color" id="npC" value="#6B7A8F" style="width:34px;height:34px;padding:0;border:0;background:none" aria-label="색"><input type="text" id="npN" class="grow" placeholder="예: 세척, 서빙, 포장" autocomplete="off"><button class="btn pri" data-a="pmadd">추가</button></div></div>
     <p class="hint" style="margin:0">아무도 없는 포지션은 카드에서 숨겨져 있다가, 이름을 끌어 놓거나 ‘빈 포지션 보기’를 켜면 보여요.</p>`,'');
  setTimeout(()=>{ const b=$('#dBody'); if(b) b.scrollTop=keep; },70);
}
function addPos(){ const name=($('#npN').value||'').trim(), color=$('#npC').value||'#6B7A8F'; if(!name) return toast('포지션 이름을 넣어주세요');
  const D=APP.D; if(D.positions.some(p=>p.name===name)) return toast('이미 있는 이름이에요');
  put('cfg','positions',[...D.positions.map(p=>({...p})),{name,color,req:[0,0,0,0,0,0,0]}]); APP.showEmpty=true; render(); dPositions(); toast(`‘${name}’ 포지션을 추가했어요`); }
function delPos(i){ const D=APP.D; const p=D.positions[i]; if(!p) return; if(D.positions.length<=1) return toast('포지션은 하나 이상 있어야 해요');
  const users=posUsers(p.name); const sel=$('#pmTo'); const to=sel?sel.value:(D.positions.find((_,j)=>j!==i)||{}).name;
  Object.values(D.staff).forEach(s=>{ if(s.pos===p.name) put('staff',s.id,{...s,pos:to}); });
  Object.values(D.spot).forEach(x=>{ if(x.pos===p.name) put('spot',x.id,{...x,pos:to}); });
  Object.values(D.rules).forEach(r=>{ if(r.pos===p.name) put('rule',r.id,{...r,pos:to}); });
  Object.keys(D.dc).forEach(k=>{ const v=D.dc[k]; if(v.pos===p.name) put('dc',k,{...v,pos:to}); });
  put('cfg','positions',D.positions.filter((_,j)=>j!==i).map(x=>({...x}))); render(); dPositions();
  toast(`‘${p.name}’ 포지션을 삭제했어요${users.length?` · ${users.length}명은 ‘${to}’로 옮겼어요`:''}`); }

/* ---------- 매출 ---------- */
function dSales(key){ const v=(APP.D.sales[key]||{}).v||'';
  openDrawer('매출',mdw(key)+' · 인건비율 계산용',`<label class="f">예상 또는 실제 매출<input type="text" id="slV" value="${v}" inputmode="decimal" placeholder="예: 320 → 320만원"></label><p class="hint">숫자 1~999는 만원 단위로 알아들어요.</p>`,
    `<button class="btn pri grow" data-a="salessave" data-k="${key}">저장</button>`); setTimeout(()=>$('#slV').focus(),80); }

/* ---------- 매장 바꾸기 / 추가 ---------- */
function dStores(){ const mine=APP.stores.filter(s=>s.role);
  openDrawer('매장 바꾸기','',`<div class="rl">${mine.map(s=>`<button class="ri" style="text-align:left;${s.id===APP.sid?'border-color:var(--amber)':''}" data-a="gostore" data-id="${s.id}"><div><div class="wn">${esc(s.name)}</div><div class="wh">${roleName(s.role)}</div></div><span>${s.id===APP.sid?'✓':'›'}</span></button>`).join('')}</div>`,''); }
function dStoreNew(){ openDrawer('매장 추가','본사만 할 수 있어요',`<label class="f">매장 이름<input type="text" id="snName" placeholder="예: 수성점"></label>
  <p class="hint">매장을 만든 뒤 설정 → 계정 만들기에서 이 매장의 점주 계정을 만드세요.</p>`,`<button class="btn pri grow" data-a="storecreate">만들기</button>`); }

/* ================= 기존 근무표 가져오기 ================= */
const OLD_URL='https://fmzpmekypmjuydgxpnlu.supabase.co', OLD_KEY='/*OLDKEY*/';
function importOld(o){
  if(!o||!Array.isArray(o.staff)) throw new Error('근무표 데이터가 아니에요');
  const D=APP.D; let n=0;
  if(o.targets){ const pos=D.positions.map(p=>({...p})); Object.keys(o.targets).forEach(name=>{ const t=o.targets[name]; let p=pos.find(x=>x.name===name); if(!p){ p={name,color:'#777',req:[0,0,0,0,0,0,0]}; pos.push(p); } p.req=[+t.we||0,+t.wd||0,+t.wd||0,+t.wd||0,+t.wd||0,+t.wd||0,+t.we||0]; }); put('cfg','positions',pos); }
  o.staff.forEach((s,i)=>{ const x={id:s.id,name:s.name,pos:s.pos,type:s.kind==='fixed'?'weekly':'regular',off:s.off||[],active:true,order:i}; if(s.wk){ x.wk={}; Object.keys(s.wk).forEach(w=>{ if(s.wk[w].sh) x.wk[w]={sh:s.wk[w].sh}; if(s.wk[w].pay) putPay('pat:'+s.id+':'+w,s.wk[w].pay); }); }
    put('staff',s.id,x); n++; });
  (o.rules||[]).forEach(r=>{ const {pay,...rest}=r; put('rule',r.id,rest); if(pay) putPay('rule:'+r.id,pay); });
  const dcs={}; const dget=k=>dcs[k]=dcs[k]||{};
  Object.keys(o.dc||{}).forEach(k=>{ const v=o.dc[k]; if(v.sh) dget(k).sh=v.sh; if(v.pay) putPay('dc:'+k,v.pay); });
  Object.keys(o.notes||{}).forEach(k=>{ if(o.notes[k]) dget(k).memo=o.notes[k]; });
  (o.ex||[]).forEach(e=>{ const k=e.date+'|'+e.staffId;
    if(e.type==='당일알바'){ const x={id:e.id,date:e.date,name:e.name,pos:e.pos,memo:e.memo||''}; const sh=e.sh||(e.pm?{k:'pm'}:null); if(sh) x.sh=sh; put('spot',e.id,x); if(e.pay) putPay('spot:'+e.id,e.pay); return; }
    const d=dget(k); if(e.type==='월차') d.st='annual'; else if(e.type==='휴무') d.st='off'; else if(e.type==='휴무지급') d.st='paidoff'; else if(e.type==='추가근무'){ d.st='extra'; if(e.pos) d.pos=e.pos; }
    else if(e.type==='근무변경'){ if(e.pos) d.pos=e.pos; } else if(e.type==='오후출근'){ if(!d.sh) d.sh={k:'pm'}; } if(e.memo&&!d.memo) d.memo=e.memo; });
  Object.keys(dcs).forEach(k=>put('dc',k,dcs[k]));
  Object.keys(o.aw||{}).forEach(w=>put('aw',w,o.aw[w]));
  return n;
}

/* ================= 이벤트 ================= */
document.addEventListener('click',async e=>{
  if(Date.now()-DRSUP<450){ DRSUP=0; e.preventDefault(); return; }
  if(e.target.id==='scrim') return closeDrawer();
  const b=e.target.closest('[data-a]'); if(!b) return; const d=b.dataset; const D=APP.D;
  switch(d.a){
    case 'view': APP.view=d.v; closeDrawer(); render(); window.scrollTo(0,0); break;
    case 'wk': APP.anchor=d.n==='0'?new Date():addDays(weekStart(APP.anchor),7*+d.n); render(); break;
    case 'cnav': { const a=APP.anchor; if(d.n==='0') APP.anchor=new Date(); else if((APP.cardMode||'month')==='month') APP.anchor=new Date(a.getFullYear(),a.getMonth()+(+d.n),1); else APP.anchor=addDays(a,7*(+d.n)); render(); break; }
    case 'cmode': APP.cardMode=d.v; APP.anchor=new Date(); render(); break;
    case 'mon': { const a=APP.anchor; APP.anchor=d.n==='0'?new Date():new Date(a.getFullYear(),a.getMonth()+(+d.n),1); render(); break; }
    case 'dayn': APP.day=d.n==='0'?todayStr:ds(addDays(pd(APP.day),+d.n)); render(); break;
    case 'gday': APP.day=d.k; APP.view='day'; render(); break;
    case 'gweek': APP.anchor=pd(d.k); APP.view='week'; render(); break;
    case 'jump': $('#'+d.to)?.scrollIntoView({behavior:'smooth'}); break;
    case 'paytog': sessionStorage.setItem('fr-pay',canPay()?'0':'1'); render(); break;
    case 'print': window.print(); break;
    case 'edit': if(!canEdit()){ if(d.sid&&role()==='staff') return; toast('보기 전용이에요'); return; }
      if(d.spot) dSpot(d.spot); else if(d.sid) dStaffDay(d.sid,d.k); break;
    case 'add': dAdd(d.pos,d.k); break;
    case 'shk': setShk(d.p,d.v); break;
    case 'qt': $('#'+d.p+'S').value=d.v+'시'; updHints(d.p); break;
    case 'stk': $('#stK').value=d.v; $$('[data-a="stk"]').forEach(x=>x.setAttribute('aria-pressed',x.dataset.v===d.v)); break;
    case 'dcsave': saveStaffDay(d.sid,d.k); break;
    case 'dcclear': put('dc',d.k+'|'+d.sid,null); if((D.pay||{})['dc:'+d.k+'|'+d.sid]) putPay('dc:'+d.k+'|'+d.sid,null); closeDrawer(); render(); toast('원래대로 되돌렸어요'); break;
    case 'spotsave': { const x={...D.spot[d.id]}; x.name=$('#spName').value.trim()||x.name; x.pos=$('#spPos').value; x.memo=$('#spMemo').value.trim();
      const t=readTime('s'); if(!t.ok) return toast(t.msg); const pr=readPay('s'); if(!pr.ok) return toast(pr.msg);
      if(t.sh&&t.sh.k!=='full') x.sh=t.sh; else delete x.sh; put('spot',d.id,x); if(!pr.skip) putPay('spot:'+d.id,pr.pay); closeDrawer(); render(); toast('저장했어요'); break; }
    case 'spotdel': put('spot',d.id,null); if((D.pay||{})['spot:'+d.id]) putPay('spot:'+d.id,null); closeDrawer(); render(); toast('뺐어요'); break;
    case 'addstaff': { const ids=$$('[data-add]').filter(x=>x.checked).map(x=>x.dataset.add); if(!ids.length) return toast('출근시킬 직원을 고르세요');
      const t=readTime('a'); if(!t.ok) return toast(t.msg); const pr=readPay('a'); if(!pr.ok) return toast(pr.msg); const pos=$('#aPos').value;
      ids.forEach(sid=>{ const k=d.k+'|'+sid; const o=Object.assign({},D.dc[k]||{}); o.st='extra'; if(pos!==D.staff[sid].pos) o.pos=pos; else delete o.pos; if(t.sh&&t.sh.k!=='full') o.sh=t.sh; put('dc',k,o); if(!pr.skip&&pr.pay) putPay('dc:'+k,pr.pay); });
      closeDrawer(); render(); toast(`${ids.length}명 출근시켰어요`); break; }
    case 'addspot': { const name=$('#aName').value.trim(); if(!name){ $('#aName').focus(); return toast('알바 이름을 넣으세요'); }
      const t=readTime('a'); if(!t.ok) return toast(t.msg); const pr=readPay('a'); if(!pr.ok) return toast(pr.msg);
      const to=$('#aTo').value||d.k; const dates=ruleDates(d.k,to<d.k?d.k:to,[]).slice(0,62);
      dates.forEach(dt=>{ const id=uid(); const x={id,date:dt,name,pos:$('#aPos').value,memo:$('#aMemo').value.trim()}; if(t.sh&&t.sh.k!=='full') x.sh=t.sh; put('spot',id,x); if(!pr.skip&&pr.pay) putPay('spot:'+id,pr.pay); });
      closeDrawer(); render(); toast(dates.length>1?`${name} ${dates.length}일 넣었어요`:`${name} 넣었어요`); break; }
    case 'weekly': dWeekly(d.k2||weekKey(pd(d.k))); break;
    case 'wcell': { const m=WD.map[d.sid], i=+d.i; if(m.off.includes(i)){ m.off=m.off.filter(x=>x!==i); m.pm.push(i); } else if(m.pm.includes(i)){ m.pm=m.pm.filter(x=>x!==i); } else { m.off.push(i); delete m.t[i]; } dWeekly(WD.wk); break; }
    case 'wmode': WD.mode=d.v; dWeekly(WD.wk); break;
    case 'wnav': dWeekly(ds(addDays(pd(WD.wk),+d.n))); break;
    case 'wcopy': { const prev=D.aw[ds(addDays(pd(WD.wk),-7))]; if(!prev) return toast('지난주 입력이 없어요'); Object.keys(WD.map).forEach(sid=>{ if(prev[sid]) Object.assign(WD.map[sid],JSON.parse(JSON.stringify({off:prev[sid].off||[],pm:prev[sid].pm||[],t:prev[sid].t||{}}))); }); dWeekly(WD.wk); toast('지난주를 불러왔어요 · 저장해야 반영돼요'); break; }
    case 'wsave': { const out=Object.assign({},D.aw[WD.wk]||{}); Object.keys(WD.map).forEach(sid=>{ const m=WD.map[sid]; out[sid]={off:[...m.off].sort(),pm:[...m.pm].sort()}; if(Object.keys(m.t).length) out[sid].t=m.t; m.saved=true; });
      put('aw',WD.wk,out); dWeekly(WD.wk); render(); toast('이번 주 입력을 저장했어요'); break; }
    case 'staff': dStaff(d.sid); break;
    case 'staffnew': dStaff(null); break;
    case 'staffsave': saveStaff(d.sid||null); break;
    case 'staffact': { const s={...D.staff[d.sid]}; s.active=s.active===false; put('staff',d.sid,s); closeDrawer(); render(); toast(s.active?'다시 근무로 바꿨어요':'그만둠으로 바꿨어요 (기록은 남아요)'); break; }
    case 'staffdel': if(!confirm('이 직원을 지울까요? 기록을 남기려면 ‘그만둠’을 쓰세요.')) return; put('staff',d.sid,null); putPay('staff:'+d.sid,null); closeDrawer(); render(); toast('지웠어요'); break;
    case 'patpay': $$('[data-patp]').forEach(i=>i.style.display=''); b.remove(); break;
    case 'rule': dRule(d.id||null); break;
    case 'rulecopy': { const r=D.rules[d.id]; if(r) dRule(null,{...r,id:undefined}); break; }
    case 'toRule': dRule(null,{ids:[d.sid],from:d.k,to:d.k}); break;
    case 'rsel': $$('#rPick label').forEach(l=>{ if(d.v==='0'||!l.hidden) l.querySelector('input').checked=d.v==='1'; }); rulePrev(); break;
    case 'rday': b.setAttribute('aria-pressed',b.getAttribute('aria-pressed')!=='true'); rulePrev(); break;
    case 'rdp': { const set=d.v==='wd'?[1,2,3,4,5]:d.v==='we'?[0,6]:[]; $$('[data-a="rday"]').forEach(x=>x.setAttribute('aria-pressed',set.includes(+x.dataset.v))); rulePrev(); break; }
    case 'rulesave': saveRule(d.id||null); break;
    case 'ruledel': if(!confirm('이 기간 설정을 지울까요?')) return; put('rule',d.id,null); if((D.pay||{})['rule:'+d.id]) putPay('rule:'+d.id,null); closeDrawer(); render(); toast('지웠어요'); break;
    case 'sales': if(canEdit()) dSales(d.k); break;
    case 'salessave': { const raw=$('#slV').value.trim(); let v=raw?parseWon(raw):null; if(raw&&(!v||isNaN(v))) return toast('숫자를 확인하세요');
      put('sales',d.k,v?{v}:null); closeDrawer(); render(); break; }
    case 'stores': dStores(); break;
    case 'gostore': closeDrawer(); await openStore(d.id); if(APP.view==='hq') APP.view='cards'; renderShell(); render(); break;
    case 'storenew': dStoreNew(); break;
    case 'storecreate': { const name=$('#snName').value.trim(); if(!name) return toast('매장 이름을 넣으세요'); const id=(name.toLowerCase().replace(/[^a-z0-9]/g,'')||'s')+Date.now().toString(36);
      try{ await APP.be.createStore(id,name); APP.stores=await APP.be.stores(); APP.sum=null; notifyStores(); closeDrawer(); renderShell(); render(); toast(`${name}을(를) 만들었어요`); }catch(err){ toast(err.message); } break; }
    case 'sumreload': APP.sum=null; render(); break;
    case 'pf': APP.pf=d.v; render(); break;
    case 'empty': APP.showEmpty=!APP.showEmpty; render(); break;
    case 'mepick': break;
    case 'img': makeImage(d.t,d.k); break;
    case 'imgshare': case 'imgcopy': case 'imgsave': imgAct(d.a.slice(3)); break;
    case 'posmgr': case 'pmmgr': dPositions(); break;
    case 'pmadd': addPos(); break;
    case 'pmdel': { const p=D.positions[+d.i]; if(!p) break; if(D.positions.length<=1) return toast('포지션은 하나 이상 있어야 해요'); dPositions(d.i); break; }
    case 'pmdel2': delPos(+d.i); break;
    case 'pmmv': { const pos=D.positions.map(p=>({...p})); const i=+d.i, j=i+(+d.n); if(j<0||j>=pos.length) break; [pos[i],pos[j]]=[pos[j],pos[i]]; put('cfg','positions',pos); render(); dPositions(); break; }
    case 'posadd': { const pos=D.positions.map(p=>({...p})); pos.push({name:'새 포지션',color:'#777777',req:[0,0,0,0,0,0,0]}); put('cfg','positions',pos); render(); break; }
    case 'posdel': { if(!confirm('이 포지션을 지울까요? 여기 있던 사람은 첫 포지션으로 보여요.')) return; const pos=D.positions.filter((_,i)=>i!==+d.i); if(!pos.length) return toast('포지션은 하나 이상 있어야 해요'); put('cfg','positions',pos); render(); break; }
    case 'posmv': { const pos=D.positions.map(p=>({...p})); const i=+d.i, j=i+(+d.n); if(j<0||j>=pos.length) return; [pos[i],pos[j]]=[pos[j],pos[i]]; put('cfg','positions',pos); render(); break; }
    case 'postpl': if(confirm('포지션과 필요 인원을 본사 표준으로 바꿀까요?')){ put('cfg','positions',defPositions()); render(); } break;
    case 'connect': { const url=$('#cfUrl').value.trim(), key=$('#cfKey').value.trim(); if(!/^https:\/\/.+supabase\.co\/?$/.test(url)||!key.startsWith('eyJ')) return toast('Supabase 주소와 anon 키를 확인하세요');
      Conf.url=url; Conf.key=key; Conf.mode='remote'; Conf.ses=null; saveConf(); location.reload(); break; }
    case 'disconnect': Conf.mode='local'; saveConf(); location.reload(); break;
    case 'retry': location.reload(); break;
    case 'logout': Remote.forget(); Conf.openOnly=false; saveConf(); location.reload(); break;
    case 'openmode': Conf.openOnly=true; Conf.mode='remote'; saveConf(); location.reload(); break;
    case 'gologin': Conf.openOnly=false; saveConf(); location.reload(); break;
    case 'demorole': Local.db.demoRole=d.v; if(d.v==='staff'){ Local.db.demoMe={bonjum:Object.keys(Local.db.items.bonjum.staff)[0]}; } Local.persist(); location.reload(); break;
    case 'resetdemo': if(confirm('체험 데이터를 처음 상태로 되돌릴까요?')){ localStorage.removeItem(LOCAL_KEY); location.reload(); } break;
    case 'storeactive': { const on=d.on==='1', nm=isClosedName(d.name)?d.name.slice(0,-CLOSED_MARK.length):d.name;
      if(!confirm(on?`‘${nm}’ 을(를) 다시 사용할까요?\n이 매장 계정들이 다시 로그인할 수 있어요.`:`‘${nm}’ 을(를) 사용 중지할까요?\n\n· 이 매장에만 연결된 점주·직원 계정은 로그인이 막혀요\n· 자료는 그대로 남아요 (언제든 다시 사용 가능)\n· 매장 이름 뒤에 (사용 중지) 가 붙어요`)) return;
      try{ const r=await APP.be.manageStores({action:'setactive',store:d.id,on}); APP.stores=await APP.be.stores(); APP.st=APP.stores.find(x=>x.id===APP.sid)||APP.st; APP.sum=null; notifyStores(); renderShell(); render();
        toast(on?`‘${nm}’ 을(를) 다시 사용해요 (계정 ${r.accounts}개 풀림)`:`‘${nm}’ 을(를) 사용 중지했어요 (계정 ${r.accounts}개 막음)`); }catch(err){ toast(err.message); } break; }
    case 'storedel': { const nm=isClosedName(d.name)?d.name.slice(0,-CLOSED_MARK.length):d.name;
      const typed=(prompt(`‘${nm}’ 매장을 완전히 지울까요?\n\n· 예약·근무표·발주·계정 등 자료가 하나도 없는 매장만 지워져요\n· 지우면 되돌릴 수 없어요\n\n지우려면 매장 이름을 그대로 입력하세요`)||'').trim(); if(!typed) return;
      try{ await APP.be.manageStores({action:'delete',store:d.id,confirm:typed}); APP.stores=await APP.be.stores(); APP.st=APP.stores.find(x=>x.id===APP.sid)||APP.stores[0]; APP.sum=null; notifyStores(); renderShell(); render(); toast(`‘${nm}’ 을(를) 지웠어요`); }catch(err){ toast(err.message); } break; }
    case 'storerename': { const wasClosed=isClosedName(d.name), cur=wasClosed?d.name.slice(0,-CLOSED_MARK.length):(d.name||''); let nm=(prompt('새 매장 이름',cur)||'').trim(); if(!nm||nm===cur) return; if(wasClosed) nm+=CLOSED_MARK;
      try{ const r=await Remote.fetchJ('/rest/v1/rpc/sch_rename_store',{method:'POST',body:JSON.stringify({p_store:d.id,p_name:nm})});
        if(r!=='ok') return toast(r==='denied'?'본사 계정만 바꿀 수 있어요':r==='bad_name'?'이름은 1~40자예요':'매장을 찾지 못했어요');
        APP.stores=await APP.be.stores(); APP.st=APP.stores.find(x=>x.id===APP.sid)||APP.st; APP.sum=null; notifyStores(); renderShell(); render(); toast(`‘${nm}’ 으로 바꿨어요`); }catch(err){ toast(err.message); } break; }
    case 'pinreset': { const id=$('#rpId').value.trim().toLowerCase(); if(!id) return toast('아이디를 넣으세요'); if(!confirm(`‘${id}’ 계정의 급여 비밀번호를 지울까요?`)) return;
      try{ const r=await Remote.fetchJ('/rest/v1/rpc/pay_pin_reset',{method:'POST',body:JSON.stringify({p_login:id})}); toast(r==='ok'?`‘${id}’ 급여 비밀번호를 초기화했어요`:r==='none'?'그런 아이디가 없어요':'본사 계정만 할 수 있어요'); if(r==='ok') $('#rpId').value=''; }catch(err){ toast(err.message); } break; }
    case 'tores': { try{ window.parent.postMessage({type:'fr-open',id:'res'},'*'); }catch(er){} break; }
    case 'syncrun': case 'syncon': case 'syncoff': { const btn=e.target.closest('button'); btn.disabled=true; const old=btn.textContent;
      try{ if(d.a==='syncon'){ await APP.be.rpcText('sync_auto_set',{p_on:true}); await APP.be.rpcText('sync_run_now',{p_full:true}); toast('자동 연동을 켰어요. 처음 한 번 가져오는 중이에요…'); }
        else if(d.a==='syncoff'){ if(!confirm('자동 연동을 끌까요? 이후 예전 사이트에서 입력한 내용은 새 시스템으로 안 와요.')){ btn.disabled=false; break; } await APP.be.rpcText('sync_auto_set',{p_on:false}); toast('자동 연동을 껐어요'); }
        else { await APP.be.rpcText('sync_run_now',{p_full:true}); toast('가져오는 중이에요…'); }
        btn.textContent='확인 중…'; await new Promise(r=>setTimeout(r,d.a==='syncoff'?300:14000)); await syncLoad(); }
      catch(err){ toast('실행하지 못했어요: '+err.message); }
      btn.disabled=false; btn.textContent=old; break; }
    case 'bkdl': { const btn=e.target.closest('button'); btn.disabled=true; const old=btn.textContent;
      try{ const o=await APP.be.backupAll(t=>{ btn.textContent='받는 중… '+t; }); const txt=JSON.stringify(o); const day=ds(new Date());
        const a=document.createElement('a'); a.href=URL.createObjectURL(new Blob([txt],{type:'application/json'})); a.download=`일품집백업_${day}.json`; document.body.appendChild(a); a.click(); a.remove(); setTimeout(()=>URL.revokeObjectURL(a.href),5000);
        try{ localStorage.setItem('ilpum-last-backup',new Date().toISOString()); }catch(er){}
        const n=Object.values(o.tables).reduce((s,x)=>s+x.length,0); toast(`백업 완료: ${n.toLocaleString('ko-KR')}건 (${Math.round(txt.length/1024).toLocaleString('ko-KR')}KB)`); render(); }
      catch(err){ toast('백업하지 못했어요: '+err.message); }
      btn.disabled=false; btn.textContent=old; break; }
    case 'bkpick': { const f=$('#bkFile'); if(f) f.click(); break; }
    case 'mkaccount': { const id=$('#mkId').value.trim().toLowerCase(), pw=$('#mkPw').value; if(!id||!pw) return toast('아이디와 비밀번호를 넣으세요'); if(pw.length<8) return toast('비밀번호는 8자 이상이에요');
      const btn=e.target.closest('button'); btn.disabled=true;
      try{ const sel=$('#mkStore'), rs=$('#mkRole'); const where=sel.options[sel.selectedIndex].text, rn=rs.options[rs.selectedIndex].text.split(' ')[0];
        await APP.be.createAccount({id,password:pw,store:sel.value,role:rs.value,pay:rs.value==='manager'&&$('#mkPay').checked});
        APP.mkNote=`✅ 계정을 만들었어요 — 아이디 ${id} · ${where} ${rn} · 비밀번호는 방금 입력한 값`; APP.accts=undefined; render(); toast(`‘${id}’ 계정을 만들었어요`); }catch(err){ toast(err.message); }
      btn.disabled=false; break; }
    case 'acctreload': APP.accts=undefined; APP.acctErr=''; render(); break;
    case 'acctpw': { const pw=(prompt(`‘${d.id}’ 의 새 비밀번호 (8자 이상)`)||''); if(!pw) return; if(pw.length<8) return toast('비밀번호는 8자 이상이에요');
      try{ const r=await APP.be.manageAccounts({action:'setpw',id:d.id,password:pw}); APP.accts=undefined; APP.mkNote=`✅ ‘${d.id}’ 비밀번호를 바꿨어요 — 새 비밀번호: ${pw}${r&&r.ownerNotified?' (점주 계정이라 점주 화면에 "본사가 바꿨다"는 알림이 떠요)':''}`; render(); toast('비밀번호를 바꿨어요'); }catch(err){ toast(err.message); } break; }
    case 'mypw': { const pw=prompt('새 비밀번호 (8자 이상)')||''; if(!pw) return; if(pw.length<8) return toast('비밀번호는 8자 이상이에요'); if((prompt('한 번 더 입력하세요')||'')!==pw) return toast('두 번 입력한 비밀번호가 달라요');
      try{ const u=await Remote.changeMyPassword(pw); if(u&&u.id) APP.user=u; render(); toast('비밀번호를 바꿨어요. 다음부터 새 비밀번호로 로그인하세요'); }catch(err){ toast('바꾸지 못했어요: '+err.message); } break; }
    case 'acctpay': { const on=d.on==='1'; if(!confirm(on?`‘${d.id}’ 매니저가 급여(금액)를 볼 수 있게 할까요?`:`‘${d.id}’ 매니저의 급여 보기를 끌까요?`)) return;
      try{ await APP.be.manageAccounts({action:'setpay',id:d.id,on}); APP.accts=undefined; APP.mkNote=`✅ ‘${d.id}’ 급여 보기를 ${on?'켰어요':'껐어요'} (다시 로그인하면 반영돼요)`; render(); }catch(err){ toast(err.message); } break; }
    case 'acctban': { const on=d.on==='1'; if(!confirm(on?`‘${d.id}’ 를 정지할까요? 로그인이 막혀요(자료는 그대로).`:`‘${d.id}’ 정지를 풀까요?`)) return;
      try{ await APP.be.manageAccounts({action:'ban',id:d.id,on}); APP.accts=undefined; APP.mkNote=`✅ ‘${d.id}’ ${on?'정지했어요':'정지를 풀었어요'}`; render(); }catch(err){ toast(err.message); } break; }
    case 'acctdel': { if(!confirm(`‘${d.id}’ 계정을 삭제할까요? 되돌릴 수 없어요.`)) return;
      try{ const r=await APP.be.manageAccounts({action:'delete',id:d.id}); APP.accts=undefined; APP.mkNote=`✅ ‘${d.id}’ `+(r.note?r.note:'계정을 삭제했어요'); render(); toast(r.note?'로그인만 막았어요':'삭제했어요'); }catch(err){ toast(err.message); } break; }
    case 'importold': { if(!confirm('기존 근무표(본점 서버)의 데이터를 이 매장으로 가져올까요? 같은 사람·설정은 덮어써요.')) return;
      try{ toast('가져오는 중…'); const r=await fetch(`${OLD_URL}/rest/v1/schedule_state?id=eq.main&select=data`,{headers:{apikey:OLD_KEY,Authorization:'Bearer '+OLD_KEY}}); const rows=await r.json(); const n=importOld(rows[0]&&rows[0].data); render(); toast(`직원 ${n}명과 설정을 가져왔어요`); }catch(err){ toast('가져오기 실패: '+err.message); } break; }
    case 'backup': { const blob=new Blob([JSON.stringify({store:APP.sid,exportedAt:new Date().toISOString(),data:APP.D},null,1)],{type:'application/json'}); const a=document.createElement('a'); a.href=URL.createObjectURL(blob); a.download=`근무표_${APP.D.store.name}_${todayStr}.json`; a.click(); setTimeout(()=>URL.revokeObjectURL(a.href),3000); break; }
  }
});
function copy(t){ (navigator.clipboard?navigator.clipboard.writeText(t):Promise.reject()).then(()=>toast('복사했어요 · 카톡에 붙여넣으세요')).catch(()=>{ const ta=document.createElement('textarea'); ta.value=t; document.body.appendChild(ta); ta.select(); try{ document.execCommand('copy'); toast('복사했어요'); }catch(e){ toast('복사하지 못했어요'); } ta.remove(); }); }
document.addEventListener('submit',async e=>{
  if(e.target.id!=='lgForm') return; e.preventDefault();
  const btn=e.target.querySelector('button[type=submit]'); const idTyped=$('#lgEmail').value.trim(), email=toLoginEmail(idTyped), pw=$('#lgPw').value, keep=$('#lgKeep').checked;
  btn.disabled=true; btn.textContent='로그인 중…';
  try{ Remote.url=(Conf.url||'').replace(/\/$/,''); Remote.key=Conf.key; await Remote.login(email,pw,keep); Conf.email=idTyped; Conf.openOnly=false; saveConf(); location.reload(); }
  catch(err){ toast(/fetch|network|load failed/i.test(err.message)?'서버에 연결하지 못했어요. 인터넷이 되는 실제 주소에서 열어주세요':err.message); btn.disabled=false; btn.textContent='로그인'; $('#lgPw').focus(); }
});
document.addEventListener('input',e=>{ const t=e.target, id=t.id||'';
  const m=id.match(/^([a-z])(S|E|Pv)$/); if(m) updHints(m[1]);
  if(id==='rQ'){ const q=t.value.trim(); $$('#rPick label').forEach(l=>l.hidden=!!q&&!l.dataset.rn.includes(q)); }
  if(t.closest&&t.closest('#dBody')&&$('#rPrev')) rulePrev();
  if(id==='staffQ'&&!e.isComposing) staffSearch(t);   // 한글 조합 중에 화면을 다시 그리면 ㅇㅣㅈㅐ 처럼 낱글자로 풀려요 → 조합이 끝난 뒤에만
});
function staffSearch(t){ APP.q=t.value; const pos=t.selectionStart; render(); const n=$('#staffQ'); if(n){ n.focus(); try{ n.setSelectionRange(pos,pos); }catch(er){} } }
document.addEventListener('compositionend',e=>{ if(e.target&&e.target.id==='staffQ') staffSearch(e.target); });
document.addEventListener('change',e=>{ const t=e.target, d=t.dataset, D=APP.D; const id=t.id||'';
  if(id==='imgDate'){ if(t.value) makeImage('day',t.value); return; }
  const m=id.match(/^([a-z])(Pk|Pc)$/); if(m) updHints(m[1]);
  if(t.closest&&t.closest('#dBody')&&$('#rPrev')) rulePrev();
  if(d.pat!==undefined){ const i=$(`[data-patt="${d.pat}"]`); i.hidden=t.value!=='t'; i.placeholder=t.value==='t'?'예: 11 또는 11~9':''; if(t.value==='t') i.focus(); }
  if(d.wt&&WD){ const mm=WD.map[d.wt], i=+d.i; const v=t.value.trim(); if(!v) delete mm.t[i]; else { const s=parseT(v,false); if(!s){ toast('시간을 알아보지 못했어요'); t.value=''; return; } mm.t[i]={s}; mm.pm=mm.pm.filter(x=>x!==i); t.value=tLbl(s); } }
  if(d.a==='mepick'){ APP.me=t.value; render(); }
  if(d.a==='stf'){ const st={...D.store}; const f=d.f; let v=t.type==='checkbox'?t.checked:t.value;
    if(['open','close','pmStart'].includes(f)){ const p=parseT(v,f!=='open'); if(!p){ toast('시간을 확인하세요 (예: 11:00)'); t.value=st[f]; return; } v=p; t.value=p; }
    if(['fullH','pmH','target'].includes(f)) v=+v||0; st[f]=v; put('cfg','store',st); if(f==='name') renderShell(),render(); toast('저장했어요'); }
  if(d.a==='pmf'){ const pos=D.positions.map(p=>({...p,req:[...(p.req||[0,0,0,0,0,0,0])]})); const p=pos[+d.i]; if(!p) return;
    if(d.f==='name'){ const v=t.value.trim(); if(!v||pos.some((x,j)=>j!==+d.i&&x.name===v)){ toast('이름이 비었거나 이미 있어요'); t.value=p.name; return; } if(v===p.name) return; const old=p.name; p.name=v; renamePos(old,v); }
    else p.color=t.value;
    put('cfg','positions',pos); render(); toast('저장했어요'); return; }
  if(d.a==='posf'){ const pos=D.positions.map(p=>({...p,req:[...p.req]})); const p=pos[+d.i];
    if(d.f==='req') p.req[+d.wd]=Math.max(0,+t.value||0); else if(d.f==='name'){ const v=t.value.trim(); if(!v||pos.some((x,j)=>j!==+d.i&&x.name===v)){ toast('이름이 비었거나 겹쳐요'); t.value=p.name; return; }
      const old=p.name; p.name=v; renamePos(old,v); } else p[d.f]=t.value;
    put('cfg','positions',pos); }
  if(id==='bkFile'&&t.files[0]){ const file=t.files[0]; t.value=''; file.text().then(async txt=>{ let o; try{ o=JSON.parse(txt); }catch(er){ return toast('파일을 읽지 못했어요'); }
      if(!o||o.app!=='ilpum'||!o.tables) return toast('일품집 백업 파일이 아니에요');
      const cnt=Object.entries(o.tables).map(([k,v])=>`${k} ${v.length}건`).join(', ');
      if(!confirm(`${String(o.createdAt||'').slice(0,10)} 백업으로 복원할까요?\n(${cnt})\n\n지금 서버의 같은 자료는 이 파일 내용으로 덮어써져요. 되돌릴 수 없어요.`)) return;
      try{ const done=await APP.be.restoreAll(o,(tb,i,n)=>setSync('복원 중… '+tb+' '+i+'/'+n,'')); toast('복원했어요: '+Object.entries(done).map(([k,v])=>k+' '+v).join(', ')); setTimeout(()=>location.reload(),1500); }
      catch(err){ toast('복원하지 못했어요: '+err.message); } }); }
  if(id==='impFile'&&t.files[0]){ t.files[0].text().then(txt=>{ try{ const o=JSON.parse(txt); const n=importOld(o.data&&o.data.staff?o.data:o); render(); toast(`직원 ${n}명과 설정을 가져왔어요`); }catch(err){ toast(err.message||'파일을 읽지 못했어요'); } }); t.value=''; }
});
document.addEventListener('keydown',e=>{ if(e.key==='Escape'&&$('#drawer').classList.contains('on')) closeDrawer();

  if(e.key==='Enter'&&e.target.id==='npN'&&!e.isComposing) addPos(); });
/* ---------- 끌어서 옮기기·복사 (마우스는 바로, 폰은 꾹 누른 채) ---------- */
let DR=null, DRSUP=0;
const srcOf=el=>({sid:el.dataset.sid,spot:el.dataset.spot,k:el.dataset.k,pos:el.dataset.pos});
function dragBegin(el,x,y,touch){ DR={el,src:srcOf(el),x,y,x0:x,y0:y,on:false,touch,tgt:null,timer:null}; }
function dragStart(){ if(!DR||DR.on) return; DR.on=true; document.body.classList.add('dragging-now');
  const g=DR.el.cloneNode(true); g.classList.add('dghost'); g.removeAttribute('data-a'); g.removeAttribute('title'); document.body.appendChild(g); DR.ghost=g; DR.el.classList.add('dragging');
  // 빈 포지션은 화면을 밀어내지 않고 카드 아래에 떠 있는 판으로 보여줘요 (끌기 시작할 때 화면이 움직이던 것 방지)
  const card=DR.el.closest('.cards .dcard'); if(card){ const rows=[...card.querySelectorAll('.cr.empty')];
    if(rows.length){ const pal=document.createElement('div'); pal.className='dpal'; pal.innerHTML='<span class="dpl">빈 포지션으로</span>'+rows.map(r=>{ const b=r.querySelector('.bc[data-drop]'); return b?`<div class="bc dpal-i" data-drop="${esc(b.dataset.drop)}" data-k="${esc(b.dataset.k)}" style="${r.getAttribute('style')||''}">${esc(b.dataset.drop)}</div>`:''; }).join('');
      document.body.appendChild(pal); const cr=card.getBoundingClientRect(), ph=pal.offsetHeight; pal.style.width=Math.max(160,cr.width)+'px'; pal.style.left=Math.max(4,Math.min(cr.left,innerWidth-pal.offsetWidth-4))+'px'; pal.style.top=Math.max(4,Math.min(cr.bottom+4,innerHeight-ph-8))+'px'; DR.pal=pal; } }
  if(navigator.vibrate) try{ navigator.vibrate(15); }catch(_){} dragMove(DR.x,DR.y); }
function dragMove(x,y){ if(!DR||!DR.ghost) return; DR.x=x; DR.y=y; DR.ghost.style.left=x+'px'; DR.ghost.style.top=y+'px';
  const w=$('.boardwrap'); if(w){ const r=w.getBoundingClientRect(); if(x>r.right-50) w.scrollLeft+=16; else if(x<r.left+130) w.scrollLeft-=16; if(y>r.bottom-40) w.scrollTop+=14; else if(y<r.top+50) w.scrollTop-=14; }
  const t=document.elementFromPoint(x,y), c=t&&t.closest?t.closest('.bc[data-drop]'):null;
  $$('.bc.drop').forEach(n=>{ if(n!==c) n.classList.remove('drop'); });
  if(c&&!(c.dataset.k===DR.src.k&&c.dataset.drop===DR.src.pos)){ c.classList.add('drop'); DR.tgt=c; DR.ghost.dataset.mode=c.dataset.k===DR.src.k?'move':'copy'; }
  else { DR.tgt=null; DR.ghost.dataset.mode=''; } }
function dragEnd(commit){ if(!DR) return; clearTimeout(DR.timer); const d=DR; DR=null;
  if(d.ghost) d.ghost.remove(); if(d.pal) d.pal.remove(); d.el.classList.remove('dragging'); $$('.bc.drop').forEach(n=>n.classList.remove('drop')); document.body.classList.remove('dragging-now');
  if(d.on){ DRSUP=Date.now(); if(commit&&d.tgt) dropTo(d.src,d.tgt.dataset.k,d.tgt.dataset.drop); } }
function dropTo(src,tk,pos){
  const D=APP.D;
  if(tk===src.k){                                   // 같은 날 → 그 날만 포지션 변경
    if(src.pos===pos) return;
    if(src.spot){ put('spot',src.spot,{...D.spot[src.spot],pos}); }
    else { const k=src.k+'|'+src.sid, b=findItem(D,src.k,src.sid,{noDc:src.sid}); const o=Object.assign({},D.dc[k]||{}); if(b&&b.pos===pos) delete o.pos; else o.pos=pos; put('dc',k,Object.keys(o).length?o:null); }
    toast(`그 날만 ${pos}(으)로 옮겼어요`); render(); return; }
  // 다른 날 → 복사
  if(src.spot){ const x=D.spot[src.spot]; if(!x) return;
    if(Object.values(D.spot).some(z=>z.date===tk&&z.name===x.name)) return toast(`${x.name}은(는) ${mdw(tk)}에 이미 있어요`);
    const id=uid(); put('spot',id,{...x,id,date:tk,pos}); const pv=(D.pay||{})['spot:'+src.spot]; if(pv) putPay('spot:'+id,pv);
    toast(`${x.name} → ${mdw(tk)} ${pos}에 복사했어요`); render(); return; }
  const s=D.staff[src.sid]; if(!s) return;
  if(findItem(D,tk,src.sid)) return toast(`${s.name}님은 ${mdw(tk)}에 이미 근무해요`);
  const from=findItem(D,src.k,src.sid); const k=tk+'|'+src.sid; const o=Object.assign({},D.dc[k]||{});
  o.st='extra'; if(pos!==s.pos) o.pos=pos; else delete o.pos; if(from&&from.shSrc==='day'&&from.sh) o.sh=from.sh;
  put('dc',k,o); toast(`${s.name} → ${mdw(tk)} ${pos}에 복사했어요`); render(); }
const chipAt=t=>t&&t.closest?t.closest('.board .chip[data-k], .cards .chip[data-k]'):null;
document.addEventListener('pointerdown',ev=>{ if(!canEdit()||ev.pointerType!=='mouse'||ev.button!==0) return; const c=chipAt(ev.target); if(c) dragBegin(c,ev.clientX,ev.clientY,false); });
document.addEventListener('pointermove',ev=>{ if(!DR||DR.touch||ev.pointerType!=='mouse') return; if(!DR.on){ if(Math.hypot(ev.clientX-DR.x0,ev.clientY-DR.y0)<6) return; dragStart(); } dragMove(ev.clientX,ev.clientY); });
document.addEventListener('pointerup',()=>{ if(DR&&!DR.touch) dragEnd(true); });
document.addEventListener('pointercancel',()=>{ if(DR&&!DR.touch) dragEnd(false); });
document.addEventListener('touchstart',ev=>{ if(!canEdit()||ev.touches.length!==1) return; const c=chipAt(ev.target); if(!c) return; const t=ev.touches[0]; dragBegin(c,t.clientX,t.clientY,true); DR.timer=setTimeout(dragStart,320); },{passive:true});
document.addEventListener('touchmove',ev=>{ if(!DR||!DR.touch) return; const t=ev.touches[0];
  if(!DR.on){ if(Math.hypot(t.clientX-DR.x0,t.clientY-DR.y0)>10){ clearTimeout(DR.timer); DR=null; } return; }
  ev.preventDefault(); dragMove(t.clientX,t.clientY); },{passive:false});
document.addEventListener('touchend',()=>{ if(DR&&DR.touch) dragEnd(true); });
document.addEventListener('touchcancel',()=>{ if(DR&&DR.touch) dragEnd(false); });
document.addEventListener('contextmenu',ev=>{ if(DR&&DR.touch) ev.preventDefault(); });
document.addEventListener('keydown',ev=>{ if(ev.key==='Escape'&&DR) dragEnd(false); });

boot();
