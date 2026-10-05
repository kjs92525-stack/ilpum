# 상권 분석 화면 (site.html) — 본사만, 주소 찾기 → 분석 → 점수·경쟁점·영업지역 경고 → 저장·비교·삭제 (가짜 서버)
# 실행 전: sh build_all.sh  (sh tests/run.sh t61)
import asyncio, json, time
from playwright.async_api import async_playwright
NEW='bdqcrbnbuoujozlpttbe.supabase.co'; BON='0134d989-757a-4b60-9cb3-93245de2cac8'; YU='ad2ffdae-f76b-44cd-a6c6-58514c4e4638'
ROLE={'v':'hq'}; FN=[]; PUTS=[]; URLS=[]; MODE={'fn':'ok'}
STORES={'hq':[{"id":BON,"name":"일품집 본점","is_hq":True,"role":"hq","can_pay":True},{"id":YU,"name":"유천점","is_hq":False,"role":"hq","can_pay":False}],
        'owner':[{"id":YU,"name":"유천점","is_hq":False,"role":"owner","can_pay":True}]}
ROWS=[{"store_id":BON,"id":"loc","data":{"addr":"부산 해운대구 본점로 1","x":129.17,"y":35.165},"updated_at":"2026-10-01T00:00:00Z"}]
AN={"at":"2026-10-05T03:00:00Z","x":129.16,"y":35.163,"radius":1000,"region":{"code":"2635052000","name":"부산광역시 해운대구 중1동"},
    "comp":[{"id":"1","name":"바다장어 <img src=x onerror=window.PWN=1>","cat":"음식점 > 한식 > 장어","addr":"해운대로 1","tel":"051-1","x":129.161,"y":35.164,"dist":320,"url":"javascript:alert(1)"},
            {"id":"2","name":"풍천장어","cat":"음식점 > 한식 > 장어","addr":"해운대로 2","tel":"","x":129.165,"y":35.166,"dist":700,"url":"http://place.map.kakao.com/2"},
            {"id":"3","name":"민물장어집","cat":"음식점 > 한식 > 장어","addr":"해운대로 3","tel":"","x":129.168,"y":35.168,"dist":950,"url":""}],
    "compMore":False,"food500":210,"food1k":640,"cafe500":80,"apt":35,"park500":4,
    "subway":[{"id":"s","name":"중동역 2호선","cat":"교통","addr":"","x":129.164,"y":35.165,"dist":450,"url":""}]}
async def handler(r):
  u=r.request.url; m=r.request.method; URLS.append(u)
  if 'localhost' in u: return await r.continue_()
  if NEW not in u: return await r.fulfill(status=404,body='')
  J=lambda o,st=200: r.fulfill(status=st,content_type='application/json',body=json.dumps(o))
  if '/rpc/sch_my_stores' in u: return await J(STORES[ROLE['v']])
  if '/functions/v1/site-analysis' in u:
    b=json.loads(r.request.post_data); FN.append(b)
    if MODE['fn']=='nokey': return await J({"error":"카카오 키가 아직 없어요. Supabase → Edge Functions → Secrets 에 KAKAO_REST_KEY 를 넣어 주세요","nokey":True},503)
    if b['action']=='geocode':
      if '서면' in b['q']: return await J({"list":[{"name":"서면역","addr":"부산 부산진구 중앙대로 730","x":129.059,"y":35.157}]})
      return await J({"list":[{"name":"부산 해운대구 중동 1394","addr":"부산 해운대구 해운대로 600","x":129.16,"y":35.163},{"name":"해운대 해수욕장","addr":"부산 해운대구 우동","x":129.158,"y":35.158}]})
    return await J(dict(AN,x=b['x'],y=b['y'],radius=b['radius']))
  if '/rest/v1/sch_items' in u:
    if m=='POST':
      b=json.loads(r.request.post_data); PUTS.append(b); return await r.fulfill(status=201,body='')
    return await J(ROWS if 'kind=eq.site' in u else [])
  if '/rest/v1/' in u: return await J([])
  await J([])
S={"ses":{"access_token":"tok","refresh_token":"r","expires_at":int(time.time())+3000,"user":{"email":"x@ilpum.invalid"}}}
async def open_page(b,url):
  ctx=await b.new_context(viewport={'width':1300,'height':900}); pg=await ctx.new_page(); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
  pg.on('dialog',lambda d: asyncio.ensure_future(d.accept(d.default_value or '부산 해운대구 유천점')))
  await pg.route('**/*',handler); await pg.route_web_socket(f'wss://{NEW}/**',lambda ws: asyncio.ensure_future(ws.close()))
  await pg.add_init_script(f"try{{ if(!localStorage.getItem('s')){{ localStorage.setItem('s','1'); localStorage.setItem('ilpum-fr-conf',{json.dumps(json.dumps(S))}); }} }}catch(e){{}}")
  await pg.goto('http://localhost:8765/'+url); await pg.wait_for_timeout(1200); return ctx,pg,errs
MENU_JS="[...document.querySelectorAll('#menu > .mi')].filter(b=>!b.hidden).map(b=>b.querySelector('span').textContent.trim())"
FAILS=[]
def ok(name,cond,extra=''):
  print(('  ok ' if cond else 'FAIL ')+name,extra)
  if not cond: FAILS.append(name)
