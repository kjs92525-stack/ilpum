/* ================= 카톡용 사진 (캔버스로 직접 그림 · 금액은 절대 안 들어감) ================= */
const IMG_FONT='"Pretendard Variable",Pretendard,"Apple SD Gothic Neo","Malgun Gothic","Noto Sans KR",sans-serif';
function mkCanvas(W,H,sc){ const c=document.createElement('canvas'); c.width=Math.ceil(W*sc); c.height=Math.ceil(H*sc); const g=c.getContext('2d'); g.scale(sc,sc); g.fillStyle='#fff'; g.fillRect(0,0,W,H); return {c,g}; }
function rr(g,x,y,w,h,r){ g.beginPath(); g.moveTo(x+r,y); g.arcTo(x+w,y,x+w,y+h,r); g.arcTo(x+w,y+h,x,y+h,r); g.arcTo(x,y+h,x,y,r); g.arcTo(x,y,x+w,y,r); g.closePath(); }
const scratch=()=>mkCanvas(10,10,1).g;
// 이름들을 폭에 맞춰 줄바꿈하며 배치
function flow(g,items,x,y,maxW,fs,lh,gap){
  let cx=x, cy=y; const ops=[]; const sf=Math.max(9,Math.round(fs*.66));
  items.forEach(it=>{ g.font=`${it.b?800:600} ${fs}px ${IMG_FONT}`; const w1=g.measureText(it.t).width; let w2=0;
    if(it.s){ g.font=`600 ${sf}px ${IMG_FONT}`; w2=g.measureText(it.s).width+2; }
    const w=w1+w2; if(cx>x&&cx+w>x+maxW){ cx=x; cy+=lh; } ops.push({it,x:cx,y:cy,w1,fs,sf}); cx+=w+gap; });
  return {ops,h:(cy-y)+lh};
}
function paintFlow(g,f){ f.ops.forEach(o=>{ g.font=`${o.it.b?800:600} ${o.fs}px ${IMG_FONT}`; g.fillStyle=o.it.c||'#111'; g.fillText(o.it.t,o.x,o.y+o.fs*.9);
  if(o.it.s){ g.font=`600 ${o.sf}px ${IMG_FONT}`; g.fillStyle=o.it.sc||'#8A6A3A'; g.fillText(o.it.s,o.x+o.w1+2,o.y+o.fs*.9); } }); }
function imgItem(x,st,color){ return {t:x.name,s:shLbl(x.sh,st),c:x.type==='spot'?'#B8621B':(color||'#111'),b:x.type==='spot'}; }
async function loadFonts(){ try{ if(document.fonts){ await Promise.race([Promise.all([document.fonts.load(`600 20px ${IMG_FONT}`),document.fonts.load(`800 20px ${IMG_FONT}`)]),new Promise(r=>setTimeout(r,1200))]); } }catch(e){} }

/* ---------- 하루 ---------- */
function drawDay(key){
  const D=APP.D, st=D.store, R=resolve(D,pd(key)), d=pd(key); const W=720, P=30, sc=2;
  const rows=D.positions.map(p=>({p,items:R.list.filter(x=>x.pos===p.name).map(x=>imgItem(x,st))})).filter(r=>r.items.length);
  const g0=scratch(), labelW=128, fs=32, lh=46, pad=16;
  const laid=rows.map(r=>({r,f:flow(g0,r.items,0,0,W-2*P-labelW-26,fs,lh,24)}));
  const bodyH=rows.length?laid.reduce((a,l)=>a+l.f.h+pad*2,0):120, top=P+134, H=top+bodyH+P+8;
  const {c,g}=mkCanvas(W,H,sc); g.textBaseline='alphabetic';
  g.font=`600 20px ${IMG_FONT}`; g.fillStyle='#777'; g.fillText('일품집 근무표',P,P+18); g.textAlign='right'; g.fillText(`${d.getFullYear()}.${d.getMonth()+1}.${d.getDate()}`,W-P,P+18); g.textAlign='left';
  g.font=`800 54px ${IMG_FONT}`; g.fillStyle='#111'; g.fillText(`${d.getMonth()+1}월 ${d.getDate()}일 (${DOW[d.getDay()]})`,P,P+78);
  g.font=`600 22px ${IMG_FONT}`; g.fillStyle='#777'; g.fillText(`${st.name} · 근무 ${R.list.length}명`,P,P+110);
  rr(g,P,top,W-2*P,bodyH,14); g.lineWidth=3; g.strokeStyle='#555'; g.stroke();
  if(!rows.length){ g.font=`600 28px ${IMG_FONT}`; g.fillStyle='#888'; g.textAlign='center'; g.fillText('근무자가 없어요',W/2,top+70); g.textAlign='left'; }
  let y=top; laid.forEach((l,i)=>{ const h=l.f.h+pad*2;
    g.save(); rr(g,P,top,W-2*P,bodyH,14); g.clip(); g.fillStyle=l.r.p.color; g.fillRect(P,y,10,h); g.restore();
    if(i){ g.save(); g.setLineDash([7,6]); g.strokeStyle='#bbb'; g.lineWidth=2; g.beginPath(); g.moveTo(P+14,y); g.lineTo(W-P-14,y); g.stroke(); g.restore(); }
    g.font=`800 28px ${IMG_FONT}`; g.fillStyle=l.r.p.color; g.fillText(l.r.p.name,P+26,y+pad+fs*.9);
    const f=flow(g,l.r.items,P+26+labelW,y+pad,W-2*P-labelW-26-16,fs,lh,24); paintFlow(g,f); y+=h; });
  return c;
}

