// 자동 생성 파일 — 고치지 말 것. 원본: src/reserve/reserve.html (tools/gen_notify_parse.py 가 빌드 때 복사)
const pad=(n)=>String(n).padStart(2,'0');
const ds=(d)=>`${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())}`;
function fmtPhone(v){
  const d=String(v||'').replace(/\D/g,''); if(!d) return String(v||'').trim();
  if(d.startsWith('02')){ if(d.length===9) return `02-${d.slice(2,5)}-${d.slice(5)}`; if(d.length===10) return `02-${d.slice(2,6)}-${d.slice(6)}`; }
  if(d.length===11) return `${d.slice(0,3)}-${d.slice(3,7)}-${d.slice(7)}`;
  if(d.length===10) return `${d.slice(0,3)}-${d.slice(3,6)}-${d.slice(6)}`;
  if(d.length===8) return `${d.slice(0,4)}-${d.slice(4)}`;
  if(d.length===7) return `${d.slice(0,3)}-${d.slice(3)}`;
  return d;
}

function parseResText(text, todayKey){
  const raw=String(text||'').replace(/\r/g,''); const out={date:'',time:'',pp:'',name:'',phone:'',req:'',cancel:false,change:false};
  if(!raw.trim()) return out;
  const today=todayKey?new Date(todayKey+'T00:00'):new Date(); today.setHours(0,0,0,0);
  const lines=raw.split('\n').map(l=>l.trim()).filter(Boolean)
    .filter(l=>!/(예약|주문|결제|승인)\s*번호|금액|결제|쿠폰|포인트|https?:\/\//.test(l));   // 번호·금액 줄은 무시 (전화·인원으로 잘못 읽지 않게)
  const body=lines.join('\n');
  const val=re=>{ for(const l of lines){ const m=l.match(re); if(m&&m[1]&&m[1].trim()) return m[1].trim(); } return ''; };
  const ph=body.match(/(?:^|[^\d])(01[016789])[\s.\-]?(\d{3,4})[\s.\-]?(\d{4})(?!\d)/) || body.match(/(?:^|[^\d])(0\d{1,2})[\s\-.](\d{3,4})[\s\-.](\d{4})(?!\d)/);
  if(ph) out.phone=fmtPhone(ph[1]+ph[2]+ph[3]);
  const noPh=ph?body.replace(ph[0],' '):body;
  const mk=(y,mo,d)=>{ const dt=new Date(y,mo-1,d); return (dt.getMonth()===mo-1&&dt.getDate()===d)?dt:null; };
  const near=(mo,d)=>{ let dt=mk(today.getFullYear(),mo,d); if(dt&&(dt-today)/864e5< -60) dt=mk(today.getFullYear()+1,mo,d); return dt; };
  let dt=null, m;
  if((m=noPh.match(/(20\d{2})\s*[.\-\/년]\s*(\d{1,2})\s*[.\-\/월]\s*(\d{1,2})/))) dt=mk(+m[1],+m[2],+m[3]);
  else if((m=noPh.match(/(\d{1,2})\s*월\s*(\d{1,2})\s*일/))) dt=near(+m[1],+m[2]);
  else if((m=noPh.match(/(?:^|[^\d.:])(\d{1,2})\s*[\/.]\s*(\d{1,2})(?=\s*\(|\s*[일월화수목금토]요일|\s|$)/m))&&+m[1]<=12) dt=near(+m[1],+m[2]);
  else if(/모레/.test(noPh)){ dt=new Date(today); dt.setDate(dt.getDate()+2); }
  else if(/내일/.test(noPh)){ dt=new Date(today); dt.setDate(dt.getDate()+1); }
  else if(/오늘|금일|당일/.test(noPh)) dt=new Date(today);
  else if((m=noPh.match(/(다음\s*주|담주)?\s*([일월화수목금토])요일/))){ const wd='일월화수목금토'.indexOf(m[2]), dow=today.getDay(); dt=new Date(today);
    if(m[1]) dt.setDate(dt.getDate()+(((1-dow+7)%7)||7)+((wd+6)%7)); else dt.setDate(dt.getDate()+(wd-dow+7)%7); }
  if(dt) out.date=ds(dt);
  const tm=noPh.match(/(오전|오후|낮|저녁|밤)?\s*(\d{1,2})\s*(?::\s*(\d{2})|시\s*(?:(\d{1,2})\s*분|(반))?)/);
  if(tm){ let h=+tm[2], mi=tm[3]!=null?+tm[3]:tm[4]!=null?+tm[4]:tm[5]?30:0; const ap=tm[1]||'';
    if(/오후|저녁|밤/.test(ap)&&h<12) h+=12; else if(!ap&&h>=1&&h<=9) h+=12;   // "6시" = 저녁 6시
    if(h<=23&&mi<=59) out.time=`${pad(h)}:${pad(mi)}`; }
  const ad=noPh.match(/(?:성인|어른|대인)\s*[:：]?\s*(\d{1,2})/), kd=noPh.match(/(?:아이|아동|어린이|소아|유아|초등학생|초등|미취학|애기|아기)\s*[:：]?\s*(\d{1,2})/);
  if(ad) out.pp=ad[1]+(kd&&+kd[1]?'+'+kd[1]:'');
  else { const pm=noPh.match(/(\d{1,2})\s*(?:명|인)(?!\s*석)/) || noPh.match(/인원\s*(?:수)?\s*[:：]?\s*(\d{1,2})/); if(pm) out.pp=pm[1]+(kd&&+kd[1]?'+'+kd[1]:''); }
  const STOP=/^(예약|예약자|예약자명|성함|이름|고객|고객명|인원|성인|어른|아이|오전|오후|저녁|오늘|내일|모레|요청|요청사항|메모|일시|이용|이용일시|예약일시|방문|확정|취소|안내|네이버|장어|일품집|본점|유천점|감사|감사합니다|부탁|부탁드려요|부탁드립니다|문의|연락처|전화|전화번호|코스|상품|상품명|룸|테이블|좌석|단체|가족|생일|예약금|입금|확인|주차|아기|의자|창가|금일|당일|입완|안녕하세요|새로운|접수|접수되었습니다|되었습니다|다음주|이번주|담주|명|가능|가능할까요|할게요|합니다|하고|싶어요|예약합니다)$/;
  let nm=val(/(?:예약자\s*(?:명|이름|정보)?|성함|이름|고객\s*명)\s*[:：]?\s*([가-힣]{2,5})/);
  if(nm&&STOP.test(nm)) nm='';
  if(!nm){ const n2=noPh.match(/([가-힣]{2,4})\s*님/); if(n2&&!STOP.test(n2[1])) nm=n2[1]; }
  if(!nm){ const n3=noPh.match(/(?:^|[^가-힣])([가-힣]{2,4}?)\s*(?:입니다|이에요|에요|예요|이요)(?![가-힣])/); if(n3&&!STOP.test(n3[1])) nm=n3[1]; }
  if(!nm){ for(const w of noPh.replace(/\[[^\]]*\]/g,' ').replace(/[^가-힣\s]/g,' ').split(/\s+/)){ if(w.length>=2&&w.length<=4&&!STOP.test(w)&&!/요일$|(시|분|명|인|월|일|반|요|다|까|고|서|에|로|은|는|이|가|을|를)$/.test(w)){ nm=w; break; } } }
  out.name=nm||'';
  { const LB=/^(?:고객\s*)?(?:요청\s*사항|요청|메모|비고|특이\s*사항|기타\s*사항|기타)\s*[:：]?\s*(.*)$/, OTHER=/^(?:예약자|이용|예약|인원|연락처|전화|상품|옵션|결제|방문|성함|이름)/;
    for(let i=0;i<lines.length;i++){ const m=lines[i].match(LB); if(!m) continue;
      let v=m[1].trim(); const more=[]; for(let j=i+1;j<lines.length&&!OTHER.test(lines[j])&&!LB.test(lines[j])&&!/^(새로운|접수|감사|일품집|\[)/.test(lines[j]);j++) more.push(lines[j]); v=[v,...more].filter(Boolean).join(' ');
      if(v&&!/^(없음|없습니다|-)$/.test(v)){ out.req=v.slice(0,500); break; } } }
  { const nb=out.req?body.split(out.req).join(' '):body;
    out.cancel=/취소(되었|됐|완료|하였|했|처리)|예약\s*취소/.test(nb);
    out.change=!out.cancel&&/변경(되었|됐|완료|하였|했|처리)|예약\s*변경/.test(nb); }
  return out;
}

export { parseResText, fmtPhone, ds };
