# 손으로 넣는 예약이 같은 날 같은 이름과 겹치면 물어봄 (2026-10-25 이은아: 네이버 자동 입력 19:30 이 있는데 매장에서 20:00 으로 또 입력 → 중복)
import asyncio, json, time, datetime
from playwright.async_api import async_playwright
NEW='bdqcrbnbuoujozlpttbe.supabase.co'; F1='0134d989-757a-4b60-9cb3-93245de2cac8'; T=datetime.date.today().isoformat()
IT=[{"id":"a1","c":T,"u":1,"pp":"4","req":"","done":False,"name":"이은아","time":"19:30","phone":"","tnote":"","tables":["12"],"auto":"new"}]
async def h(r):
  u=r.request.url
  if 'localhost' in u: return await r.continue_()
  J=lambda o: r.fulfill(status=200,content_type='application/json',body=json.dumps(o))
  if '/rpc/sch_my_stores' in u: return await J([{"id":F1,"name":"본점","is_hq":True,"role":"hq","can_pay":True}])
  if '/rest/v1/res_days' in u:
    if r.request.method!='GET': return await J([{"rev":4}])
    return await J([{"id":T,"rev":3,"data":{"items":IT}}] if 'select=data' in u else [{"rev":3}])
  return await J([])
S={"ses":{"access_token":"t","refresh_token":"r","expires_at":int(time.time())+3000,"user":{"email":"x@ilpum.invalid"}}}
async def main():
  ok=True
  def chk(n,c,x=''):
    nonlocal ok; ok&=bool(c); print('OK  ' if c else 'FAIL',n,x)
  async with async_playwright() as p:
    b=await p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
    c=await b.new_context(viewport={'width':1500,'height':900}); pg=await c.new_page(); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
    await pg.route('**/*',h); await pg.route_web_socket(f'wss://{NEW}/**',lambda ws: asyncio.ensure_future(ws.close()))
    await pg.add_init_script(f"localStorage.setItem('ilpum-fr-conf',{json.dumps(json.dumps(S))})")
    await pg.goto('http://localhost:8765/reserve.html'); await pg.wait_for_timeout(2500)
    live=lambda: pg.evaluate("items(ui.date).filter(x=>!x.deleted).map(x=>[x.name,x.time,(x.tables||[]).join(),x.phone||'',x.auto||''])")
    async def typ():
      await pg.fill('#qTime','2000'); await pg.fill('#qName','이은아'); await pg.fill('#qPP','4'); await pg.fill('#qTables','4'); await pg.fill('#qPhone','01093622776'); await pg.press('#qName','Enter'); await pg.wait_for_timeout(300)
    await typ()
    chk('같은 이름이 있으면 바로 넣지 않고 물어봄', await pg.is_visible('#dlgBody [data-d="dupfix"]') and len(await live())==1, str(await live()))
    await pg.click('#dlgBody [data-d="close"]'); await pg.wait_for_timeout(200)
    chk('취소 → 입력 칸은 그대로, 예약 1건', await pg.input_value('#qName')=='이은아' and len(await live())==1)
    await pg.press('#qName','Enter'); await pg.wait_for_timeout(300); await pg.click('#dlgBody [data-d="dupfix"]'); await pg.wait_for_timeout(300)
    L=await live()
    chk('그 예약 고치기 → 1건, 20:00·4번·전화, 자동 표시 지움', len(L)==1 and L[0][1]=='20:00' and L[0][2]=='4' and L[0][3]=='010-9362-2776' and L[0][4]=='', str(L))
    chk('입력 칸 비워짐', await pg.input_value('#qName')=='')
    await typ(); await pg.click('#dlgBody [data-d="dupnew"]'); await pg.wait_for_timeout(300)
    chk('다른 손님 — 따로 추가 → 2건', len(await live())==2, str(await live()))
    await pg.fill('#qTime','1800'); await pg.fill('#qName','새손님'); await pg.press('#qName','Enter'); await pg.wait_for_timeout(300)
    chk('다른 이름은 묻지 않고 바로 추가', len(await live())==3 and not await pg.is_visible('#dlgBody [data-d="dupfix"]'))
    pt=await pg.evaluate("[printTb({tables:['22']}),printTb({tables:['31','32']}),printTb({tables:['R1-1','R1-2']}),printTb({tables:['5'],tnote:'네이버취소'})]")
    chk('인쇄 테이블 번호 뒤에 T (룸·메모는 그대로)', pt[0]=='22T' and pt[1]=='31T, 32T' and 'T' not in pt[2] and pt[3]=='5T, 네이버취소', str(pt))
    await pg.evaluate("window.print=()=>{}; printDay()"); await pg.wait_for_timeout(200)
    chk('인쇄 화면에 4T', '4T' in await pg.evaluate("document.getElementById('printRoot').innerText"))
    chk('오류 없음', not errs, str(errs)); await b.close()
  print('전체 OK' if ok else '실패 있음')
asyncio.run(main())
