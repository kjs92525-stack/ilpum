# 예약 현황판: 점주가 층·구역 이름에 코드를 넣어도 본사 화면에서 실행되지 않는지 (가짜 서버)
import asyncio, json, time, datetime
from playwright.async_api import async_playwright
NEW='bdqcrbnbuoujozlpttbe.supabase.co'; F1='ad2ffdae-f76b-44cd-a6c6-58514c4e4638'
X='<img src=x onerror="window.__pwned=1">'
TODAY=datetime.date.today().isoformat()
GRID={"floors":[{"key":"1","name":X,"groups":[{"title":X,"cols":[[1,2],[3]]}],"bar":{"title":X,"row":[4,5]}}]}
BAD_SHAPE={"floors":[{"key":"1","mode":"free","name":"홀","tables":[{"id":"1","x":10,"y":10,"w":90,"h":90,"shape":'round" onmouseover="window.__pwned=1'}]}]}
BAD_ID={"floors":[{"key":"1","mode":"free","name":"홀","tables":[{"id":X,"x":10,"y":10,"w":90,"h":90}]}]}
BAD_KEY={"floors":[{"key":'1" onclick="window.__pwned=1',"name":"홀","groups":[{"title":"A","cols":[[1]]}]}]}
LAYOUT=None
async def handler(r):
  u=r.request.url
  if 'localhost' in u: return await r.continue_()
  if NEW not in u: return await r.fulfill(status=404,body='{}')
  J=lambda o: r.fulfill(status=200,content_type='application/json',body=json.dumps(o))
  if '/rpc/sch_my_stores' in u: return await J([{"id":F1,"name":"유천점","is_hq":False,"role":"hq"}])
  if '/rest/v1/sch_items' in u: return await J([{"data":LAYOUT}])
  if '/rest/v1/res_days' in u: return await J([{"id":TODAY,"rev":1,"data":{"items":[]}}] if 'select=data' in u else [{"rev":1}])
  await J([])
S={"ses":{"access_token":"tok","refresh_token":"r","expires_at":int(time.time())+3000,"user":{"email":"x@ilpum.invalid"}}}
async def main():
  global LAYOUT; ok=True
  async with async_playwright() as p:
    b=await p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
    for name,L,expect_text in (('이름에 코드',GRID,True),('모양에 코드',BAD_SHAPE,False),('번호에 코드',BAD_ID,False),('층 key에 코드',BAD_KEY,False)):
      LAYOUT=L
      ctx=await b.new_context(viewport={'width':1500,'height':900}); pg=await ctx.new_page(); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
      await pg.route('**/*',handler); await pg.route_web_socket(f'wss://{NEW}/**',lambda ws: asyncio.ensure_future(ws.close()))
      await pg.add_init_script(f"try{{ localStorage.setItem('ilpum-fr-conf',{json.dumps(json.dumps(S))}); }}catch(e){{}}")
      await pg.goto('http://localhost:8765/reserve.html'); await pg.wait_for_timeout(2000)
      for el in await pg.query_selector_all('#boardPanel *'):
        try: await el.hover(timeout=200)
        except Exception: pass
      pw=await pg.evaluate('window.__pwned||0'); imgs=await pg.locator('#boardPanel img').count()
      shown=X in await pg.inner_text('#boardPanel')
      good= pw==0 and imgs==0 and not errs and (shown if expect_text else not shown)
      ok&=good
      print('OK  ' if good else 'FAIL', name, '| 실행됨', pw, '| img', imgs, '| 글자로 보임', shown, '| errs', errs)
      await ctx.close()
    await b.close()
  print('전체 OK' if ok else '실패 있음')
asyncio.run(main())
