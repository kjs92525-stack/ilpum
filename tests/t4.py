import asyncio, json, re
from playwright.async_api import async_playwright
URL='https://abcd.supabase.co'
ITEMS=[]; POSTS=[]; SUMS=[]
async def main():
  async with async_playwright() as p:
    b=await p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
    pg=await b.new_page(viewport={'width':1300,'height':900}); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
    async def route(r):
      u=r.request.url; m=r.request.method
      if 'jsdelivr' in u: return await r.abort()
      if 'fmzpmekypmjuydgxpnlu' in u:   # 기존 근무표 서버
        old={"staff":[{"id":"a1","name":"김지수","pos":"홀","kind":"staff","off":[5],"wk":{"1":{"sh":{"k":"pm"},"pay":{"k":"day","v":70000}}}},{"id":"a3","name":"준우","pos":"그릴","kind":"fixed","off":[]}],
             "ex":[{"id":"e1","date":"2026-10-01","type":"당일알바","name":"박알바","pos":"홀","pay":{"k":"day","v":50000},"pm":True},{"id":"e2","date":"2026-10-02","type":"월차","staffId":"a1"}],
             "rules":[{"id":"r1","ids":["a1"],"from":"2026-10-05","to":"2026-10-07","days":[],"w":"off","memo":"휴가","pay":{"k":"day","v":1},"at":1}],
             "dc":{"2026-10-01|a1":{"sh":{"k":"t","s":"11:00","e":""},"pay":{"k":"day","v":150000}}},"notes":{"2026-10-01|a1":"메모테스트"},
             "aw":{"2026-09-28":{"a3":{"off":[0],"pm":[1]}}},"targets":{"홀":{"wd":2,"we":3}}}
        return await r.fulfill(status=200,content_type='application/json',body=json.dumps([{"data":old}]))
      if not u.startswith(URL): return await r.continue_()
      if '/auth/v1/token' in u:
        return await r.fulfill(status=200,content_type='application/json',body=json.dumps({"access_token":"tok","refresh_token":"ref","expires_at":9999999999,"user":{"id":"u1","email":"boss@ilpum.kr"}}))
      if '/sch_members' in u: return await r.fulfill(status=200,content_type='application/json',body=json.dumps([{"store_id":"bonjum","role":"hq","can_pay":True,"staff_id":None}]))
      if '/sch_stores' in u: return await r.fulfill(status=200,content_type='application/json',body=json.dumps([{"id":"bonjum","name":"일품집 본점"},{"id":"suseong","name":"수성점"}]))
      if '/sch_summaries' in u:
        if m=='POST': SUMS.append(json.loads(r.request.post_data)); return await r.fulfill(status=201,body='')
        return await r.fulfill(status=200,content_type='application/json',body=json.dumps([{"store_id":"suseong","week":"2026-09-28","data":{"fill":95.5,"short":2,"hours":400,"ratio":27.1},"updated_at":"2026-09-30T01:00:00Z"}]))
      if '/sch_items' in u:
        assert r.request.headers.get('authorization')=='Bearer tok', r.request.headers
        if m=='POST': POSTS.append(json.loads(r.request.post_data)); return await r.fulfill(status=201,body='')
        if 'updated_at=gt' in u:
          return await r.fulfill(status=200,content_type='application/json',body=json.dumps([{"kind":"staff","id":"zz","data":{"id":"zz","name":"다른기기추가","pos":"홀","type":"regular","off":[]},"deleted":False,"updated_at":"2026-09-30T05:00:00Z"}]))
        return await r.fulfill(status=200,content_type='application/json',body=json.dumps([]))
      await r.fulfill(status=404,body='{}')
    await pg.route('**/*', route)
    await pg.goto('file:///home/claude/fr/ilpum-schedule.html'); await pg.evaluate("localStorage.clear()"); await pg.reload(); await pg.wait_for_timeout(400)
    await pg.click('#nav [data-v="set"]'); await pg.fill('#cfUrl',URL); await pg.fill('#cfKey','eyJtest'); await pg.click('[data-a="connect"]'); await pg.wait_for_timeout(700)
    print('login screen:', await pg.is_visible('#lgEmail'))
    await pg.fill('#lgEmail','boss@ilpum.kr'); await pg.fill('#lgPw','pw'); await pg.click('[data-a="login"]'); await pg.wait_for_timeout(900)
    print('after login role:', await pg.evaluate("role()"), '| sync:', await pg.inner_text('#sync'))
    # 가져오기
    pg.once('dialog', lambda d: asyncio.ensure_future(d.accept()))
    await pg.click('#nav [data-v="set"]'); await pg.click('[data-a="importold"]'); await pg.wait_for_timeout(1500)
    print('toast:', await pg.inner_text('#toast'))
    kinds={}
    for x in POSTS: kinds[x['kind']]=kinds.get(x['kind'],0)+1
    print('upserts by kind:', kinds)
    print('pay rows:', sorted(x['id'] for x in POSTS if x['kind']=='pay'))
    print('dc rows:', [(x['id'],x['data']) for x in POSTS if x['kind']=='dc'])
    print('staff types:', [(x['data']['name'],x['data']['type']) for x in POSTS if x['kind']=='staff'])
    print('rule has no pay inside:', all('pay' not in x['data'] for x in POSTS if x['kind']=='rule'))
    # 폴링 반영
    await pg.evaluate("poll()"); await pg.wait_for_timeout(300)
    print('polled staff:', await pg.evaluate("!!APP.D.staff.zz"))
    await pg.wait_for_timeout(3000); print('summaries posted:', len(SUMS), SUMS[0]['data'] if SUMS else None)
    await pg.click('#nav [data-v="hq"]'); await pg.wait_for_timeout(500); print('hq cards:', (await pg.inner_text('.stores')).replace('\n',' ')[:160])
    print('errs',errs); await b.close()
asyncio.run(main())
