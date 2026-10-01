# 발주 받는 사람(본사): 모든 매장의 진행 중 발주를 한 번에 / 매장 이름표 / 메뉴 빨간 숫자 / 오늘 현황 "들어온 발주" (가짜 서버)
# 실행 전: cd dist && python3 -m http.server 8765
import asyncio, json, time
from playwright.async_api import async_playwright
NEW='bdqcrbnbuoujozlpttbe.supabase.co'; BON='0134d989-757a-4b60-9cb3-93245de2cac8'; YU='ad2ffdae-f76b-44cd-a6c6-58514c4e4638'
def line(n,q): return {"id":"i"+n,"qty":q,"done":False,"name":n,"unit":"box","links":[{"n":"쿠팡","u":"https://www.coupang.com/x"}],"buy_url":None}
ORD=[{"store_id":YU,"code":"YU01","created_at":"2026-10-01T05:00:00+00:00","status":"open","lines":[line("앞치마",2),line("장갑",1)]},
     {"store_id":BON,"code":"BN01","created_at":"2026-10-01T03:00:00+00:00","status":"open","lines":[line("종이컵",5)]},
     {"store_id":BON,"code":"BN00","created_at":"2026-09-30T03:00:00+00:00","status":"done","lines":[{**line("물티슈",1),"done":True}]}]
ROLE={'v':'hq'}; PATCH=[]
STORES={'hq':[{"id":BON,"name":"일품집 본점","is_hq":True,"role":"hq","can_pay":True},{"id":YU,"name":"유천점","is_hq":False,"role":"hq","can_pay":False}],
        'owner':[{"id":YU,"name":"유천점","is_hq":False,"role":"owner","can_pay":True}]}
async def handler(r):
  u=r.request.url; m=r.request.method
  if 'localhost' in u: return await r.continue_()
  if NEW not in u: return await r.fulfill(status=404,body='{}')
  J=lambda o,st=200: r.fulfill(status=st,content_type='application/json',body=json.dumps(o))
  if '/rpc/sch_my_stores' in u: return await J(STORES[ROLE['v']])
  if '/rest/v1/wh_orders' in u:
    allowed={'hq':{BON,YU},'owner':{YU}}[ROLE['v']]
    if m=='PATCH':
      code=u.split('code=eq.')[1].split('&')[0]; sid=u.split('store_id=eq.')[1].split('&')[0]; b=json.loads(r.request.post_data); PATCH.append((sid,code,b['status']))
      for o in ORD:
        if o['code']==code and o['store_id']==sid: o.update(lines=b['lines'],status=b['status'])
      return await r.fulfill(status=204,body='')
    rows=[o for o in ORD if o['store_id'] in allowed]
    if 'store_id=eq.' in u: sid=u.split('store_id=eq.')[1].split('&')[0]; rows=[o for o in rows if o['store_id']==sid]
    if 'status=eq.open' in u: rows=[o for o in rows if o['status']=='open']
    if 'select=store_id,code' in u: rows=[{k:o[k] for k in ('store_id','code','created_at')} for o in rows]
    return await J(rows)
  if '/rest/v1/wh_items' in u: return await J([])
  if '/rest/v1/sch_items' in u: return await J([])
  if '/rest/v1/res_days' in u: return await J([])
  await J([])
S={"ses":{"access_token":"tok","refresh_token":"r","expires_at":int(time.time())+3000,"user":{"email":"x@ilpum.invalid"}}}
async def open_page(b,url):
  ctx=await b.new_context(viewport={'width':1200,'height':900}); pg=await ctx.new_page(); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
  pg.on('dialog',lambda d: asyncio.ensure_future(d.accept()))
  await pg.route('**/*',handler); await pg.route_web_socket(f'wss://{NEW}/**',lambda ws: asyncio.ensure_future(ws.close()))
  await pg.add_init_script(f"try{{ if(!localStorage.getItem('s')){{ localStorage.setItem('s','1'); localStorage.setItem('ilpum-fr-conf',{json.dumps(json.dumps(S))}); }} }}catch(e){{}}")
  await pg.goto('http://localhost:8765/'+url); await pg.wait_for_timeout(1600); return ctx,pg,errs
async def main():
  async with async_playwright() as p:
    b=await p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
    ctx,pg,errs=await open_page(b,'order.html')
    print('1) 본사: 전체 현황 탭:', await pg.inner_text('#allTab'), '| 보임:', await pg.is_visible('#allTab'), '| 매장 선택 목록:', await pg.evaluate("[...document.querySelectorAll('#storeSel option')].map(o=>o.textContent)"))
    await pg.click('#allTab'); await pg.wait_for_timeout(200)
    print('2) 전체 현황: 매장 칸', await pg.evaluate("[...document.querySelectorAll('.stchip')].map(c=>c.innerText.replace(/\\s+/g,' '))"), '| 발주 카드 이름표:', await pg.evaluate("[...document.querySelectorAll('.ord .sname')].map(e=>e.textContent)"), '| 진행 중 건수:', await pg.evaluate("document.querySelectorAll('.ord').length"))
    await pg.click('[data-ck="YU01"][data-i="0"]'); await pg.wait_for_timeout(300); await pg.click('[data-ck="YU01"][data-i="1"]'); await pg.wait_for_timeout(500)
    print('3) 유천점 발주 체크 → 그 매장 것으로 저장:', PATCH, '| 모두 체크하면 목록에서 빠짐:', await pg.evaluate("[...document.querySelectorAll('.ord .code')].map(e=>e.textContent)"), '| 탭 숫자:', await pg.inner_text('#allTab'))
    print('   errs', errs); await ctx.close()
    ctx,pg,errs=await open_page(b,'index.html#dash')
    print('4) 통합 틀(본사): 발주 메뉴 숫자:', await pg.evaluate("(document.querySelector('#menu [data-m=ord] .bdg')||{}).textContent"), '| 오늘 현황 들어온 발주:', await pg.evaluate("(document.querySelector('#dash .panel h2:not(:empty)')?[...document.querySelectorAll('#dash .panel')].filter(p=>p.innerText.includes('들어온 발주'))[0].innerText.replace(/\\s+/g,' '):'없음')"))
    print('   errs', errs); await ctx.close()
    ROLE['v']='owner'; ctx,pg,errs=await open_page(b,'order.html')
    print('5) 점주: 전체 현황 탭 숨김:', not await pg.is_visible('#allTab'), '| 내 매장 발주만:', await pg.evaluate("[...document.querySelectorAll('.ord .code')].map(e=>e.textContent)")); print('   errs', errs); await ctx.close()
asyncio.run(main())