/* ---------- 한 주 ---------- */
function drawWeek(wk){
  const D=APP.D, st=D.store, ws=pd(wk), rules=rulesSorted(D); const P=24, PC=94, CW=168, W=P*2+PC+CW*7, sc=2;
  const days=[...Array(7)].map((_,i)=>{ const d=addDays(ws,i); return {d,R:resolve(D,d,{rules,quiet:true})}; });
  const g0=scratch(); const fs=19, lh=27;
  const pos=D.positions.filter(p=>days.some(x=>x.R.list.some(z=>z.pos===p.name)));
  const cellF=(list,cw)=>flow(g0,list.map(x=>imgItem(x,st,null)),0,0,cw-14,fs,lh,10);
  const rowsH=pos.map(p=>Math.max(...days.map(x=>cellF(x.R.list.filter(z=>z.pos===p.name),CW).h))+14);
  const offF=days.map(x=>flow(g0,x.R.offs.filter(o=>!o.missing).map(o=>({t:o.name,c:'#777'})),0,0,CW-14,16,22,8)); const offH=Math.max(...offF.map(f=>f.h),22)+14;
  const top=P+84, hh=58, H=top+hh+rowsH.reduce((a,b)=>a+b,0)+offH+P;
  const {c,g}=mkCanvas(W,H,sc); const we=addDays(ws,6);
  g.font=`800 40px ${IMG_FONT}`; g.fillStyle='#111'; g.fillText(`${ws.getMonth()+1}/${ws.getDate()}(${DOW[ws.getDay()]}) ~ ${we.getMonth()+1}/${we.getDate()}(${DOW[we.getDay()]})`,P,P+40);
  g.font=`600 20px ${IMG_FONT}`; g.fillStyle='#777'; g.fillText(`${st.name} 근무표`,P,P+70);
  const X=i=>P+PC+i*CW; g.lineWidth=1.5; g.strokeStyle='#999';
  days.forEach((x,i)=>{ const wd=x.d.getDay(); g.fillStyle=x.R.key===todayStr?'#FBEBDD':'#F3F0EB'; g.fillRect(X(i),top,CW,hh);
    g.font=`800 26px ${IMG_FONT}`; g.fillStyle=wd===0?'#C0392B':wd===6?'#3C5A86':'#111'; const ns=String(x.d.getDate()); g.fillText(ns,X(i)+10,top+38); const nw=g.measureText(ns).width; g.font=`700 18px ${IMG_FONT}`; g.fillText(DOW[wd],X(i)+10+nw+6,top+38); });
  g.fillStyle='#F3F0EB'; g.fillRect(P,top,PC,hh);
  let y=top+hh; pos.forEach((p,r)=>{ const h=rowsH[r]; g.fillStyle=p.color; g.fillRect(P,y,7,h); g.font=`800 20px ${IMG_FONT}`; g.fillText(p.name,P+18,y+34);
    days.forEach((x,i)=>{ const f=flow(g,x.R.list.filter(z=>z.pos===p.name).map(z=>imgItem(z,st,null)),X(i)+8,y+8,CW-14,fs,lh,10); paintFlow(g,f); }); y+=h; });
  g.fillStyle='#F7F5F2'; g.fillRect(P,y,PC+CW*7,offH); g.font=`800 18px ${IMG_FONT}`; g.fillStyle='#777'; g.fillText('휴무',P+18,y+30);
  days.forEach((x,i)=>{ const f=flow(g,x.R.offs.filter(o=>!o.missing).map(o=>({t:o.name,c:'#777'})),X(i)+8,y+8,CW-14,16,22,8); paintFlow(g,f); });
  // 격자
  g.strokeStyle='#bbb'; g.lineWidth=1.5; g.strokeRect(P,top,PC+CW*7,H-top-P); g.beginPath();
  for(let i=0;i<=7;i++){ g.moveTo(P+PC+i*CW,top); g.lineTo(P+PC+i*CW,H-P); } g.moveTo(P,top+hh); g.lineTo(P+PC+CW*7,top+hh);
  let yy=top+hh; rowsH.forEach(h=>{ yy+=h; g.moveTo(P,yy); g.lineTo(P+PC+CW*7,yy); }); g.stroke();
  return c;
}

