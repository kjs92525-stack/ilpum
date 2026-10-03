import asyncio
from playwright.async_api import async_playwright
async def main():
  async with async_playwright() as p:
    b=await p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome',ignore_default_args=['--hide-scrollbars'])
    pg=await b.new_page(viewport={'width':1440,'height':900}); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.on('dialog', lambda d: asyncio.ensure_future(d.accept()))
    await pg.route('**/*', lambda r: r.abort() if 'jsdelivr' in r.request.url or 'supabase' in r.request.url else r.continue_())
    await pg.goto('http://localhost:8765/ilpum-schedule.html'); await pg.evaluate("localStorage.clear(); localStorage.setItem('ilpum-fr-conf','{\"mode\":\"local\"}')"); await pg.reload(); await pg.wait_for_timeout(600)
    names=lambda: pg.evaluate("APP.D.positions.map(p=>p.name).join(',')")
    print('start:', await names())
    await pg.click('[data-a="posmgr"]'); await pg.wait_for_timeout(250); print('drawer:', await pg.inner_text('#dTitle'))
    # 추가
    await pg.fill('#npN','세척'); await pg.press('#npN','Enter'); await pg.wait_for_timeout(200); print('after add:', await names(), '| toast:', await pg.inner_text('#toast'))
    print('새 줄이 카드에 보임:', await pg.evaluate("[...document.querySelectorAll('.dcard:first-child .cl')].some(e=>e.textContent==='세척' && getComputedStyle(e.parentElement).display!=='none')"))
    # 직원 1명 배정 → 이름 바꾸기 → 반영
    sid=await pg.evaluate("Object.values(APP.D.staff)[0].id"); await pg.evaluate(f"put('staff','{sid}',{{...APP.D.staff['{sid}'],pos:'세척'}})")
    inp=pg.locator('#dBody input[data-f="name"]').nth(8); print('9th name input:', await inp.input_value())
    await inp.fill('세척실'); await inp.dispatch_event('change'); await pg.wait_for_timeout(200)
    print('rename ->', await names(), '| staff pos:', await pg.evaluate(f"APP.D.staff['{sid}'].pos"))
    # 색 바꾸기
    await pg.locator('#dBody input[data-f="color"]').nth(8).evaluate("e=>{e.value='#ff0000'; e.dispatchEvent(new Event('change',{bubbles:true}));}"); await pg.wait_for_timeout(150)
    print('color:', await pg.evaluate("APP.D.positions[8].color"))
    # 순서: 위로
    await pg.locator('[data-a="pmmv"][data-n="-1"]').nth(8).click(); await pg.wait_for_timeout(150); print('after move up:', await names())
    # 삭제 (사람 있음) → 이동
    idx=await pg.evaluate("APP.D.positions.findIndex(p=>p.name==='세척실')")
    await pg.locator(f'[data-a="pmdel"][data-i="{idx}"]').click(); await pg.wait_for_timeout(200)
    print('delete panel:', (await pg.inner_text('.why')).replace('\n',' ')[:80]); await pg.select_option('#pmTo','주방'); await pg.screenshot(path='p1.png')
    await pg.click('[data-a="pmdel2"]'); await pg.wait_for_timeout(250)
    print('after delete:', await names(), '| staff moved to:', await pg.evaluate(f"APP.D.staff['{sid}'].pos"))
    # 빈 포지션 삭제 (장치)
    idx=await pg.evaluate("APP.D.positions.findIndex(p=>p.name==='장치')"); await pg.locator(f'[data-a="pmdel"][data-i="{idx}"]').click(); await pg.wait_for_timeout(150)
    print('empty-pos panel has select?', await pg.evaluate("!!document.querySelector('#pmTo')")); await pg.click('[data-a="pmdel2"]'); await pg.wait_for_timeout(200); print('after delete 장치:', await names())
    # 중복 이름 막기
    inp=pg.locator('#dBody input[data-f="name"]').nth(1); await inp.fill('카운터'); await inp.dispatch_event('change'); await pg.wait_for_timeout(100); print('dup toast:', await pg.inner_text('#toast'), '| name kept:', await inp.input_value())
    # 마지막 하나 못 지움
    await pg.evaluate("put('cfg','positions',[APP.D.positions[0]])"); await pg.evaluate("dPositions()"); await pg.wait_for_timeout(150)
    await pg.click('[data-a="pmdel"]'); await pg.wait_for_timeout(100); print('last one toast:', await pg.inner_text('#toast'))
    print('errs',errs); await b.close()
asyncio.run(main())
