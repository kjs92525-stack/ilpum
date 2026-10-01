# 예약 화면(reserve.html) — 새 서버(res_days): 로그인 필요 / 매장별 / 실패해도 서버를 두드리지 않음 (가짜 서버)
# 실행 전: cd dist && python3 -m http.server 8765
import asyncio, json, time
from playwright.async_api import async_playwright
NEW='https://bdqcrbnbuoujozlpttbe.supabase.co'
BON='0134d989-757a-4b60-9cb3-93245de2cac8'; F1='ad2ffdae-f76b-44cd-a6c6-58514c4e4638'
ROLES={'hqtok':[{"id":BON,"name":"일품집 본점","is_hq":True,"role":"hq"},{"id":F1,"name":"가맹점 1","is_hq":False,"role":"hq"}],
       'ownertok':[{"id":F1,"name":"가맹점 1","is_hq":False,"role":"owner"}]}
DB={}; REQ=[]; FAIL={'on':False}
async def handler(r):
  u=r.request.url; m=r.request.method; h=r.request.headers
  if 'localhost' in u: return await r.continue_()
  J=lambda o,st=200: r.fulfill(status=st,content_type='application/json',body=json.dumps(o))
  tok=h.get('authorization','').replace('Bearer ','')
  if '/rpc/sch_my_stores' in u: return await J(ROLES[tok]) if tok in ROLES else await J({},401)
  if '/rest/v1/res_days' in u:
    REQ.append((m,u,tok))
    if FAIL['on']: return await J({"message":"boom"},500)
    q=dict(p.split('=',1) for p in u.split('?',1)[1].split('&'))
    sid=q.get('store_id','').replace('eq.','')
    if m=='GET':
      d=q.get('id','').replace('eq.','')
      row=DB.get((sid,d)); 
      if 'select=rev' in u: return await J([{"rev":row['rev']}] if row else [])
      return await J([row] if row else [])
    if m=='POST':
      b=json.loads(r.request.post_data); DB[(b['store_id'],b['id'])]={"id":b['id'],"data":b['data'],"rev":b['rev']}; return await J([{"rev":b['rev']}],201)
    if m=='PATCH':
      b=json.loads(r.request.post_data); d=q['id'].replace('eq.',''); DB[(sid,d)].update(data=b['data'],rev=b['rev']); return await J([{"rev":b['rev']}])
  await J([])
async def run(b,conf,fn):
  ctx=await b.new_context(viewport={'width':1300,'height':800}); pg=await ctx.new_page(); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
  await pg.route('**/*',handler); REQ.clear()
  await pg.add_init_script(f"try{{ if(!localStorage.getItem('seeded')){{ localStorage.setItem('seeded','1'); localStorage.setItem('ilpum-fr-conf',{json.dumps(json.dumps(conf))}); }} }}catch(e){{}}")
  await pg.goto('http://localhost:8765/reserve.html'); await pg.wait_for_timeout(1200)
  await fn(pg); print('   errs', errs); await ctx.close()
S=lambda t,**k:{"ses":{"access_token":t,"refresh_token":"r","expires_at":int(time.time())+3000,"user":{"email":"x@ilpum.invalid"}},**k}
ITEM="({id:'a1',name:'테스트손님',time:'18:00',pp:'2',tables:[],req:'',u:Date.now()})"
async def main():
  async with async_playwright() as p:
    b=await p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
    async def t_none(pg): print('1) 로그인 없음:', await pg.inner_text('#sync'), '| 서버 호출 수:', len(REQ))
    print('1) 로그인 없음'); await run(b,{},t_none)
    async def t_owner(pg):
      print('2) 점주: 매장 표시:', await pg.inner_text('#storeBox'), '| 동기 상태:', await pg.inner_text('#sync'))
      d=await pg.evaluate("ui.date"); await pg.evaluate(f"saveItem(ui.date,{ITEM})"); await pg.wait_for_timeout(1500)
      print('   저장됨:', await pg.inner_text('#sync'), '| 서버에 저장된 매장:', [k[0][:8] for k in DB], '| 보낸 토큰:', {t for m,u,t in REQ if m!='GET'})
      print('   기기 저장 키:', await pg.evaluate("Object.keys(localStorage).filter(k=>k.startsWith('ilpum-res-'))"))
      print('   모든 요청이 내 매장만:', all(f'store_id=eq.{F1}' in u or (m=='POST') for m,u,t in REQ))
    print('2) 점주'); await run(b,S('ownertok'),t_owner)
    async def t_hq(pg):
      print('3) 본사: 매장 선택 목록:', await pg.evaluate("[...document.querySelectorAll('#storeSel option')].map(o=>o.textContent)"), '| 지금 매장:', await pg.evaluate("SID===%r"%BON))
      await pg.select_option('#storeSel',F1); await pg.wait_for_timeout(1500)
      print('   가맹점 1로 바꿈 → SID 일치:', await pg.evaluate("SID===%r"%F1), '| 기억된 매장:', json.loads(await pg.evaluate("localStorage.getItem('ilpum-fr-conf')")).get('sid')==F1)
    print('3) 본사'); await run(b,S('hqtok'),t_hq)
    async def t_fail(pg):
      FAIL['on']=True; REQ.clear(); await pg.evaluate(f"saveItem(ui.date,{ITEM})"); await pg.wait_for_timeout(14000)
      print('4) 서버 오류가 나도: 14초 동안 요청 수:', len(REQ), '(예전 방식이면 5초마다 계속) | 상태:', await pg.inner_text('#sync')); FAIL['on']=False
    print('4) 실패 시'); await run(b,S('ownertok'),t_fail)
asyncio.run(main())
