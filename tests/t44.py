# 점주(유천점): 우리 매장 직원·발주 전용 계정 만들기·목록, "데이터" 카드 숨김 / 본사는 그대로 (가짜 서버)
import asyncio, json, time
from playwright.async_api import async_playwright
NEW='bdqcrbnbuoujozlpttbe.supabase.co'; BON='0134d989-757a-4b60-9cb3-93245de2cac8'; F1='ad2ffdae-f76b-44cd-a6c6-58514c4e4638'
ROLE={'v':'owner'}; CALLS=[]
async def handler(r):
  u=r.request.url
  if 'localhost' in u: return await r.continue_()
  if NEW not in u: return await r.fulfill(status=404,body='{}')
  J=lambda o,st=200: r.fulfill(status=st,content_type='application/json',body=json.dumps(o))
  if '/rpc/sch_my_stores' in u:
    if ROLE['v']=='hq': return await J([{"id":BON,"name":"일품집 본점","is_hq":True,"role":"hq","can_pay":True}])
    return await J([{"id":F1,"name":"유천점","is_hq":False,"role":"owner","can_pay":True}])
  if '/functions/v1/manage-accounts' in u:
    CALLS.append(json.loads(r.request.post_data)); return await J({"ok":True,"rows":[{"id":"staff1","hq":False,"me":False,"links":[{"store":"유천점","role":"order","pay":False}],"last":None,"banned":False}]})
  if '/functions/v1/create-account' in u: CALLS.append(json.loads(r.request.post_data)); return await J({"ok":True})
  await J([])
S={"ses":{"access_token":"tok","refresh_token":"r","expires_at":int(time.time())+3000,"user":{"email":"x@ilpum.invalid"}},"mode":"remote","url":"https://"+NEW,"key":"k"}
async def run(b):
  ctx=await b.new_context(viewport={'width':1200,'height':900}); pg=await ctx.new_page(); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
  pg.on('dialog',lambda d: asyncio.ensure_future(d.accept()))
  await pg.route('**/*',handler); await pg.route_web_socket(f'wss://{NEW}/**',lambda ws: asyncio.ensure_future(ws.close()))
  await pg.add_init_script(f"try{{ localStorage.setItem('ilpum-fr-conf',{json.dumps(json.dumps(S))}); }}catch(e){{}}")
  await pg.goto('http://localhost:8765/ilpum-schedule.html?view=acct'); await pg.wait_for_timeout(1800); return ctx,pg,errs
async def main():
  async with async_playwright() as p:
    b=await p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
    ctx,pg,errs=await run(b); t=await pg.inner_text('#main')
    print('점주 1) 계정 만들기 카드:', '계정 만들기' in t, '| 계정 목록:', 'staff1' in t, '| 데이터 카드 없음:', '기존 근무표 서버에서' not in t, '| 백업 카드 없음:', '전체 백업' not in t, '| 급여 비번 초기화 없음:', '급여 비밀번호 초기화' not in t)
    print('   역할 목록:', await pg.evaluate("[...document.querySelectorAll('#mkRole option')].map(o=>o.textContent.split(' ')[0])"), '| 매장:', await pg.evaluate("[...document.querySelectorAll('#mkStore option')].map(o=>o.textContent)"))
    await pg.fill('#mkId','yc_order'); await pg.fill('#mkPw','abcd1234'); await pg.select_option('#mkRole','order'); await pg.click('[data-a=mkaccount]'); await pg.wait_for_timeout(700)
    print('   만들기 호출:', [c for c in CALLS if 'id' in c][-1], '| 안내:', 'yc_order' in await pg.inner_text('#main'), '| errs', errs); await ctx.close()
    ROLE['v']='hq'; ctx,pg,errs=await run(b); t=await pg.inner_text('#main')
    print('   canEdit:', await pg.evaluate('canEdit()'), await pg.evaluate('JSON.stringify(APP.st)')); print('본사 2) 데이터 카드(본점):', '기존 근무표 서버에서' in t, '| 점주 옵션:', '점주' in await pg.evaluate("[...document.querySelectorAll('#mkRole option')].map(o=>o.textContent).join()"), '| 급여 비번 초기화:', '급여 비밀번호 초기화' in t, '| errs', errs); await ctx.close()
asyncio.run(main())
