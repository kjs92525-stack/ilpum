# 통합 틀: 매장관리에서 가맹점을 추가하면 이미 열어 둔 예약·발주 화면에도 새 매장이 뜸 / "계정 · 권한" 메뉴는 본사·점주에게만 보이고 급여 권한 버튼이 거기 있음 (가짜 서버)
import asyncio, json, time
from playwright.async_api import async_playwright
NEW='bdqcrbnbuoujozlpttbe.supabase.co'; BON='0134d989-757a-4b60-9cb3-93245de2cac8'; F1='ad2ffdae-f76b-44cd-a6c6-58514c4e4638'
ROLE={'v':'hq'}; EXTRA=[]
ROWS=[{"id":"mgr1","hq":False,"me":False,"links":[{"store":"유천점","role":"manager","pay":False}],"last":None,"banned":False}]
def stores():
  if ROLE['v']=='hq':
    out=[{"id":BON,"name":"일품집 본점","is_hq":True,"role":"hq","can_pay":True},{"id":F1,"name":"유천점","is_hq":False,"role":"hq","can_pay":False}]
    out+=[{"id":i,"name":n,"is_hq":False,"role":"hq","can_pay":False} for i,n in EXTRA]; return out
  r={'owner':'owner','manager':'manager','staff':'staff'}[ROLE['v']]
  return [{"id":F1,"name":"유천점","is_hq":False,"role":r,"can_pay":r=='owner'}]
async def handler(r):
  u=r.request.url
  if 'localhost' in u: return await r.continue_()
  if NEW not in u: return await r.fulfill(status=404,body='{}')
  J=lambda o,st=200: r.fulfill(status=st,content_type='application/json',body=json.dumps(o))
  if '/rpc/sch_my_stores' in u: return await J(stores())
  if '/rpc/sch_create_store' in u:
    n=json.loads(r.request.post_data)['p_name']; EXTRA.append(('new-'+str(len(EXTRA)),n)); return await J('new-%d'%(len(EXTRA)-1))
  if '/functions/v1/manage-accounts' in u: return await J({"ok":True,"rows":ROWS})
  if '/rpc/pay_pin_status' in u: return await J({"has":True,"locked":0})
  await J([])
S={"ses":{"access_token":"tok","refresh_token":"r","expires_at":int(time.time())+3000,"user":{"email":"x@ilpum.invalid"}},"mode":"remote","url":"https://"+NEW,"key":"k"}
async def open_portal(b,hash_=''):
  ctx=await b.new_context(viewport={'width':1400,'height':900}); pg=await ctx.new_page(); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
  await pg.route('**/*',handler); await pg.route_web_socket(f'wss://{NEW}/**',lambda ws: asyncio.ensure_future(ws.close()))
  await pg.add_init_script(f"try{{ localStorage.setItem('ilpum-fr-conf',{json.dumps(json.dumps(S))}); }}catch(e){{}}")
  await pg.goto('http://localhost:8765/index.html'+hash_); await pg.wait_for_timeout(2500); return ctx,pg,errs
def fr(pg,name): return next((f for f in pg.frames if name in f.url),None)
async def main():
  ok=True
  def chk(n,c,x=''):
    nonlocal ok; ok&=bool(c); print('OK  ' if c else 'FAIL',n,x)
  async with async_playwright() as p:
    b=await p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
    # 1) 본사: 예약을 먼저 열어 둠 → 매장관리에서 가맹점 추가 → 다시 예약
    ctx,pg,errs=await open_portal(b)
    await pg.click('[data-go=res]'); await pg.wait_for_timeout(2500)
    opts=await fr(pg,'reserve.html').evaluate("[...document.querySelectorAll('#storeSel option')].map(o=>o.textContent)")
    chk('처음 예약 화면 매장 목록', len(opts)==2, str(opts))
    await pg.click('[data-go=hq]'); await pg.wait_for_timeout(2500)
    await fr(pg,'ilpum-schedule.html').evaluate("(async()=>{ await APP.be.createStore('x','수성점'); APP.stores=await APP.be.stores(); notifyStores(); })()"); await pg.wait_for_timeout(500)
    chk('가맹점 추가하면 열어 둔 예약 화면이 정리됨', fr(pg,'reserve.html') is None)
    await pg.click('[data-go=res]'); await pg.wait_for_timeout(3000)
    opts=await fr(pg,'reserve.html').evaluate("[...document.querySelectorAll('#storeSel option')].map(o=>o.textContent)")
    chk('다시 열면 새 매장이 예약 화면 목록에 있음', '수성점' in opts, str(opts))
    vis=await pg.evaluate("[...document.querySelectorAll('#menu [data-acct]')].map(b=>b.hidden)")
    chk('본사: 계정·권한 메뉴 보임', vis==[False], str(vis))
    await pg.click('[data-go=acct]'); await pg.wait_for_timeout(2500)
    f=fr(pg,'ilpum-schedule.html'); t=await f.inner_text('#main')
    chk('계정·권한 화면에 계정 만들기·목록', '계정 만들기' in t and 'mgr1' in t)
    chk('오류 없음(본사)', not errs, str(errs)); await ctx.close()
    # 2) 점주: 메뉴 보임 + 매니저 급여 버튼
    ROLE['v']='owner'; ctx,pg,errs=await open_portal(b)
    vis=await pg.evaluate("[...document.querySelectorAll('#menu [data-acct]')].map(b=>b.hidden)")
    chk('점주: 계정·권한 메뉴 보임', vis==[False], str(vis))
    await pg.click('[data-go=acct]'); await pg.wait_for_timeout(2500)
    f=fr(pg,'ilpum-schedule.html'); btn=await f.evaluate("!!document.querySelector('[data-a=acctpay][data-id=mgr1]')")
    chk('점주: 매니저 급여 보기 버튼이 계정·권한 화면에 있음', btn)
    chk('오류 없음(점주)', not errs, str(errs)); await ctx.close()
    # 3) 매니저·직원: 메뉴 안 보임
    for role in ('manager','staff'):
      ROLE['v']=role; ctx,pg,errs=await open_portal(b)
      vis=await pg.evaluate("[...document.querySelectorAll('#menu [data-acct]')].map(b=>b.hidden)")
      chk(f'{role}: 계정·권한 메뉴 숨김', vis==[True], str(vis)); await ctx.close()
    await b.close()
  print('전체 OK' if ok else '실패 있음')
asyncio.run(main())
