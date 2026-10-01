import asyncio, json
from playwright.async_api import async_playwright
URL='https://bdqcrbnbuoujozlpttbe.supabase.co'
BON='0134d989-757a-4b60-9cb3-93245de2cac8'
STATE={'pin':False}; CALLS=[]; ITEMS=[]; AUTHED=[]
async def main():
  async with async_playwright() as p:
    b=await p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome',ignore_default_args=['--hide-scrollbars'])
    pg=await b.new_page(viewport={'width':1300,'height':860}); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
    async def route(r):
      u=r.request.url; m=r.request.method; h=r.request.headers
      if 'jsdelivr' in u: return await r.abort()
      if not u.startswith(URL): return await r.continue_()
      J=lambda o: r.fulfill(status=200,content_type='application/json',body=json.dumps(o))
      if '/auth/v1/token' in u: return await J({"access_token":"tok","refresh_token":"ref","expires_at":9999999999,"user":{"id":"u","email":"yoyo925@naver.com"}})
      if '/rpc/sch_open_store' in u: return await J([{"id":BON,"name":"일품집 본점","has_pin":STATE['pin']}])
      if '/rpc/sch_my_stores' in u: return await J([{"id":BON,"name":"일품집 본점","is_hq":True,"role":"hq","can_pay":True,"staff_id":None}])
      body=json.loads(r.request.post_data) if r.request.post_data else {}
      if '/rpc/sch_put_many' in u:
        CALLS.append(('put_many',body['p_pin'],len(body['p_rows']),[x['kind'] for x in body['p_rows']]))
        if STATE['pin'] and body['p_pin']!='secret12': return await J('bad_pin')
        return await J('ok')
      if '/rpc/sch_put_summary' in u: CALLS.append(('summary',body['p_pin'])); return await J('ok' if (not STATE['pin'] or body['p_pin']=='secret12') else 'bad_pin')
      if '/rpc/sch_check_pin' in u: return await J('ok' if (not STATE['pin'] or body['p_pin']=='secret12') else 'bad_pin')
      if '/rpc/sch_set_pin' in u:
        STATE['pin']=True; CALLS.append(('set_pin',body['p_new'])); return await J('ok')
      if '/rpc/sch_clear_pin' in u:
        CALLS.append(('clear_pin',body['p_old'])); 
        if STATE['pin'] and body['p_old']!='secret12': return await J('bad_pin')
        STATE['pin']=False; return await J('ok')
      if '/sch_items' in u:
        if m=='POST': AUTHED.append(('rest_post',h.get('authorization','')[:9])); return await r.fulfill(status=201,body='')
        assert h.get('authorization','').startswith('Bearer eyJ') or h.get('authorization')=='Bearer tok'
        if 'updated_at=gt' in u: return await J([])
        return await J([{"kind":"cfg","id":"positions","data":[{"name":"카운터","color":"#3C5A86","req":[0]*7},{"name":"홀","color":"#2F6B3F","req":[0]*7}],"deleted":False,"updated_at":"2026-09-30T00:00:00Z"}])
      if '/sch_summaries' in u: return await J([])
      await r.fulfill(status=404,body='{}')
    await pg.route('**/*', route)
    await pg.goto('file:///home/claude/fr/ilpum-schedule.html'); await pg.evaluate("localStorage.clear(); sessionStorage.clear()"); await pg.reload(); await pg.wait_for_timeout(900)
    print('로그인 화면 없이 바로 열림:', not await pg.is_visible('#lgEmail'), '| 열린 매장:', await pg.evaluate("APP.st&&APP.st.name"), '| role:', await pg.evaluate("role()"))
    print('편집 가능(비번 없음):', await pg.evaluate("canEdit()"), '| 금액 버튼 숨김:', not await pg.is_visible('[data-a="paytog"]'), '| 잠금 버튼 없음:', not await pg.is_visible('[data-a="pinopen"]'))
    # 직원 추가 (비밀번호 묻지 않고 저장)
    await pg.click('#nav [data-v="staff"]'); await pg.click('[data-a="staffnew"]'); await pg.fill('#sfName','홍길동'); await pg.click('[data-a="staffsave"]'); await pg.wait_for_timeout(1000)
    print('저장 호출:', CALLS[-1], '| 표시:', await pg.inner_text('#sync'))
    # 설정: 비밀번호 카드
    await pg.click('#nav [data-v="set"]'); await pg.wait_for_timeout(200)
    txt=await pg.inner_text('#main'); print('설정에 비밀번호 카드:', '편집 비밀번호' in txt and '꺼져 있어요' in txt, '| 관리자 로그인 버튼:', await pg.is_visible('.card [data-a="adminlogin"]'))
    # 비밀번호 켜기
    await pg.fill('#pnNew','secret12'); await pg.click('[data-a="pinset"]'); await pg.wait_for_timeout(500)
    print('켠 뒤: hasPin', await pg.evaluate("APP.st.hasPin"), '| 편집중 잠금버튼:', await pg.is_visible('[data-a="pinlock"]'))
    # 새로고침 → 잠금 상태에서 시작 (세션 기억은 켠 직후 세션에 저장되므로 지우고 확인)
    await pg.evaluate("sessionStorage.clear(); localStorage.clear()"); await pg.reload(); await pg.wait_for_timeout(900)
    print('새로고침 후 편집 잠김:', not await pg.evaluate("canEdit()"), '| 잠금해제 버튼:', await pg.is_visible('[data-a="pinopen"]'))
    await pg.click('#nav [data-v="cards"]'); await pg.locator('.dcard .chip').first.click() if await pg.locator('.dcard .chip').count() else None
    await pg.click('[data-a="pinopen"]'); await pg.fill('#pinIn','wrong'); await pg.click('[data-a="pinok"]'); await pg.wait_for_timeout(400); print('틀린 비번:', await pg.inner_text('#toast'))
    await pg.fill('#pinIn','secret12'); await pg.click('[data-a="pinok"]'); await pg.wait_for_timeout(500); print('맞는 비번 → 편집:', await pg.evaluate("canEdit()"))
    # 비밀번호 끄기
    await pg.click('#nav [data-v="set"]'); await pg.fill('#pnOld','secret12'); await pg.click('[data-a="pinclear"]'); await pg.wait_for_timeout(500)
    print('끈 뒤: hasPin', await pg.evaluate("APP.st.hasPin"), '| 편집 가능:', await pg.evaluate("canEdit()"))
    # 관리자 로그인 경로
    await pg.click('.card [data-a="adminlogin"]'); await pg.wait_for_timeout(900)
    print('관리자 로그인 화면:', await pg.is_visible('#lgEmail'), '| "로그인 없이 열기" 버튼:', await pg.is_visible('[data-a="openmode"]'))
    await pg.fill('#lgEmail','yoyo925@naver.com'); await pg.fill('#lgPw','pw'); await pg.click('[data-a="login"]'); await pg.wait_for_timeout(1200)
    print('로그인 후: role', await pg.evaluate("role()"), '| 금액 보기 버튼:', await pg.is_visible('[data-a="paytog"]'), '| 사용자:', await pg.evaluate("APP.user.email"))
    await pg.click('#nav [data-v="staff"]'); await pg.click('[data-a="staffnew"]'); await pg.fill('#sfName','로그인직원'); await pg.click('[data-a="staffsave"]'); await pg.wait_for_timeout(900); print('로그인 저장 경로:', AUTHED[-1])
    await pg.evaluate("Conf.ses=null; Conf.forceLogin=false; saveConf()"); await pg.reload(); await pg.wait_for_timeout(700); print('로그아웃 후 다시 로그인 없이 열림:', not await pg.is_visible('#lgEmail') and await pg.evaluate("role()")=='open')
    print('errs',errs); await b.close()
asyncio.run(main())
