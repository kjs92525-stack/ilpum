"""일용직 원장 복사/붙여넣기·새 월·연도 전환 (실제 클립보드, 가짜 서버)."""
import asyncio
import json
import os
import shutil
import time

from playwright.async_api import async_playwright
import t82 as fixture


async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=os.environ.get('CHROMIUM_PATH') or shutil.which('chromium'), args=['--no-sandbox'])
        ctx = await b.new_context(viewport={'width': 1500, 'height': 1050}, permissions=['clipboard-read', 'clipboard-write'])
        await ctx.route('**/*', fixture.handler)
        await ctx.route_web_socket(f'wss://{fixture.HOST}/**', lambda ws: asyncio.ensure_future(ws.close()))
        ses = {'mode': 'remote', 'ses': {'access_token': 'test', 'refresh_token': 'test', 'expires_at': int(time.time())+3000, 'user': {'email': 'test@ilpum.invalid'}}}
        await ctx.add_init_script(f"localStorage.setItem('ilpum-fr-conf',{json.dumps(json.dumps(ses))});sessionStorage.setItem('fr-pay','1');")
        pg = await ctx.new_page()
        errors = []
        pg.on('pageerror', lambda e: errors.append(str(e)))
        await pg.goto('http://localhost:8765/ilpum-schedule.html?view=daily')
        await pg.locator('.dw-grid').wait_for()
        def cell(r, c):
            return pg.locator(f'.dw-grid td[data-dwr="{r}"][data-dwc="{c}"]')
        # 실제 드래그 → Ctrl+C → 다른 월에서 Ctrl+V. 문자열·앞자리 0 보존.
        a, z = await cell(1, 0).bounding_box(), await cell(1, 2).bounding_box()
        await pg.mouse.move(a['x']+15, a['y']+12)
        await pg.mouse.down()
        await pg.mouse.move(z['x']+15, z['y']+12, steps=12)
        await pg.wait_for_timeout(80)
        await pg.mouse.up()
        await pg.keyboard.press('Control+c')
        copied = await pg.evaluate('navigator.clipboard.readText()')
        assert copied == '\t'.join(fixture.SHEET['rows'][1][:3]), copied
        await pg.locator('[data-dw-month="daily:2026-10"]').click()
        await cell(2, 0).click()
        await pg.keyboard.press('Control+v')
        await pg.wait_for_function("dwSheet().rows[2][1]==='테스트가'")
        assert await cell(2, 2).inner_text() == '000000-0000000'
        assert await cell(2, 0).evaluate('(e)=>getComputedStyle(e).backgroundColor') == 'rgb(248, 241, 221)'
        # 버튼으로 줄바꿈·따옴표가 포함된 셀을 복사하고 원문 그대로 붙여넣기.
        await pg.locator('[data-dw-month="daily:2026-11"]').click()
        await cell(1, 8).dblclick()
        special = '1行目\n2行目 "引用"\t末尾'
        await pg.locator('.dw-editor').fill(special)
        await pg.locator('.dw-editor').press('Escape')
        # Escape는 취소하므로 다시 입력해 확정.
        await cell(1, 8).dblclick()
        await pg.locator('.dw-editor').fill(special)
        await pg.locator('.dw-editor').press('Tab')
        await pg.locator('.dw-editor').press('Escape')
        await cell(1, 8).click()
        await pg.locator('[data-dw=copy]').click()
        await pg.wait_for_function("document.querySelector('#toast').textContent.includes('선택 범위를 복사')")
        assert await pg.evaluate('async()=>dwParseTsv(await navigator.clipboard.readText())') == [[special]]
        await cell(2, 8).click()
        await pg.keyboard.press('Control+v')
        await pg.wait_for_function('dwSheet().rows[2][8].includes("2行目")')
        assert await cell(2, 8).inner_text() == special
        # 표 끝에 여러 행·열을 붙이면 내용을 버리지 않고 표를 확장.
        await cell(2, 8).click()
        await pg.evaluate("navigator.clipboard.writeText('甲\\t乙\\n丙\\t丁')")
        await pg.keyboard.press('Control+v')
        await pg.wait_for_function('dwSheet().rows.length===4 && dwSheet().widths.length===10')
        assert await pg.evaluate('dwSheet().rows[3].slice(8)') == ['丙', '丁']
        # 선택한 사람만 복사한 뒤 빈 12월 생성. 실패해도 원래 월·수정 내용 보존, 재시도 가능.
        await cell(1, 1).click()
        await pg.locator('[data-dw=copypeople]').click()
        await pg.locator('[data-dw-newmonth="12"]').click()
        assert await pg.locator('#dw-new-mode').count() == 0
        fixture.FAIL = True
        await pg.locator('[data-dw=createmonth]').click()
        await pg.wait_for_function('!DW.busy')
        assert '만들지 못' in await pg.locator('#dw-new-error').inner_text()
        assert await pg.evaluate('DW.sheet') == 'daily:2026-11'
        assert not any(r['id']=='daily:2026-12' for r in fixture.ROWS)
        fixture.FAIL = False
        await pg.locator('[data-dw=createmonth]').click()
        await pg.wait_for_function("DW.sheet==='daily:2026-12' && !DW.busy")
        assert await pg.evaluate('dwSheet().rows.length') == 2
        await pg.locator('[data-dw=pastepeople]').click()
        assert await pg.evaluate('dwSheet().rows[1].slice(0,8)') == ['홀','테스트가','000000-0000000','가능','','','테스트은행 001','010-0000-0000']
        assert await pg.evaluate('dwSheet().rows[1][8]') == ''
        assert await pg.evaluate('dwSheet().rows.length') == 2
        assert await pg.locator('[data-dw-month="daily:2026-12"]').get_attribute('aria-pressed') == 'true'
        assert await pg.evaluate("DW.drafts.get(APP.sid+'|daily:2026-11').rows[1][8]") == special
        # 복사본은 원본과 독립. 이미 있는 월은 덮어쓰지 않음.
        await cell(1, 1).dblclick()
        await pg.locator('.dw-editor').fill('12월직원')
        await pg.locator('[data-dw=save]').click()
        await pg.wait_for_function('!DW.busy')
        assert await pg.evaluate("DW.drafts.get(APP.sid+'|daily:2026-11').rows[1][1]") == '테스트가'
        await pg.locator('[data-dw=newmonth]').click()
        await pg.locator('#dw-new-year').fill('2026')
        await pg.select_option('#dw-new-month', '12')
        before = len(fixture.WRITES)
        await pg.locator('[data-dw=createmonth]').click()
        assert '이미 있는 월' in await pg.locator('#dw-new-error').inner_text()
        assert len(fixture.WRITES) == before
        await pg.locator('#dFoot [data-dw=cancelmonth]').click()
        # 내년의 빈 1월 생성. 이전 연도를 보존하고 연도 전체 검색으로 이동.
        reads = len(fixture.READS)
        await pg.select_option('#dw-year', '2027')
        assert await pg.locator('.dw-grid').count() == 0
        await pg.locator('[data-dw-newmonth="1"]').click()
        await pg.locator('[data-dw=createmonth]').click()
        await pg.wait_for_function("DW.sheet==='daily:2027-01' && !DW.busy")
        assert await pg.evaluate('dwSheet().rows.length') == 2
        assert await pg.evaluate('dwSheet().rows[1].every(x=>x===\'\')')
        await pg.locator('#dw-search').fill('12월직원')
        await pg.wait_for_function("DW.sheet==='daily:2026-12' && DW.year===2026")
        assert '2026년 12월' in await pg.locator('.dw-result').inner_text()
        assert len(fixture.READS) == reads
        await pg.reload()
        await pg.locator('.dw-grid').wait_for()
        assert await pg.locator('#dw-year').input_value() == '2027'
        await pg.select_option('#dw-year', '2026')
        assert await pg.evaluate('dwSheet().rows[1][1]') == '12월직원'
        assert not errors, errors
        await b.close()
        print('전체 OK: Ctrl+C/V·복사 버튼·줄바꿈/따옴표·표 확장·월 생성/복사/실패·중복 방지·연도·전체 검색')


if __name__ == '__main__':
    asyncio.run(main())