/* ---------- 한 달 (전체 이름) ---------- */
function drawMonth(ym){
  const D=APP.D, st=D.store, [y,m0]=ym.split('-').map(Number), m=m0-1; const rules=rulesSorted(D), order=D.positions.map(p=>p.name);
  const first=new Date(y,m,1), last=new Date(y,m+1,0).getDate(), lead=(first.getDay()+6)%7; const P=22, CW=196, W=P*2+CW*7, sc=2;
  const g0=scratch(); const fs=16, lh=22; const cells=[]; const used=new Set();
  for(let day=1;day<=last;day++){ const d=new Date(y,m,day); const R=resolve(D,d,{rules,quiet:true});
    const list=R.list.slice().sort((a,b)=>order.indexOf(a.pos)-order.indexOf(b.pos)); list.forEach(x=>used.add(x.pos));
    const items=list.map(x=>imgItem(x,st,posColor(x.pos))); const offs=R.offs.filter(o=>!o.missing).map(o=>({t:o.name,c:'#888'}));
    const f=flow(g0,items,0,0,CW-14,fs,lh,9), of=offs.length?flow(g0,[{t:'휴',c:'#aaa'},...offs],0,0,CW-14,14,19,7):null;
    cells.push({day,d,items,offs,f,of,h:34+f.h+(of?of.h+6:0)+8}); }
  const weeks=[]; let row=Array(lead).fill(null); cells.forEach(c=>{ row.push(c); if(row.length===7){ weeks.push(row); row=[]; } }); if(row.length){ while(row.length<7) row.push(null); weeks.push(row); }
  const wh=weeks.map(w=>Math.max(80,...w.map(c=>c?c.h:0))); const top=P+96, hh=34, H=top+hh+wh.reduce((a,b)=>a+b,0)+P;
  const {c,g}=mkCanvas(W,H,sc);
  g.font=`800 42px ${IMG_FONT}`; g.fillStyle='#111'; g.fillText(`${y}년 ${m+1}월 근무표`,P,P+40); g.font=`600 20px ${IMG_FONT}`; g.fillStyle='#777'; g.fillText(st.name,P,P+70);
  let lx=W-P; [...used].reverse().forEach(n=>{ g.font=`700 16px ${IMG_FONT}`; const w=g.measureText(n).width+22; lx-=w+12; g.fillStyle=posColor(n); g.fillRect(lx,P+22,14,14); g.fillStyle='#333'; g.fillText(n,lx+20,P+35); });
  ['월','화','수','목','금','토','일'].forEach((n,i)=>{ g.fillStyle='#F3F0EB'; g.fillRect(P+i*CW,top,CW,hh); g.font=`800 18px ${IMG_FONT}`; g.fillStyle=i===6?'#C0392B':i===5?'#3C5A86':'#333'; g.textAlign='center'; g.fillText(n,P+i*CW+CW/2,top+24); g.textAlign='left'; });
  let y0=top+hh; weeks.forEach((w,wi)=>{ w.forEach((cell,i)=>{ if(!cell) { g.fillStyle='#FAF9F7'; g.fillRect(P+i*CW,y0,CW,wh[wi]); return; }
      const x=P+i*CW, wd=cell.d.getDay(); g.font=`800 22px ${IMG_FONT}`; g.fillStyle=wd===0?'#C0392B':wd===6?'#3C5A86':'#111'; g.fillText(String(cell.day),x+8,y0+26);
      const f=flow(g,cell.items,x+8,y0+34,CW-14,fs,lh,9); paintFlow(g,f);
      if(cell.of){ const f2=flow(g,[{t:'휴',c:'#aaa'},...cell.offs],x+8,y0+34+f.h+4,CW-14,14,19,7); paintFlow(g,f2); } });
    y0+=wh[wi]; });
  g.strokeStyle='#bbb'; g.lineWidth=1.5; g.strokeRect(P,top,CW*7,H-top-P); g.beginPath();
  for(let i=1;i<7;i++){ g.moveTo(P+i*CW,top); g.lineTo(P+i*CW,H-P); } let yy=top+hh; g.moveTo(P,yy); g.lineTo(P+CW*7,yy); wh.forEach(h=>{ yy+=h; g.moveTo(P,yy); g.lineTo(P+CW*7,yy); }); g.stroke();
  return c;
}

