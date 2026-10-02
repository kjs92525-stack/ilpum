# 유천점(자유 배치·인원 지정·예약 있음)에서 "연결 실패(... reading 'length')" 재현 (가짜 서버)
import asyncio, json, time, datetime
from playwright.async_api import async_playwright
NEW='bdqcrbnbuoujozlpttbe.supabase.co'; F1='ad2ffdae-f76b-44cd-a6c6-58514c4e4638'
T=[{"id":str(i),"x":20+(i%10)*90,"y":20+(i//10)*100,"w":86,"h":86,"shape":"square"} for i in range(1,32)]+[{"id":"R1","x":20,"y":420,"w":120,"h":86,"shape":"rect"},{"id":"R2","x":160,"y":420,"w":120,"h":86,"shape":"rect"}]
LAYOUT={"v":1,"seats":{str(i):6 for i in (11,13,17,21,23,26,27,28,29,30,31)},"floors":[{"key":"1","mode":"free","name":"1층","tables":T}]}
TODAY=datetime.date.today().isoformat()
ITEMS=[{"id":"a1","c":TODAY,"u":1790909475866,"pp":"4","req":"","done":False,"name":"김","time":"18:00","tables":["13"],"phone":"0101","tnote":""},{"id":"a2","c":TODAY,"u":1790909475867,"pp":"2+3","name":"이","time":"","tables":[]}]
async def handler(r):
  u=r.request.url; m=r.request.method
  if 'localhost' in u: return await r.continue_()
  if NEW not in u: return await r.fulfill(status=404,body='{}')
  J=lambda o,st=200: r.fulfill(status=st,content_type='application/json',body=json.dumps(o))
  if '/rpc/sch_my_stores' in u: return await J([{"id":F1,"name":"유천점","is_hq":False,"role":"owner"}])
  if '/rest/v1/sch_items' in u: return await J([{"data":LAYOUT}])
  if '/rest/v1/res_days' in u:
    if m=='GET': return await J([{"id":TODAY,"rev":3,"data":{"items":ITEMS}}] if 'select=data' in u else [{"rev":3}])
    return await J([{"rev":4}])
  await J([])
S={"ses":{"access_token":"tok","refresh_token":"r","expires_at":int(time.time())+3000,"user":{"email":"x@ilpum.invalid"}}}
async def main():
  async with async_playwright() as p:
    b=await p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
    for cache in (None,'{"rev":0}','{"items":null}','garbage'):
      ctx=await b.new_context(viewport={'width':1500,'height':900}); pg=await ctx.new_page(); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
      await pg.route('**/*',handler); await pg.route_web_socket(f'wss://{NEW}/**',lambda ws: asyncio.ensure_future(ws.close()))
      init=f"try{{ localStorage.setItem('ilpum-fr-conf',{json.dumps(json.dumps(S))}); "+(f"localStorage.setItem('ilpum-res-{F1}-{TODAY}',{json.dumps(cache)});" if cache else "")+"}catch(e){}"
      await pg.add_init_script(init)
      await pg.goto('http://localhost:8765/reserve.html'); await pg.wait_for_timeout(2000)
      print('캐시',cache,'| 상태:', await pg.inner_text('#sync'), '| errs', errs, '| 예약줄', await pg.locator('.res').count() if False else '')
      await ctx.close()
asyncio.run(main())
