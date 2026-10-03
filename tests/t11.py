import asyncio, json
from playwright.async_api import async_playwright
URL='https://bdqcrbnbuoujozlpttbe.supabase.co'
BON='0134d989-757a-4b60-9cb3-93245de2cac8'; FR='ad2ffdae-f76b-44cd-a6c6-58514c4e4638'
POSTS=[]; SUMS=[]; RPC=[]; AUTH=[]
async def main():
  async with async_playwright() as p:
    b=await p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
    pg=await b.new_page(viewport={'width':1300,'height':900}); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
    async def route(r):
      u=r.request.url; m=r.request.method; h=r.request.headers
      if 'jsdelivr' in u: return await r.abort()
      if 'fmzpmekypmjuydgxpnlu' in u:
        old={"staff":[{"id":"a1","name":"김지수","pos":"홀","kind":"staff","off":[5],"wk":{"1":{"sh":{"k":"pm"},"pay":{"k":"day","v":70000}}}}],"ex":[],"rules":[],"dc":{},"notes":{},"aw":{},"targets":{}}
        return await r.fulfill(status=200,content_type='application/json',body=json.dumps([{"data":old}]))
      if not u.startswith(URL): return await r.continue_()
      assert h.get('apikey','').startswith('eyJ'), 'apikey 누락'
      if '/auth/v1/token' in u:
        AUTH.append(json.loads(r.request.post_data)['email'])
        return await r.fulfill(status=200,content_type='application/json',body=json.dumps({"access_token":"tok","refresh_token":"ref","expires_at":9999999999,"user":{"id":"b9898dd7","email":"yoyo925@naver.com"}}))
      if '/rpc/sch_my_stores' in u:
        assert h.get('authorization')=='Bearer tok'
        return await r.fulfill(status=200,content_type='application/json',body=json.dumps([{"id":BON,"name":"일품집 본점","is_hq":True,"role":"hq","can_pay":True,"staff_id":None},{"id":FR,"name":"가맹점 1","is_hq":False,"role":None,"can_pay":False,"staff_id":None}]))
      if '/rpc/' in u:
        RPC.append((u.split('/rpc/')[1],json.loads(r.request.post_data))); return await r.fulfill(status=200,content_type='application/json',body='null')
      if '/sch_summaries' in u:
        if m=='POST': SUMS.append(json.loads(r.request.post_data)); return await r.fulfill(status=201,body='')
        return await r.fulfill(status=200,content_type='application/json',body=json.dumps([{"store_id":FR,"week":"2026-09-28","data":{"hours":420,"staff":9,"ratio":26.4},"updated_at":"2026-09-30T01:00:00Z"}]))
      if '/sch_items' in u:
        assert h.get('authorization')=='Bearer tok'
        if m=='POST': POSTS.append(json.loads(r.request.post_data)); return await r.fulfill(status=201,body='')
        if 'updated_at=gt' in u: return await r.fulfill(status=200,content_type='application/json',body='[]')
        assert BON in u, u
        seed=[{"kind":"cfg","id":"store","data":{"name":"일품집 본점","open":"11:00","close":"22:00","fullH":10,"pmH":5,"pmStart":"17:00","fivePlus":True,"vis":"week","target":25},"deleted":False,"updated_at":"2026-09-30T00:00:00Z"},
              {"kind":"cfg","id":"positions","data":[{"name":"카운터","color":"#3C5A86","req":[0]*7},{"name":"홀","color":"#2F6B3F","req":[0]*7},{"name":"그릴","color":"#B8621B","req":[0]*7}],"deleted":False,"updated_at":"2026-09-30T00:00:00Z"}]
        return await r.fulfill(status=200,content_type='application/json',body=json.dumps(seed))
      await r.fulfill(status=404,body='{}')
    await pg.route('**/*', route)
    await pg.goto('http://localhost:8765/ilpum-schedule.html'); await pg.evaluate("localStorage.clear()"); await pg.reload(); await pg.wait_for_timeout(700)
    print('첫 화면=로그인:', await pg.is_visible('#lgEmail'))
    await pg.fill('#lgEmail','yoyo925@naver.com'); await pg.fill('#lgPw','pw'); await pg.click('[data-a="login"]'); await pg.wait_for_timeout(1200)
    print('로그인 후 role:', await pg.evaluate("role()"), '| 매장:', await pg.evaluate("APP.stores.map(s=>s.name+':'+(s.role||'-')).join(', ')"), '| 포지션:', await pg.evaluate("APP.D.positions.map(p=>p.name).join(',')"), '| sync:', await pg.inner_text('#sync'))
    print('금액 보기 버튼(본사=허용):', await pg.is_visible('[data-a="paytog"]'))
    # 직원 추가 → 서버에 저장되는지
    await pg.click('#nav [data-v="staff"]'); await pg.click('[data-a="staffnew"]'); await pg.fill('#sfName','테스트직원'); await pg.click('[data-a="staffsave"]'); await pg.wait_for_timeout(900)
    print('저장 요청:', [(x['kind'],x['store_id'][:8]) for x in POSTS])
    # 기존 근무표 가져오기
    pg.once('dialog', lambda d: asyncio.ensure_future(d.accept()))
    await pg.click('#nav [data-v="set"]'); await pg.click('[data-a="importold"]'); await pg.wait_for_timeout(1500); print('가져오기:', await pg.inner_text('#toast'))
    print('가져온 pay 행:', sorted(x['id'] for x in POSTS if x['kind']=='pay'), '| 모두 본점 store_id:', all(x['store_id']==BON for x in POSTS))
    await pg.wait_for_timeout(3000); print('본사 집계 업로드:', len(SUMS), '건, store', SUMS[0]['store_id'][:8] if SUMS else None, 'keys', sorted(SUMS[0]['data'].keys()) if SUMS else None)
    await pg.click('#nav [data-v="hq"]'); await pg.wait_for_timeout(600); print('본사 현황:', (await pg.inner_text('.stores')).replace('\n',' ')[:170])
    # 매장 만들기
    await pg.click('[data-a="storenew"]'); await pg.fill('#snName','수성점'); await pg.click('[data-a="storecreate"]'); await pg.wait_for_timeout(500); print('매장 생성 RPC:', RPC)
    # 계정 연결
    await pg.click('#nav [data-v="set"]'); await pg.wait_for_timeout(200)
    await pg.fill('#amEmail','owner@x.kr'); await pg.select_option('#amStore',FR); await pg.select_option('#amRole','owner'); await pg.click('[data-a="addmember"]'); await pg.wait_for_timeout(400); print('계정 연결 RPC:', RPC[-1])
    print('errs',errs); await b.close()
asyncio.run(main())
