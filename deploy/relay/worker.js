// 일품집 상권분석 — 공공데이터 중계 서버 (Cloudflare Worker)
// 화면(sangkwon)이 이 서버에 물어보면, 이 서버가 공공데이터포털 키를 붙여 대신 받아 와서 돌려줌.
// 키는 코드에 넣지 않고 Cloudflare → 이 Worker → Settings → Variables and Secrets 에 DATA_KEY(공공데이터포털 "일반 인증키(Decoding)")로 넣기.
// 통계청 SGIS(사업체·종사자 수 = 직장인 수): SGIS_KEY / SGIS_SECRET (sgis.kostat.go.kr 개발지원센터 → 서비스 신청의 서비스 ID / 보안 Key) 도 Secret 으로.
// 네이버 블로그 글 수(장어집 인기도): NAVER_ID / NAVER_SECRET (네이버 개발자센터 → 애플리케이션 → 검색 API 의 Client ID / Client Secret) 도 Secret 으로.
const ALLOW = [
  'https://sangkwon.yoyo925.workers.dev',
  'https://ancient-morning-30ee.yoyo925.workers.dev',
  'http://localhost', 'http://localhost:8765',
];
const API = {
  // 국토교통부 아파트 매매 실거래가 (시군구 5자리 LAWD_CD, 계약년월 DEAL_YMD)
  apt: { url: 'https://apis.data.go.kr/1613000/RTMSDataSvcAptTrade/getRTMSDataSvcAptTrade', keys: ['LAWD_CD', 'DEAL_YMD', 'numOfRows', 'pageNo'], ttl: 86400 },
  // 소상공인시장진흥공단 상가(상권)정보 — 반경 안 상가
  store: { url: 'https://apis.data.go.kr/B553077/api/open/sdsc2/storeListInRadius', keys: ['radius', 'cx', 'cy', 'numOfRows', 'pageNo', 'type', 'indsLclsCd'], ttl: 86400 },
  // 행정안전부 행정동별(통반단위) 성/연령별 주민등록 인구수 — 행정동 코드 10자리(admmCd), 기준연월 srchFrYm~srchToYm
  pop: { url: 'https://apis.data.go.kr/1741000/admmSexdAgePpltn/selectAdmmSexdAgePpltn', keys: ['admmCd', 'srchFrYm', 'srchToYm', 'lv', 'regSeCd', 'type', 'numOfRows', 'pageNo'], ttl: 86400 },
  // 행정안전부 식품 일반음식점 조회서비스 — 인허가·폐업 (도로명주소 글자 LIKE, 인허가일자, 영업상태 01=영업·03=폐업, 지자체 코드로 거름)
  rest: { url: 'https://apis.data.go.kr/1741000/general_restaurants/info', keys: ['pageNo', 'numOfRows', 'returnType', 'cond[ROAD_NM_ADDR::LIKE]', 'cond[BPLC_NM::LIKE]', 'cond[LCPMT_YMD::GTE]', 'cond[SALS_STTS_CD::EQ]', 'cond[OPN_ATMY_GRP_CD::EQ]'], ttl: 86400 },
};
// SGIS 는 키로 먼저 accessToken 을 받아 붙여야 함 — 이 서버가 받아서 몇 시간 재사용
let SGIS_TOKEN = '', SGIS_UNTIL = 0;
async function sgisToken(env, force) {
  if (!force && SGIS_TOKEN && Date.now() < SGIS_UNTIL) return SGIS_TOKEN;
  const r = await fetch('https://sgisapi.kostat.go.kr/OpenAPI3/auth/authentication.json?consumer_key=' + encodeURIComponent(env.SGIS_KEY) + '&consumer_secret=' + encodeURIComponent(env.SGIS_SECRET));
  const j = await r.json().catch(() => ({}));
  const t = j && j.result && j.result.accessToken; if (!t) throw new Error('SGIS 인증 실패: ' + (j.errMsg || j.errCd || r.status));
  SGIS_TOKEN = t; SGIS_UNTIL = Date.now() + 3 * 3600 * 1000; return t;
}
const SGIS_PATHS = { stage: 'addr/stage.json', company: 'stats/company.json' };   // 시군구·읍면동 목록 / 사업체·종사자 수
export default {
  async fetch(req, env, ctx) {
    const origin = req.headers.get('Origin') || '';
    const ok = ALLOW.some(a => origin === a || origin.startsWith(a + ':'));
    const cors = { 'Access-Control-Allow-Origin': ok ? origin : ALLOW[0], 'Access-Control-Allow-Methods': 'GET, OPTIONS', 'Vary': 'Origin' };
    if (req.method === 'OPTIONS') return new Response(null, { headers: cors });
    const u = new URL(req.url), name = u.pathname.replace(/^\/+/, '');
    const out = (status, obj) => new Response(JSON.stringify(obj), { status, headers: { ...cors, 'Content-Type': 'application/json; charset=utf-8' } });
    if (name === 'ping') return out(200, { ok: true, hasKey: !!env.DATA_KEY, hasNaver: !!(env.NAVER_ID && env.NAVER_SECRET), hasSgis: !!(env.SGIS_KEY && env.SGIS_SECRET), origin, allowed: ok });
    if (!ok) return out(403, { error: '허용되지 않은 주소에서 온 요청이에요 (' + origin + ')' });
    // 통계청 SGIS — /sgis?p=stage&cd=22 · /sgis?p=company&adm_cd=22040&low_search=1&year=2023 . 7일 캐시
    if (name === 'sgis') {
      if (!env.SGIS_KEY || !env.SGIS_SECRET) return out(503, { error: 'SGIS_KEY·SGIS_SECRET(통계청 SGIS 키)가 아직 없어요' });
      const path = SGIS_PATHS[u.searchParams.get('p') || '']; if (!path) return out(400, { error: '모르는 SGIS 요청' });
      const qs = new URLSearchParams(); for (const k of ['cd', 'adm_cd', 'low_search', 'year', 'pg_yn']) { const v = u.searchParams.get(k); if (v != null) qs.set(k, v); }
      const ck = new Request('https://cache.local/sgis/' + path + '?' + qs.toString()), hit = await caches.default.match(ck);
      if (hit) { const h = new Response(hit.body, hit); Object.entries(cors).forEach(([k, v]) => h.headers.set(k, v)); return h; }
      let j;
      try {
        for (let tryNo = 0; tryNo < 2; tryNo++) {
          const tk = await sgisToken(env, tryNo > 0); qs.set('accessToken', tk);
          const r = await fetch('https://sgisapi.kostat.go.kr/OpenAPI3/' + path + '?' + qs.toString()); j = await r.json().catch(() => ({ errMsg: 'HTTP ' + r.status }));
          if (String(j.errCd) === '-401') continue;   // 토큰 만료 → 새로 받아 한 번 더
          break;
        }
      } catch (e) { return out(502, { error: 'SGIS 에 연결하지 못했어요: ' + e.message }); }
      qs.delete('accessToken');
      const res = new Response(JSON.stringify(j), { headers: { ...cors, 'Content-Type': 'application/json; charset=utf-8', 'Cache-Control': 'max-age=604800' } });
      if (String(j.errCd) === '0') ctx.waitUntil(caches.default.put(ck, res.clone()));
      return res;
    }
    // 네이버 블로그 검색 — 글 수(total)만 돌려줌. 7일 캐시
    if (name === 'blog') {
      if (!env.NAVER_ID || !env.NAVER_SECRET) return out(503, { error: 'NAVER_ID·NAVER_SECRET(네이버 검색 API 키)가 아직 없어요' });
      const q = (u.searchParams.get('query') || '').slice(0, 60); if (!q) return out(400, { error: 'query 없음' });
      const ck = new Request('https://cache.local/blog?q=' + encodeURIComponent(q)), hit = await caches.default.match(ck);
      if (hit) { const h = new Response(hit.body, hit); Object.entries(cors).forEach(([k, v]) => h.headers.set(k, v)); return h; }
      let r; try { r = await fetch('https://openapi.naver.com/v1/search/blog.json?display=1&query=' + encodeURIComponent(q), { headers: { 'X-Naver-Client-Id': env.NAVER_ID, 'X-Naver-Client-Secret': env.NAVER_SECRET } }); }
      catch (e) { return out(502, { error: '네이버에 연결하지 못했어요: ' + e.message }); }
      const j = await r.json().catch(() => ({}));
      if (!r.ok) return out(r.status, { error: '네이버 검색 오류: ' + (j.errorMessage || r.status) });
      const res = new Response(JSON.stringify({ total: +j.total || 0 }), { headers: { ...cors, 'Content-Type': 'application/json; charset=utf-8', 'Cache-Control': 'max-age=604800' } });
      ctx.waitUntil(caches.default.put(ck, res.clone())); return res;
    }
    if (!env.DATA_KEY) return out(503, { error: 'DATA_KEY(공공데이터포털 인증키)가 아직 없어요' });
    const a = API[name]; if (!a) return out(404, { error: '모르는 요청: ' + name });
    const t = new URL(a.url);
    for (const k of a.keys) { const v = u.searchParams.get(k); if (v != null) t.searchParams.set(k, v); }
    const cacheKey = new Request('https://cache.local/' + name + '?' + t.searchParams.toString());
    const cache = caches.default; const hit = await cache.match(cacheKey);
    if (hit) { const h = new Response(hit.body, hit); Object.entries(cors).forEach(([k, v]) => h.headers.set(k, v)); return h; }
    t.searchParams.set('serviceKey', env.DATA_KEY);
    let r;
    try { r = await fetch(t.toString(), { headers: { 'Accept': '*/*' } }); }
    catch (e) { return out(502, { error: '공공데이터포털에 연결하지 못했어요: ' + e.message }); }
    const body = await r.text();
    const res = new Response(body, { status: r.status, headers: { ...cors, 'Content-Type': r.headers.get('Content-Type') || 'text/plain; charset=utf-8', 'Cache-Control': 'max-age=' + a.ttl } });
    if (r.ok && !/SERVICE_KEY|LIMITED|ERROR/i.test(body.slice(0, 600))) ctx.waitUntil(cache.put(cacheKey, res.clone()));
    return res;
  },
};
