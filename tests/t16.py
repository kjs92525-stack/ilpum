import asyncio, json, time
from playwright.async_api import async_playwright
URL='https://bdqcrbnbuoujozlpttbe.supabase.co'; BON='0134d989-757a-4b60-9cb3-93245de2cac8'
SENT=[]
ST={'valid_refresh':{'r1'}, 'n':0, 'logins':0, 'refreshes':0, 'tokens_seen':[]}
async def handler(r):
  u=r.request.url; m=r.request.method; h=r.request.headers
  if 'jsdelivr' in u: return await r.abort()
  if not u.startswith(URL): return await r.continue_()
  J=lambda o,st=200: r.fulfill(status=st,content_type='application/json',body=json.dumps(o))
  if '/auth/v1/token' in u:
    body=json.loads(r.request.post_data)
    if 'grant_type=password' in u:
      SENT.append(body['email'])
      if body['password']!='good' or body['email'] not in ('ilpum@ilpum.invalid',): return await J({"error_description":"Invalid login credentials"},400)
      ST['logins']+=1; ST['n']+=1; rt=f"r{ST['n']+1}"; ST['valid_refresh']={rt}
      return await J({"access_token":f"at{ST['n']}","refresh_token":rt,"expires_at":int(time.time())+3600,"user":{"id":"u","email":body['email']}})
    if 'grant_type=refresh_token' in u:
      if body['refresh_token'] not in ST['valid_refresh']: return await J({"error_description":"Invalid Refresh Token"},400)
      ST['refreshes']+=1; ST['n']+=1; rt=f"r{ST['n']+1}"; ST['valid_refresh']={rt}
      return await J({"access_token":f"at{ST['n']}","refresh_token":rt,"expires_at":int(time.time())+3600,"user":{"id":"u","email":"yoyo925@naver.com"}})
  if '/rpc/sch_my_stores' in u:
    ST['tokens_seen'].append(h.get('authorization')); return await J([{"id":BON,"name":"일품집 본점","is_hq":True,"role":"hq","can_pay":True,"staff_id":None}])
  if '/rpc/sch_open_store' in u: return await J([{"id":BON,"name":"일품집 본점","has_pin":False}])
  if '/sch_items' in u:
    if m=='POST': return await r.fulfill(status=201,body='')
    if 'updated_at=gt' in u: return await J([])
    return await J([{"kind":"cfg","id":"positions","data":[{"name":"홀","color":"#2F6B3F","req":[0]*7}],"deleted":False,"updated_at":"2026-09-30T00:00:00Z"}])
  if '/rpc/' in u or '/sch_summaries' in u: return await J([])
  await r.fulfill(status=404,body='{}')
