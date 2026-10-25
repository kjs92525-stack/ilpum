# 남색 테마 고르기: 통합관리 위쪽 "테마" 버튼 → 이 기기 ilpum-theme=navy, 다른 화면(예약·근무표 등)도 바로 바뀜. 기본은 원래 색.
import asyncio
from playwright.async_api import async_playwright
async def main():
  ok=True
  def chk(n,c,x=''):
    nonlocal ok; ok&=bool(c); print('OK  ' if c else 'FAIL',n,x)
  async with async_playwright() as p:
    b=await p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
    ctx=await b.new_context(viewport={'width':1300,'height':800}); errs=[]
    await ctx.route('**/*',lambda r: r.continue_() if 'localhost' in r.request.url else r.fulfill(status=404,body='{}'))
    pg=await ctx.new_page(); pg.on('pageerror',lambda e:errs.append(str(e)))
    await pg.goto('http://localhost:8765/index.html'); await pg.wait_for_timeout(800)
    bg0=await pg.evaluate("getComputedStyle(document.querySelector('.bar')).backgroundColor")
    chk('기본은 남색 아님', not await pg.evaluate("document.documentElement.classList.contains('th-navy')"), bg0)
    pages={}
    for f in ['reserve.html','ilpum-schedule.html','order.html','notice.html','board.html','pay.html']:
      q=await ctx.new_page(); q.on('pageerror',lambda e:errs.append(str(e))); await q.goto('http://localhost:8765/'+f); pages[f]=q
    await pg.wait_for_timeout(800)
    await pg.evaluate("document.getElementById('themeBtn').click()"); await pg.wait_for_timeout(400)
    bg1=await pg.evaluate("getComputedStyle(document.querySelector('.bar')).backgroundColor")
    chk('버튼 → 남색 + 저장', await pg.evaluate("document.documentElement.classList.contains('th-navy')&&localStorage.getItem('ilpum-theme')==='navy'") and bg1!=bg0 and await pg.evaluate("document.querySelector('meta[name=theme-color]').content")=='#191C2E', bg1)
    for f,q in pages.items():
      chk(f+' 도 바로 남색', await q.evaluate("document.documentElement.classList.contains('th-navy')"))
    r=pages['reserve.html']; await r.reload(); await r.wait_for_timeout(500)
    chk('새로 열어도 남색 유지 (예약 바탕 #161929)', await r.evaluate("getComputedStyle(document.body).backgroundColor")=='rgb(22, 25, 41)')
    await pg.evaluate("document.getElementById('themeBtn').click()"); await pg.wait_for_timeout(400)
    chk('한 번 더 → 원래 색', not await pg.evaluate("document.documentElement.classList.contains('th-navy')") and not await r.evaluate("document.documentElement.classList.contains('th-navy')") and await pg.evaluate("getComputedStyle(document.querySelector('.bar')).backgroundColor")==bg0)
    chk('오류 없음', not errs, str(errs[:3])); await b.close()
  print('전체 OK' if ok else '실패 있음')
asyncio.run(main())
