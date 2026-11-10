/* 일용직 원장: 개인정보는 공개 HTML 대신 기존 pay RLS로 보호되는 행에만 보관. */
const DW={sheet:null,year:null,store:null,a:null,b:null,drag:null,drafts:new Map(),busy:false,search:'',hits:[],target:null,searchTimer:null};
const dwClone=x=>JSON.parse(JSON.stringify(x));
const dwKey=()=>APP.sid+'|'+DW.sheet;
const dwSheets=()=>Object.keys(APP.D.pay||{}).filter(k=>k.startsWith('daily:')).sort();
const dwLabel=key=>`${key.slice(6,10)}년 ${+key.slice(-2)}월`;
const dwMonthKey=(year,month)=>`daily:${year}-${String(month).padStart(2,'0')}`;
function dwSheet(){ return DW.drafts.get(dwKey())||APP.D.pay[DW.sheet]; }
function dwDraft(){ const k=dwKey(); if(!DW.drafts.has(k)) DW.drafts.set(k,dwClone(dwSheet())); return DW.drafts.get(k); }
function dwCol(c){ let s=''; for(c++;c;c=Math.floor((c-1)/26)) s=String.fromCharCode(65+(c-1)%26)+s; return s; }
function dwRange(){ if(!DW.a||!DW.b) return null; return {r0:Math.min(DW.a.r,DW.b.r),r1:Math.max(DW.a.r,DW.b.r),c0:Math.min(DW.a.c,DW.b.c),c1:Math.max(DW.a.c,DW.b.c)}; }
function dwRangeText(){ const q=dwRange(); return q?`${dwCol(q.c0)}${q.r0+1}:${dwCol(q.c1)}${q.r1+1}`:'선택 없음'; }
const dwNormalize=s=>String(s??'').normalize('NFKC').replace(/\s+/g,'').toLocaleLowerCase('ko-KR');
function dwFind(){
  const query=dwNormalize(DW.search),hits=[];
  if(query) for(const key of dwSheets().reverse()){
    const s=DW.drafts.get(APP.sid+'|'+key)||APP.D.pay[key];
    s.rows.forEach((row,r)=>{ if(r>0&&row.some(v=>dwNormalize(v).includes(query))) hits.push({key,r,name:row[1]||'(이름 없음)',pos:row[0]||'',month:dwLabel(key)}); });
  }
  DW.hits=hits; return hits;
}
function dwReveal(){ if(DW.target&&DW.target.key===DW.sheet) $(`.dw-grid td[data-dwr="${DW.target.r}"][data-dwc="1"]`)?.scrollIntoView({block:'center',inline:'nearest'}); }
function dwGoSheet(key,r=null){
  if(DW.busy||!dwSheets().includes(key)) return;
  dwCommitEditor();
  DW.sheet=key; DW.year=+key.slice(6,10); DW.a=DW.b=null;
  DW.target=r==null?DW.hits.find(h=>h.key===key)||null:{key,r}; render(); dwReveal();
}
function dwSearchRun(){
  if(APP.view!=='daily'||!canPay()) return;
  const input=$('#dw-search'),focused=document.activeElement===input;
  dwFind(); DW.target=DW.hits[0]||null;
  if(DW.target){ DW.sheet=DW.target.key; DW.year=+DW.sheet.slice(6,10); DW.a=DW.b=null; }
  render(); dwReveal(); if(focused) $('#dw-search')?.focus({preventScroll:true});
}
function dwSearchBox(){
  return `<div class="dw-searchbar"><label for="dw-search">전체 기간 검색</label><input id="dw-search" type="search" placeholder="이름·연락처·메모 검색" value="${esc(DW.search)}" autocomplete="off" ${DW.busy?'disabled':''}><span role="status">${DW.search.trim()?`${DW.hits.length}건`:'모든 연도·월에서 찾아요'}</span></div>
    ${DW.search.trim()?`<div class="dw-results" aria-label="전체 월 검색 결과">${DW.hits.length?DW.hits.map((h,i)=>`<button type="button" class="dw-result" data-dw-hit="${i}" aria-current="${DW.target?.key===h.key&&DW.target?.r===h.r?'true':'false'}"><b>${esc(h.name)}</b><span>${esc(h.month)} · ${esc(h.pos)} · ${h.r+1}행</span></button>`).join(''):'<p class="dw-noresult">일치하는 내용이 없어요.</p>'}</div>`:''}`;
}
function dwCellText(row,r,c,hit){
  const value=esc(row[c]||'');
  return hit&&(c===1||dwNormalize(row[c]).includes(dwNormalize(DW.search)))?`<mark>${value}</mark>`:value;
}
// 원본 강조 구분은 유지하고 화면과 PDF에 같은 차분한 팔레트를 사용.
function dwTone(color,ink=false){
  const m=/^#([\da-f]{6})$/i.exec(color||''); if(!m) return ink?'#34413c':null;
  const v=[0,2,4].map(i=>parseInt(m[1].slice(i,i+2),16)/255),max=Math.max(...v),min=Math.min(...v),d=max-min;
  if(d<.08) return ink?'#34413c':null;
  let h=max===v[0]?(v[1]-v[2])/d:max===v[1]?2+(v[2]-v[0])/d:4+(v[0]-v[1])/d; h=(h*60+360)%360;
  if(h<35||h>=345) return ink?'#925e58':'#f6e9e4';
  if(h<75) return ink?'#887044':'#f8f1dd';
  if(h<175) return ink?'#52705d':'#e9f1e9';
  if(h<265) return ink?'#5c718b':'#eaf0f7';
  return ink?'#886879':'#f3eaf0';
}
function dwCellTheme(s,r,c){ const t=(s.styles||{})[r+','+c]||{},pos=r>0&&c===0?({홀:'#f8f1dd',주방:'#e9f1e9',주차:'#f3eaf0'}[dwNormalize(s.rows[r]?.[c])]):null; return {bg:pos||dwTone(t.bg)||(r===0?'#edf2ee':r%2?'#ffffff':'#fafbf9'),fg:t.fg?dwTone(t.fg,true):r===0?'#3d5747':'#26362d',bold:r===0||!!t.bold,align:t.align||'left'}; }
function dwStyle(s,r,c){ const t=dwCellTheme(s,r,c); return `background:${t.bg};color:${t.fg};font-weight:${t.bold?700:600};text-align:${t.align}`; }
function dwMonthTools(){
  const years=[...new Set([...dwSheets().map(k=>+k.slice(6,10)),DW.year-1,DW.year,DW.year+1])].sort((a,b)=>a-b);
  return `<div class="card dw-tools">${dwSearchBox()}<div class="dw-yearbar"><button class="btn sm" data-dw-year="${DW.year-1}" ${DW.busy?'disabled':''} aria-label="이전 연도">‹</button><label>연도 <select id="dw-year" ${DW.busy?'disabled':''}>${years.map(y=>`<option value="${y}" ${y===DW.year?'selected':''}>${y}년</option>`).join('')}</select></label><button class="btn sm" data-dw-year="${DW.year+1}" ${DW.busy?'disabled':''} aria-label="다음 연도">›</button><button class="btn sm" data-dw="newmonth" ${DW.busy?'disabled':''}>+ 월 만들기 / 월 복사</button></div>
    <div class="dw-months" role="group" aria-label="월 선택">${Array.from({length:12},(_,i)=>{ const key=dwMonthKey(DW.year,i+1),exists=dwSheets().includes(key); return `<button type="button" ${exists?`data-dw-month="${key}"`:`data-dw-newmonth="${i+1}" class="dw-month-empty"`} aria-pressed="${key===DW.sheet}" ${DW.busy?'disabled':''}>${exists?'':'+ '}${i+1}월</button>`; }).join('')}</div></div>`;
}
function vDaily(){
  if(!navAllowed('daily')) return '';
  const sheets=dwSheets();
  if(DW.store!==APP.sid){ DW.store=APP.sid; DW.sheet=sheets.at(-1)||null; DW.year=DW.sheet?+DW.sheet.slice(6,10):new Date().getFullYear(); DW.a=DW.b=null; DW.search=''; DW.hits=[]; DW.target=null; clearTimeout(DW.searchTimer); }
  if(DW.sheet&&!sheets.includes(DW.sheet)){ DW.sheet=sheets.filter(k=>+k.slice(6,10)===DW.year).at(-1)||null; DW.a=DW.b=null; }
  if(!canPay()) return `<div class="vh"><h1>일용직근무자</h1>${payToggle()}</div><div class="card empty"><b>개인정보가 포함된 원장이에요</b>위의 ‘금액 보기’를 눌러 열어주세요.</div>`;
  const s=dwSheet();
  dwFind();
  if(!s) return `<div class="vh dw-heading"><h1>일용직근무자</h1>${payToggle()}</div>${dwMonthTools()}<div class="card empty"><b>${DW.year}년에 등록된 원장이 없어요</b>원하는 월의 + 버튼을 눌러 새로 만들거나 기존 월을 복사하세요.</div>`;
  const hitRows=new Set(DW.hits.filter(h=>h.key===DW.sheet).map(h=>h.r));
  return `<div class="vh dw-heading"><div><h1>일용직근무자</h1><div class="sub">월별 근무 기록 · 칸을 두 번 누르면 수정할 수 있어요</div></div><span class="sp"></span>${payToggle()}</div>
    ${dwMonthTools()}
    <div class="card dw-toolbar">
    <button class="btn" data-dw="all">전체 선택</button><button class="btn" data-dw="clear">선택 해제</button><button class="btn" data-dw="copy" ${DW.busy||!dwRange()?'disabled':''}>선택 범위 복사</button><button class="btn" data-dw="add" ${DW.busy?'disabled':''}>+ 행 추가</button>
    <span class="sp"></span><span id="dw-status" role="status">${DW.busy?'저장 중…':DW.drafts.has(dwKey())?'수정됨 · 저장해 주세요':'저장됨'}</span>
    <button class="btn" data-dw="save" ${DW.busy?'disabled':''}>저장</button><button class="btn pri" data-dw="pdf" ${DW.busy||!dwRange()?'disabled':''}>선택 범위 PDF</button></div>
    <p class="help dw-help">드래그 선택 후 Ctrl+C 복사 / Ctrl+V 붙여넣기 · 버튼으로도 복사 가능 · 더블클릭 수정 · Tab 오른쪽 / Enter 아래쪽 · Alt+Enter 줄바꿈. 수정 후 ‘저장’을 누르세요.</p>
    <div class="dw-selection" id="dw-range" aria-live="polite">${dwRangeText()}</div>
    <div class="dw-scroll" tabindex="0" role="region" aria-label="일용직근무자 표"><table class="dw-grid" role="grid" aria-label="${esc(s.name)} 일용직근무자"><colgroup><col style="width:44px">${s.widths.map(w=>`<col style="width:${Math.max(76,Math.round(w*.92))}px">`).join('')}</colgroup>
    <thead><tr><th></th>${s.widths.map((_,c)=>`<th>${dwCol(c)}</th>`).join('')}</tr></thead><tbody>${s.rows.map((row,r)=>`<tr class="${hitRows.has(r)?'dw-search-hit':''} ${DW.target?.key===DW.sheet&&DW.target?.r===r?'dw-search-current':''}"><th>${r+1}</th>${s.widths.map((_,c)=>`<td data-dwr="${r}" data-dwc="${c}" style="${dwStyle(s,r,c)}" aria-selected="${dwContains(r,c)}" class="${dwContains(r,c)?'dw-selected':''} ${[2,3,7].includes(c)?'dw-compact':''}">${dwCellText(row,r,c,hitRows.has(r))}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`;
}
function dwContains(r,c){ const q=dwRange(); return !!q&&r>=q.r0&&r<=q.r1&&c>=q.c0&&c<=q.c1; }
function dwPaint(){
  $$('.dw-grid td').forEach(t=>{ const on=dwContains(+t.dataset.dwr,+t.dataset.dwc); t.classList.toggle('dw-selected',on); t.setAttribute('aria-selected',String(on)); });
  if($('#dw-range')) $('#dw-range').textContent=dwRangeText();
  for(const action of ['pdf','copy']){ const btn=$(`[data-dw="${action}"]`); if(btn) btn.disabled=DW.busy||!dwRange(); }
}
function dwDirty(){ const el=$('#dw-status'); if(el) el.textContent='수정됨 · 저장해 주세요'; }
function dwCommitEditor(){ $('.dw-editor')?.dwCommit?.(); }
function dwFocusCell(r,c,edit=false){
  DW.a=DW.b={r,c}; dwPaint();
  const td=$(`.dw-grid td[data-dwr="${r}"][data-dwc="${c}"]`);
  td?.scrollIntoView({block:'nearest',inline:'nearest'});
  if(edit) dwEdit(td); else $('.dw-scroll')?.focus({preventScroll:true});
}
function dwStep(r,c,key,reverse,edit){
  const s=dwSheet(),last=s.widths.length-1,dir=reverse?-1:1;
  if(key==='Tab'){ c+=dir; if(c>last){ if(r<s.rows.length-1){ r++; c=0; } else c=last; } if(c<0){ if(r>0){ r--; c=last; } else c=0; } }
  else r=Math.max(0,Math.min(s.rows.length-1,r+dir));
  dwFocusCell(r,c,edit);
}
function dwEdit(td,initial){
  if(!td||DW.busy||!canPay()||!navAllowed('daily')||$('.dw-editor')) return;
  const r=+td.dataset.dwr,c=+td.dataset.dwc,old=dwSheet().rows[r][c]||'';
  const input=document.createElement('textarea'); input.className='dw-editor'; input.value=initial??old; input.setAttribute('aria-label',`${dwCol(c)}${r+1} 수정`);
  const height=Math.max(28,td.clientHeight-10);
  td.textContent=''; td.append(input); input.style.height=height+'px'; input.focus({preventScroll:true}); if(initial==null) input.select();
  let done=false;
  const finish=cancel=>{ if(done) return; done=true; const v=cancel?old:input.value; if(v!==old){ dwDraft().rows[r][c]=v; dwDirty(); } input.remove(); td.textContent=v; td.setAttribute('style',dwStyle(dwSheet(),r,c)); };
  input.dwCommit=()=>finish(false);
  input.addEventListener('blur',()=>finish(false));
  input.addEventListener('keydown',e=>{
    e.stopPropagation(); if(e.isComposing||e.keyCode===229) return; // 한글 조합 확정 Enter는 이동하지 않음
    if(e.key==='Escape'){ e.preventDefault(); finish(true); $('.dw-scroll')?.focus({preventScroll:true}); }
    else if((e.key==='Enter'&&!e.altKey)||e.key==='Tab'){ e.preventDefault(); finish(false); dwStep(r,c,e.key,e.shiftKey,true); }
    else if(e.key==='Enter'&&e.altKey){ e.preventDefault(); input.setRangeText('\n',input.selectionStart,input.selectionEnd,'end'); }
  });
}
async function dwSave(){
  if(DW.busy||!canPay()||!navAllowed('daily')) return false;
  dwCommitEditor();
  const key=dwKey(),s=DW.drafts.get(key); if(!s) return true;
  const sid=APP.sid,id=DW.sheet,data=dwClone(s); DW.busy=true; render();
  try{
    if(APP.be.putMany) await APP.be.putMany([{sid,kind:'pay',id,data}]); else await APP.be.put(sid,'pay',id,data);
    if(APP.sid===sid) APP.D.pay[id]=data;
    DW.drafts.delete(key); toast('일용직 원장을 저장했어요'); return true;
  }catch(e){ toast('저장하지 못했어요. 수정 내용은 유지돼요. 다시 저장해 주세요.'); return false; }
  finally{ DW.busy=false; render(); }
}

function dwChangeYear(year){
  if(DW.busy||!Number.isInteger(year)||year<1900||year>9999) return;
  dwCommitEditor();
  DW.year=year; DW.sheet=dwSheets().filter(k=>+k.slice(6,10)===year).at(-1)||null; DW.a=DW.b=null; DW.target=null; render();
}
function dwMonthDialog(year=DW.year,month=null){
  if(DW.busy||!canPay()||!navAllowed('daily')) return;
  dwCommitEditor();
  if(month==null){ const next=DW.sheet?new Date(+DW.sheet.slice(6,10),+DW.sheet.slice(-2),1):new Date(year,0,1); year=next.getFullYear(); month=next.getMonth()+1; }
  openDrawer('월 만들기 / 월 복사','기존 원장은 그대로 두고 새 월을 만들어요',
    `<div class="dw-monthform"><label>연도<input id="dw-new-year" type="number" min="1900" max="9999" value="${year}"></label><label>월<select id="dw-new-month">${Array.from({length:12},(_,i)=>`<option value="${i+1}" ${i+1===month?'selected':''}>${i+1}월</option>`).join('')}</select></label><label>만드는 방법<select id="dw-new-mode"><option value="blank">빈 원장 만들기 (제목 행 유지)</option><option value="copy">기존 월 그대로 복사</option></select></label><label>양식 / 복사할 월<select id="dw-new-source">${dwSheets().map(k=>`<option value="${esc(k)}" ${k===(DW.sheet||dwSheets().at(-1))?'selected':''}>${dwLabel(k)}</option>`).join('')}</select></label><p class="help">복사를 선택하면 직원·금액·메모까지 그대로 가져와요. 새 월에서 고친 내용은 원래 월에 영향을 주지 않아요.</p><p id="dw-new-error" role="alert"></p></div>`,
    '<button class="btn" data-dw="cancelmonth">취소</button><button class="btn pri" data-dw="createmonth">만들기</button>');
}
async function dwCreateMonth(){
  if(DW.busy||!canPay()||!navAllowed('daily')) return;
  const year=Number($('#dw-new-year').value),month=Number($('#dw-new-month').value),key=dwMonthKey(year,month),error=$('#dw-new-error');
  if(!Number.isInteger(year)||year<1900||year>9999||!Number.isInteger(month)||month<1||month>12){ error.textContent='연도와 월을 확인해 주세요.'; return; }
  if(dwSheets().includes(key)){ error.textContent='이미 있는 월이에요. 다른 연도·월을 골라주세요.'; return; }
  const source=$('#dw-new-source').value,mode=$('#dw-new-mode').value,sid=APP.sid;
  const fallback={rows:[['근무형태','성함','주민번호','신고가능여부','신고금액','근무일','계좌번호','연락처','비고(근무일자 등)']],widths:[90,130,140,100,100,100,220,140,250],styles:{}};
  const data=dwClone(DW.drafts.get(sid+'|'+source)||APP.D.pay[source]||fallback); data.name=month+'월';
  if(mode==='blank'){ data.rows=[data.rows[0].slice(),data.widths.map(()=>'')]; data.styles=Object.fromEntries(Object.entries(data.styles||{}).filter(([k])=>k.startsWith('0,'))); }
  const btn=$('[data-dw="createmonth"]'); btn.disabled=true; DW.busy=true; error.textContent='저장 중…';
  try{
    if(APP.be===Remote){ // upsert하지 않아 다른 기기에서 먼저 만든 월도 덮어쓰지 않음
      await Remote.fetchJ('/rest/v1/sch_items',{method:'POST',headers:{Prefer:'return=minimal'},body:JSON.stringify({store_id:sid,kind:'pay',id:key,data,deleted:false})});
    }else await APP.be.put(sid,'pay',key,data);
    if(APP.sid===sid){ APP.D.pay[key]=data; DW.sheet=key; DW.year=year; DW.a=DW.b=null; DW.search=''; DW.hits=[]; DW.target=null; }
    closeDrawer(); toast(`${year}년 ${month}월을 ${mode==='copy'?'복사했어요':'만들었어요'}`);
  }catch(e){ error.textContent=/duplicate|23505|409/i.test(e.message)?'이미 만들어진 월이에요. 새로고침 후 확인해 주세요.':'만들지 못했어요. 다시 시도해 주세요.'; }
  finally{ DW.busy=false; btn.disabled=false; render(); }
}

// 탭·줄바꿈·따옴표를 포함한 셀도 스프레드시트와 왕복 가능하게 처리.
function dwCopyData(){
  dwCommitEditor();
  const q=dwRange(),s=dwSheet(); if(!q||!s) return null;
  const rows=s.rows.slice(q.r0,q.r1+1).map(row=>row.slice(q.c0,q.c1+1));
  const quote=v=>/[\t\r\n"]/.test(String(v))?'"'+String(v).replace(/"/g,'""')+'"':String(v);
  return {text:rows.map(row=>row.map(quote).join('\t')).join('\r\n'),html:`<table>${rows.map(row=>`<tr>${row.map(v=>`<td style="white-space:pre-wrap;mso-number-format:'\\@'">${esc(v).replace(/\r?\n/g,'<br>')}</td>`).join('')}</tr>`).join('')}</table>`};
}
function dwParseTsv(text){
  const rows=[],row=[]; let cell='',quoted=false;
  text=String(text).replace(/\r\n?/g,'\n');
  for(let i=0;i<text.length;i++){
    const ch=text[i];
    if(ch==='"'&&(quoted||cell==='')){ if(quoted&&text[i+1]==='"'){ cell+='"'; i++; }else quoted=!quoted; }
    else if(!quoted&&(ch==='\t'||ch==='\n')){ row.push(cell); cell=''; if(ch==='\n'){ rows.push(row.splice(0)); } }
    else cell+=ch;
  }
  if(cell!==''||row.length||!text.endsWith('\n')){ row.push(cell); rows.push(row); }
  return rows.length?rows:[['']];
}
async function dwCopyButton(){
  if(DW.busy||!canPay()||!navAllowed('daily')) return;
  const data=dwCopyData(); if(!data) return;
  try{
    if(navigator.clipboard?.write&&window.ClipboardItem) await navigator.clipboard.write([new ClipboardItem({'text/plain':new Blob([data.text],{type:'text/plain'}),'text/html':new Blob([data.html],{type:'text/html'})})]);
    else if(navigator.clipboard?.writeText) await navigator.clipboard.writeText(data.text);
    else throw new Error('clipboard unavailable');
    toast('선택 범위를 복사했어요. 붙일 칸을 누르고 Ctrl+V 하세요.');
  }catch(e){ toast('이 브라우저에서는 선택 후 Ctrl+C로 복사해 주세요.'); }
}
function dwPasteRows(rows){
  const q=dwRange(); if(!q||!rows.length) return;
  const s=dwDraft(),cols=Math.max(...rows.map(row=>row.length)),need=q.c0+cols;
  while(s.widths.length<need){ s.widths.push(120); s.rows.forEach(row=>row.push('')); }
  while(s.rows.length<q.r0+rows.length) s.rows.push(s.widths.map(()=>''));
  const single=rows.length===1&&cols===1,r1=single?q.r1:q.r0+rows.length-1,c1=single?q.c1:q.c0+cols-1;
  for(let r=q.r0;r<=r1;r++) for(let c=q.c0;c<=c1;c++) s.rows[r][c]=single?rows[0][0]:(rows[r-q.r0][c-q.c0]??'');
  DW.a={r:q.r0,c:q.c0}; DW.b={r:r1,c:c1}; render(); dwPaint(); $('.dw-scroll')?.focus({preventScroll:true});
}

// PDF는 브라우저 안에서만 생성. 외부 변환 서버로 개인정보를 보내지 않음.
function dwWrap(g,text,width){
  const lines=[]; for(const line of String(text).split('\n')){ let part=''; for(const ch of line){ if(part&&g.measureText(part+ch).width>width){ lines.push(part); part=''; } part+=ch; } lines.push(part); } return lines;
}
function dwPdfBlob(pages,pageW,pageH){
  const enc=new TextEncoder(),chunks=[],offsets=[0]; let size=0;
  const add=x=>{ const a=typeof x==='string'?enc.encode(x):x; chunks.push(a); size+=a.length; };
  const obj=(n,body)=>{ offsets[n]=size; add(`${n} 0 obj\n`); add(body); add('\nendobj\n'); };
  add('%PDF-1.4\n'); obj(1,'<< /Type /Catalog /Pages 2 0 R >>');
  obj(2,`<< /Type /Pages /Count ${pages.length} /Kids [${pages.map((_,i)=>`${3+i*3} 0 R`).join(' ')}] >>`);
  pages.forEach((p,i)=>{ const n=3+i*3; obj(n,`<< /Type /Page /Parent 2 0 R /MediaBox [0 0 ${pageW} ${pageH}] /Resources << /XObject << /Im ${n+1} 0 R >> >> /Contents ${n+2} 0 R >>`);
    offsets[n+1]=size; add(`${n+1} 0 obj\n<< /Type /XObject /Subtype /Image /Width ${p.w} /Height ${p.h} /ColorSpace /DeviceRGB /BitsPerComponent 8 /Filter /DCTDecode /Length ${p.bytes.length} >>\nstream\n`); add(p.bytes); add('\nendstream\nendobj\n');
    const stream=`q ${pageW} 0 0 ${pageH} 0 0 cm /Im Do Q\n`; obj(n+2,`<< /Length ${enc.encode(stream).length} >>\nstream\n${stream}endstream`);
  });
  const start=size; add(`xref\n0 ${offsets.length}\n0000000000 65535 f \n`); offsets.slice(1).forEach(o=>add(String(o).padStart(10,'0')+' 00000 n \n'));
  add(`trailer\n<< /Size ${offsets.length} /Root 1 0 R >>\nstartxref\n${start}\n%%EOF`); return new Blob(chunks,{type:'application/pdf'});
}
async function dwMakePdf(s,q,store){
  await loadFonts();
  const widths=s.widths.slice(q.c0,q.c1+1).map(w=>Math.max(76,Math.round(w*.92))),sum=widths.reduce((a,b)=>a+b,0),land=sum>780;
  const W=land?1684:1190,H=land?1190:1684,margin=44,scale=Math.min(1.65,(W-2*margin)/sum),cw=widths.map(w=>w*scale),font=Math.max(14,16*scale),lh=font*1.3,pad=5;
  const pages=[]; let canvas,g,y;
  function newPage(){ canvas=document.createElement('canvas'); canvas.width=W; canvas.height=H; g=canvas.getContext('2d'); g.fillStyle='#fff'; g.fillRect(0,0,W,H); g.font=`700 24px ${IMG_FONT}`; g.fillStyle='#344b3f'; g.fillText(`일용직근무자 · ${s.name}`,margin,45); g.font=`14px ${IMG_FONT}`; g.fillStyle='#7b8980'; g.fillText(`${store} · ${dwCol(q.c0)}${q.r0+1}:${dwCol(q.c1)}${q.r1+1}`,margin,72); y=95; }
  async function endPage(){ g.font=`12px ${IMG_FONT}`; g.fillStyle='#666'; g.fillText(String(pages.length+1),W-margin-16,H-20); const blob=await new Promise(ok=>canvas.toBlob(ok,'image/jpeg',.97)); if(!blob) throw new Error('PDF 이미지 생성 실패'); pages.push({w:W,h:H,bytes:new Uint8Array(await blob.arrayBuffer())}); }
  newPage();
  for(let r=q.r0;r<=q.r1;r++){
    const cells=cw.map((w,i)=>{ const c=q.c0+i,t=dwCellTheme(s,r,c),fs=[2,3,7].includes(c)?Math.max(10,font*.8):font; g.font=`${t.bold?700:600} ${fs}px ${IMG_FONT}`; return {t,fs,lines:dwWrap(g,s.rows[r][c]||'',w-pad*2)}; });
    const count=Math.max(...cells.map(c=>c.lines.length)); let offset=0;
    while(offset<count){
      if(y+lh+pad*2>H-margin){ await endPage(); newPage(); }
      const n=Math.min(count-offset,Math.floor((H-margin-y-pad*2)/lh)),height=n*lh+pad*2; let x=margin;
      cells.forEach(({t,fs,lines},i)=>{ const w=cw[i]; g.fillStyle=t.bg; g.fillRect(x,y,w,height); g.strokeStyle='#dde5df'; g.lineWidth=.8; g.strokeRect(x,y,w,height); g.fillStyle=t.fg; g.font=`${t.bold?700:600} ${fs}px ${IMG_FONT}`;
        lines.slice(offset,offset+n).forEach((line,j)=>{ const tw=g.measureText(line).width,tx=t.align==='center'?x+(w-tw)/2:t.align==='right'?x+w-pad-tw:x+pad; g.fillText(line,tx,y+pad+font+j*lh); }); x+=w; });
      offset+=n; y+=height;
    }
  }
  await endPage(); return dwPdfBlob(pages,land?842:595,land?595:842);
}
async function dwExport(){
  if(DW.busy||!canPay()||!navAllowed('daily')||!dwRange()) return;
  dwCommitEditor();
  const q={...dwRange()},s={...dwClone(dwSheet()),name:dwLabel(DW.sheet)},name=`일용직근무자_${s.name}_${dwRangeText().replace(':','-')}.pdf`,store=APP.D.store.name;
  if(!await dwSave()) return;
  DW.busy=true; render();
  try{ const blob=await dwMakePdf(s,q,store),url=URL.createObjectURL(blob),a=document.createElement('a'); a.href=url; a.download=name; a.click(); setTimeout(()=>URL.revokeObjectURL(url),30000); toast('선택한 범위의 PDF를 내보냈어요'); }
  catch(e){ toast('PDF를 만들지 못했어요. 다시 시도해 주세요.'); }
  finally{ DW.busy=false; render(); }
}

document.addEventListener('input',e=>{ if(e.target.id!=='dw-search'||DW.busy) return; DW.search=e.target.value; clearTimeout(DW.searchTimer); if(!e.isComposing) DW.searchTimer=setTimeout(dwSearchRun,180); });
document.addEventListener('compositionend',e=>{ if(e.target.id==='dw-search'){ DW.search=e.target.value; clearTimeout(DW.searchTimer); DW.searchTimer=setTimeout(dwSearchRun,180); } });
document.addEventListener('keydown',e=>{ if(e.target.id==='dw-search'&&e.key==='Enter'&&!e.isComposing&&e.keyCode!==229){ e.preventDefault(); clearTimeout(DW.searchTimer); dwSearchRun(); } });
document.addEventListener('change',e=>{ if(e.target.id==='dw-year'&&canPay()&&navAllowed('daily')) dwChangeYear(+e.target.value); });
document.addEventListener('click',e=>{
  const year=e.target.closest('[data-dw-year]'),newmonth=e.target.closest('[data-dw-newmonth]');
  if((year||newmonth)&&canPay()&&navAllowed('daily')&&!DW.busy){ if(year) dwChangeYear(+year.dataset.dwYear); else dwMonthDialog(DW.year,+newmonth.dataset.dwNewmonth); return; }
  const month=e.target.closest('[data-dw-month]'),hit=e.target.closest('[data-dw-hit]');
  if((month||hit)&&canPay()&&navAllowed('daily')&&!DW.busy){ if(month) dwGoSheet(month.dataset.dwMonth); else { const h=DW.hits[+hit.dataset.dwHit]; if(h) dwGoSheet(h.key,h.r); } return; }
  const a=e.target.closest('[data-dw]')?.dataset.dw; if(!a||DW.busy||!canPay()||!navAllowed('daily')) return;
  dwCommitEditor();
  if(a==='all'){ const s=dwSheet(); DW.a={r:0,c:0}; DW.b={r:s.rows.length-1,c:s.widths.length-1}; dwPaint(); }
  if(a==='clear'){ DW.a=DW.b=null; dwPaint(); }
  if(a==='add'){ const s=dwDraft(); s.rows.push(s.widths.map(()=>'')); render(); $('.dw-scroll').scrollTop=1e7; }
  if(a==='cancelmonth') closeDrawer(); if(a==='save') dwSave(); if(a==='pdf') dwExport(); if(a==='copy') dwCopyButton(); if(a==='newmonth') dwMonthDialog(); if(a==='createmonth') dwCreateMonth();
});
document.addEventListener('dblclick',e=>{ const td=e.target.closest('.dw-grid td'); if(td) dwEdit(td); });
document.addEventListener('pointerdown',e=>{
  const td=e.target.closest('.dw-grid td'); if(!td||e.target.closest('.dw-editor')||e.button!==0||DW.busy) return;
  e.preventDefault(); const p={r:+td.dataset.dwr,c:+td.dataset.dwc}; if(!e.shiftKey||!DW.a) DW.a=p; DW.b=p; DW.drag={id:e.pointerId,x:e.clientX,y:e.clientY}; $('.dw-scroll').focus({preventScroll:true}); dwPaint(); requestAnimationFrame(dwDragFrame);
});
function dwDragFrame(){
  const d=DW.drag,box=$('.dw-scroll'); if(!d||!box) return;
  const rect=box.getBoundingClientRect(),speed=(p,lo,hi)=>p<lo+28?-Math.min(24,(lo+28-p)/2):p>hi-28?Math.min(24,(p-hi+28)/2):0;
  box.scrollBy(speed(d.x,rect.left,rect.right),speed(d.y,rect.top,rect.bottom));
  const td=document.elementFromPoint(Math.max(rect.left+46,Math.min(rect.right-2,d.x)),Math.max(rect.top+34,Math.min(rect.bottom-2,d.y)))?.closest('.dw-grid td');
  if(td){ const p={r:+td.dataset.dwr,c:+td.dataset.dwc}; if(p.r!==DW.b.r||p.c!==DW.b.c){ DW.b=p; dwPaint(); } }
  requestAnimationFrame(dwDragFrame);
}
document.addEventListener('pointermove',e=>{ if(DW.drag&&DW.drag.id===e.pointerId){ DW.drag.x=e.clientX; DW.drag.y=e.clientY; } });
document.addEventListener('pointerup',()=>DW.drag=null);
document.addEventListener('pointercancel',()=>DW.drag=null);
window.addEventListener('blur',()=>DW.drag=null);
document.addEventListener('keydown',e=>{
  if(!e.target.matches('.dw-scroll')||DW.busy||!canPay()) return;
  if((e.ctrlKey||e.metaKey)&&e.key==='a'){ e.preventDefault(); $('[data-dw="all"]').click(); return; }
  if(!DW.b) return;
  const s=dwSheet(),arrows={ArrowUp:[-1,0],ArrowDown:[1,0],ArrowLeft:[0,-1],ArrowRight:[0,1]};
  if(arrows[e.key]){ e.preventDefault(); const [r,c]=arrows[e.key]; DW.b={r:Math.max(0,Math.min(s.rows.length-1,DW.b.r+r)),c:Math.max(0,Math.min(s.widths.length-1,DW.b.c+c))}; if(!e.shiftKey) DW.a=DW.b; dwPaint(); $(`.dw-grid td[data-dwr="${DW.b.r}"][data-dwc="${DW.b.c}"]`)?.scrollIntoView({block:'nearest',inline:'nearest'}); }
  else if(e.key==='Tab'||e.key==='Enter'){ e.preventDefault(); dwStep(DW.b.r,DW.b.c,e.key,e.shiftKey,true); }
  else if(e.key==='F2'||(e.key.length===1&&!e.ctrlKey&&!e.metaKey&&!e.altKey)){ e.preventDefault(); dwEdit($(`.dw-grid td[data-dwr="${DW.b.r}"][data-dwc="${DW.b.c}"]`),e.key.length===1?e.key:undefined); }
  else if(e.key==='Delete'||e.key==='Backspace'){ e.preventDefault(); const q=dwRange(),d=dwDraft(); for(let r=q.r0;r<=q.r1;r++) for(let c=q.c0;c<=q.c1;c++) d.rows[r][c]=''; render(); }
});
document.addEventListener('copy',e=>{
  if(!e.target.matches('.dw-scroll')||!canPay()||!navAllowed('daily')||DW.busy) return;
  const data=dwCopyData(); if(!data) return; e.preventDefault(); e.clipboardData.setData('text/plain',data.text); e.clipboardData.setData('text/html',data.html);
});
document.addEventListener('paste',e=>{
  if(!e.target.matches('.dw-scroll,.dw-editor')||!DW.b||DW.busy||!canPay()||!navAllowed('daily')) return;
  const rows=dwParseTsv(e.clipboardData.getData('text/plain'));
  if(e.target.matches('.dw-editor')&&rows.length===1&&rows[0].length===1) return;
  e.preventDefault(); dwCommitEditor(); dwPasteRows(rows);
});
window.addEventListener('beforeunload',e=>{ if(DW.drafts.size){ e.preventDefault(); e.returnValue=''; } });
