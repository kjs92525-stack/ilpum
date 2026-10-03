import asyncio
from playwright.async_api import async_playwright
async def main():
  async with async_playwright() as p:
    b=await p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
    pg=await b.new_page(viewport={'width':1440,'height':1000}); errs=[]
    pg.on('pageerror',lambda e:errs.append(str(e))); pg.on('console',lambda m: errs.append(m.text) if m.type=='error' and 'net::' not in m.text and 'Failed to load' not in m.text else None)
    await pg.route('**/*', lambda r: r.abort() if 'jsdelivr' in r.request.url or 'supabase' in r.request.url else r.continue_())
    await pg.goto('http://localhost:8765/ilpum-schedule.html'); await pg.wait_for_timeout(700)
    await pg.screenshot(path='w1.png')
    await pg.click('[data-a="paytog"]'); await pg.wait_for_timeout(200); await pg.screenshot(path='w2.png',full_page=True)
    print('errs',errs); await b.close()
asyncio.run(main())
