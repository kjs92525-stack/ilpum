# 매장 이름 바꾸기(본사만) 화면 — 가짜 서버
# 실행 전: cd dist && python3 -m http.server 8765
import asyncio, json, time
from playwright.async_api import async_playwright
NEW='bdqcrbnbuoujozlpttbe.supabase.co'; BON='0134d989-757a-4b60-9cb3-93245de2cac8'; F1='ad2ffdae-f76b-44cd-a6c6-58514c4e4638'
NAMES={BON:'일품집 본점',F1:'가맹점 1'}; CALLS=[]; ROLE={'v':'hq'}
async def handler(r):
  u=r.request.url; m=r.request.method
  if 'localhost' in u: return await r.continue_()
  if NEW not in u: return await r.fulfill(status=404,body='{}')
  J=lambda o,st=200: r.fulfill(status=st,content_type='application/json',body=json.dumps(o))
  if '/rpc/sch_my_stores' in u:
    if ROLE['v']=='hq': return await J([{"id":BON,"name":NAMES[BON],"is_hq":True,"role":"hq","can_pay":True},{"id":F1,"name":NAMES[F1],"is_hq":False,"role":"hq","can_pay":False}])
    return await J([{"id":F1,"name":NAMES[F1],"is_hq":False,"role":"owner","can_pay":True}])
  if '/rpc/sch_rename_store' in u:
    b=json.loads(r.request.post_data); CALLS.append(b); NAMES[b['p_store']]=b['p_name']; return await J('ok')
  if '/rest/v1/sch_items' in u: return await J([])
  await J([])
S={"ses":{"access_token":"tok","refresh_token":"r","expires_at":int(time.time())+3000,"user":{"email":"x@ilpum.invalid"}},"mode":"remote","url":"https://"+NEW,"key":"k"}
async def open_page(b,prompt_value=None):
  ctx=await b.new_context(viewport={'width':1200,'height':900}); pg=await ctx.new_page(); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
  pg.on('dialog',lambda d: asyncio.ensure_future(d.accept(prompt_value) if d.type=='prompt' else d.accept()))
  await pg.route('**/*',handler); await pg.route_web_socket(f'wss://{NEW}/**',lambda ws: asyncio.ensure_future(ws.close()))
  await pg.add_init_script(f"try{{ localStorage.setItem('ilpum-fr-conf',{json.dumps(json.dumps(S))}); }}catch(e){{}}")
  await pg.goto('http://localhost:8765/ilpum-schedule.html?view=hq'); await pg.wait_for_timeout(1500); return ctx,pg,errs
async def main():
  async with async_playwright() as p:
    b=await p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
    ctx,pg,errs=await open_page(b,'유천점')
    print('1) 본사 현황에 이름 바꾸기 버튼:', await pg.evaluate("[...document.querySelectorAll('[data-a=storerename]')].length"), '개 (매장 수만큼)')
    await pg.click(f'[data-a="storerename"][data-id="{F1}"]'); await pg.wait_for_timeout(800)
    print('2) 서버로 보낸 내용:', CALLS, '| 화면 매장 이름:', await pg.evaluate("APP.stores.map(s=>s.name)"), '| 안내:', await pg.inner_text('#toast'))
    print('   카드에 새 이름 보임:', '유천점' in await pg.inner_text('#main'), '| errs', errs); await ctx.close()
    ROLE['v']='owner'; ctx,pg,errs=await open_page(b)
    print('3) 점주: 이름 바꾸기 버튼 없음:', await pg.evaluate("document.querySelectorAll('[data-a=storerename]').length")==0, '| 매장 이름:', await pg.evaluate("APP.stores.map(s=>s.name)"), '| errs', errs); await ctx.close()
asyncio.run(main())
