// 스마트플레이스 예약 알림 → 예약 자동 처리. 알림 받는 안드로이드 폰의 MacroDroid 가 알림 글을 POST 로 보냄.
// - 4인 이하만: 새 예약 넣기 / 취소(테이블 칸에 "네이버취소") / 변경(날짜·시간·인원). 5인 이상·애매한 건 손대지 않고 기록만.
// - 자동 처리한 예약에는 auto 표시 → 예약 목록에 보라색으로 보이고 "확인"을 누르면 원래 색.
// - 비밀 값(TOKEN)은 배포할 때만 채움(저장소에는 자리표시). 서버 키는 Supabase 가 함수 안에만 넣어 줌.
import { createClient } from "npm:@supabase/supabase-js@2";
import { parseResText, ds } from "./parse.js";

const TOKEN = "__NOTIFY_TOKEN__";
const HQ_STORE = "0134d989-757a-4b60-9cb3-93245de2cac8";
const out = (status: number, body: unknown) => new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json; charset=utf-8" } });
const uid = () => Date.now().toString(36) + Math.random().toString(36).slice(2, 7);
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
  const log = async (res: Record<string, unknown>) => {
    try {
      const cur = (await db.from("sync_state").select("val").eq("key", "naver_log").maybeSingle()).data?.val || [];
      const row = { at: new Date().toISOString(), text: text.slice(0, 300), ...res };
      await db.from("sync_state").upsert({ key: "naver_log", val: [row, ...cur].slice(0, 50), updated_at: new Date().toISOString() });
    } catch (_) {}
    return out(200, res);
  };
  if (!/예약/.test(text) || !/(접수|신청|확정|취소|변경)/.test(text)) return log({ skip: "예약 알림 아님" });

  // 지금은 본점 알림만 처리 (같은 폰에 유천점 알림도 옴 — 사용자 지시 2026-10-10)
  if (!/본점/.test(text)) return log({ skip: "본점 알림 아님" });
  const SID = HQ_STORE;
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
  const lbl = (d: string, x: any) => `${md(d)} ${x.time} ${x.name} ${x.pp}명`;
  try {
    if (r.cancel || r.change) {
      const from = ds(new Date(new Date(today + "T00:00").getTime() - 864e5));
      const rows = (await db.from("res_days").select("id,data").eq("store_id", SID).gte("id", from)).data || [];
      let cs: any[] = []; rows.forEach((row: any) => (row.data?.items || []).forEach((x: any) => { if (!x.deleted && r.name && x.name === r.name) cs.push({ d: row.id, x }); }));
      const big = (c: any) => ppNum(c.x.pp) > 4 || (r.change && ppNum(r.pp) > 4);
      if (r.cancel) {
        let pick = cs.filter((c) => !isCxl(c.x)); if (r.date) pick = pick.filter((c) => c.d === r.date); if (r.time && pick.length > 1) pick = pick.filter((c) => c.x.time === r.time);
        if (!pick.length) return log({ cancel: cs.some((c) => isCxl(c.x)) ? "이미 취소돼 있음" : "취소할 예약 못 찾음", name: r.name, date: r.date });
        if (pick.length > 1) return log({ cancel: "같은 이름 여러 건 — 직접 처리", name: r.name });
        if (big(pick[0])) return log({ cancel: "5인 이상 — 직접 처리", item: lbl(pick[0].d, pick[0].x) });
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
      const c = live[0]; if (big(c)) return log({ change: "5인 이상 — 직접 처리", item: lbl(c.d, c.x) });
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
    if (ppNum(r.pp) > 4) return log({ skip: "5인 이상 — 직접 입력", r });
    const day = await getDay(r.date);
    const dupe = (day?.data?.items || []).find((x: any) => !x.deleted && !isCxl(x) && x.name === r.name && x.time === r.time);
    if (dupe) return log({ skip: "이미 있는 예약", item: lbl(r.date, dupe) });
    const it = { id: uid(), c: today, u: Date.now(), name: r.name, time: r.time, pp: r.pp, tables: [], tnote: "", phone: r.phone || "", req: r.req || "", done: false, auto: "new" };
    await editDay(r.date, (items) => { items.push(it); });
    return log({ ok: true, add: lbl(r.date, it) });
  } catch (e) {
    return log({ error: String((e as Error).message || e) });
  }
});