/* ---------- 내 근무 (이번 주 + 다음 주) ---------- */
function drawMe(sid){
  const D=APP.D, st=D.store, s=D.staff[sid]; const W=640, P=28, sc=2, rowH=62;
  const ws=weekStart(new Date()); const rows=[];
  for(let i=0;i<14;i++){ const d=addDays(ws,i), R=resolve(D,d); const x=R.list.find(z=>z.sid===sid), o=R.offs.find(z=>z.sid===sid);
    let txt='휴무', sub='', on=false; if(x){ on=true; const [a,b]=spanOf(st,x.sh); txt=`${pad(Math.floor(a/60))}:${pad(a%60)} – ${pad(Math.floor(b/60))}:${pad(b%60)}`; sub=x.pos; } else if(o&&o.reason!=='고정휴무'&&o.reason!=='주간휴무'&&!o.missing) txt='휴무 ('+o.reason+')';
    rows.push({d,txt,sub,on,pos:x&&x.pos}); }
  const H=P+96+rows.length*rowH+14*0+40+P;
  const {c,g}=mkCanvas(W,H,sc);
  g.font=`600 20px ${IMG_FONT}`; g.fillStyle='#777'; g.fillText(`${st.name} 근무표`,P,P+18);
  g.font=`800 44px ${IMG_FONT}`; g.fillStyle='#111'; g.fillText(`${s?s.name:''}님 근무`,P,P+70);
  let y=P+96;
  rows.forEach((r,i)=>{ if(i===7){ y+=14; }
    const wd=r.d.getDay(); g.fillStyle=r.d.toDateString()===new Date().toDateString()?'#FBEBDD':(r.on?'#fff':'#F7F5F2'); rr(g,P,y,W-2*P,rowH-8,12); g.fill(); g.strokeStyle='#ddd'; g.lineWidth=1.5; g.stroke();
    g.font=`800 26px ${IMG_FONT}`; g.fillStyle=wd===0?'#C0392B':wd===6?'#3C5A86':'#111'; const ds1=`${r.d.getMonth()+1}/${r.d.getDate()}`; g.fillText(ds1,P+16,y+34); const dw=g.measureText(ds1).width; g.font=`700 18px ${IMG_FONT}`; g.fillText(DOW[wd],P+16+dw+6,y+34);
    g.font=`${r.on?800:600} 26px ${IMG_FONT}`; g.fillStyle=r.on?'#111':'#999'; g.fillText(r.txt,P+140,y+34);
    if(r.sub){ g.font=`800 20px ${IMG_FONT}`; g.fillStyle=posColor(r.pos); g.textAlign='right'; g.fillText(r.sub,W-P-16,y+33); g.textAlign='left'; }
    y+=rowH; });
  return c;
}

