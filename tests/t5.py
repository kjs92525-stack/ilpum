import asyncio
from playwright.async_api import async_playwright
async def main():
  async with async_playwright() as p:
    b=await p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
    ctx=await b.new_context(viewport={'width':1280,'height':800},has_touch=True); pg=await ctx.new_page(); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
    await pg.route('**/*', lambda r: r.abort() if 'jsdelivr' in r.request.url or 'supabase' in r.request.url else r.continue_())
    await pg.goto('file:///home/claude/fr/ilpum-schedule.html'); await pg.evaluate("localStorage.clear(); localStorage.setItem('ilpum-fr-conf','{\"mode\":\"local\"}')"); await pg.reload(); await pg.wait_for_timeout(600)
    await pg.click('#nav [data-v="week"]'); await pg.wait_for_timeout(200)
    await pg.screenshot(path='c1.png')
    print('board h/w:', await pg.evaluate("(()=>{const w=document.querySelector('.boardwrap'); return [w.clientHeight,w.scrollHeight,w.clientWidth,w.scrollWidth,innerHeight]})()"))
    print('no 부족 text on page:', '부족' not in await pg.inner_text('#main'))
    print('rows shown:', await pg.evaluate("[...document.querySelectorAll('.bl b')].map(b=>b.textContent).join(',')"))
    # 좁은 창에서 가로 스크롤바
    await pg.set_viewport_size({'width':900,'height':800}); await pg.wait_for_timeout(200)
    print('narrow 900: scrollable X =', await pg.evaluate("(()=>{const w=document.querySelector('.boardwrap'); return w.scrollWidth>w.clientWidth})()"), '| scrollbar thickness', await pg.evaluate("(()=>{const w=document.querySelector('.boardwrap'); return w.offsetHeight-w.clientHeight})()"))
    await pg.screenshot(path='c2.png'); await pg.set_viewport_size({'width':1280,'height':800}); await pg.wait_for_timeout(200)
    T=await pg.evaluate("todayStr"); T2=await pg.evaluate("ds(addDays(pd(todayStr),1))")
    # 같은 날 이동: 김지수 홀→카운터
    kim=await pg.evaluate("Object.values(APP.D.staff).find(s=>s.name==='김지수').id")
    chip=pg.locator(f'.bc[data-k="{T}"] .chip[data-sid="{kim}"]'); tgt=pg.locator(f'.bc[data-k="{T}"][data-drop="카운터"]')
    cb=await chip.bounding_box(); tb=await tgt.bounding_box()
    await pg.mouse.move(cb['x']+10,cb['y']+8); await pg.mouse.down(); await pg.mouse.move(cb['x']+40,cb['y']-10,steps=4)
    await pg.mouse.move(tb['x']+40,tb['y']+12,steps=8); print('ghost mode:', await pg.evaluate("document.querySelector('.dghost')?.dataset.mode")); await pg.screenshot(path='c3.png')
    await pg.mouse.up(); await pg.wait_for_timeout(150)
    print('same-day move pos:', await pg.evaluate(f"findItem(APP.D,'{T}','{kim}').pos"), '| drawer opened?', await pg.evaluate("document.querySelector('#drawer').classList.contains('on')"))
    # 다른 날로 복사: 오늘 신지은? → 김지수 내일(이미 근무) 대신 쉬는 날 찾기
    who=await pg.evaluate(f"(()=>{{const a=resolve(APP.D,pd('{T}')).offs.filter(o=>!o.missing); return a.length?a[0].sid:null}})()")
    # 오늘 근무하고 내일 쉬는 사람
    pair=await pg.evaluate(f"(()=>{{const t=resolve(APP.D,pd('{T}')).list.filter(x=>x.sid&&x.type==='regular'), n=new Set(resolve(APP.D,pd('{T2}')).list.map(x=>x.sid)); const f=t.find(x=>!n.has(x.sid)); return f?[f.sid,f.name,f.pos]:null}})()")
    print('candidate', pair)
    if pair:
      sid,name,pos=pair
      chip=pg.locator(f'.bc[data-k="{T}"] .chip[data-sid="{sid}"]'); tgt=pg.locator(f'.bc[data-k="{T2}"][data-drop="{pos}"]')
      cb=await chip.bounding_box(); tb=await tgt.bounding_box()
      await pg.mouse.move(cb['x']+8,cb['y']+8); await pg.mouse.down(); await pg.mouse.move(cb['x']+30,cb['y']+20,steps=3); await pg.mouse.move(tb['x']+30,tb['y']+10,steps=8)
      print('copy ghost mode:', await pg.evaluate("document.querySelector('.dghost')?.dataset.mode")); await pg.mouse.up(); await pg.wait_for_timeout(150)
      print('copied onto next day:', await pg.evaluate(f"!!findItem(APP.D,'{T2}','{sid}')"), '| still on today:', await pg.evaluate(f"!!findItem(APP.D,'{T}','{sid}')"), '| toast:', await pg.inner_text('#toast'))
    # 클릭은 여전히 편집 서랍
    await pg.locator(f'.bc[data-k="{T}"] .chip').first.click(); await pg.wait_for_timeout(200); print('click still opens drawer:', await pg.evaluate("document.querySelector('#drawer').classList.contains('on')")); await pg.keyboard.press('Escape')
    # 터치 꾹 누르기 드래그 (CDP)
    cdp=await ctx.new_cdp_session(pg)
    sid2=await pg.evaluate(f"resolve(APP.D,pd('{T}')).list.find(x=>x.sid&&x.pos==='홀'&&x.sid!=='{kim}').sid")
    chip=pg.locator(f'.bc[data-k="{T}"] .chip[data-sid="{sid2}"]'); tgt=pg.locator(f'.bc[data-k="{T}"][data-drop="그릴"]'); cb=await chip.bounding_box(); tb=await tgt.bounding_box()
    sx,sy=cb['x']+12,cb['y']+8; ex,ey=tb['x']+40,tb['y']+12
    await cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':sx,'y':sy}]}); await pg.wait_for_timeout(450)
    print('after long press ghost?', await pg.evaluate("!!document.querySelector('.dghost')"))
    for i in range(1,9):
      await cdp.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':sx+(ex-sx)*i/8,'y':sy+(ey-sy)*i/8}]}); await pg.wait_for_timeout(20)
    await cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]}); await pg.wait_for_timeout(200)
    print('touch drag moved to 그릴:', await pg.evaluate(f"findItem(APP.D,'{T}','{sid2}').pos"))
    # 짧은 터치는 드래그 안 됨 (스크롤)
    await cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':sx,'y':sy+200}]}); 
    await cdp.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':sx,'y':sy+120}]}); await pg.wait_for_timeout(450)
    print('quick swipe ghost?', await pg.evaluate("!!document.querySelector('.dghost')")); await cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]})
    print('errs',errs); await b.close()
asyncio.run(main())
