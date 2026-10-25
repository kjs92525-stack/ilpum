// 스마트플레이스 예약 알림 → 예약 자동 처리. 알림 받는 안드로이드 폰의 MacroDroid 가 알림 글을 POST 로 보냄.
// - 새 예약 넣기 / 취소(테이블 칸에 "네이버취소") / 변경(날짜·시간·인원). 테이블 자동 지정은 8인 이하만(2026-10-18 사용자: 9인 이상도 예약은 다 써주고 테이블만 비움). 애매한 건 손대지 않고 기록만.
// - 자동 처리한 예약에는 auto 표시 → 예약 목록에 초록색으로 보이고 "확인"을 누르면 원래 색.
// - 비밀 값(TOKEN)은 배포할 때만 채움(저장소에는 자리표시). 서버 키는 Supabase 가 함수 안에만 넣어 줌.
import { createClient } from "npm:@supabase/supabase-js@2";
import { parseResText, ds } from "./parse.js";

const TOKEN = "__NOTIFY_TOKEN__";
const HQ_STORE = "0134d989-757a-4b60-9cb3-93245de2cac8";
const YC_STORE = "ad2ffdae-f76b-44cd-a6c6-58514c4e4638";
// 같은 폰에 여러 매장 알림이 옴 → 알림 글의 매장 이름으로 나눔 (본점·유천점만, 달서직영점 등 나머지는 무시)
const STORES = [{ re: /유천/, id: YC_STORE, name: "유천점" }, { re: /본점/, id: HQ_STORE, name: "본점" }];
const out = (status: number, body: unknown) => new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json; charset=utf-8" } });
const uid = () => Date.now().toString(36) + Math.random().toString(36).slice(2, 7);
const AUTO_MAX = 8;
const ppNum = (pp: string) => String(pp || "").split(/[+,]/).reduce((n, x) => n + (parseInt(x, 10) || 0), 0);
const toMin = (t: string) => { const m = String(t || "").match(/(\d{1,2}):(\d{2})/); return m ? +m[1] * 60 + +m[2] : null; };
const kstToday = () => { const d = new Date(Date.now() + 9 * 3600e3); return `${d.getUTCFullYear()}-${String(d.getUTCMonth() + 1).padStart(2, "0")}-${String(d.getUTCDate()).padStart(2, "0")}`; };
const isCxl = (x: any) => /취소/.test(x.tnote || "");
const md = (k: string) => { const [, m, d] = k.split("-"); return `${+m}/${+d}`; };

