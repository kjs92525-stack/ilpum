// 매장 사용 중지 / 다시 사용 / (빈 매장만) 삭제 — 본사만. 사용 중지는 지우지 않고 자료를 그대로 둠.
// - 삭제: 이미 "사용 중지" 상태이고 자료(예약·근무표·발주·게시판·계정 등)가 하나도 없는 매장만. 매장 이름을 직접 쳐야 함. 자료가 있으면 거부.
// - 중지: 그 매장에만 연결된 점주·매니저·직원·발주 전용 계정의 로그인을 막고(정지), 매장 이름 뒤에 " (사용 중지)" 를 붙여 모든 화면 목록에서 한눈에 보이게 함
// - 다시 사용: 정지를 풀고 이름 뒤의 표시를 뗌
// - 본점·본사 계정은 건드리지 않음. 다른 매장에도 연결된 계정은 정지하지 않음.
import { createClient } from "npm:@supabase/supabase-js@2";

const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};
const out = (status: number, body: Record<string, unknown>) =>
  new Response(JSON.stringify(body), { status, headers: { ...CORS, "Content-Type": "application/json" } });
const MARK = " (사용 중지)";

Deno.serve(async (req: Request) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: CORS });
  if (req.method !== "POST") return out(405, { error: "POST만 가능해요" });
  const url = Deno.env.get("SUPABASE_URL")!, anon = Deno.env.get("SUPABASE_ANON_KEY")!, svc = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;
  const jwt = (req.headers.get("Authorization") || "").replace(/^Bearer\s+/i, "");
  if (!jwt) return out(401, { error: "로그인이 필요해요" });
  const caller = createClient(url, anon, { global: { headers: { Authorization: `Bearer ${jwt}` } } });
  const { data: who, error: whoErr } = await caller.auth.getUser(jwt);
  if (whoErr || !who?.user) return out(401, { error: "로그인이 만료됐어요. 다시 로그인해 주세요" });
  const admin = createClient(url, svc, { auth: { persistSession: false, autoRefreshToken: false } });
  const { data: me } = await admin.from("profiles").select("role").eq("user_id", who.user.id).maybeSingle();
  if (me?.role !== "hq") return out(403, { error: "매장 관리는 본사만 할 수 있어요" });

  let b: Record<string, unknown>;
  try { b = await req.json(); } catch { return out(400, { error: "요청 형식이 올바르지 않아요" }); }
  const store = String(b.store ?? ""), on = b.on !== false;      // on=true → 다시 사용, false → 사용 중지
  const action = String(b.action ?? "");
  if (action !== "setactive" && action !== "delete") return out(400, { error: "알 수 없는 요청이에요" });
  if (!/^[0-9a-f-]{36}$/.test(store)) return out(400, { error: "매장을 골라 주세요" });
  const { data: st } = await admin.from("stores").select("id,name,is_hq").eq("id", store).maybeSingle();
  if (!st) return out(404, { error: "없는 매장이에요" });
  if (st.is_hq) return out(403, { error: "본점은 사용 중지할 수 없어요" });

  if (action === "delete") {
    if (!String(st.name).endsWith(MARK)) return out(400, { error: "먼저 사용 중지를 해야 지울 수 있어요" });
    const base0 = String(st.name).slice(0, -MARK.length);
    if (String(b.confirm ?? "").trim() !== base0) return out(400, { error: "매장 이름을 정확히 입력해야 지워져요" });
    const checks: [string, string, (q: any) => any][] = [
      ["res_days", "예약", (q) => q], ["wh_items", "발주 품목", (q) => q], ["wh_orders", "발주 내역", (q) => q], ["board_msgs", "게시판 글", (q) => q],
      ["sch_members", "연결된 계정", (q) => q], ["profiles", "점주 계정", (q) => q], ["sch_items", "근무표 자료", (q) => q.neq("kind", "cfg")],
      ["orders", "발주(구)", (q) => q], ["reservations", "예약(구)", (q) => q], ["floors", "층", (q) => q], ["dining_tables", "테이블", (q) => q],
      ["positions", "포지션(구)", (q) => q], ["staff", "직원(구)", (q) => q], ["shifts", "근무(구)", (q) => q], ["staff_rates", "시급(구)", (q) => q],
      ["shift_pay", "급여(구)", (q) => q], ["payments", "정산", (q) => q], ["tickets", "문의", (q) => q], ["sales_reports", "매출", (q) => q],
      ["inspections", "점검", (q) => q], ["notice_reads", "공지 읽음", (q) => q],
    ];
    const left: string[] = [];
    for (const [tbl, label, f] of checks) {
      const { count, error } = await f(admin.from(tbl).select("*", { count: "exact", head: true }).eq("store_id", store));
      if (error) return out(500, { error: `${label} 확인 중 오류: ${error.message}` });
      if ((count || 0) > 0) left.push(`${label} ${count}건`);
    }
    if (left.length) return out(400, { error: "자료가 남아 있어서 앱에서는 지울 수 없어요 (" + left.join(", ") + "). 사용 중지로 두세요" });
    const { error: dErr } = await admin.from("stores").delete().eq("id", store);
    if (dErr) return out(400, { error: "지우지 못했어요: " + dErr.message });
    await admin.from("audit_log").insert({ actor: who.user.id, tbl: "stores", row_id: store, action: "delete", old: { name: st.name }, new: { by: who.user.email } });
    return out(200, { ok: true, deleted: base0 });
  }

  // 이 매장에 연결된 계정 (점주 + 매니저·직원·발주 전용)
  const [{ data: profs }, { data: mems }] = await Promise.all([
    admin.from("profiles").select("user_id,role,store_id"),
    admin.from("sch_members").select("user_id,store_id"),
  ]);
  const linked = new Map<string, Set<string>>();       // user → 연결된 매장들
  (profs || []).forEach((p: { user_id: string; store_id: string }) => { if (!linked.has(p.user_id)) linked.set(p.user_id, new Set()); linked.get(p.user_id)!.add(p.store_id); });
  (mems || []).forEach((m: { user_id: string; store_id: string }) => { if (!linked.has(m.user_id)) linked.set(m.user_id, new Set()); linked.get(m.user_id)!.add(m.store_id); });
  const hqIds = new Set((profs || []).filter((p: { role: string }) => p.role === "hq").map((p: { user_id: string }) => p.user_id));
  const targets = [...linked.entries()].filter(([uid, set]) => set.has(store) && set.size === 1 && !hqIds.has(uid)).map(([uid]) => uid);

  let changed = 0, failed = 0;
  for (const uid of targets) {
    const { error } = await admin.auth.admin.updateUserById(uid, { ban_duration: on ? "none" : "876000h" });
    if (error) failed++; else changed++;
  }
  const base = String(st.name).endsWith(MARK) ? String(st.name).slice(0, -MARK.length) : String(st.name);
  const name = on ? base : base + MARK;
  const { error: nErr } = await admin.from("stores").update({ name }).eq("id", store);
  if (nErr) return out(400, { error: "이름을 바꾸지 못했어요: " + nErr.message });
  await admin.from("audit_log").insert({ actor: who.user.id, tbl: "stores", row_id: store, action: on ? "reactivate" : "deactivate", new: { by: who.user.email, name, accounts: changed } });
  return out(200, { ok: true, name, accounts: changed, failed });
});