async def main():
  async with async_playwright() as p:
    b=await p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
    ctx=await b.new_context(viewport={'width':420,'height':800}); pg=await ctx.new_page(); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
    await pg.route('**/*', handler)
    await pg.goto('http://localhost:8765/ilpum-schedule.html'); await pg.wait_for_timeout(800)
    print('1) 처음엔 로그인 화면:', await pg.is_visible('#lgForm'), '| 자동 로그인 기본 체크:', await pg.is_checked('#lgKeep'), '| 입력칸 autocomplete:', await pg.get_attribute('#lgEmail','autocomplete'), '/', await pg.get_attribute('#lgPw','autocomplete'))
    await pg.fill('#lgEmail','ilpum'); await pg.fill('#lgPw','wrong'); await pg.press('#lgPw','Enter'); await pg.wait_for_timeout(500); print('2) 틀린 비번:', await pg.inner_text('#toast'))
    await pg.fill('#lgPw','good'); await pg.press('#lgPw','Enter'); await pg.wait_for_timeout(1300)
    print('3) 로그인됨 role:', await pg.evaluate("role()"), '| 금액 보기 버튼:', await pg.is_visible('[data-a="paytog"]'), '| 로그아웃 버튼:', await pg.is_visible('[data-a="logout"]'))
    saved=await pg.evaluate("JSON.parse(localStorage.getItem('ilpum-fr-conf'))")
    print('   서버로 보낸 로그인 주소:', SENT, '| 입력칸 종류:', await pg.evaluate('0') if False else '')
    print('4) 저장된 것: 토큰 있음', bool(saved.get('ses',{}).get('refresh_token')), '| 기억된 아이디', saved.get('email'), '| 비밀번호가 저장소에 그대로 있나:', 'good' in json.dumps(saved))
    await pg.reload(); await pg.wait_for_timeout(1000); print('5) 새로고침 → 로그인 화면 안 나옴:', not await pg.is_visible('#lgForm'), '| role', await pg.evaluate("role()"))
    # 토큰 만료 → 자동 갱신
    await pg.evaluate("const c=JSON.parse(localStorage.getItem('ilpum-fr-conf')); c.ses.expires_at=Math.floor(Date.now()/1000)-10; localStorage.setItem('ilpum-fr-conf',JSON.stringify(c))")
    rf=ST['refreshes']; await pg.reload(); await pg.wait_for_timeout(1000); print('6) 만료된 토큰 → 자동 갱신 후 바로 열림:', not await pg.is_visible('#lgForm'), '| 갱신 횟수 증가', ST['refreshes']-rf)
    # 갱신 토큰이 취소됨 → 로그인 화면(이메일은 채워짐)
    ST['valid_refresh']=set(); await pg.evaluate("const c=JSON.parse(localStorage.getItem('ilpum-fr-conf')); c.ses.expires_at=Math.floor(Date.now()/1000)-10; localStorage.setItem('ilpum-fr-conf',JSON.stringify(c))")
    await pg.reload(); await pg.wait_for_timeout(1000); print('7) 토큰 취소됨 → 로그인 화면:', await pg.is_visible('#lgForm'), '| 아이디 미리 채워짐:', await pg.input_value('#lgEmail'))
    # 다시 로그인 → 로그아웃
    await pg.fill('#lgPw','good'); await pg.press('#lgPw','Enter'); await pg.wait_for_timeout(1200)
    await pg.click('#mbar [data-v="set"]'); await pg.wait_for_timeout(300); print('   (폰) 설정 화면에 로그아웃 버튼:', await pg.is_visible('#main [data-a="logout"]'))
    await pg.click('#main [data-a="logout"]'); await pg.wait_for_timeout(900); print('8) 로그아웃 → 로그인 화면:', await pg.is_visible('#lgForm'), '| 토큰 삭제됨:', not (await pg.evaluate("JSON.parse(localStorage.getItem('ilpum-fr-conf')).ses")))
    await pg.reload(); await pg.wait_for_timeout(700); print('9) 로그아웃 뒤 새로고침해도 로그인 화면:', await pg.is_visible('#lgForm'))
    # 자동 로그인 끄고 로그인 → 같은 탭에선 유지, 새 창에선 다시 로그인
    await pg.fill('#lgPw','good'); await pg.uncheck('#lgKeep'); await pg.press('#lgPw','Enter'); await pg.wait_for_timeout(1200)
    await pg.reload(); await pg.wait_for_timeout(900); print('10) 자동 로그인 끔: 같은 탭 새로고침은 유지:', not await pg.is_visible('#lgForm'), '| 기기 저장소엔 토큰 없음:', not (await pg.evaluate("JSON.parse(localStorage.getItem('ilpum-fr-conf')).ses")))
    pg2=await ctx.new_page(); await pg2.route('**/*',handler); await pg2.goto('http://localhost:8765/ilpum-schedule.html'); await pg2.wait_for_timeout(900); print('11) 새 탭에선 다시 로그인 요구:', await pg2.is_visible('#lgForm'))
    # 로그인 없이 보기 / 다시 로그인
    await pg2.click('[data-a="openmode"]'); await pg2.wait_for_timeout(1000); print('12) 로그인 없이 보기:', await pg2.evaluate("role()"), '| 금액 버튼 숨김:', not await pg2.is_visible('[data-a="paytog"]'), '| 로그인 버튼:', await pg2.is_visible('[data-a="gologin"]'))
    await pg2.click('#mbar [data-v="set"]'); await pg2.wait_for_timeout(300); await pg2.click('#main [data-a="gologin"]'); await pg2.wait_for_timeout(800); print('13) 로그인 버튼 → 로그인 화면:', await pg2.is_visible('#lgForm'))
    await pg2.fill('#lgEmail','ILPUM'); await pg2.fill('#lgPw','good'); await pg2.press('#lgPw','Enter'); await pg2.wait_for_timeout(1200)
    print('14) 대문자 ILPUM 도 로그인됨:', await pg2.evaluate("role()"), '| 화면에 표시되는 아이디:', await pg2.evaluate("showId(APP.user.email)"))
    await pg2.click('#mbar [data-v="set"]'); await pg2.wait_for_timeout(300); print('15) 설정의 로그인 표시:', [l for l in (await pg2.inner_text('#main')).split('\n') if l.startswith('로그인:')][:1])
    await pg2.click('#main [data-a="logout"]'); await pg2.wait_for_timeout(800)
    await pg2.fill('#lgEmail','ilpum@ilpum.invalid'); await pg2.fill('#lgPw','good'); await pg2.press('#lgPw','Enter'); await pg2.wait_for_timeout(1200); print('16) 이메일 형식으로 쳐도 로그인됨:', await pg2.evaluate("role()"))
    print('서버로 나간 주소들:', sorted(set(SENT)))
    print('errs',errs); await b.close()
asyncio.run(main())
