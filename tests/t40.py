# 본사=모든 매장 관리 / 가맹점=자기 매장만 / 계정 만들기는 본사만 (가짜 서버)
import asyncio, json, time, os
from playwright.async_api import async_playwright
DIST=os.environ.get('DIST','/home/user/ilpum/dist')
URL='https://bdqcrbnbuoujozlpttbe.supabase.co'; BON='0134d989-757a-4b60-9cb3-93245de2cac8'; F1='ad2ffdae-f76b-44cd-a6c6-58514c4e4638'
WHO={'v':'hq'}; CALLS=[]; ITEMS_FOR=[]; RESTORED=[]; NEWROWS={}; SYNC={'auto':False,'calls':[]}
STORES={'hq':[{"id":BON,"name":"일품집 본점","is_hq":True,"role":"hq","can_pay":True,"staff_id":None},{"id":F1,"name":"가맹점 1","is_hq":False,"role":"hq","can_pay":False,"staff_id":None}],
        'owner':[{"id":F1,"name":"가맹점 1","is_hq":False,"role":"owner","can_pay":True,"staff_id":None}]}
async def handler(r):
  u=r.request.url; m=r.request.method; h=r.request.headers
  if 'jsdelivr' in u: return await r.abort()
  if not u.startswith(URL): return await r.continue_()
  J=lambda o,st=200: r.fulfill(status=st,content_type='application/json',body=json.dumps(o))
  if '/auth/v1/token' in u:
    b=json.loads(r.request.post_data); WHO['v']='hq' if b['email']=='ilpum@ilpum.invalid' else 'owner'
    return await J({"access_token":"at","refresh_token":"rt","expires_at":int(time.time())+3600,"user":{"id":"u","email":b['email']}})
  if '/rpc/sch_my_stores' in u: return await J(STORES[WHO['v']])
  if '/functions/v1/create-account' in u:
    b=json.loads(r.request.post_data); CALLS.append((b,h.get('authorization')))
    if b['id']=='dup': return await J({"error":"이미 있는 아이디예요"},409)
    return await J({"ok":True})
  if '/rpc/sync_status' in u: return await J({'enabled':True,'auto':SYNC['auto'],'last':{'ok':True,'daysChanged':42,'sched':{'upserted':3,'pruned':1}},'at':'2026-10-02T06:00:00Z'})
  if '/rpc/sync_run_now' in u: SYNC['calls'].append(('run',json.loads(r.request.post_data))); return await r.fulfill(status=204,body='')
  if '/rpc/sync_auto_set' in u: b=json.loads(r.request.post_data); SYNC['calls'].append(('auto',b)); SYNC['auto']=b['p_on']; return await r.fulfill(status=204,body='')
  if '/rest/v1/res_days' in u and m=='GET': return await J([{"store_id":BON,"id":"2026-10-01","data":{"items":[{"name":"손님"}]},"rev":3}])
  if '/rest/v1/res_days' in u and m=='POST': RESTORED.append(('res_days',u,json.loads(r.request.post_data),h.get('prefer'))); return await r.fulfill(status=201,body='')
  if '/rest/v1/board_msgs' in u and m=='POST': RESTORED.append(('board_msgs',)); return await r.fulfill(status=201,body='')
  if any(t in u for t in ('/rest/v1/wh_items','/rest/v1/wh_orders','/rest/v1/board_notices','/rest/v1/board_msgs')) and m=='GET': return await J([])
  if '/sch_items' in u:
    if m=='POST': RESTORED.append(('sch_items',u,json.loads(r.request.post_data),h.get('prefer'))); return await r.fulfill(status=201,body='')
    if 'offset=' in u: return await J([{"store_id":BON,"kind":"cfg","id":"positions","data":[{"name":"홀"}],"deleted":False,"updated_at":"2026-09-30T00:00:00Z"}])
    if 'updated_at=gt' in u: return await J([])
    ITEMS_FOR.append(u.split('store_id=eq.')[1][:36] if 'store_id=eq.' in u else '')
    return await J([{"kind":"cfg","id":"positions","data":[{"name":"홀","color":"#2F6B3F","req":[0]*7}],"deleted":False,"updated_at":"2026-09-30T00:00:00Z"}])
  if '/rpc/' in u or '/sch_summaries' in u: return await J([])
  await r.fulfill(status=404,body='{}')
async def login(pg,uid):
  await pg.goto(f'file://{DIST}/ilpum-schedule.html'); await pg.wait_for_timeout(600)
  await pg.fill('#lgEmail',uid); await pg.fill('#lgPw','pw12345678'); await pg.press('#lgPw','Enter'); await pg.wait_for_timeout(1200)
async def main():
  ok=True
  def chk(n,c):
    nonlocal ok; ok&=bool(c); print(('OK  ' if c else 'FAIL'),n)
  async with async_playwright() as p:
    b=await p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
    ctx=await b.new_context(viewport={'width':1200,'height':900}); pg=await ctx.new_page(); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.on('dialog',lambda d: asyncio.ensure_future(d.accept()))
    await pg.route('**/*', handler); await login(pg,'ilpum')
    await pg.evaluate("APP.view='set'; render()"); await pg.wait_for_timeout(600)
    txt=await pg.inner_text('#main')
    chk('본사: 자동 연동 카드 + 상태(꺼짐) + 마지막 실행 요약', '예전 서버 자동 연동' in txt and '자동 연동 꺼짐' in txt and '예약 42일 확인' in txt and '근무표 3줄 바뀜' in txt)
    await pg.click('[data-a="syncon"]'); await pg.wait_for_timeout(15500)
    chk('자동 켜기 → 켜고 처음부터 한 번 실행 요청', SYNC['calls'][:2]==[('auto',{'p_on':True}),('run',{'p_full':True})])
    chk('켜진 뒤 화면: 켜짐 + 끄기 버튼', '자동 연동 켜짐' in await pg.inner_text('#main') and await pg.is_visible('[data-a="syncoff"]'))
    await pg.click('[data-a="syncoff"]'); await pg.wait_for_timeout(1200)
    chk('끄기 → 꺼짐', SYNC['calls'][-1]==('auto',{'p_on':False}) and '자동 연동 꺼짐' in await pg.inner_text('#main'))
    await pg.click('[data-a="syncrun"]'); await pg.wait_for_timeout(500); chk('지금 한 번 가져오기 요청', SYNC['calls'][-1]==('run',{'p_full':True}))
    chk('오류 없음', not errs); await ctx.close()
    ctx2=await b.new_context(viewport={'width':1200,'height':900}); pg2=await ctx2.new_page(); await pg2.route('**/*', handler); await login(pg2,'suseong')
    await pg2.evaluate("APP.view='set'; render()"); await pg2.wait_for_timeout(400)
    chk('점주: 카드 안 보임', '예전 서버 자동 연동' not in await pg2.inner_text('#main'))
  print('전체','OK' if ok else 'FAIL')
asyncio.run(main())
