// 매장 사용 중지 / 다시 사용 (본사만). 지우지 않고 자료는 그대로 둠.
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
  if (String(b.action ?? "") !== "setactive") return out(400, { error: "알 수 없는 요청이에요" });
  if (!/^[0-9a-f-]{36}$/.test(store)) return out(400, { error: "매장을 골라 주세요" });
  const { data: st } = await admin.from("stores").select("id,name,is_hq").eq("id", store).maybeSingle();
  if (!st) return out(404, { error: "없는 매장이에요" });
  if (st.is_hq) return out(403, { error: "본점은 사용 중지할 수 없어요" });

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
