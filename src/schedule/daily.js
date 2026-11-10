/* 일용직 원장: 개인정보는 공개 HTML 대신 기존 pay RLS로 보호되는 행에만 보관. */
const DW={sheet:null,store:null,a:null,b:null,drag:null,drafts:new Map(),busy:false,search:'',hits:[],target:null,searchTimer:null};
const dwClone=x=>JSON.parse(JSON.stringify(x));
const dwKey=()=>APP.sid+'|'+DW.sheet;
const dwSheets=()=>Object.keys(APP.D.pay||{}).filter(k=>k.startsWith('daily:')).sort();
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
    s.rows.forEach((row,r)=>{ if(r>0&&row.some(v=>dwNormalize(v).includes(query))) hits.push({key,r,name:row[1]||'(이름 없음)',pos:row[0]||'',month:s.name}); });
  }
  DW.hits=hits; return hits;
}
function dwReveal(){ if(DW.target&&DW.target.key===DW.sheet) $(`.dw-grid td[data-dwr="${DW.target.r}"][data-dwc="1"]`)?.scrollIntoView({block:'center',inline:'nearest'}); }
function dwGoSheet(key,r=null){
  if(DW.busy||!dwSheets().includes(key)) return;
  DW.sheet=key; DW.a=DW.b=null;
  DW.target=r==null?DW.hits.find(h=>h.key===key)||null:{key,r}; render(); dwReveal();
}
function dwSearchRun(){
  if(APP.view!=='daily'||!canPay()) return;
  const input=$('#dw-search'),focused=document.activeElement===input;
  dwFind(); DW.target=DW.hits[0]||null;
  if(DW.target){ DW.sheet=DW.target.key; DW.a=DW.b=null; }
  render(); dwReveal(); if(focused) $('#dw-search')?.focus({preventScroll:true});
}
function dwSearchBox(){
  return `<div class="dw-searchbar"><label for="dw-search">전체 월 검색</label><input id="dw-search" type="search" placeholder="이름·연락처·메모 검색" value="${esc(DW.search)}" autocomplete="off" ${DW.busy?'disabled':''}><span role="status">${DW.search.trim()?`${DW.hits.length}건`:'모든 월에서 찾아요'}</span></div>
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
function dwCellTheme(s,r,c){ const t=(s.styles||{})[r+','+c]||{}; return {bg:dwTone(t.bg)||(r===0?'#edf2ee':r%2?'#ffffff':'#fafbf9'),fg:t.fg?dwTone(t.fg,true):r===0?'#3d5747':'#26362d',bold:r===0||!!t.bold,align:t.align||'left'}; }
function dwStyle(s,r,c){ const t=dwCellTheme(s,r,c); return `background:${t.bg};color:${t.fg};font-weight:${t.bold?700:600};text-align:${t.align}`; }
function vDaily(){
  if(!navAllowed('daily')) return '';
  const sheets=dwSheets();
  if(DW.store!==APP.sid){ DW.store=APP.sid; DW.sheet=null; DW.a=DW.b=null; DW.search=''; DW.hits=[]; DW.target=null; clearTimeout(DW.searchTimer); }
  if(!sheets.includes(DW.sheet)){ DW.sheet=sheets.at(-1); DW.a=DW.b=null; }
  if(!canPay()) return `<div class="vh"><h1>일용직근무자</h1>${payToggle()}</div><div class="card empty"><b>개인정보가 포함된 원장이에요</b>위의 ‘금액 보기’를 눌러 열어주세요.</div>`;
  const s=dwSheet();
  if(!s) return '<div class="vh"><h1>일용직근무자</h1></div><div class="card empty">등록된 일용직 원장이 없어요.</div>';
  dwFind();
  const hitRows=new Set(DW.hits.filter(h=>h.key===DW.sheet).map(h=>h.r));
  return `<div class="vh dw-heading"><div><h1>일용직근무자</h1><div class="sub">월별 근무 기록 · 칸을 한 번 누르면 바로 수정할 수 있어요</div></div><span class="sp"></span>${payToggle()}</div>
    <div class="card dw-tools">${dwSearchBox()}<div class="dw-months" role="group" aria-label="월 선택">${sheets.map(k=>`<button type="button" data-dw-month="${esc(k)}" aria-pressed="${k===DW.sheet}" ${DW.busy?'disabled':''}>${esc(APP.D.pay[k].name)}</button>`).join('')}</div></div>
    <div class="card dw-toolbar">
    <button class="btn" data-dw="all">전체 선택</button><button class="btn" data-dw="clear">선택 해제</button><button class="btn" data-dw="add" ${DW.busy?'disabled':''}>+ 행 추가</button>
    <span class="sp"></span><span id="dw-status" role="status">${DW.busy?'저장 중…':DW.drafts.has(dwKey())?'수정됨 · 저장해 주세요':'저장됨'}</span>
    <button class="btn" data-dw="save" ${DW.busy?'disabled':''}>저장</button><button class="btn pri" data-dw="pdf" ${DW.busy||!dwRange()?'disabled':''}>선택 범위 PDF</button></div>
    <p class="help dw-help">클릭해서 바로 수정 · Tab 오른쪽 / Enter 아래쪽 · Shift와 함께 누르면 반대로 이동 · Alt+Enter 줄바꿈. 드래그 또는 Shift+클릭으로 PDF 범위를 선택하세요. 수정 후 ‘저장’을 누르세요.</p>
    <div class="dw-selection" id="dw-range" aria-live="polite">${dwRangeText()}</div>
    <div class="dw-scroll" tabindex="0" role="region" aria-label="일용직근무자 표"><table class="dw-grid" role="grid" aria-label="${esc(s.name)} 일용직근무자"><colgroup><col style="width:44px">${s.widths.map(w=>`<col style="width:${Math.max(76,Math.round(w*.92))}px">`).join('')}</colgroup>
    <thead><tr><th></th>${s.widths.map((_,c)=>`<th>${dwCol(c)}</th>`).join('')}</tr></thead><tbody>${s.rows.map((row,r)=>`<tr class="${hitRows.has(r)?'dw-search-hit':''} ${DW.target?.key===DW.sheet&&DW.target?.r===r?'dw-search-current':''}"><th>${r+1}</th>${s.widths.map((_,c)=>`<td data-dwr="${r}" data-dwc="${c}" style="${dwStyle(s,r,c)}" aria-selected="${dwContains(r,c)}" class="${dwContains(r,c)?'dw-selected':''} ${[2,3,7].includes(c)?'dw-compact':''}">${dwCellText(row,r,c,hitRows.has(r))}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`;
}
function dwContains(r,c){ const q=dwRange(); return !!q&&r>=q.r0&&r<=q.r1&&c>=q.c0&&c<=q.c1; }
function dwPaint(){
  $$('.dw-grid td').forEach(t=>{ const on=dwContains(+t.dataset.dwr,+t.dataset.dwc); t.classList.toggle('dw-selected',on); t.setAttribute('aria-selected',String(on)); });
  if($('#dw-range')) $('#dw-range').textContent=dwRangeText();
  const btn=$('[data-dw="pdf"]'); if(btn) btn.disabled=DW.busy||!dwRange();
}
function dwDirty(){ const el=$('#dw-status'); if(el) el.textContent='수정됨 · 저장해 주세요'; }
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
  const finish=cancel=>{ if(done) return; done=true; const v=cancel?old:input.value; if(v!==old){ dwDraft().rows[r][c]=v; dwDirty(); } input.remove(); td.textContent=v; };
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
  const key=dwKey(),s=DW.drafts.get(key); if(!s) return true;
  const sid=APP.sid,id=DW.sheet,data=dwClone(s); DW.busy=true; render();
  try{
    if(APP.be.putMany) await APP.be.putMany([{sid,kind:'pay',id,data}]); else await APP.be.put(sid,'pay',id,data);
    if(APP.sid===sid) APP.D.pay[id]=data;
    DW.drafts.delete(key); toast('일용직 원장을 저장했어요'); return true;
  }catch(e){ toast('저장하지 못했어요. 수정 내용은 유지돼요. 다시 저장해 주세요.'); return false; }
  finally{ DW.busy=false; render(); }
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
  const q={...dwRange()},s=dwClone(dwSheet()),name=`일용직근무자_${s.name}_${dwRangeText().replace(':','-')}.pdf`,store=APP.D.store.name;
  if(!await dwSave()) return;
  DW.busy=true; render();
  try{ const blob=await dwMakePdf(s,q,store),url=URL.createObjectURL(blob),a=document.createElement('a'); a.href=url; a.download=name; a.click(); setTimeout(()=>URL.revokeObjectURL(url),30000); toast('선택한 범위의 PDF를 내보냈어요'); }
  catch(e){ toast('PDF를 만들지 못했어요. 다시 시도해 주세요.'); }
  finally{ DW.busy=false; render(); }
}

document.addEventListener('input',e=>{ if(e.target.id!=='dw-search'||DW.busy) return; DW.search=e.target.value; clearTimeout(DW.searchTimer); if(!e.isComposing) DW.searchTimer=setTimeout(dwSearchRun,180); });
document.addEventListener('compositionend',e=>{ if(e.target.id==='dw-search'){ DW.search=e.target.value; clearTimeout(DW.searchTimer); DW.searchTimer=setTimeout(dwSearchRun,180); } });
document.addEventListener('keydown',e=>{ if(e.target.id==='dw-search'&&e.key==='Enter'&&!e.isComposing&&e.keyCode!==229){ e.preventDefault(); clearTimeout(DW.searchTimer); dwSearchRun(); } });
document.addEventListener('click',e=>{
  const month=e.target.closest('[data-dw-month]'),hit=e.target.closest('[data-dw-hit]');
  if((month||hit)&&canPay()&&navAllowed('daily')&&!DW.busy){ if(month) dwGoSheet(month.dataset.dwMonth); else { const h=DW.hits[+hit.dataset.dwHit]; if(h) dwGoSheet(h.key,h.r); } return; }
  const a=e.target.closest('[data-dw]')?.dataset.dw; if(!a||DW.busy||!canPay()||!navAllowed('daily')) return;
  if(a==='all'){ const s=dwSheet(); DW.a={r:0,c:0}; DW.b={r:s.rows.length-1,c:s.widths.length-1}; dwPaint(); }
  if(a==='clear'){ DW.a=DW.b=null; dwPaint(); }
  if(a==='add'){ const s=dwDraft(); s.rows.push(s.widths.map(()=>'')); render(); $('.dw-scroll').scrollTop=1e7; }
  if(a==='save') dwSave(); if(a==='pdf') dwExport();
});
document.addEventListener('dblclick',e=>{ const td=e.target.closest('.dw-grid td'); if(td) dwEdit(td); });
document.addEventListener('pointerdown',e=>{
  const td=e.target.closest('.dw-grid td'); if(!td||e.target.closest('.dw-editor')||e.button!==0||DW.busy) return;
  e.preventDefault(); const p={r:+td.dataset.dwr,c:+td.dataset.dwc}; if(!e.shiftKey||!DW.a) DW.a=p; DW.b=p; DW.drag={id:e.pointerId,x:e.clientX,y:e.clientY,startX:e.clientX,startY:e.clientY,moved:false,shift:e.shiftKey}; $('.dw-scroll').focus({preventScroll:true}); dwPaint(); requestAnimationFrame(dwDragFrame);
});
function dwDragFrame(){
  const d=DW.drag,box=$('.dw-scroll'); if(!d||!box) return;
  const rect=box.getBoundingClientRect(),speed=(p,lo,hi)=>p<lo+28?-Math.min(24,(lo+28-p)/2):p>hi-28?Math.min(24,(p-hi+28)/2):0;
  box.scrollBy(speed(d.x,rect.left,rect.right),speed(d.y,rect.top,rect.bottom));
  const td=document.elementFromPoint(Math.max(rect.left+46,Math.min(rect.right-2,d.x)),Math.max(rect.top+34,Math.min(rect.bottom-2,d.y)))?.closest('.dw-grid td');
  if(td){ const p={r:+td.dataset.dwr,c:+td.dataset.dwc}; if(p.r!==DW.b.r||p.c!==DW.b.c){ DW.b=p; dwPaint(); } }
  requestAnimationFrame(dwDragFrame);
}
document.addEventListener('pointermove',e=>{ if(DW.drag&&DW.drag.id===e.pointerId){ const d=DW.drag; d.x=e.clientX; d.y=e.clientY; if(Math.hypot(d.x-d.startX,d.y-d.startY)>5) d.moved=true; } });
document.addEventListener('pointerup',e=>{ const d=DW.drag; DW.drag=null; if(!d||d.id!==e.pointerId||d.moved||d.shift) return; const td=e.target.closest('.dw-grid td'); if(td) dwEdit(td); });
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
document.addEventListener('paste',e=>{
  if(!e.target.matches('.dw-scroll')||!DW.b||DW.busy||!canPay()) return;
  e.preventDefault(); const q=dwRange(),s=dwDraft(),rows=e.clipboardData.getData('text/plain').replace(/\r\n?/g,'\n').replace(/\n$/,'').split('\n').map(l=>l.split('\t'));
  rows.forEach((row,i)=>{ const r=q.r0+i; if(r>=s.rows.length) s.rows.push(s.widths.map(()=>'')); row.forEach((v,j)=>{ if(q.c0+j<s.widths.length) s.rows[r][q.c0+j]=v; }); }); render();
});
window.addEventListener('beforeunload',e=>{ if(DW.drafts.size){ e.preventDefault(); e.returnValue=''; } });
