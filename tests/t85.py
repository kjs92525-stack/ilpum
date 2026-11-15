"""일용직 원장 자동 저장(2026-11-15): 고치고 2초 뒤 저절로 저장·선택/입력 유지·실패 시 내용 보존 후 다시 저장 (가짜 서버)."""
import asyncio, json, shutil, time
from playwright.async_api import async_playwright
import t82 as fixture

async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path=shutil.which('chromium') or '/opt/pw-browsers/chromium-1194/chrome-linux/chrome',args=['--no-sandbox'])
        ctx=await b.new_context(viewport={'width':1500,'height':1050})
        await ctx.route('**/*',fixture.handler)
        await ctx.route_web_socket(f'wss://{fixture.HOST}/**',lambda ws:asyncio.ensure_future(ws.close()))
        ses={'mode':'remote','ses':{'access_token':'test','refresh_token':'test','expires_at':int(time.time())+3000,'user':{'email':'test@ilpum.invalid'}}}
        await ctx.add_init_script(f"localStorage.setItem('ilpum-fr-conf',{json.dumps(json.dumps(ses))});sessionStorage.setItem('fr-pay','1');")
        pg=await ctx.new_page(); errors=[]; pg.on('pageerror',lambda e:errors.append(str(e)))
        await pg.goto('http://localhost:8765/ilpum-schedule.html?view=daily')
        await pg.locator('.dw-grid').wait_for()
        cell=pg.locator('.dw-grid td[data-dwr="1"][data-dwc="4"]')
        before=len(fixture.WRITES)
        await cell.dblclick(); await pg.locator('.dw-editor').fill('170,000'); await pg.locator('.dw-editor').press('Enter')
        assert '곧 자동 저장' in await pg.locator('#dw-status').inner_text()
        # 다음 칸 입력 중에는 기다림
        assert await pg.locator('.dw-editor').count()==1
        await pg.locator('.dw-editor').press('Escape')
        await pg.wait_for_function("DW.drafts.size===0", timeout=6000)
        w=[x for x in fixture.WRITES[before:] if x['id']=='daily:2026-11']
        assert w and w[-1]['data']['rows'][1][4]=='170,000', w
        assert '자동 저장됨' in await pg.locator('#dw-status').inner_text()
        assert await pg.evaluate('document.activeElement.matches(".dw-scroll")')   # 화면을 다시 그리지 않아 키보드 그대로
        # 실패하면 내용 유지 → 서버가 돌아오면 다시 저장
        fixture.FAIL=True
        await cell.dblclick(); await pg.locator('.dw-editor').fill('180,000'); await pg.locator('.dw-editor').press('Escape')
        await cell.dblclick(); await pg.locator('.dw-editor').fill('180,000'); await pg.locator('.dw-editor').press('Tab'); await pg.locator('.dw-editor').press('Escape')
        await pg.wait_for_function("DW.auto.fail>0", timeout=6000)
        assert '저장 실패' in await pg.locator('#dw-status').inner_text()
        assert await pg.evaluate("dwSheet().rows[1][4]")=='180,000'
        fixture.FAIL=False
        await pg.wait_for_function("DW.drafts.size===0", timeout=9000)
        assert [x for x in fixture.WRITES if x['id']=='daily:2026-11'][-1]['data']['rows'][1][4]=='180,000'
        assert not errors, errors
        print('전체 OK: 일용직 자동 저장')
        await b.close()
asyncio.run(main())
