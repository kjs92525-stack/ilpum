import asyncio, json
from playwright.async_api import async_playwright
URL='https://bdqcrbnbuoujozlpttbe.supabase.co'; BON='0134d989-757a-4b60-9cb3-93245de2cac8'
CALLS=[]
async def main():
  async with async_playwright() as p:
    b=await p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome',ignore_default_args=['--hide-scrollbars'])
    pg=await b.new_page(viewport={'width':1300,'height':860}); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
    async def route(r):
      u=r.request.url; m=r.request.method
      if 'jsdelivr' in u: return await r.abort()
      if not u.startswith(URL): return await r.continue_()
      J=lambda o: r.fulfill(status=200,content_type='application/json',body=json.dumps(o))
      fn=u.split('/rpc/')[1] if '/rpc/' in u else u.split('/rest/v1/')[1][:20]; CALLS.append(fn)
      assert '/auth/' not in u
      if '/rpc/sch_open_store' in u: return await J([{"id":BON,"name":"일품집 본점","has_pin":False}])
      if '/rpc/sch_put_many' in u: return await J('ok')
      if '/sch_items' in u:
        if 'updated_at=gt' in u: return await J([])
        return await J([{"kind":"cfg","id":"positions","data":[{"name":"카운터","color":"#3C5A86","req":[0]*7},{"name":"홀","color":"#2F6B3F","req":[0]*7}],"deleted":False,"updated_at":"2026-09-30T00:00:00Z"},
                        {"kind":"staff","id":"s1","data":{"id":"s1","name":"홍길동","pos":"홀","type":"regular","off":[],"active":True,"order":0},"deleted":False,"updated_at":"2026-09-30T00:00:00Z"}])
      await r.fulfill(status=404,body='{}')
    await pg.route('**/*', route)
    await pg.goto('file:///home/claude/fr/ilpum-schedule.html'); await pg.evaluate("localStorage.clear(); sessionStorage.clear(); localStorage.setItem('ilpum-fr-conf', JSON.stringify({mode:'remote',openOnly:true}))"); await pg.reload(); await pg.wait_for_timeout(900)
    body=await pg.inner_text('body')
    print('바로 열림:', await pg.evaluate("role()")=='open', '| 편집 가능:', await pg.evaluate("canEdit()"), '| 화면에 직원 보임:', '홍길동' in body)
    print('(로그인 없이 보기) 화면에 비밀번호/잠금 글자 없음:', not any(w in body for w in ['비밀번호','잠금']))
    await pg.click('#nav [data-v="set"]'); await pg.wait_for_timeout(200)
    body=await pg.inner_text('#main'); print('설정에 비밀번호 글자 없음:', '비밀번호' not in body)
    await pg.click('#nav [data-v="staff"]'); await pg.click('[data-a="staffnew"]'); await pg.fill('#sfName','새직원'); await pg.click('[data-a="staffsave"]'); await pg.wait_for_timeout(900)
    print('저장 호출:', [c for c in CALLS if 'put' in c], '| 표시:', await pg.inner_text('#sync'))
    print('비번·인증 서버 호출 없음:', not any(('pin' in c or 'auth' in c) for c in CALLS))
    print('errs',errs); await b.close()
asyncio.run(main())
