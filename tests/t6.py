import asyncio
from playwright.async_api import async_playwright
async def main():
  async with async_playwright() as p:
    b=await p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome',ignore_default_args=['--hide-scrollbars'])
    pg=await b.new_page(viewport={'width':1000,'height':760}); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
    await pg.route('**/*', lambda r: r.abort() if 'jsdelivr' in r.request.url or 'supabase' in r.request.url else r.continue_())
    await pg.goto('http://localhost:8765/ilpum-schedule.html'); await pg.evaluate("localStorage.clear()"); await pg.reload(); await pg.wait_for_timeout(600)
    print('scrollbar thickness (px):', await pg.evaluate("(()=>{const w=document.querySelector('.boardwrap'); return [w.offsetHeight-w.clientHeight, w.scrollWidth>w.clientWidth]})()"))
    print('scrollbar bottom visible in viewport:', await pg.evaluate("(()=>{const r=document.querySelector('.boardwrap').getBoundingClientRect(); return [Math.round(r.bottom), innerHeight]})()"))
    await pg.screenshot(path='c4.png')
    await pg.locator('.board .chip').first.click(); await pg.wait_for_timeout(300)
    print('click opens drawer:', await pg.evaluate("document.querySelector('#drawer').classList.contains('on')")); await pg.keyboard.press('Escape')
    # 드래그 직후엔 클릭 무시, 잠시 후엔 정상
    c=pg.locator('.board .chip').first; bb=await c.bounding_box()
    await pg.mouse.move(bb['x']+8,bb['y']+8); await pg.mouse.down(); await pg.mouse.move(bb['x']+60,bb['y']+8,steps=5); await pg.mouse.up(); await pg.wait_for_timeout(60)
    print('drawer right after drag (should be False):', await pg.evaluate("document.querySelector('#drawer').classList.contains('on')"))
    print('빈 포지션 버튼:', await pg.inner_text('[data-a="empty"]')); await pg.click('[data-a="empty"]'); print('rows after toggle:', await pg.evaluate("document.querySelectorAll('.bl b').length"))
    print('errs',errs); await b.close()
asyncio.run(main())
