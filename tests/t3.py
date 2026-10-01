import asyncio, json
from playwright.async_api import async_playwright
async def main():
  async with async_playwright() as p:
    b=await p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
    errs=[]
    m=await b.new_page(viewport={'width':390,'height':844},device_scale_factor=2); m.on('pageerror',lambda e:errs.append(str(e)))
    await m.route('**/*', lambda r: r.abort() if 'jsdelivr' in r.request.url or 'supabase' in r.request.url else r.continue_())
    await m.goto('file:///home/claude/fr/ilpum-schedule.html'); await m.evaluate("localStorage.clear()"); await m.reload(); await m.wait_for_timeout(600)
    await m.screenshot(path='m1.png')
    T=await m.evaluate("todayStr"); await m.click(f'.bc[data-k="{T}"] .chip >> nth=0'); await m.wait_for_timeout(300); await m.screenshot(path='m2.png')
    await m.keyboard.press('Escape'); await m.click('#mbar [data-v="day"]'); await m.wait_for_timeout(200); await m.screenshot(path='m3.png')
    # roles
    for r in ['hq','owner','manager','staff']:
      await m.evaluate(f"(()=>{{const d=JSON.parse(localStorage.getItem('ilpum-fr-v1')); d.demoRole='{r}'; if('{r}'==='staff') d.demoMe={{bonjum:Object.keys(d.items.bonjum.staff)[0]}}; localStorage.setItem('ilpum-fr-v1',JSON.stringify(d));}})()")
      await m.reload(); await m.wait_for_timeout(500)
      info=await m.evaluate("({role:role(),stores:APP.stores.map(s=>s.name+':'+s.role).join(','),nav:[...document.querySelectorAll('#nav button')].map(b=>b.textContent.trim()).join(','),view:APP.view,payBtn:!!document.querySelector('[data-a=paytog]'),edit:canEdit()})")
      print(r, info)
      if r=='staff': await m.screenshot(path='m4.png')
    print('errs',errs); await b.close()
asyncio.run(main())
