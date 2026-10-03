import asyncio
from playwright.async_api import async_playwright
async def main():
  async with async_playwright() as p:
    b=await p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
    pg=await b.new_page(viewport={'width':1440,'height':950}); errs=[]
    pg.on('pageerror',lambda e:errs.append(str(e)))
    await pg.route('**/*', lambda r: r.abort() if 'jsdelivr' in r.request.url or 'supabase' in r.request.url else r.continue_())
    await pg.goto('http://localhost:8765/ilpum-schedule.html'); await pg.evaluate("localStorage.clear()"); await pg.reload(); await pg.wait_for_timeout(600)
    await pg.click('[data-a="paytog"]')
    T=await pg.evaluate("todayStr"); print('today',T)
    kim=await pg.evaluate("Object.values(APP.D.staff).find(s=>s.name==='김지수').id")
    # 1) 김지수 오늘 11시 출근 + 그날 금액 15만
    await pg.click(f'.bc[data-k="{T}"] .chip[data-sid="{kim}"]'); await pg.wait_for_timeout(300)
    await pg.screenshot(path='d1.png')
    await pg.click('[data-a="shk"][data-p="c"][data-v="t"]'); await pg.fill('#cS','11'); await pg.dispatch_event('#cS','input')
    print('hint', await pg.inner_text('#cH'))
    await pg.select_option('#cPk','day'); await pg.fill('#cPv','15'); await pg.dispatch_event('#cPv','input'); print('payhint',await pg.inner_text('#cPH'))
    await pg.click('[data-a="dcsave"]'); await pg.wait_for_timeout(200)
    print('dc', await pg.evaluate(f"JSON.stringify(APP.D.dc['{T}|{kim}'])"), await pg.evaluate(f"JSON.stringify(APP.D.pay['dc:{T}|{kim}'])"))
    print('chip', await pg.inner_text(f'.bc[data-k="{T}"] .chip[data-sid="{kim}"]'))
    # 2) 알바 3일
    await pg.click(f'.bc[data-k="{T}"][data-drop="주방"] .add', force=True); await pg.wait_for_timeout(250)
    await pg.fill('#aName','단기철수'); await pg.select_option('#aPk','day'); await pg.fill('#aPv','13')
    to=await pg.evaluate(f"ds(addDays(pd('{T}'),2))"); await pg.fill('#aTo',to)
    await pg.click('[data-a="addspot"]'); await pg.wait_for_timeout(200); print('toast',await pg.inner_text('#toast'))
    print('spots', await pg.evaluate("Object.values(APP.D.spot).filter(x=>x.name==='단기철수').map(x=>x.date+':'+x.pos).join(',')"))
    # 3) 휴무 처리 via 드로어
    lee=await pg.evaluate(f"resolve(APP.D,pd('{T}')).list.filter(x=>x.sid&&x.sid!=='{kim}'&&x.type==='regular')[0].sid")
    await pg.click(f'.bc[data-k="{T}"] .chip[data-sid="{lee}"]'); await pg.click('[data-a="stk"][data-v="annual"]'); await pg.click('[data-a="dcsave"]'); await pg.wait_for_timeout(150)
    print('offs today', await pg.evaluate(f"resolve(APP.D,pd('{T}')).offs.map(o=>o.name+':'+o.reason).join(',')"))
    # 4) drag: 홍주 홀→카운터
    hong=await pg.evaluate(f"resolve(APP.D,pd('{T}')).list.filter(x=>x.sid&&x.pos==='홀'&&x.sid!=='{kim}')[0].sid")
    src=f'.bc[data-k="{T}"] .chip[data-sid="{hong}"]'
    if await pg.query_selector(src):
      await pg.drag_and_drop(src, f'.bc[data-k="{T}"][data-drop="카운터"]'); await pg.wait_for_timeout(200)
      print('hong pos', await pg.evaluate(f"findItem(APP.D,'{T}','{hong}').pos"))
    # 5) 기간 설정: 이과장 다음주 휴가 이미 있음 → 새로: 전체 홀 주말 11시
    await pg.click('[data-a="view"][data-v="rules"]'); await pg.click('.vh [data-a="rule"]'); await pg.wait_for_timeout(200)
    await pg.fill('#rQ','김'); await pg.dispatch_event('#rQ','input'); await pg.click('[data-a="rsel"][data-v="1"]')
    await pg.fill('#rTo', to); await pg.dispatch_event('#rTo','change'); await pg.click('[data-a="shk"][data-p="r"][data-v="t"]'); await pg.fill('#rS','12'); await pg.dispatch_event('#rS','input')
    await pg.fill('#rMemo','테스트'); await pg.dispatch_event('#rMemo','input')
    print('prev', (await pg.inner_text('#rPrev')).replace('\n',' | ')); await pg.screenshot(path='d2.png')
    await pg.click('[data-a="rulesave"]'); await pg.wait_for_timeout(200); print('toast',await pg.inner_text('#toast'))
    await pg.screenshot(path='v_rules.png')
    # 6) 매주 변동 입력
    await pg.click('[data-a="view"][data-v="week"]'); await pg.click('.vh [data-a="weekly"]'); await pg.wait_for_timeout(200)
    await pg.click('[data-a="wmode"][data-v="time"]'); await pg.wait_for_timeout(100)
    inp=(await pg.query_selector_all('[data-wt]'))[0]; await inp.fill('5시반'); await inp.dispatch_event('change')
    await pg.click('[data-a="wsave"]'); await pg.wait_for_timeout(150); await pg.screenshot(path='d3.png'); await pg.keyboard.press('Escape'); await pg.wait_for_timeout(250)
    # 7) 화면들
    for v in ['month','day','staff','me','hq','set']:
      await pg.click(f'#nav [data-a="view"][data-v="{v}"]'); await pg.wait_for_timeout(300); await pg.screenshot(path=f'v_{v}.png')
    await pg.click('#nav [data-a="view"][data-v="staff"]'); await pg.click('tr[data-a="staff"]'); await pg.wait_for_timeout(200); await pg.screenshot(path='d4.png')
    print('errs',errs); await b.close()
asyncio.run(main())