/* ---------- 미리보기 · 보내기 ---------- */
let IMGS=null;
async function makeImage(type,k){
  toast('사진 만드는 중…'); await loadFonts();
  let c,name,title; const st=APP.D.store.name;
  try{
    if(type==='day'){ c=drawDay(k); const d=pd(k); name=`${st}_${d.getMonth()+1}월${d.getDate()}일.png`; title=`${d.getMonth()+1}월 ${d.getDate()}일 근무표`; }
    else if(type==='week'){ c=drawWeek(k); const d=pd(k); name=`${st}_${d.getMonth()+1}월${d.getDate()}일주.png`; title='이번 주 근무표'; }
    else if(type==='month'){ c=drawMonth(k); name=`${st}_${k}.png`; title=`${+k.split('-')[1]}월 근무표`; }
    else { c=drawMe(k); const s=APP.D.staff[k]; name=`${st}_${s?s.name:'내'}_근무.png`; title=`${s?s.name:''}님 근무`; }
  }catch(e){ console.error(e); return toast('사진을 만들지 못했어요'); }
  const blob=await new Promise(r=>c.toBlob(r,'image/png')); if(!blob) return toast('사진을 만들지 못했어요');
  let data=''; try{ data=c.toDataURL('image/png'); }catch(e){}
  const url=data||URL.createObjectURL(blob), file=new File([blob],name,{type:'image/png'}); IMGS={blob,url,name,title,file,canvas:c};
  const canShare=!!(navigator.canShare&&navigator.canShare({files:[file]})), canCopy=!!(navigator.clipboard&&window.ClipboardItem);
  const touchy=matchMedia('(pointer:coarse)').matches; const first=(canShare&&touchy)?'share':(canCopy?'copy':(canShare?'share':'save'));
  const btn=(a,t)=>`<button class="btn ${first===a?'pri grow':''}" data-a="img${a}">${t}</button>`;
  openDrawer(title,'카톡에 보낼 사진이에요 · 금액·휴무자는 들어가지 않아요',
    `${type==='day'?`<div class="row" style="flex-wrap:nowrap"><button class="btn sm" data-a="img" data-t="day" data-k="${ds(addDays(pd(k),-1))}">‹ 전날</button><input type="date" id="imgDate" value="${k}" class="grow" style="text-align:center"><button class="btn sm" data-a="img" data-t="day" data-k="${ds(addDays(pd(k),1))}">다음날 ›</button></div>`:''}
     <img src="${url}" alt="${esc(title)}" style="width:100%;border:1px solid var(--line);border-radius:10px;background:#fff">
     <p class="hint" style="margin:0">사진을 길게 누르면(컴퓨터는 마우스 오른쪽) 바로 저장·복사도 돼요.<br>${first==='copy'?'‘사진 복사’를 누른 뒤 카톡 채팅창에서 붙여넣기(Ctrl+V)하면 사진으로 올라가요.':first==='share'?'‘카톡·공유로 보내기’를 누르고 카카오톡을 고르세요.':'사진을 저장해서 카톡에 올리세요.'}</p>`,
    `${canShare?btn('share','카톡·공유로 보내기'):''}${canCopy?btn('copy','사진 복사'):''}${btn('save','사진 저장')}`, type!=='day'&&type!=='me');
  $('#toast').classList.remove('on');
  // 미리보기 창이 사진 주소를 막으면 캔버스를 그대로 보여줌
  const im=$('#dBody img'); if(im){ const swap=()=>{ c.style.cssText='width:100%;height:auto;border:1px solid var(--line);border-radius:10px;background:#fff;display:block'; im.replaceWith(c); };
    im.addEventListener('error',swap); if(im.complete&&im.naturalWidth===0) swap(); }
}
async function imgAct(a){
  if(!IMGS) return;
  if(a==='share'){ try{ await navigator.share({files:[IMGS.file],title:IMGS.title}); }catch(e){ if(e&&e.name!=='AbortError') toast('이 화면에서는 공유가 막혀 있어요. 사진을 길게 눌러 저장하세요'); } }
  else if(a==='copy'){ try{ await navigator.clipboard.write([new ClipboardItem({'image/png':IMGS.blob})]); toast('사진을 복사했어요 · 카톡에 붙여넣기(Ctrl+V)'); }catch(e){ toast('이 화면에서는 복사가 막혀 있어요. 사진을 길게 눌러 저장하세요'); } }
  else { try{ const a2=document.createElement('a'); a2.href=IMGS.url; a2.download=IMGS.name; document.body.appendChild(a2); a2.click(); a2.remove(); toast('사진을 저장했어요 · 안 되면 사진을 길게 눌러 저장하세요'); }catch(e){ toast('사진을 길게 눌러 저장하세요'); } }
}
