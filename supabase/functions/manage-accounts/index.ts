// 본사 전용 계정 관리: 목록 보기 · 비밀번호 바꾸기 · 삭제.
// - 호출자의 로그인 토큰으로 "본사(hq)" 인지 확인한다. 아니면 거부.
// - 본사 계정(hq)과 본인 계정은 바꾸거나 지울 수 없다 (잠기는 사고 방지).
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

  const caller = createClient(url, anon, { global: { headers: { Authorization: `Bearer ${jwt}` } } });
  const { data: who, error: whoErr } = await caller.auth.getUser(jwt);
  if (whoErr || !who?.user) return out(401, { error: "로그인이 만료됐어요. 다시 로그인해 주세요" });
  const admin = createClient(url, svc, { auth: { persistSession: false, autoRefreshToken: false } });
  const { data: me } = await admin.from("profiles").select("role,store_id").eq("user_id", who.user.id).maybeSingle();
  const isHq = me?.role === "hq", isOwner = me?.role === "franchise";
  if (!isHq && !isOwner) return out(403, { error: "계정 관리는 본사나 점주만 할 수 있어요" });
  const myStore: string | null = isOwner ? me!.store_id : null;   // 점주는 자기 매장의 직원·매니저·발주 전용만

  let b: Record<string, unknown>;
  try { b = await req.json(); } catch { return out(400, { error: "요청 형식이 올바르지 않아요" }); }
  const action = String(b.action ?? "");

  // ---- 목록 ----
  if (action === "list") {
    const users: { id: string; email: string; last: string | null; created: string; banned: boolean }[] = [];
    for (let page = 1; page <= 10; page++) {
      const { data, error } = await admin.auth.admin.listUsers({ page, perPage: 200 });
      if (error) return out(500, { error: "목록을 불러오지 못했어요: " + error.message });
      for (const u of data.users) users.push({ id: u.id, email: u.email || "", last: u.last_sign_in_at || null, created: u.created_at,
        banned: !!(u.banned_until && new Date(u.banned_until) > new Date()) });
      if (data.users.length < 200) break;
    }
    const [{ data: profs }, { data: mems }, { data: stores }] = await Promise.all([
      admin.from("profiles").select("user_id,store_id,role"),
      admin.from("sch_members").select("user_id,store_id,role,can_pay"),
      admin.from("stores").select("id,name"),
    ]);
    const sname = new Map((stores || []).map((s: { id: string; name: string }) => [s.id, s.name]));
    const mine = (uid: string) => (mems || []).filter((x: { user_id: string }) => x.user_id === uid);
    const rows = users.filter((u) => isHq || mine(u.id).some((x: { store_id: string }) => x.store_id === myStore)).map((u) => {
      const p = (profs || []).find((x: { user_id: string }) => x.user_id === u.id);
      const m = mine(u.id).filter((x: { store_id: string }) => isHq || x.store_id === myStore);
      const links = m.map((x: { store_id: string; role: string; can_pay: boolean }) => ({ store: sname.get(x.store_id) || "", role: x.role, pay: !!x.can_pay }));
      if (isHq && p && p.role === "franchise") links.unshift({ store: sname.get(p.store_id) || "", role: "owner", pay: true });
      return { id: u.email.replace(/@ilpum\.invalid$/, ""), email: u.email, hq: p?.role === "hq", me: u.id === who.user.id,
        links, last: u.last, created: u.created, banned: u.banned };
    }).sort((a, b) => Number(b.hq) - Number(a.hq) || a.id.localeCompare(b.id));
    return out(200, { ok: true, rows });
  }

  // ---- 비밀번호 바꾸기 · 삭제: 대상 확인 ----
  const id = String(b.id ?? "").trim().toLowerCase();
  if (!/^[a-z0-9][a-z0-9._-]{2,19}$/.test(id)) return out(400, { error: "아이디가 올바르지 않아요" });
  const email = `${id}@ilpum.invalid`;
  let target: { id: string } | null = null;
  for (let page = 1; page <= 10 && !target; page++) {
    const { data, error } = await admin.auth.admin.listUsers({ page, perPage: 200 });
    if (error) return out(500, { error: error.message });
    target = data.users.find((u) => (u.email || "").toLowerCase() === email) || null;
    if (data.users.length < 200) break;
  }
  if (!target) return out(404, { error: "그런 아이디가 없어요" });
  const { data: tp } = await admin.from("profiles").select("role").eq("user_id", target.id).maybeSingle();
  if (tp?.role === "hq") return out(403, { error: "본사 계정은 여기서 바꾸거나 지울 수 없어요" });
  if (target.id === who.user.id) return out(403, { error: "내 계정은 바꿀 수 없어요" });
  let tMems: { store_id: string }[] = [];
  if (!isHq) {
    // 점주: 이 매장에만 연결된 직원·매니저·발주 전용 계정만
    if (tp) return out(403, { error: "점주·본사 계정은 바꿀 수 없어요" });
    const { data: tm } = await admin.from("sch_members").select("store_id").eq("user_id", target.id);
    tMems = tm || [];
    if (!tMems.length || tMems.some((x) => x.store_id !== myStore)) return out(403, { error: "우리 매장 계정이 아니에요" });
  }

  if (action === "setpw") {
    const password = String(b.password ?? "");
    if (password.length < 8 || password.length > 72) return out(400, { error: "비밀번호는 8자 이상이어야 해요" });
    const { error } = await admin.auth.admin.updateUserById(target.id, { password });
    if (error) return out(400, { error: "비밀번호를 바꾸지 못했어요: " + error.message });
    return out(200, { ok: true, id });
  }

  if (action === "ban") {
    const on = b.on !== false;
    const { error } = await admin.auth.admin.updateUserById(target.id, { ban_duration: on ? "876000h" : "none" });
    if (error) return out(400, { error: "처리하지 못했어요: " + error.message });
    return out(200, { ok: true, id, banned: on });
  }

  if (action === "delete") {
    await admin.from("sch_members").delete().eq("user_id", target.id);
    await admin.from("profiles").delete().eq("user_id", target.id).neq("role", "hq");
    const { error } = await admin.auth.admin.deleteUser(target.id);
    if (error) {
      // 이 계정이 쓴 글 등이 남아 지울 수 없으면 접속만 막는다 (자료는 보존)
      await admin.auth.admin.updateUserById(target.id, { ban_duration: "876000h" });
      return out(200, { ok: true, id, banned: true, note: "이 계정이 남긴 기록이 있어 완전히 지우지 못하고 로그인만 막았어요" });
    }
    return out(200, { ok: true, id });
  }
  return out(400, { error: "알 수 없는 요청이에요" });
});
