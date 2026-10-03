# 계정 목록·비밀번호 바꾸기·정지·삭제·만들기 안내 — 가짜 서버
# 실행 전: cd dist && python3 -m http.server 8765
import asyncio, json, time
from playwright.async_api import async_playwright
NEW='bdqcrbnbuoujozlpttbe.supabase.co'; BON='0134d989-757a-4b60-9cb3-93245de2cac8'; F1='ad2ffdae-f76b-44cd-a6c6-58514c4e4638'
CALLS=[]; ROWS=[{"id":"ilpum","hq":True,"me":True,"links":[],"last":None,"banned":False},{"id":"yucheon","hq":False,"me":False,"links":[{"store":"유천점","role":"owner","pay":True}],"last":None,"banned":False}]
async def handler(r):
  u=r.request.url
  if 'localhost' in u: return await r.continue_()
  if NEW not in u: return await r.fulfill(status=404,body='{}')
  J=lambda o,st=200: r.fulfill(status=st,content_type='application/json',body=json.dumps(o))
  if '/rpc/sch_my_stores' in u: return await J([{"id":BON,"name":"일품집 본점","is_hq":True,"role":"hq","can_pay":True},{"id":F1,"name":"유천점","is_hq":False,"role":"hq","can_pay":False}])
  if '/functions/v1/manage-accounts' in u:
    b=json.loads(r.request.post_data); CALLS.append(b)
    if b['action']=='list': return await J({"ok":True,"rows":ROWS})
    return await J({"ok":True})
  if '/functions/v1/create-account' in u: CALLS.append(json.loads(r.request.post_data)); return await J({"ok":True})
  await J([])
S={"ses":{"access_token":"tok","refresh_token":"r","expires_at":int(time.time())+3000,"user":{"email":"ilpum@ilpum.invalid"}},"mode":"remote","url":"https://"+NEW,"key":"k"}
async def main():
  async with async_playwright() as p:
    b=await p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
    ctx=await b.new_context(viewport={'width':1200,'height':900}); pg=await ctx.new_page(); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.on('dialog',lambda d: asyncio.ensure_future(d.accept('newpass1234') if d.type=='prompt' else d.accept()))
    await pg.route('**/*',handler); await pg.route_web_socket(f'wss://{NEW}/**',lambda ws: asyncio.ensure_future(ws.close()))
    await pg.add_init_script(f"try{{ localStorage.setItem('ilpum-fr-conf',{json.dumps(json.dumps(S))}); }}catch(e){{}}")
    await pg.goto('http://localhost:8765/ilpum-schedule.html?view=acct'); await pg.wait_for_timeout(1800)
    t=await pg.inner_text('#main')
    print('1) 목록에 아이디:', 'yucheon' in t and '유천점 점주' in t, '| 본사/내 계정은 버튼 없음:', await pg.evaluate("document.querySelectorAll('[data-a=acctdel]').length")==1)
    await pg.click('[data-a=acctpw][data-id=yucheon]'); await pg.wait_for_timeout(600)
    print('2) 비밀번호 바꾸기:', CALLS[-1], '|', 'newpass1234' in await pg.inner_text('#main'))
    await pg.click('[data-a=acctban][data-id=yucheon]'); await pg.wait_for_timeout(600); print('3) 정지:', CALLS[-1])
    await pg.click('[data-a=acctdel][data-id=yucheon]'); await pg.wait_for_timeout(600); print('4) 삭제:', CALLS[-1])
    await pg.fill('#mkId','suseong'); await pg.fill('#mkPw','abcd1234'); await pg.click('[data-a=mkaccount]'); await pg.wait_for_timeout(800)
    print('   호출 순서:',[c.get('action') or 'create' for c in CALLS]); print('5) 만들기 안내:', 'suseong' in await pg.inner_text('#main') and '계정을 만들었어요' in await pg.inner_text('#main'), CALLS[-2:] , '| errs', errs)
    await ctx.close()
asyncio.run(main())