Deno.serve(async (req: Request) => {
  const u = new URL(req.url);
  const tok = u.searchParams.get("t") || req.headers.get("x-token") || "";
  if (TOKEN.startsWith("__") || tok !== TOKEN) return out(401, { error: "denied" });
  if (req.method === "GET") return out(200, { ok: true, msg: "연결됨" });
  const raw = await req.text();
  let text = raw; try { const j = JSON.parse(raw); text = [j.title, j.text, j.big, j.msg].filter(Boolean).join("\n") || raw; } catch (_) {}
  text = String(text || "").slice(0, 3000);
  const db = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!, { auth: { persistSession: false, autoRefreshToken: false } });
  let SNAME = "";
  const log = async (res: Record<string, unknown>) => {
    if (SNAME) res = { store: SNAME, ...res };
    try {
      const cur = (await db.from("sync_state").select("val").eq("key", "naver_log").maybeSingle()).data?.val || [];
      const row = { at: new Date().toISOString(), text: text.slice(0, 300), ...res };
      await db.from("sync_state").upsert({ key: "naver_log", val: [row, ...cur].slice(0, 300), updated_at: new Date().toISOString() });
    } catch (_) {}
    return out(200, res);
  };
  // "확정이 필요한 예약건이 있습니다" 재촉 알림은 몇 분마다 와서 기록을 덮어버림(2026-10-25) → 기록 없이 무시
  if (/확정이 필요한 예약건/.test(text) && !/님/.test(text)) return out(200, { skip: "확정 재촉 알림" });
  if (!/예약/.test(text) || !/(접수|신청|확정|취소|변경)/.test(text)) return log({ skip: "예약 알림 아님" });

  // 본점·유천점 알림만 처리 (2026-10-10 본점만 → 2026-10-25 사용자: 유천점도)
  const st = STORES.find((x) => x.re.test(text));
  if (!st) return log({ skip: "본점·유천점 알림 아님" });
  const SID = st.id; SNAME = st.name;
  const today = kstToday();
  const r: any = parseResText(text, today);

  const getDay = async (d: string) => (await db.from("res_days").select("id,rev,data").eq("store_id", SID).eq("id", d).maybeSingle()).data;
  // 그날 예약 목록을 고쳐서 저장(동시에 다른 기기가 저장하면 다시 받아 합침)
  const editDay = async (d: string, fn: (items: any[]) => void) => {
    for (let i = 0; i < 5; i++) {
      const row = await getDay(d);
      const items = JSON.parse(JSON.stringify(row?.data?.items || []));
      fn(items);
      const rev = (row?.rev || 0) + 1, body = { data: { items }, rev, updated_at: new Date().toISOString() };
      if (row) { const { data } = await db.from("res_days").update(body).eq("store_id", SID).eq("id", d).eq("rev", row.rev || 0).select("rev"); if (data && data.length) return true; }
      else { const { error } = await db.from("res_days").insert({ store_id: SID, id: d, ...body }); if (!error) return true; }
    }
    throw new Error("저장 충돌");
  };
  // 테이블 자동 지정(새 예약): 배치(sch_items cfg tables)에서 앞뒤 2시간 비어 있는 일반 테이블. 큰 자리(6인 이상)·룸은 아끼고, 창가 요청이면 본점 창가 먼저.
  const lay = (await db.from("sch_items").select("data").eq("store_id", SID).eq("kind", "cfg").eq("id", "tables").eq("deleted", false).maybeSingle()).data?.data || null;
  const seats: Record<string, number> = (lay && typeof lay.seats === "object" && lay.seats) || {};
  const allT: string[] = []; ((lay && lay.floors) || []).forEach((fl: any) => {
    if (fl.mode === "free") (fl.tables || []).forEach((t: any) => allT.push(String(t.id)));
    else { (fl.groups || []).forEach((g: any) => (g.cols || []).forEach((c: any) => (c || []).forEach((t: any) => { if (t != null) allT.push(String(t)); }))); ((fl.bar && fl.bar.row) || []).forEach((t: any) => { if (t != null) allT.push(String(t)); }); }
  });
  if (!allT.length && SID === HQ_STORE) for (let i = 1; i <= 53; i++) allT.push(String(i));   // 본점은 배치를 저장한 적이 없으면 예약 화면 기본 배치(1~53번)
  const BIG_OLD = ["6", "7", "8", "9", "10", "42", "43", "44", "45", "51", "52", "53", "29", "30", "31", "32", "33", "34"];
  const PREF = ["12", "13", "14", "16", "17", "18", "2", "3", "4", "21", "22", "25", "26", "27"];
  const WINDOW = ["1", "2", "3", "4", "5", "36", "37", "38", "39", "40", "41"];
  const isBig = (t: string) => Object.keys(seats).length ? (seats[t] || 0) >= 6 : (SID === HQ_STORE && BIG_OLD.includes(t));
  const BIG8_OLD = [["29", "30"], ["31", "32"], ["33", "34"]];
  const capOf = (t: string) => seats[t] || (!Object.keys(seats).length && SID === HQ_STORE && BIG_OLD.includes(t) && !BIG8_OLD.flat().includes(t) ? 6 : 4);
  // 5~8명: 그 인원이 앉는 자리(6인석, 8인석 짝, 룸) 중 남는 의자가 가장 적은 것, 1층 먼저. 없으면 비워 둠(직접 지정)
  const pickGroup = (items: any[], time: string, n: number): string[] => {
    const m = toMin(time); if (m == null || !allT.length) return [];
    const busy = new Set<string>(); items.forEach((x: any) => { if (x.deleted || isCxl(x)) return; const xm = toMin(x.time); if (xm != null && Math.abs(xm - m) < 120) (x.tables || []).forEach((t: string) => busy.add(String(t))); });
    const all = [...new Set(allT)], free = (t: string) => !busy.has(t);
    const cands: { ts: string[]; cap: number; room: boolean }[] = [];
    all.filter((t) => !/^R/i.test(t) && free(t)).forEach((t) => { const c = capOf(t); if (c >= n) cands.push({ ts: [t], cap: c, room: false }); });
    if (!Object.keys(seats).length && SID === HQ_STORE) BIG8_OLD.forEach((p) => { if (p.every((t) => all.includes(t) && free(t))) cands.push({ ts: p, cap: 8, room: false }); });
    const rooms: Record<string, string[]> = {}; all.forEach((t) => { const r = /^R(\d+)-\d+$/i.exec(t); if (r) (rooms[r[1]] = rooms[r[1]] || []).push(t); });
    Object.values(rooms).forEach((ts) => { if (ts.every(free)) { const c = ts.reduce((a, t) => a + capOf(t), 0); if (c >= n) cands.push({ ts, cap: c, room: true }); } });
    all.filter((t) => /^R\d+$/i.test(t) && free(t)).forEach((t) => { const c = seats[t] || 8; if (c >= n) cands.push({ ts: [t], cap: c, room: true }); });
    const num = (t: string) => (/^\d+$/.test(t) ? +t : 999);
    const score = (x: any) => (x.cap - n) * 10 + (x.room ? 25 : 0) + (num(x.ts[0]) > 34 && num(x.ts[0]) < 999 ? 5 : 0);
    cands.sort((a, b) => score(a) - score(b) || num(a.ts[0]) - num(b.ts[0]));
    return cands[0]?.ts || [];
  };
  const pickTable = (items: any[], time: string, req: string) => {
    const m = toMin(time); if (m == null || !allT.length) return "";
    const busy = new Set<string>(); items.forEach((x: any) => { if (x.deleted || isCxl(x)) return; const xm = toMin(x.time); if (xm != null && Math.abs(xm - m) < 120) (x.tables || []).forEach((t: string) => busy.add(String(t))); });
    const free = [...new Set(allT)].filter((t) => !busy.has(t) && !/^R/i.test(t) && !isBig(t));
    const win = /창가|창문|창쪽|창 쪽/.test(req) && SID === HQ_STORE ? free.filter((t) => WINDOW.includes(t)) : [];
    const num = (t: string) => (/^\d+$/.test(t) ? +t : 999);
    // 본점 주로 쓰는 순서(사용자 지정 2026-10-11): 1층 12~14 → 16~18 → 2~4 → 21~22 → 25~27, 그다음 나머지 1층(창가는 뒤로) → 2층
    const rank = (t: string) => { if (SID !== HQ_STORE) return num(t); const i = PREF.indexOf(t); if (i >= 0) return i; return 100 + (num(t) > 34 ? 1000 : 0) + (WINDOW.includes(t) ? 500 : 0) + num(t); };
    return (win.length ? win.sort((a, b) => rank(a) - rank(b)) : free.sort((a, b) => rank(a) - rank(b)))[0] || "";
  };
  const lbl = (d: string, x: any) => `${md(d)} ${x.time} ${x.name} ${x.pp}명`;
  try {
    if (r.cancel || r.change) {
      const from = ds(new Date(new Date(today + "T00:00").getTime() - 864e5));
      const rows = (await db.from("res_days").select("id,data").eq("store_id", SID).gte("id", from)).data || [];
      let cs: any[] = []; rows.forEach((row: any) => (row.data?.items || []).forEach((x: any) => { if (!x.deleted && r.name && x.name === r.name) cs.push({ d: row.id, x }); }));
            if (r.cancel) {
        let pick = cs.filter((c) => !isCxl(c.x)); if (r.date) pick = pick.filter((c) => c.d === r.date); if (r.time && pick.length > 1) pick = pick.filter((c) => c.x.time === r.time);
        if (!pick.length) return log({ cancel: cs.some((c) => isCxl(c.x)) ? "이미 취소돼 있음" : "취소할 예약 못 찾음", name: r.name, date: r.date });
        if (pick.length > 1) return log({ cancel: "같은 이름 여러 건 — 직접 처리", name: r.name });
        const c = pick[0];
        await editDay(c.d, (items) => { const it = items.find((y) => y.id === c.x.id); if (it) { it.tnote = ((it.tnote || "").replace(/(네이버)?취소/g, "").trim() + " 네이버취소").trim(); it.auto = "cxl"; it.u = Date.now(); } });
        return log({ ok: true, cancel: "취소 처리", item: lbl(c.d, c.x) });
      }
      // 변경
      const live = cs.filter((c) => !isCxl(c.x));
      const same = live.find((c) => c.d === (r.date || c.d) && c.x.time === (r.time || c.x.time) && (!r.pp || c.x.pp === r.pp));
      if (same) return log({ change: "이미 반영됨", item: lbl(same.d, same.x) });
      if (!live.length) return log({ change: "바꿀 예약 못 찾음", name: r.name });
      if (live.length > 1) return log({ change: "같은 이름 여러 건 — 직접 처리", name: r.name });
      const c = live[0];
      const nd = r.date || c.d, nt = r.time || c.x.time;
      const nx: any = { ...c.x, time: nt, auto: "chg", u: Date.now() }; if (r.pp) nx.pp = r.pp; if (r.req) nx.req = r.req;
      // 원래 테이블이 새 시간에 차 있으면 비움
      const nrow = await getDay(nd); const m = toMin(nt)!;
      const busy = new Set<string>(); (nrow?.data?.items || []).forEach((x: any) => { if (x.deleted || isCxl(x) || x.id === c.x.id) return; const xm = toMin(x.time); if (xm != null && Math.abs(xm - m) < 120) (x.tables || []).forEach((t: string) => busy.add(t)); });
      if ((nx.tables || []).some((t: string) => busy.has(t))) nx.tables = [];
      if (nd !== c.d) {
        await editDay(c.d, (items) => { const it = items.find((y) => y.id === c.x.id); if (it) { it.deleted = true; it.u = Date.now(); } });
        nx.id = uid(); delete nx.deleted; await editDay(nd, (items) => { items.push(nx); });
      } else await editDay(nd, (items) => { const i = items.findIndex((y) => y.id === c.x.id); if (i >= 0) items[i] = nx; });
      return log({ ok: true, change: "변경", from: lbl(c.d, c.x), to: lbl(nd, nx) });
    }
    // 새 예약
    if (!/(접수|신청|확정)/.test(text)) return log({ skip: "새 예약 알림 아님" });
    if (!r.date || !r.time || !r.name) return log({ skip: "날짜·시간·이름을 못 읽음", r });
    if (!r.pp) return log({ skip: "인원을 못 읽음 — 직접 입력", r });
    const day = await getDay(r.date);
    const dupe = (day?.data?.items || []).find((x: any) => !x.deleted && !isCxl(x) && x.name === r.name && x.time === r.time);
    if (dupe) return log({ skip: "이미 있는 예약", item: lbl(r.date, dupe) });
    const it: any = { id: uid(), c: today, u: Date.now(), name: r.name, time: r.time, pp: r.pp, tables: [], tnote: "", phone: r.phone || "", req: r.req || "", done: false, auto: "new" };
    await editDay(r.date, (items) => { if (ppNum(r.pp) > AUTO_MAX) it.tables = []; else if (ppNum(r.pp) > 4) it.tables = pickGroup(items, r.time, ppNum(r.pp)); else { const t = pickTable(items, r.time, r.req || ""); it.tables = t ? [t] : []; } items.push(it); });
    return log({ ok: true, add: lbl(r.date, it) });
  } catch (e) {
    return log({ error: String((e as Error).message || e) });
  }
});
