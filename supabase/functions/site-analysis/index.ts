// 상권 분석 — 본사만. 카카오 로컬 API 로 주소 찾기 · 반경 안 경쟁점(장어)·음식점·카페·아파트·지하철·주차장을 모아 돌려줌.
// 카카오 REST 키는 화면·저장소에 넣지 않음: Supabase 대시보드 → Edge Functions → Secrets 에 KAKAO_REST_KEY 로 넣기.
// 요청: {action:'geocode', q:'부산 해운대구 …'} / {action:'analyze', x, y, radius(500|1000|1500)}
import { createClient } from "npm:@supabase/supabase-js@2";

const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};
const out = (status: number, body: unknown) =>
  new Response(JSON.stringify(body), { status, headers: { ...CORS, "Content-Type": "application/json" } });

const KAKAO = "https://dapi.kakao.com/v2/local";
type Doc = Record<string, string>;
async function kakao(key: string, path: string, q: Record<string, string | number>) {
  const u = new URL(KAKAO + path);
  for (const [k, v] of Object.entries(q)) u.searchParams.set(k, String(v));
  const r = await fetch(u, { headers: { Authorization: "KakaoAK " + key } });
  if (!r.ok) {
    const t = await r.text().catch(() => "");
    throw new Error(r.status === 401 || r.status === 403 ? "카카오 키가 맞지 않거나 로컬 API 사용 설정이 꺼져 있어요" : `카카오 오류 ${r.status} ${t.slice(0, 120)}`);
  }
  return await r.json() as { meta: { total_count: number; pageable_count: number; is_end: boolean }; documents: Doc[] };
}
// 한 번에 15개씩, 최대 3쪽(45개)
async function allPages(key: string, path: string, q: Record<string, string | number>) {
  const docs: Doc[] = []; let total = 0;
  for (let page = 1; page <= 3; page++) {
    const j = await kakao(key, path, { ...q, page, size: 15 });
    total = j.meta.total_count; docs.push(...j.documents);
    if (j.meta.is_end) break;
  }
  return { total, docs };
}
const place = (d: Doc) => ({
  id: d.id, name: d.place_name, cat: d.category_name, addr: d.road_address_name || d.address_name,
  tel: d.phone || "", x: +d.x, y: +d.y, dist: d.distance === "" || d.distance == null ? null : +d.distance, url: d.place_url || "",
});

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
  if (me?.role !== "hq") return out(403, { error: "상권 분석은 본사만 쓸 수 있어요" });

  const key = Deno.env.get("KAKAO_REST_KEY") || "";
  if (!key) return out(503, { error: "카카오 키가 아직 없어요. Supabase → Edge Functions → Secrets 에 KAKAO_REST_KEY 를 넣어 주세요", nokey: true });

  let b: Record<string, unknown>;
  try { b = await req.json(); } catch { return out(400, { error: "요청 형식이 올바르지 않아요" }); }
  try {
    if (b.action === "geocode") {
      const q = String(b.q ?? "").trim().slice(0, 100);
      if (q.length < 2) return out(400, { error: "주소나 장소 이름을 두 글자 이상 넣어 주세요" });
      const a = await kakao(key, "/search/address.json", { query: q, size: 10 });
      let list = a.documents.map((d) => ({ name: d.address_name, addr: (d as any).road_address?.address_name || d.address_name, x: +d.x, y: +d.y }));
      if (!list.length) {      // 주소가 아니면 장소 이름으로 (예: "서면역", "해운대 해수욕장")
        const k = await kakao(key, "/search/keyword.json", { query: q, size: 10 });
        list = k.documents.map((d) => ({ name: d.place_name, addr: d.road_address_name || d.address_name, x: +d.x, y: +d.y }));
      }
      return out(200, { list });
    }
    if (b.action === "analyze") {
      const x = Number(b.x), y = Number(b.y), radius = [500, 1000, 1500].includes(Number(b.radius)) ? Number(b.radius) : 1000;
      if (!(x > 124 && x < 132 && y > 33 && y < 39)) return out(400, { error: "위치가 올바르지 않아요" });
      const at = { x, y };
      const cnt = async (code: string, r: number) => (await kakao(key, "/search/category.json", { ...at, category_group_code: code, radius: r, size: 1 })).meta.total_count;
      const [eelA, eelB, food500, food1k, cafe500, apt, subway, park500, region] = await Promise.all([
        allPages(key, "/search/keyword.json", { ...at, query: "장어", radius, sort: "distance" }),
        allPages(key, "/search/keyword.json", { ...at, query: "민물장어", radius, sort: "distance" }),
        cnt("FD6", 500), cnt("FD6", 1000), cnt("CE7", 500),
        kakao(key, "/search/keyword.json", { ...at, query: "아파트", radius: 1000, size: 1 }),
        kakao(key, "/search/category.json", { ...at, category_group_code: "SW8", radius: 2000, sort: "distance", size: 3 }),
        cnt("PK6", 500),
        kakao(key, "/geo/coord2regioncode.json", at),
      ]);
      // 장어 식당만 (수산물 가게·정육점 등 제외), 같은 가게는 한 번만
      const seen = new Set<string>(); const comp = [];
      for (const d of [...eelA.docs, ...eelB.docs]) {
        if (seen.has(d.id) || !String(d.category_name || "").startsWith("음식점")) continue;
        seen.add(d.id); comp.push(place(d));
      }
      comp.sort((a, b2) => (a.dist ?? 1e9) - (b2.dist ?? 1e9));
      const h = region.documents.find((d) => d.region_type === "H") || region.documents[0];
      return out(200, {
        at: new Date().toISOString(), x, y, radius,
        region: h ? { code: h.code, name: h.address_name, sido: h.region_1depth_name, gu: h.region_2depth_name, dong: h.region_3depth_name } : null,
        comp, compMore: eelA.total > 45,      // 45개가 넘으면 일부만 받음
        food500, food1k, cafe500, apt: apt.meta.total_count, park500,
        subway: subway.documents.map(place),
      });
    }
    return out(400, { error: "알 수 없는 요청이에요" });
  } catch (e) {
    return out(502, { error: (e as Error).message || "카카오에 연결하지 못했어요" });
  }
});
