import asyncio
from playwright.async_api import async_playwright
async def main():
  async with async_playwright() as p:
    b=await p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome',ignore_default_args=['--hide-scrollbars'])
    pg=await b.new_page(viewport={'width':1440,'height':900}); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
    await pg.route('**/*', lambda r: r.abort() if 'jsdelivr' in r.request.url or 'supabase' in r.request.url else r.continue_())
    await pg.goto('file:///home/claude/fr/ilpum-schedule.html'); await pg.evaluate("localStorage.clear(); localStorage.setItem('ilpum-fr-conf','{\"mode\":\"local\"}')"); await pg.reload(); await pg.wait_for_timeout(600)
    print('default view:', await pg.evaluate("APP.view"), '| title:', await pg.inner_text('.vh h1'), '| cards:', await pg.evaluate("document.querySelectorAll('.dcard').length"))
    print('nav:', await pg.evaluate("[...document.querySelectorAll('#nav button')].map(b=>b.textContent.trim()).join(' / ')"))
    await pg.screenshot(path='h1.png')
    # 7일 모드
    await pg.click('[data-a="cmode"][data-v="week7"]'); await pg.wait_for_timeout(200); print('7일 cards:', await pg.evaluate("document.querySelectorAll('.dcard').length"), '| title', await pg.inner_text('.vh h1'))
    await pg.click('[data-a="cnav"][data-n="1"]'); print('next 7일 title', await pg.inner_text('.vh h1'))
    await pg.click('[data-a="cmode"][data-v="month"]'); await pg.click('[data-a="cnav"][data-n="1"]'); print('next month', await pg.inner_text('.vh h1'), await pg.evaluate("document.querySelectorAll('.dcard').length"))
    await pg.click('[data-a="cnav"][data-n="0"]')
    T=await pg.evaluate("todayStr"); T2=await pg.evaluate("ds(addDays(pd(todayStr),1))")
    # 이름 클릭 → 편집
    await pg.locator(f'.dcard .bc[data-k="{T}"] .chip').first.click(); await pg.wait_for_timeout(250); print('click opens drawer:', await pg.evaluate("document.querySelector('#drawer').classList.contains('on')")); await pg.keyboard.press('Escape'); await pg.wait_for_timeout(300)
    await pg.click('[data-a="cmode"][data-v="week7"]'); await pg.wait_for_timeout(150)
    pair=await pg.evaluate(f"(()=>{{const t=resolve(APP.D,pd('{T}')).list.filter(x=>x.sid&&x.type==='regular'), n=new Set(resolve(APP.D,pd('{T2}')).list.map(x=>x.sid)); const f=t.find(x=>!n.has(x.sid)); return f?[f.sid,f.pos]:null}})()")
    print('pair', pair)
    if pair:
      sid,pos=pair; chip=pg.locator(f'.dcard .bc[data-k="{T}"] .chip[data-sid="{sid}"]'); await chip.scroll_into_view_if_needed(); cb=await chip.bounding_box()
      await pg.mouse.move(cb['x']+8,cb['y']+8); await pg.mouse.down(); await pg.mouse.move(cb['x']+30,cb['y']+20,steps=3)
      empt=await pg.evaluate("[...document.querySelectorAll('.cr.empty')].filter(e=>getComputedStyle(e).display!=='none').length")
      print('empty rows revealed while dragging:', empt>0)
      tgt=pg.locator(f'.dcard .bc[data-k="{T2}"][data-drop="{pos}"]'); tb=await tgt.bounding_box()
      await pg.mouse.move(tb['x']+30,tb['y']+10,steps=8)
      print('mode:', await pg.evaluate("document.querySelector('.dghost')?.dataset.mode")); await pg.mouse.up(); await pg.wait_for_timeout(200)
      print('copied to next day:', await pg.evaluate(f"!!findItem(APP.D,'{T2}','{sid}')"), '|', await pg.inner_text('#toast'))
    await pg.wait_for_timeout(700)
    await pg.click(f'.dcard .ch [data-a="img"][data-k="{T}"]'); await pg.wait_for_timeout(700); print('photo drawer:', await pg.inner_text('#dTitle')); await pg.keyboard.press('Escape')
    print('errs',errs); await b.close()
asyncio.run(main())
