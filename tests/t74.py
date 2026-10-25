# 손님 나감: 앞 손님이 나가서 다음 예약을 같은 테이블로 옮기면 "중복"이 뜨던 문제 (2026-10-25 사진: 9번 이청희 12:30 / 윤하나 14:00)
import asyncio, json, time, datetime
from playwright.async_api import async_playwright
NEW='bdqcrbnbuoujozlpttbe.supabase.co'; F1='0134d989-757a-4b60-9cb3-93245de2cac8'; T=datetime.date.today().isoformat()
def it(i,n,tm,tb,pp="4",**k): d={"id":"i%d"%i,"c":"2026-01-01","u":1,"pp":pp,"req":"","done":False,"name":n,"time":tm,"phone":"","tnote":"","tables":tb}; d.update(k); return d
IT=[it(1,"이청희","12:30",["9"],"5",done=True),it(2,"윤하나","14:00",["9"],"5+1"),it(3,"정은재","12:00",["6"],"5",done=True),it(4,"정소정","13:00",["6"],"4+2",done=True),it(5,"김중복","13:00",["5"]),it(6,"박중복","13:30",["5"])]
POSTS=[]
async def h(r):
  u=r.request.url
  if 'localhost' in u: return await r.continue_()
  J=lambda o: r.fulfill(status=200,content_type='application/json',body=json.dumps(o))
  if '/rpc/sch_my_stores' in u: return await J([{"id":F1,"name":"본점","is_hq":True,"role":"hq","can_pay":True}])
  if '/rest/v1/res_days' in u:
    if r.request.method!='GET': POSTS.append(r.request.post_data); return await J([{"rev":4}])
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
    cf=await pg.evaluate("Object.keys(dayConflicts(ui.date).table).sort()")
    chk('두 팀 다 도착(6번)은 중복 아님, 9번·5번은 중복', cf==['5','9'], str(cf))
    await pg.evaluate("followNow=false;ui.t=14*60;renderBoard()"); await pg.wait_for_timeout(200)
    chk('6번 칸은 나중 팀(정소정)만 보임', await pg.evaluate("(()=>{const c=document.querySelector('.cell[data-cell=\"6\"]');return c&&!c.classList.contains('st-dup')&&c.textContent.includes('정소정')&&!c.textContent.includes('정은재')})()"))
    chk('목록 줄에 바로 "나감" 버튼(앞 손님만, 겹치지 않는 5번 뒤 팀·6번 나중 팀엔 없음)', await pg.is_visible('#listPanel [data-outq="i1"]') and not await pg.is_visible('[data-outq="i2"]') and not await pg.is_visible('[data-outq="i4"]') and not await pg.is_visible('[data-outq="i6"]'))
    await pg.click('#listPanel [data-outq="i5"]'); await pg.wait_for_timeout(300)
    chk('목록 "나감"(5번 김중복) → 5번 중복 사라짐', '5' not in await pg.evaluate("Object.keys(dayConflicts(ui.date).table)"))
    await pg.click('.cell[data-cell="9"]'); await pg.wait_for_timeout(300)
    chk('9번 칸 누르면 앞 손님에 "나감" 버튼', await pg.is_visible('[data-pout="i1"]') and not await pg.is_visible('[data-pout="i2"]'))
    await pg.click('[data-pout="i1"]'); await pg.wait_for_timeout(400)
    st=await pg.evaluate("(()=>{const x=items(ui.date).find(y=>y.id==='i1');return [x.outT||'',x.done,Object.keys(dayConflicts(ui.date).table).sort()]})()")
    chk('나감 → 시각 기록·도착, 9번 중복 사라짐', st[0] and st[1] and st[2]==[], str(st))
    chk('서버에 저장됨', any('"outT"' in (x or '') for x in POSTS))
    await pg.click('#dlgBody [data-d="close"]'); await pg.evaluate("followNow=false;ui.t=Math.max(toMin(items(ui.date).find(y=>y.id==='i1').outT),14*60);renderBoard()"); await pg.wait_for_timeout(200)
    chk('현황판 9번 칸은 윤하나만, 중복 표시 없음', await pg.evaluate("(()=>{const c=document.querySelector('.cell[data-cell=\"9\"]');return c&&!c.classList.contains('st-dup')&&c.textContent.includes('윤하나')})()"))
    chk('목록에 "나감" 표시', '나감' in await pg.inner_text('#listPanel'))
    await pg.click('.cell[data-cell="9"]'); await pg.wait_for_timeout(300); await pg.click('[data-pin="i1"]'); await pg.wait_for_timeout(300)
    chk('나감 취소 → 다시 중복', '9' in await pg.evaluate("Object.keys(dayConflicts(ui.date).table)"))
    chk('오류 없음', not errs, str(errs)); await b.close()
  print('전체 OK' if ok else '실패 있음')
asyncio.run(main())
