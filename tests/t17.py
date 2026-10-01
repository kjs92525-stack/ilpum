# 본사=모든 매장 관리 / 가맹점=자기 매장만 / 계정 만들기는 본사만 (가짜 서버)
import asyncio, json, time, os
from playwright.async_api import async_playwright
DIST=os.environ.get('DIST','/home/user/ilpum/dist')
URL='https://bdqcrbnbuoujozlpttbe.supabase.co'; BON='0134d989-757a-4b60-9cb3-93245de2cac8'; F1='ad2ffdae-f76b-44cd-a6c6-58514c4e4638'
WHO={'v':'hq'}; CALLS=[]; ITEMS_FOR=[]
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
  if '/sch_items' in u:
    if m=='POST': return await r.fulfill(status=201,body='')
    if 'updated_at=gt' in u: return await J([])
    ITEMS_FOR.append(u.split('store_id=eq.')[1][:36] if 'store_id=eq.' in u else '')
    return await J([{"kind":"cfg","id":"positions","data":[{"name":"홀","color":"#2F6B3F","req":[0]*7}],"deleted":False,"updated_at":"2026-09-30T00:00:00Z"}])
  if '/rpc/' in u or '/sch_summaries' in u: return await J([])
  await r.fulfill(status=404,body='{}')
async def login(pg,uid):
  await pg.goto(f'file://{DIST}/ilpum-schedule.html'); await pg.wait_for_timeout(600)
  await pg.fill('#lgEmail',uid); await pg.fill('#lgPw','pw12345678'); await pg.press('#lgPw','Enter'); await pg.wait_for_timeout(1200)
async def main():
  async with async_playwright() as p:
    b=await p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
    # ---- 본사
    ctx=await b.new_context(viewport={'width':1200,'height':900}); pg=await ctx.new_page(); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
    await pg.route('**/*', handler); await login(pg,'ilpum')
    print('본사 role:', await pg.evaluate("role()"), '| 본사 현황 메뉴:', await pg.is_visible('#nav [data-v="hq"], #nav button:has-text("본사 현황")'))
    await pg.click('[data-a="stores"]'); await pg.wait_for_timeout(300)
    names=await pg.evaluate("[...document.querySelectorAll('#drawer [data-a=gostore] .wn')].map(e=>e.textContent)"); print('매장 바꾸기 목록:', names)
    await pg.click(f'#drawer [data-a="gostore"][data-id="{F1}"]'); await pg.wait_for_timeout(600)
    print('가맹점 1 열림:', await pg.evaluate("APP.sid")==F1, '| 가맹점 데이터 요청함:', F1 in ITEMS_FOR, '| 편집 가능:', await pg.evaluate("canEdit()"), '| 금액 권한:', await pg.evaluate("APP.st.pay"))
    await pg.evaluate("APP.view='set'; render()"); await pg.wait_for_timeout(300)
    print('계정 만들기 카드 보임:', await pg.is_visible('#mkForm'), '| 매장 선택지:', await pg.evaluate("[...document.querySelectorAll('#mkStore option')].map(o=>o.textContent)"))
    await pg.click('[data-a="mkaccount"]'); print('빈 칸 안내:', await pg.inner_text('#toast'))
    await pg.fill('#mkId','suseong'); await pg.fill('#mkPw','short'); await pg.click('[data-a="mkaccount"]'); print('짧은 비번 안내:', await pg.inner_text('#toast'), '| 서버 호출 수:', len(CALLS))
    await pg.fill('#mkPw','longpassword1'); await pg.select_option('#mkStore',F1); await pg.select_option('#mkRole','owner'); await pg.click('[data-a="mkaccount"]'); await pg.wait_for_timeout(400)
    print('만들기 결과:', await pg.inner_text('#toast'), '| 보낸 내용:', CALLS[-1][0], '| 로그인 토큰 첨부:', CALLS[-1][1]=='Bearer at', '| 입력칸 비워짐:', await pg.input_value('#mkPw')=='')
    await pg.fill('#mkId','dup'); await pg.fill('#mkPw','longpassword1'); await pg.click('[data-a="mkaccount"]'); await pg.wait_for_timeout(400); print('중복 아이디:', await pg.inner_text('#toast'))
    print('본사 errs', errs)
    # ---- 가맹점 점주
    ctx2=await b.new_context(viewport={'width':1200,'height':900}); pg2=await ctx2.new_page(); errs2=[]; pg2.on('pageerror',lambda e:errs2.append(str(e)))
    await pg2.route('**/*', handler); await login(pg2,'suseong')
    print('점주 role:', await pg2.evaluate("role()"), '| 매장:', await pg2.evaluate("APP.stores.map(s=>s.name)"), '| 본사 현황 메뉴:', await pg2.is_visible('#nav button:has-text("본사 현황")'))
    await pg2.evaluate("APP.view='set'; render()"); await pg2.wait_for_timeout(300)
    print('점주에게 계정 만들기 카드:', await pg2.is_visible('#mkForm'), '| 매장 바꾸기 버튼:', await pg2.is_visible('[data-a="stores"] small:has-text("매장 바꾸기")'))
    print('점주 errs', errs2)
asyncio.run(main())