async def main():
  async with async_playwright() as p:
    b=await p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
    ctx,pg,errs=await open_page(b,'site.html')
    ok('1) 본사: 검색칸 보임', await pg.is_visible('#q'))
    await pg.fill('#q','해운대 중동'); await pg.click('#find'); await pg.wait_for_timeout(500)
    ok('   후보 2곳', await pg.evaluate("document.querySelectorAll('[data-cand]').length")==2)
    await pg.click('[data-cand="0"]'); await pg.wait_for_timeout(800)
    ok('   분석 요청(반경 1km)', FN[-1]=={'action':'analyze','x':129.16,'y':35.163,'radius':1000}, FN[-1])
    sc=await pg.inner_text('.score .n'); g=await pg.inner_text('.score .g')
    ok('2) 점수 76 좋음 (경쟁15+음식점22+아파트15+지하철12+주차12)', sc=='76' and '좋음' in g, (sc,g))
    ok('   경쟁점 3곳 표', await pg.evaluate("document.querySelectorAll('#rcard tbody')[1].rows.length")==3)
    ok('   경쟁점 이름 안전하게 표시(코드 실행 안 됨)', await pg.evaluate("!window.PWN && !document.querySelector('#rcard img')"))
    ok('   javascript: 링크 안 만듦', await pg.evaluate("![...document.querySelectorAll('#rcard a')].some(a=>a.href.startsWith('javascript'))"))
    w=await pg.inner_text('.warnbox') if await pg.query_selector('.warnbox') else ''
    ok('3) 본점 2km 안 → 영업지역 경고', '일품집 본점' in w, w)
    await pg.fill('#sname','해운대 1안'); await pg.fill('#smemo','보증금 5천'); await pg.click('#save'); await pg.wait_for_timeout(500)
    sv=PUTS[-1]; ok('4) 저장: 본점 칸 kind=site id=a:…', sv['store_id']==BON and sv['kind']=='site' and sv['id'].startswith('a:') and sv['data']['name']=='해운대 1안' and sv['data']['memo']=='보증금 5천' and sv['data']['res']['food500']==210, {k:sv[k] for k in ('store_id','kind','id')})
    ok('   비교표 1줄', await pg.evaluate("document.querySelectorAll('#cmp tbody tr').length")==1)
    ok('   다시 저장하면 같은 id 덮어쓰기', True)
    await pg.click('#save'); await pg.wait_for_timeout(400); ok('   (덮어쓰기 id 같음)', PUTS[-1]['id']==sv['id'])
    await pg.click('#locs summary'); await pg.wait_for_timeout(200)
    await pg.select_option('#zone','0.5'); await pg.wait_for_timeout(500)
    ok('5) 영업지역 0.5km로 → 설정 저장, 경고 대신 안내', PUTS[-1]['id']=='cfg' and PUTS[-1]['data']['zoneKm']==0.5 and not await pg.query_selector('.warnbox') and await pg.query_selector('.okbox') is not None)
    await pg.click('[data-loc="%s"]'%YU); await pg.wait_for_timeout(500)
    ok('6) 유천점 위치 정하기 → 후보 2곳 중 고르기', await pg.evaluate("document.querySelectorAll('[data-lc]').length")==2)
    await pg.click('[data-lc="1"]'); await pg.wait_for_timeout(400)
    ok('   유천점 칸 loc 저장', PUTS[-1]['store_id']==YU and PUTS[-1]['id']=='loc' and PUTS[-1]['data']['x']==129.158, PUTS[-1])
    await pg.click('[data-del]'); await pg.wait_for_timeout(400)
    ok('7) 삭제 = deleted 표시', PUTS[-1]['deleted'] is True and PUTS[-1]['data'] is None and await pg.evaluate("!document.querySelector('#cmp')"))
    await pg.fill('#q','서면역'); await pg.click('#find'); await pg.wait_for_timeout(800)
    ok('8) 후보 1곳이면 바로 분석', FN[-1]['action']=='analyze' and FN[-1]['x']==129.059)
    ok('   오류 없음', not errs, errs); await ctx.close()
    MODE['fn']='nokey'
    ctx,pg,errs=await open_page(b,'site.html'); await pg.fill('#q','해운대'); await pg.click('#find'); await pg.wait_for_timeout(500)
    ok('9) 카카오 키 없으면 안내', 'KAKAO_REST_KEY' in await pg.inner_text('#cands')); await ctx.close(); MODE['fn']='ok'
    ROLE['v']='owner'; n=len(FN)
    ctx,pg,errs=await open_page(b,'site.html')
    ok('10) 점주: 막힘', '본사 계정만' in await pg.inner_text('#main') and len(FN)==n and not await pg.query_selector('#q')); await ctx.close()
    ctx,pg,errs=await open_page(b,'index.html#site')
    ok('    점주 메뉴에 상권 분석 없음 · 주소로 열어도 안 열림', '상권 분석' not in await pg.evaluate(MENU_JS) and await pg.inner_text('#ttl')!='상권 분석', await pg.evaluate(MENU_JS)); await ctx.close()
    ROLE['v']='hq'; URLS.clear()
    ctx,pg,errs=await open_page(b,'index.html#site'); await pg.wait_for_timeout(800)
    ok('11) 본사 메뉴에 상권 분석 (매장 관리 다음)', '상권 분석' in (await pg.evaluate(MENU_JS)) and await pg.inner_text('#ttl')=='상권 분석', await pg.evaluate(MENU_JS))
    await pg.goto('http://localhost:8765/index.html#dash'); await pg.wait_for_timeout(1500)
    q=[x for x in URLS if 'sch_items' in x and 'store_id=eq.' in x]
    ok('    오늘 현황·근무표는 상권 자료를 안 받음(kind=neq.site)', q and all('kind=neq.site' in x for x in q), q[:2])
    ok('    오류 없음', not errs, errs); await ctx.close()
    await b.close()
  print('모두 통과' if not FAILS else '실패 있음: '+', '.join(FAILS))
asyncio.run(main())
