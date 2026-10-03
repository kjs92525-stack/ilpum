// 본사 전용 계정 만들기: 아이디 + 비밀번호로 계정을 만들고 매장·역할에 연결한다.
// - 호출자의 로그인 토큰으로 "본사(hq)" 인지 확인한다. 아니면 거부.
// - 계정 이메일은 아이디@ilpum.invalid (로그인 때 앱이 같은 규칙으로 변환)
// - service_role 키는 이 함수 안(Supabase 서버)에서만 쓰고 앱·저장소에는 없다.
import { createClient } from "npm:@supabase/supabase-js@2";

const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};
const out = (status: number, body: Record<string, unknown>) =>
  new Response(JSON.stringify(body), { status, headers: { ...CORS, "Content-Type": "application/json" } });

Deno.serve(async (req: Request) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: CORS });
  if (req.method !== "POST") return out(405, { error: "POST만 가능해요" });

  const url = Deno.env.get("SUPABASE_URL")!;
  const anon = Deno.env.get("SUPABASE_ANON_KEY")!;
  const svc = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;
  const jwt = (req.headers.get("Authorization") || "").replace(/^Bearer\s+/i, "");
  if (!jwt) return out(401, { error: "로그인이 필요해요" });

  // 1) 호출자 확인 — 본사 계정만
  const caller = createClient(url, anon, { global: { headers: { Authorization: `Bearer ${jwt}` } } });
  const { data: who, error: whoErr } = await caller.auth.getUser(jwt);
  if (whoErr || !who?.user) return out(401, { error: "로그인이 만료됐어요. 다시 로그인해 주세요" });
  const admin = createClient(url, svc, { auth: { persistSession: false, autoRefreshToken: false } });
  const { data: prof } = await admin.from("profiles").select("role,store_id").eq("user_id", who.user.id).maybeSingle();
  // 본사는 모든 매장에, 점주(franchise)는 자기 매장에 직원·매니저·발주 전용만 만들 수 있다
  const isHq = prof?.role === "hq";
  const isOwner = prof?.role === "franchise";
  if (!isHq && !isOwner) return out(403, { error: "계정은 본사나 점주만 만들 수 있어요" });

  // 2) 입력 확인
  let b: Record<string, unknown>;
  try { b = await req.json(); } catch { return out(400, { error: "요청 형식이 올바르지 않아요" }); }
  const id = String(b.id ?? "").trim().toLowerCase();
  const password = String(b.password ?? "");
  const store = String(b.store ?? "");
  const role = String(b.role ?? "");
  const pay = b.pay === true && role === "manager";   // 급여는 점주가 정한 매니저만. 직원·발주 전용은 절대 못 봄
  if (!/^[a-z0-9][a-z0-9._-]{2,19}$/.test(id)) return out(400, { error: "아이디는 영문 소문자·숫자·._- 로 3~20자예요" });
  if (password.length < 8 || password.length > 72) return out(400, { error: "비밀번호는 8자 이상이어야 해요" });
  if (!["owner", "manager", "staff", "order"].includes(role)) return out(400, { error: "역할이 올바르지 않아요" });
  if (!/^[0-9a-f-]{36}$/.test(store)) return out(400, { error: "매장을 골라 주세요" });
  if (!isHq && (store !== prof!.store_id || role === "owner")) return out(403, { error: "우리 매장의 직원·매니저·발주 전용 계정만 만들 수 있어요" });
  const { data: st } = await admin.from("stores").select("id,is_hq").eq("id", store).maybeSingle();
  if (!st) return out(400, { error: "없는 매장이에요" });
  if (role === "owner" && st.is_hq) return out(400, { error: "본점은 본사 계정을 써요. 가맹점에만 점주를 만들 수 있어요" });

  // 3) 계정 만들기 → 매장 연결 (연결이 실패하면 방금 만든 계정을 지움)
  const email = `${id}@ilpum.invalid`;
  const { data: created, error: cErr } = await admin.auth.admin.createUser({ email, password, email_confirm: true });
  if (cErr || !created?.user) {
    const dup = /already|registered|exists/i.test(cErr?.message || "");
    return out(dup ? 409 : 400, { error: dup ? "이미 있는 아이디예요" : "계정을 만들지 못했어요: " + (cErr?.message || "") });
  }
  const { error: lErr } = await caller.rpc("sch_add_member", { p_email: email, p_store: store, p_role: role, p_pay: pay });
  if (lErr) {
    await admin.auth.admin.deleteUser(created.user.id);
    return out(400, { error: "매장에 연결하지 못했어요: " + lErr.message });
  }
  return out(200, { ok: true, id, email });
});
