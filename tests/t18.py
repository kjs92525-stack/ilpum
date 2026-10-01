# 통합 틀(index.html): 로그인 없으면 로그인 화면 / 가맹점은 예약·급여·발주 숨김 + 자기 매장만 / 본사는 전부 (가짜 서버)
# 실행 전: cd dist && python3 -m http.server 8765
import asyncio, json, time, os
from playwright.async_api import async_playwright
NEW='https://bdqcrbnbuoujozlpttbe.supabase.co'; OLDH='fmzpmekypmjuydgxpnlu.supabase.co'
BON='0134d989-757a-4b60-9cb3-93245de2cac8'; F1='ad2ffdae-f76b-44cd-a6c6-58514c4e4638'
REQ=[]
ROLES={'hqtok':[{"id":BON,"name":"일품집 본점","is_hq":True,"role":"hq"},{"id":F1,"name":"가맹점 1","is_hq":False,"role":"hq"}],
       'ownertok':[{"id":F1,"name":"가맹점 1","is_hq":False,"role":"owner"}]}
async def handler(r):
  u=r.request.url; h=r.request.headers
  if 'localhost' in u: return await r.continue_()
  J=lambda o,st=200: r.fulfill(status=st,content_type='application/json',body=json.dumps(o))
  REQ.append((u,h.get('authorization','')))
  if '/auth/v1/token' in u: return await J({"access_token":"ownertok","refresh_token":"r2","expires_at":int(time.time())+3600,"user":{"id":"u","email":"suseong@ilpum.invalid"}})
  if OLDH in u: return await J([{"data":{"items":[{"name":"손님","time":"18:00","pp":"4"}]}}])
  if '/rpc/sch_my_stores' in u:
    t=h.get('authorization','').replace('Bearer ','')
    return await J(ROLES[t]) if t in ROLES else await J({"message":"JWT expired"},401)
  if '/rpc/sch_open_store' in u: return await J([{"id":BON,"name":"일품집 본점","has_pin":False}])
  if '/sch_items' in u: return await J([{"kind":"cfg","id":"positions","data":[{"name":"홀","color":"#2F6B3F","req":[0]*7}]}])
  await J([])
async def run(b,conf,session=None,hash_='#dash'):
  ctx=await b.new_context(viewport={'width':1300,'height':800}); pg=await ctx.new_page(); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
  await pg.route('**/*',handler); REQ.clear()
  await pg.add_init_script(f"try{{ if(!localStorage.getItem('seeded')){{ localStorage.setItem('seeded','1'); localStorage.setItem('ilpum-fr-conf',{json.dumps(json.dumps(conf))}); }} }}catch(e){{}}")
  await pg.goto('http://localhost:8765/index.html'+hash_); await pg.wait_for_timeout(1500)
  vis=lambda t: pg.evaluate(f"[...document.querySelectorAll('#menu .mi')].some(b=>b.textContent.includes('{t}')&&!b.hidden&&b.offsetParent!==null)")
  res={'gate':await pg.is_visible('#gate'),'예약':await vis('예약 관리'),'급여':await vis('급여 관리'),'발주':await vis('발주 관리'),'근무':await vis('근무 스케줄'),
       'title':await pg.evaluate("document.querySelector('#ttl')&&document.querySelector('#ttl').textContent"),
       'oldReq':any(OLDH in u for u,_ in REQ),'itemsStores':sorted({u.split('store_id=eq.')[1][:8] for u,_ in REQ if '/sch_items' in u and 'store_id=eq.' in u}),
       'bearers':sorted({a for u,a in REQ if '/sch_items' in u}),'errs':errs}
  res['dash']=await pg.evaluate("document.querySelector('#dash')&&document.querySelector('#dash').innerText.slice(0,200).replace(/\\n/g,' | ')")
  await ctx.close(); return res
async def main():
  async with async_playwright() as p:
    b=await p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
    print('1) 로그인 없음   :', await run(b,{}))
    S=lambda t:{"ses":{"access_token":t,"refresh_token":"r","expires_at":int(time.time())+3000,"user":{"email":"x@ilpum.invalid"}}}
    print('2) 본사 로그인   :', await run(b,S('hqtok')))
    print('3) 점주 로그인   :', await run(b,S('ownertok')))
    print('4) 점주가 #res 주소로 열기:', await run(b,S('ownertok'),hash_='#res'))
    print('5) 만료 토큰     :', await run(b,S('expired')))
async def gate_login(b):
  ctx=await b.new_context(viewport={'width':1300,'height':800}); pg=await ctx.new_page(); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
  await pg.route('**/*',handler); REQ.clear()
  await pg.goto('http://localhost:8765/index.html'); await pg.wait_for_timeout(1200)
  fr=pg.frame_locator('#gate'); await fr.locator('#lgEmail').fill('suseong'); await fr.locator('#lgPw').fill('pw12345678'); await fr.locator('#lgPw').press('Enter'); await pg.wait_for_timeout(3000)
  vis=lambda t: pg.evaluate(f"[...document.querySelectorAll('#menu .mi')].some(b=>b.textContent.includes('{t}')&&!b.hidden&&b.offsetParent!==null)")
  print('6) 로그인 화면에서 점주 로그인 → 게이트 사라짐:', not await pg.is_visible('#gate'), '| 예약 메뉴:', await vis('예약 관리'), '| 근무 메뉴:', await vis('근무 스케줄'), '| 가맹점 데이터만 요청:', sorted({u.split('store_id=eq.')[1][:8] for u,_ in REQ if '/sch_items' in u and 'store_id=eq.' in u}), '| errs', errs)
async def main2():
  async with async_playwright() as p:
    b=await p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome'); await gate_login(b)
asyncio.run(main()); asyncio.run(main2())
