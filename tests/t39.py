# 끌기 시작해도 카드 높이가 안 변함(화면이 안 밀림) + 빈 포지션 판에 놓으면 그 날만 포지션 변경 (체험 모드)
import asyncio
from playwright.async_api import async_playwright
async def main():
  ok=True
  def chk(n,c):
    nonlocal ok; ok&=bool(c); print(('OK  ' if c else 'FAIL'),n)
  async with async_playwright() as p:
    b=await p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome'); pg=await b.new_page(viewport={'width':1300,'height':900}); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
    await pg.route('**/*', lambda r: r.abort() if 'jsdelivr' in r.request.url or 'supabase' in r.request.url else r.continue_())
    await pg.goto('http://localhost:8765/ilpum-schedule.html')
    await pg.evaluate("localStorage.clear(); localStorage.setItem('ilpum-fr-conf', JSON.stringify({mode:'local'}))"); await pg.reload(); await pg.wait_for_timeout(1200)
    # 7일 첫 카드에서 칩 하나
    heights=lambda: pg.evaluate("[...document.querySelectorAll('.dcard')].map(c=>Math.round(c.getBoundingClientRect().height))")
    top=lambda: pg.evaluate("Math.round(document.querySelectorAll('.dcard')[3].getBoundingClientRect().top)")
    h0=await heights(); t0=await top()
    chip=pg.locator('.dcard').first.locator('.chip[data-sid]').first; bb=await chip.bounding_box(); sid=await chip.get_attribute('data-sid'); k=await chip.get_attribute('data-k'); pos0=await chip.get_attribute('data-pos')
    await pg.mouse.move(bb['x']+8,bb['y']+8); await pg.mouse.down(); await pg.mouse.move(bb['x']+30,bb['y']+22,steps=4); await pg.wait_for_timeout(150)
    chk('끌기 시작: 카드 높이 그대로', await heights()==h0)
    chk('끌기 시작: 다른 카드 위치 그대로(화면 안 밀림)', await top()==t0)
    chk('빈 포지션 판이 떠 있음', await pg.locator('.dpal .dpal-i').count()>=1)
    tgt=pg.locator('.dpal .dpal-i').first; name=await tgt.get_attribute('data-drop'); tb=await tgt.bounding_box()
    await pg.mouse.move(tb['x']+tb['width']/2,tb['y']+tb['height']/2,steps=6); await pg.wait_for_timeout(100)
    await pg.mouse.up(); await pg.wait_for_timeout(300)
    chk('놓으면 판이 사라짐', await pg.locator('.dpal').count()==0)
    now=await pg.evaluate(f"findItem(APP.D,'{k}','{sid}').pos")
    chk(f'그 날만 포지션 변경 ({pos0} → {name})', now==name)
    chk('오류 없음', not errs)
  print('전체','OK' if ok else 'FAIL')
asyncio.run(main())
