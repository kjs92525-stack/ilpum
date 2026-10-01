import asyncio, json
from playwright.async_api import async_playwright
OLD='https://fmzpmekypmjuydgxpnlu.supabase.co'; NEW='https://bdqcrbnbuoujozlpttbe.supabase.co'
async def main():
  async with async_playwright() as p:
    b=await p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
    ctx=await b.new_context(viewport={'width':390,'height':844},device_scale_factor=2,is_mobile=True,has_touch=True)
    await ctx.add_init_script("try{ localStorage.setItem('ilpum-fr-conf', JSON.stringify({mode:'remote',openOnly:true})); }catch(e){}")
    pg=await ctx.new_page(); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
    async def route(r):
      u=r.request.url
      if u.startswith('http://localhost'): return await r.continue_()
      if u.startswith(OLD) or u.startswith(NEW): return await r.fulfill(status=200,content_type='application/json',body='[]')
      await r.abort()
    await pg.route('**/*', route)
    await pg.goto('http://localhost:8765/index.html#dash'); await pg.wait_for_timeout(1200)
    hidden=lambda: pg.evaluate("document.body.classList.contains('nav-hidden')")
    print('폰: 처음엔 메뉴 숨김:', await hidden()); await pg.screenshot(path='m_a.png')
    await pg.click('#tog'); await pg.wait_for_timeout(400); print('햄버거 → 메뉴 열림:', not await hidden(), '| 어두운 배경(닫기용) 보임:', await pg.evaluate("getComputedStyle(document.getElementById('scrim')).opacity")=='1'); await pg.screenshot(path='m_b.png')
    await pg.click('#menu [data-m="res"]'); await pg.wait_for_timeout(700); print('메뉴 선택 → 자동으로 닫힘:', await hidden(), '| 제목:', await pg.inner_text('#ttl'))
    await pg.click('#tog'); await pg.wait_for_timeout(300); await pg.click('#scrim', position={'x':360,'y':400}); await pg.wait_for_timeout(300); print('바깥(어두운 곳) 누르면 닫힘:', await hidden())
    print('errs',errs); await b.close()
asyncio.run(main())
