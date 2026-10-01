import asyncio
from playwright.async_api import async_playwright
async def main():
  async with async_playwright() as p:
    b=await p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome',ignore_default_args=['--hide-scrollbars'])
    ctx=await b.new_context(viewport={'width':1300,'height':820},accept_downloads=True); await ctx.grant_permissions(['clipboard-read','clipboard-write'])
    pg=await ctx.new_page(); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
    await pg.route('**/*', lambda r: r.abort() if 'jsdelivr' in r.request.url or 'supabase' in r.request.url else r.continue_())
    await pg.goto('file:///home/claude/fr/ilpum-schedule.html'); await pg.evaluate("localStorage.clear()"); await pg.reload(); await pg.wait_for_timeout(500)
    for v in ['week','month','day']:
      await pg.click(f'#nav [data-v="{v}"]'); await pg.wait_for_timeout(150)
      print(v,'button:', await pg.inner_text('.vh .btn.pri'))
    await pg.click('#nav [data-v="week"]'); await pg.click('.vh .btn.pri'); await pg.wait_for_timeout(700)
    print('title:', await pg.inner_text('#dTitle'))
    await pg.click('#dBody [data-a="img"] >> text=다음날'); await pg.wait_for_timeout(700); print('next day title:', await pg.inner_text('#dTitle'))
    await pg.fill('#imgDate','2026-10-03'); await pg.dispatch_event('#imgDate','change'); await pg.wait_for_timeout(700); print('picked date title:', await pg.inner_text('#dTitle'))
    await pg.screenshot(path='f1.png')
    await pg.click('[data-a="imgcopy"]'); await pg.wait_for_timeout(250); print(await pg.inner_text('#toast'))
    print('errs',errs); await b.close()
asyncio.run(main())
