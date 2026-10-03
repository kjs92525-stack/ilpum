// 예전 서버(예약·근무표) → 새 서버 본점 자동 연동. pg_cron 이 5분마다 부름. 읽기만 하는 예전 서버 공개 키로 읽고, 새 서버에는 서비스 키로 합쳐 넣는다.
// - 예전 서버는 "바뀐 것만" 받는다(rev 비교) → 전송량 최소
// - 새 서버에서 사람이 고친 줄은 DB 함수(sync_merge_*)가 덮어쓰지 않는다
import { createClient } from "npm:@supabase/supabase-js@2";
import MIG from "./mig.ts";

const OLD_URL = "https://fmzpmekypmjuydgxpnlu.supabase.co";
const OLD_KEY = "__OLD_KEY__";      // 예전 서버 공개(anon) 키 — 배포할 때만 채움(저장소에는 안 올림)
const TOKEN = "__SYNC_TOKEN__";     // 부르는 쪽(pg_cron)과 같은 비밀 값 — 배포할 때만 채움
const MAX_DAYS_PER_RUN = 60;
const HQ_STORE = "0134d989-757a-4b60-9cb3-93245de2cac8";   // 본점 (예전 서버 자료는 본점 것)

const out = (status: number, body: unknown) => new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });
const oldGet = async (path: string) => {
  const r = await fetch(OLD_URL + path, { headers: { apikey: OLD_KEY, Authorization: "Bearer " + OLD_KEY } });
  if (!r.ok) throw new Error(`예전 서버 ${r.status}: ${(await r.text()).slice(0, 120)}`);
  return r.json();
};

Deno.serve(async (req: Request) => {
  if (req.headers.get("x-sync-token") !== TOKEN || TOKEN.startsWith("__")) return out(401, { error: "denied" });
  const url = Deno.env.get("SUPABASE_URL")!, svc = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;
  const db = createClient(url, svc, { auth: { persistSession: false, autoRefreshToken: false } });
  const getState = async (key: string) => (await db.from("sync_state").select("val").eq("key", key).maybeSingle()).data?.val ?? null;
  const setState = (key: string, val: unknown) => db.from("sync_state").upsert({ key, val, updated_at: new Date().toISOString() });
  const dry = new URL(req.url).searchParams.get("dry") === "1";
  const log: Record<string, unknown> = { at: new Date().toISOString(), dry };
  try {
    const en = await getState("enabled"); if (en && en.v === false) { return out(200, { skipped: "꺼져 있어요" }); }
    const st = (await getState("revs")) || { sched: null, days: {} };

    // 1) 근무표: rev 가 바뀌었을 때만 통째로 받아 변환 후 합침
    const sRev = await oldGet("/rest/v1/schedule_state?id=eq.main&select=rev");
    const rev = sRev?.[0]?.rev ?? null;
    if (rev !== null && rev !== st.sched) {
      const sRow = await oldGet("/rest/v1/schedule_state?id=eq.main&select=data,rev");
      const data = sRow?.[0]?.data;
      if (data && Array.isArray(data.staff)) {
        const pos = (await db.from("sch_items").select("data").eq("store_id", HQ_STORE).eq("kind", "cfg").eq("id", "positions").eq("deleted", false).limit(1)).data?.[0]?.data || [];
        const conv = MIG.convertSchedule(data, pos);
        const rows: unknown[] = [];
        for (const kind of ["staff", "rule", "dc", "spot", "aw", "pay"]) for (const [id, d] of Object.entries(conv.items[kind])) rows.push({ kind, id, data: d, deleted: false });
        if (conv.added > 0) rows.push({ kind: "cfg", id: "positions", data: conv.positions, deleted: false });
        log.schedRows = rows.length;
        if (!dry) {
          const r = await db.rpc("sync_merge_items", { p_rows: rows, p_prune: true });
          if (r.error) throw new Error("근무표 합치기: " + r.error.message);
          log.sched = r.data; st.sched = rev;
        }
      } else log.sched = "예전 근무표가 비어 있어요(건너뜀)";
    }

    // 2) 예약: 날짜별 rev 만 먼저 받아 바뀐 날짜만 가져옴
    // 최근 날짜부터, 1000개씩 끝까지 넘겨 받음 (자료가 많아져도 최신 예약이 빠지지 않게)
    const list: { id: string; rev: number }[] = [];
    for (let off = 0; off < 20000; off += 1000) {
      const page = await oldGet(`/rest/v1/reservations_day?select=id,rev&order=id.desc&limit=1000&offset=${off}`);
      list.push(...page); if (page.length < 1000) break;
    }
    const changed = list.filter((x) => /^\d{4}-\d{2}-\d{2}$/.test(x.id) && st.days[x.id] !== x.rev).slice(0, MAX_DAYS_PER_RUN);
    log.daysChanged = changed.length;
    for (let i = 0; i < changed.length; i += 20) {
      const part = changed.slice(i, i + 20);
      const rows = await oldGet(`/rest/v1/reservations_day?select=id,data,rev&id=in.(${part.map((x) => x.id).join(",")})`);
      if (!dry) {
        const r = await db.rpc("sync_merge_resdays", { p_rows: rows });
        if (r.error) throw new Error("예약 합치기: " + r.error.message);
        part.forEach((x) => (st.days[x.id] = x.rev));
      }
    }
    if (!dry) { await setState("revs", st); log.ok = true; await setState("last_run", log); }
    return out(200, log);
  } catch (e) {
    log.error = String((e as Error).message || e);
    if (!dry) await setState("last_run", log);
    return out(200, log);   // 실패해도 200 (다음 5분에 다시 시도). 상태는 sync_state.last_run 에 남음
  }
});
