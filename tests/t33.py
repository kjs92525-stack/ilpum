# 햄버거로 연 메뉴는 빈 화면을 누르면 닫힘(PC) + 근무표에서 "예약 보기" 로 바로 이동 (가짜 서버)
# 실행 전: cd dist && python3 -m http.server 8765
import asyncio, json, time
from playwright.async_api import async_playwright
NEW='bdqcrbnbuoujozlpttbe.supabase.co'; BON='0134d989-757a-4b60-9cb3-93245de2cac8'
async def h(r):
  u=r.request.url
  if 'localhost' in u: return await r.continue_()
  J=lambda o: r.fulfill(status=200,content_type='application/json',body=json.dumps(o))
  if '/rpc/sch_my_stores' in u: return await J([{"id":BON,"name":"본점","is_hq":True,"role":"hq","can_pay":False}])
  await J([])
S={"ses":{"access_token":"t","refresh_token":"r","expires_at":int(time.time())+3000,"user":{"email":"x@ilpum.invalid"}}}
async def main():
  ok=True
  def chk(n,c):
    nonlocal ok; ok&=bool(c); print(('OK  ' if c else 'FAIL'),n)
  async with async_playwright() as p:
    b=await p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
    pg=await b.new_page(viewport={'width':1300,'height':800}); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
    await pg.route('**/*',h); await pg.add_init_script(f"try{{ if(!localStorage.getItem('s')){{ localStorage.setItem('s','1'); localStorage.setItem('ilpum-fr-conf',{json.dumps(json.dumps(S))}); localStorage.setItem('ilpum-nav','hidden'); }} }}catch(e){{}}")
    await pg.goto('http://localhost:8765/index.html#cards'); await pg.wait_for_timeout(1800)
    nav=lambda: pg.evaluate("!document.body.classList.contains('nav-hidden')")
    chk('처음엔 메뉴 숨김(저장된 상태)', not await nav())
    await pg.click('#tog'); await pg.wait_for_timeout(300); chk('햄버거 → 메뉴 열림', await nav())
    await pg.mouse.click(900,500); await pg.wait_for_timeout(300); chk('빈 화면 누르면 메뉴 닫힘', not await nav())
    chk('이 동작이 저장되지 않음(고정 아님)', await pg.evaluate("localStorage.getItem('ilpum-nav')")=='hidden')
    # 고정으로 열려 있을 때는 빈 화면 눌러도 안 닫힘
    await pg.evaluate("setNav(true)"); await pg.wait_for_timeout(200); await pg.mouse.click(900,500); await pg.wait_for_timeout(300); chk('메뉴 항상 보이기 상태에선 그대로', await nav())
    await pg.evaluate("setNav(false)")
    fr=pg.frame_locator('#fr-sch') if await pg.locator('#fr-sch').count() else pg.frame_locator('iframe').first
    await fr.locator('[data-a="tores"]').first.click(); await pg.wait_for_timeout(800)
    chk('근무표의 "예약 보기" → 예약 관리로 이동', await pg.evaluate("document.querySelector('#ttl').textContent")=='예약 관리')
    chk('오류 없음', not errs)
  print('전체','OK' if ok else 'FAIL')
asyncio.run(main())
