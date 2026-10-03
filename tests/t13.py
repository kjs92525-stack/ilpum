import asyncio
from playwright.async_api import async_playwright
async def main():
  async with async_playwright() as p:
    b=await p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
    ctx=await b.new_context(viewport={'width':390,'height':844},device_scale_factor=2,is_mobile=True,has_touch=True,color_scheme='dark'); pg=await ctx.new_page(); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
    await pg.route('**/*', lambda r: r.abort() if 'supabase.co' in r.request.url or 'jsdelivr' in r.request.url else r.continue_())   # 접속 막힌 환경 흉내
    await pg.goto('http://localhost:8765/ilpum-schedule.html'); await pg.evaluate("localStorage.clear()"); await pg.reload(); await pg.wait_for_timeout(1200)
    print('세션 없음+접속 막힘 → 로그인 화면:', await pg.is_visible('#lgForm'))
    await pg.fill('#lgEmail','a@b.kr'); await pg.fill('#lgPw','x'); await pg.press('#lgPw','Enter'); await pg.wait_for_timeout(700); print('   로그인 시도 메시지:', await pg.inner_text('#toast'))
    await pg.evaluate("localStorage.setItem('ilpum-fr-conf', JSON.stringify({mode:'remote',openOnly:true}))"); await pg.reload(); await pg.wait_for_timeout(1000)
    print('로그인 없이 보기+접속 막힘 → 안내 화면:', await pg.inner_text('h2'))
    await pg.screenshot(path='n1.png')
    await pg.click('[data-a="disconnect"]'); await pg.wait_for_timeout(900); print('체험 모드로:', await pg.evaluate("APP.be===Local"), '| 카드 수:', await pg.evaluate("document.querySelectorAll('.dcard').length"))
    # 로그인 화면 버튼 배치
    await pg.evaluate("localStorage.setItem('ilpum-fr-conf', JSON.stringify({mode:'remote'}))"); await pg.reload(); await pg.wait_for_timeout(700)
    print('로그인 화면:', await pg.is_visible('#lgForm')); await pg.screenshot(path='n2.png')
    boxes=await pg.evaluate("[...document.querySelectorAll('.card .btn')].map(b=>{const r=b.getBoundingClientRect(); return [b.textContent.trim(), Math.round(r.left), Math.round(r.right), Math.round(r.top)]})"); print('버튼 위치:', boxes)
    print('errs',errs); await b.close()
asyncio.run(main())
