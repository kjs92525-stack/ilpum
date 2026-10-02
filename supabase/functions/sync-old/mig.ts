// @ts-nocheck
/* ================= 예전 → 새 프로젝트 변환 (순수 함수, 서버 접속 없음) ================= */
const MIG = (() => {
  const pad = n => String(n).padStart(2, '0');
  const PALETTE = ['#3C5A86', '#2F6B3F', '#B8621B', '#8A2E2E', '#5B3F86', '#1F6F78', '#8A6A12', '#55605A', '#6B7A8F'];

  // 당일알바 메모 → 금액 / 출근시간 / 남길 메모
  //  '일급110,000' → 11만 · '13' → 13만 · '6.5' → 6.5만 · '일당백6.5' → 6.5만 + 메모 '일당백'
  //  '11-19시' → 11~19시 · '직원지원 / 11시 출근' → 11시 출근 + 메모 '직원지원'
  function parseAlbaMemo(memo, pm) {
    const m = String(memo || '').trim();
    let sh = pm ? { k: 'pm' } : null, pay = null, note = m, mm;
    if ((mm = m.match(/^일급\s*([\d,]+)$/))) { pay = parseInt(mm[1].replace(/,/g, ''), 10); note = ''; }
    else if (/^\d+(\.\d+)?$/.test(m)) { pay = Math.round(parseFloat(m) * 10000); note = ''; }
    else if ((mm = m.match(/^일당백\s*(\d+(\.\d+)?)$/))) { pay = Math.round(parseFloat(mm[1]) * 10000); note = '일당백'; }
    else if ((mm = m.match(/^(\d{1,2})-(\d{1,2})시$/))) { const a = +mm[1], b = +mm[2]; sh = { k: 't', s: pad(a) + ':00', e: b !== 22 ? pad(b) + ':00' : '' }; note = ''; }
    else if ((mm = m.match(/^(.*?)\s*\/\s*(\d{1,2})시\s*출근$/))) { sh = { k: 't', s: pad(+mm[2]) + ':00', e: '' }; note = mm[1].trim(); }
    return { sh, pay, note };
  }

  // 예전 schedule_state.data → 새 근무표 항목들 { staff, rule, dc, spot, aw, pay }
  function convertSchedule(old, existingPositions) {
    const out = { staff: {}, rule: {}, dc: {}, spot: {}, aw: {}, pay: {} };
    const usedPos = new Set();
    (old.staff || []).forEach((s, i) => {
      const x = { id: s.id, name: s.name, pos: s.pos, type: s.kind === 'fixed' ? 'weekly' : 'regular', off: (s.off || []).slice().sort(), active: true, order: i };
      usedPos.add(s.pos);
      if (s.wk) { x.wk = {}; Object.keys(s.wk).forEach(w => { const c = s.wk[w] || {}; if (c.sh) x.wk[w] = { sh: c.sh }; if (c.pay) out.pay['pat:' + s.id + ':' + w] = c.pay; }); if (!Object.keys(x.wk).length) delete x.wk; }
      out.staff[s.id] = x;
    });
    (old.rules || []).forEach(r => {
      if (!r || !r.id) return; const { pay, ...rest } = r; out.rule[r.id] = rest; if (pay) out.pay['rule:' + r.id] = pay; if (r.pos) usedPos.add(r.pos);
    });
    const dc = k => (out.dc[k] = out.dc[k] || {});
    Object.keys(old.dc || {}).forEach(k => { const v = old.dc[k] || {}; if (v.sh) dc(k).sh = v.sh; if (v.pay) out.pay['dc:' + k] = v.pay; });
    Object.keys(old.notes || {}).forEach(k => { if (old.notes[k]) dc(k).memo = old.notes[k]; });
    (old.ex || []).forEach(e => {
      if (!e || !e.date) return;
      if (e.type === '당일알바') {
        const p = parseAlbaMemo(e.memo, !!e.pm);
        const x = { id: e.id, date: e.date, name: e.name, pos: e.pos };
        const sh = e.sh || p.sh; if (sh) x.sh = sh; if (p.note) x.memo = p.note; usedPos.add(e.pos);
        out.spot[e.id] = x;
        const pay = e.pay || (p.pay ? { k: 'day', v: p.pay } : null); if (pay) out.pay['spot:' + e.id] = pay;
        return;
      }
      if (!e.staffId) return;
      const d = dc(e.date + '|' + e.staffId);
      if (e.type === '월차') d.st = 'annual'; else if (e.type === '휴무') d.st = 'off'; else if (e.type === '휴무지급') d.st = 'paidoff';
      else if (e.type === '추가근무') { d.st = 'extra'; if (e.pos) { d.pos = e.pos; usedPos.add(e.pos); } }
      else if (e.type === '근무변경') { if (e.pos) { d.pos = e.pos; usedPos.add(e.pos); } }
      else if (e.type === '오후출근') { if (!d.sh) d.sh = { k: 'pm' }; }
      if (e.memo && !d.memo) d.memo = e.memo;
    });
    Object.keys(old.aw || {}).forEach(w => { out.aw[w] = old.aw[w]; });
    // 새 근무표에 없는 포지션은 추가 (이름이 사라지지 않게)
    const pos = (existingPositions || []).map(p => ({ ...p }));
    const names = new Set(pos.map(p => p.name));
    [...usedPos].filter(n => n && !names.has(n)).forEach((n, i) => pos.push({ name: n, color: PALETTE[(pos.length + i) % PALETTE.length], req: [0, 0, 0, 0, 0, 0, 0] }));
    return { items: out, positions: pos, added: pos.length - (existingPositions || []).length };
  }

  // ----- 예약 -----
  const normTime = v => {
    const s = String(v || '').trim(); if (!s) return '';
    let m = s.match(/^(\d{1,2})\s*[:시.]\s*(\d{1,2})?\s*분?$/) || s.match(/^(\d{1,2})$/), h, mi;
    if (m) { h = +m[1]; mi = +(m[2] || 0); } else { m = s.match(/^(\d{3,4})$/); if (!m) return ''; h = +s.slice(0, -2); mi = +s.slice(-2); }
    if (h > 23 || mi > 59) return ''; return pad(h) + ':' + pad(mi);
  };
  const people = s => String(s || '').split(/[+,]/).reduce((a, x) => a + (parseInt(x, 10) || 0), 0);
  const isCxl = x => /취소/.test(x.tnote || '');
  // 같은 예약은 몇 번을 돌려도 같은 id가 되도록 (128비트 해시 → uuid 모양)
  function hash128(str) {
    let h1 = 1779033703, h2 = 3144134277, h3 = 1013904242, h4 = 2773480762;
    for (let i = 0, k; i < str.length; i++) { k = str.charCodeAt(i); h1 = h2 ^ Math.imul(h1 ^ k, 597399067); h2 = h3 ^ Math.imul(h2 ^ k, 2869860233); h3 = h4 ^ Math.imul(h3 ^ k, 951274213); h4 = h1 ^ Math.imul(h4 ^ k, 2716044179); }
    h1 = Math.imul(h3 ^ (h1 >>> 18), 597399067); h2 = Math.imul(h4 ^ (h2 >>> 22), 2869860233); h3 = Math.imul(h1 ^ (h3 >>> 17), 951274213); h4 = Math.imul(h2 ^ (h4 >>> 19), 2716044179);
    return [(h1 ^ h2 ^ h3 ^ h4) >>> 0, (h2 ^ h1) >>> 0, (h3 ^ h1) >>> 0, (h4 ^ h1) >>> 0];
  }
  function uuidFor(key) {
    const a = hash128(key), b = hash128(key + '#2'); const hex = [a[0], a[1], a[2], a[3]].map(n => n.toString(16).padStart(8, '0')).join('') + b[0].toString(16).padStart(8, '0');
    const h = hex.slice(0, 32).split(''); h[12] = '4'; h[16] = '89ab'[parseInt(h[16], 16) % 4];
    const s = h.join(''); return `${s.slice(0, 8)}-${s.slice(8, 12)}-${s.slice(12, 16)}-${s.slice(16, 20)}-${s.slice(20, 32)}`;
  }
  // rows: [{id:'2026-10-01', data:{items:[...]}}]
  function convertReservations(rows, storeId, opt) {
    opt = opt || {}; const out = [], stat = { days: 0, total: 0, deleted: 0, cancelled: 0, noTime: 0, noName: 0, noSize: 0, dup: 0 };
    const seen = new Set();
    (rows || []).forEach(row => {
      const date = row.id; if (!/^\d{4}-\d{2}-\d{2}$/.test(date)) return; stat.days++;
      ((row.data && row.data.items) || []).forEach(x => {
        stat.total++;
        if (x.deleted) { stat.deleted++; return; }
        const cx = isCxl(x); if (cx) { stat.cancelled++; if (!opt.withCancelled) return; }
        const t = normTime(x.time); if (!t) stat.noTime++;
        const size = people(x.pp); if (!size) stat.noSize++;
        const name = String(x.name || '').trim(); if (!name) stat.noName++;
        const tables = (x.tables || []).map(String);
        const notes = [];
        if (!t) notes.push('시간 미정');
        if (cx) notes.push('취소됨');
        if (x.req) notes.push(String(x.req).trim());
        if (x.tnote && !cx) notes.push('테이블: ' + String(x.tnote).trim());
        if (x.pp && !/^\d+$/.test(String(x.pp).trim())) notes.push('인원 ' + String(x.pp).trim());
        const id = uuidFor(date + '|' + x.id);
        if (seen.has(id)) { stat.dup++; return; } seen.add(id);
        out.push({ id, store_id: storeId, rdate: date, rtime: t || '00:00', name: name || '(이름 없음)', phone: x.phone ? String(x.phone).trim() : null,
          size: Math.max(1, size), table_no: tables.length ? tables.join(',') : null, note: notes.length ? notes.join(' / ') : null, arrived: !!x.done });
      });
    });
    stat.out = out.length; return { rows: out, stat };
  }
  return { convertSchedule, convertReservations, parseAlbaMemo, normTime, people, uuidFor };
})();
export default MIG;
