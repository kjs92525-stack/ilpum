# 급여 보기 권한: 점주는 우리 매장 매니저에게만 켜고 끌 수 있음, 직원·발주 전용엔 버튼 없음 / 계정 만들 때 직원에 pay 안 보냄 (가짜 서버)
import asyncio, json, time
from playwright.async_api import async_playwright
NEW='bdqcrbnbuoujozlpttbe.supabase.co'; BON='0134d989-757a-4b60-9cb3-93245de2cac8'; F1='ad2ffdae-f76b-44cd-a6c6-58514c4e4638'
ROLE={'v':'owner'}; CALLS=[]
ROWS=[{"id":"mgr1","hq":False,"me":False,"links":[{"store":"유천점","role":"manager","pay":False}],"last":None,"banned":False},
      {"id":"stf1","hq":False,"me":False,"links":[{"store":"유천점","role":"staff","pay":False}],"last":None,"banned":False},
      {"id":"ord1","hq":False,"me":False,"links":[{"store":"유천점","role":"order","pay":False}],"last":None,"banned":False}]
HQROWS=[{"id":"hqmgr","hq":False,"me":False,"links":[{"store":"일품집 본점","role":"manager","pay":True}],"last":None,"banned":False},
        {"id":"ycmgr","hq":False,"me":False,"links":[{"store":"유천점","role":"manager","pay":False}],"last":None,"banned":False}]
async def handler(r):
  u=r.request.url
  if 'localhost' in u: return await r.continue_()
  if NEW not in u: return await r.fulfill(status=404,body='{}')
  J=lambda o,st=200: r.fulfill(status=st,content_type='application/json',body=json.dumps(o))
  if '/rpc/sch_my_stores' in u:
    if ROLE['v']=='hq': return await J([{"id":BON,"name":"일품집 본점","is_hq":True,"role":"hq","can_pay":True},{"id":F1,"name":"유천점","is_hq":False,"role":"hq","can_pay":False}])
    return await J([{"id":F1,"name":"유천점","is_hq":False,"role":"owner","can_pay":True}])
  if '/functions/v1/manage-accounts' in u:
    b=json.loads(r.request.post_data); CALLS.append(b)
    return await J({"ok":True,"rows":ROWS if ROLE['v']=='owner' else HQROWS})
  if '/functions/v1/create-account' in u: CALLS.append(json.loads(r.request.post_data)); return await J({"ok":True})
  await J([])
S={"ses":{"access_token":"tok","refresh_token":"r","expires_at":int(time.time())+3000,"user":{"email":"x@ilpum.invalid"}},"mode":"remote","url":"https://"+NEW,"key":"k"}
async def run(b):
  ctx=await b.new_context(viewport={'width':1200,'height':900}); pg=await ctx.new_page(); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
  pg.on('dialog',lambda d: asyncio.ensure_future(d.accept()))
  await pg.route('**/*',handler); await pg.route_web_socket(f'wss://{NEW}/**',lambda ws: asyncio.ensure_future(ws.close()))
  await pg.add_init_script(f"try{{ localStorage.setItem('ilpum-fr-conf',{json.dumps(json.dumps(S))}); }}catch(e){{}}")
  await pg.goto('http://localhost:8765/ilpum-schedule.html?view=set'); await pg.wait_for_timeout(1800); return ctx,pg,errs
async def main():
  ok=True
  def chk(n,c,x=''):
    nonlocal ok; ok&=bool(c); print('OK  ' if c else 'FAIL',n,x)
  async with async_playwright() as p:
    b=await p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
    ctx,pg,errs=await run(b)
    btns=await pg.evaluate("[...document.querySelectorAll('[data-a=acctpay]')].map(x=>x.dataset.id)")
    chk('점주: 매니저에게만 급여 버튼', btns==['mgr1'], str(btns))
    await pg.click('[data-a=acctpay][data-id=mgr1]'); await pg.wait_for_timeout(600)
    chk('점주: 켜기 호출', {'action':'setpay','id':'mgr1','on':True} in CALLS, str(CALLS[-2:]))
    await pg.select_option('#mkRole','staff'); await pg.check('#mkPay'); await pg.fill('#mkId','newstaff'); await pg.fill('#mkPw','abcd1234'); await pg.click('[data-a=mkaccount]'); await pg.wait_for_timeout(600)
    mk=[c for c in CALLS if c.get('id')=='newstaff']
    chk('점주: 직원 계정엔 급여 권한을 안 보냄', mk and mk[-1]['pay'] is False, str(mk))
    chk('점주: 오류 없음', not errs, str(errs)); await ctx.close()
    ROLE['v']='hq'; ctx,pg,errs=await run(b)
    btns=await pg.evaluate("[...document.querySelectorAll('[data-a=acctpay]')].map(x=>x.dataset.id)")
    chk('본사: 본점 매니저에게만 급여 버튼(가맹점 매니저는 없음)', btns==['hqmgr'], str(btns))
    chk('본사: 오류 없음', not errs, str(errs)); await ctx.close(); await b.close()
  print('전체 OK' if ok else '실패 있음')
asyncio.run(main())
