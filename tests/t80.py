# 현황판 테이블 창(테이블 누르면 뜨는 창)의 10% 버튼 (2026-11-07): 누르면 요청사항에 10% 넣고 바로 저장, 다시 누르면 뺌 (가짜 서버, 본점)
import asyncio, json, time
from playwright.async_api import async_playwright
NEW='bdqcrbnbuoujozlpttbe.supabase.co'; HQ='0134d989-757a-4b60-9cb3-93245de2cac8'
ITEMS=[{"id":"i1","c":"x","u":1,"pp":"4","req":"아기의자","done":False,"name":"홍길동","time":"18:00","phone":"","tnote":"","tables":["1"]}]
SAVED=[]
LAYOUT={"floors":[{"key":"1","name":"1층","groups":[{"title":"홀","cols":[["1","2"]]}]}],"seats":{}}
async def handler(r):
  u=r.request.url
  if 'localhost' in u: return await r.continue_()
  if NEW not in u: return await r.fulfill(status=404,body='{}')
  J=lambda o: r.fulfill(status=200,content_type='application/json',body=json.dumps(o))
  if '/rpc/sch_my_stores' in u: return await J([{"id":HQ,"name":"일품집 본점","is_hq":True,"role":"hq","can_pay":True}])
  if '/rest/v1/sch_items' in u: return await J([{"data":LAYOUT}])
  if '/rest/v1/res_days' in u:
    if r.request.method=='GET': return await J([{"rev":3,"data":{"items":ITEMS}}] if 'select=data' in u else [{"rev":3}])
    SAVED.append(r.request.post_data or ''); return await J([{"rev":4}])
  await J([])
S={"ses":{"access_token":"tok","refresh_token":"r","expires_at":int(time.time())+10**8,"user":{"email":"x@ilpum.invalid"}}}
async def main():
  ok=True
  def chk(n,c,x=''):
    nonlocal ok; ok&=bool(c); print('OK  ' if c else 'FAIL',n,x)
  async with async_playwright() as p:
    b=await p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
    pg=await (await b.new_context(viewport={'width':1280,'height':900})).new_page(); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
    await pg.route('**/*',handler); await pg.route_web_socket(f'wss://{NEW}/**',lambda ws: None)
    await pg.add_init_script(f"try{{ localStorage.setItem('ilpum-fr-conf',{json.dumps(json.dumps(S))}); }}catch(e){{}}")
    await pg.goto('http://localhost:8765/reserve.html'); await pg.wait_for_timeout(2500)
    await pg.click('.cell[data-pick="1"]'); await pg.wait_for_timeout(300)
    chk('테이블 창에 10% 버튼', await pg.locator('[data-ppct="i1"]').count()==1)
    chk('수정 창에는 없음', await pg.locator('[data-fpct]').count()==0)
    await pg.click('[data-ppct="i1"]'); await pg.wait_for_timeout(800)
    chk('누르면 10% 넣고 바로 저장', ITEMS[0]['req']=='아기의자 10%' or any('아기의자 10%' in s for s in SAVED), len(SAVED))
    chk('버튼 켜짐·창 그대로', 'on' in (await pg.get_attribute('[data-ppct="i1"]','class')) and '아기의자 10%' in await pg.inner_text('.pick'))
    n=len(SAVED); await pg.click('[data-ppct="i1"]'); await pg.wait_for_timeout(800)
    await pg.wait_for_timeout(1500); txt=await pg.inner_text('.pick .sub')
    chk('다시 누르면 뺌(저장됨)', len(SAVED)>n and '10%' not in txt and 'on' not in (await pg.get_attribute('[data-ppct="i1"]','class')), (len(SAVED),n,txt))
    chk('오류 없음', not errs, errs); await b.close()
  print('전체 OK' if ok else '실패 있음')
asyncio.run(main())
