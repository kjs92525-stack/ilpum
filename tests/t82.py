"""일용직 원장: 원문·권한·편집 저장·범위 드래그·PDF·실패 보존 (가짜 서버)."""
import asyncio
import copy
import json
import os
import re
import shutil
import time
from playwright.async_api import async_playwright

BON = '0134d989-757a-4b60-9cb3-93245de2cac8'
HOST = 'bdqcrbnbuoujozlpttbe.supabase.co'
SHEET = {'name': '11월', 'widths': [90, 130, 170, 110, 100, 100, 220, 160, 250],
         'rows': [['근무형태', '성함', '주민번호', '신고가능여부', '신고금액', '근무일', '계좌번호', '연락처', '비고(근무일자 등)'],
                  ['홀', '테스트가', '000000-0000000', '가능', '120,000', '2', '테스트은행 001', '010-0000-0000', '줄바꿈\n원문 <>&'],
                  ['주방', '선택제외', '', '불가능', '', '', '현찰', '', '메모']],
         'styles': {'1,0': {'bg': '#FFFF00', 'bold': True}, '1,1': {'bg': '#FFFF00', 'bold': True}}}
ROWS = [{'kind': 'pay', 'id': 'daily:2026-11', 'data': copy.deepcopy(SHEET)},
        {'kind': 'pay', 'id': 'daily:2026-10', 'data': {**copy.deepcopy(SHEET), 'name': '10월'}}]
ROWS[1]['data']['rows'][2][1] = '지난달직원'
FAIL = False
PAY = True
WRITES = []
READS = []


async def handler(route):
    global ROWS
    req = route.request
    if 'localhost' in req.url:
        return await route.continue_()
    async def j(value, status=200):
        await route.fulfill(status=status, content_type='application/json', body=json.dumps(value))
    if HOST not in req.url:
        return await route.abort()
    if '/rpc/sch_my_stores' in req.url:
        return await j([{'id': BON, 'name': '일품집 본점', 'is_hq': True, 'role': 'hq', 'can_pay': PAY}])
    if '/rest/v1/sch_items' in req.url:
        if req.method == 'GET':
            READS.append(req.url)
            return await j([] if 'updated_at=gt' in req.url or not PAY else [{**r, 'updated_at': '2026-11-01T00:00:00Z', 'deleted': False} for r in ROWS])
        if FAIL:
            return await j({'message': 'permission denied'}, 403)
        body = json.loads(req.post_data)
        if isinstance(body, dict):
            if any(r['id'] == body['id'] for r in ROWS):
                return await j({'message': 'duplicate key 23505'}, 409)
            body = [body]
        WRITES.extend(body)
        for new in body:
            ROWS = [r for r in ROWS if r['id'] != new['id']] + [new]
        return await route.fulfill(status=201, body='')
    await j([])


async def main():
    global FAIL, PAY
    async with async_playwright() as p:
        browser = await p.chromium.launch(executable_path=os.environ.get('CHROMIUM_PATH') or shutil.which('chromium') or '/opt/pw-browsers/chromium-1194/chrome-linux/chrome', args=['--no-sandbox'])
        ctx = await browser.new_context(viewport={'width': 1500, 'height': 950})
        await ctx.route('**/*', handler)
        await ctx.route_web_socket(f'wss://{HOST}/**', lambda ws: asyncio.ensure_future(ws.close()))
        conf = {'mode': 'remote', 'ses': {'access_token': 'test', 'refresh_token': 'test', 'expires_at': int(time.time()) + 3000, 'user': {'email': 'test@ilpum.invalid'}}}
        await ctx.add_init_script(f"localStorage.setItem('ilpum-fr-conf', {json.dumps(json.dumps(conf))});")
        pg = await ctx.new_page()
        errors = []
        pg.on('pageerror', lambda e: errors.append(str(e)))
        await pg.goto('http://localhost:8765/ilpum-schedule.html?view=daily')
        await pg.get_by_text('개인정보가 포함된 원장이에요').wait_for()
        assert await pg.locator('.dw-grid').count() == 0
        await pg.locator('[data-a=paytog]').click()
        await pg.locator('.dw-grid').wait_for()
        assert await pg.locator('[data-dw-month="daily:2026-11"]').get_attribute('aria-pressed') == 'true'
        assert await pg.locator('.dw-grid td[data-dwr="1"][data-dwc="8"]').inner_text() == SHEET['rows'][1][8]
        assert await pg.locator('.dw-grid td[data-dwr="1"][data-dwc="1"]').evaluate('(e)=>getComputedStyle(e).backgroundColor') == 'rgb(248, 241, 221)'
        nav = await pg.locator('#nav button').evaluate_all('(bs)=>bs.map(b=>b.dataset.v)')
        assert nav.index('staff') < nav.index('daily') < nav.index('rules')
        # 월 전체 검색은 추가 서버 조회 없이 다른 월로 이동하고 해당 행을 강조.
        reads_before = len(READS)
        await pg.locator('#dw-search').fill('지난달직원')
        await pg.wait_for_function("DW.sheet==='daily:2026-10' && DW.hits.length===1")
        assert await pg.locator('.dw-search-current mark').inner_text() == '지난달직원'
        assert await pg.locator('[data-dw-month="daily:2026-10"]').get_attribute('aria-pressed') == 'true'
        await pg.locator('#dw-search').fill('테스트가')
        await pg.wait_for_function("DW.hits.length===2 && DW.sheet==='daily:2026-11'")
        await pg.locator('.dw-result').filter(has_text='10월').click()
        assert await pg.evaluate('DW.sheet') == 'daily:2026-10'
        assert await pg.locator('.dw-search-current mark').inner_text() == '테스트가'
        await pg.locator('#dw-search').fill('없는직원')
        await pg.locator('.dw-noresult').wait_for()
        assert await pg.locator('.dw-search-hit').count() == 0
        await pg.locator('#dw-search').fill('')
        await pg.wait_for_function("DW.hits.length===0 && DW.search===''")
        await pg.locator('.dw-results').wait_for(state='hidden')
        await pg.locator('[data-dw-month="daily:2026-11"]').click()
        assert len(READS) == reads_before, '검색·월 이동에서 추가 조회 발생'
        for col in [2, 3, 7]:
            td = pg.locator(f'.dw-grid td[data-dwr="1"][data-dwc="{col}"]')
            assert await td.evaluate('(e)=>getComputedStyle(e).whiteSpace') == 'nowrap'
            assert await td.evaluate('(e)=>parseFloat(getComputedStyle(e).fontSize)') == 15
        cell = pg.locator('.dw-grid td[data-dwr="1"][data-dwc="4"]')
        # 한 번 클릭은 선택만, 더블클릭으로 입력. Tab 오른쪽, Enter 아래쪽.
        await cell.click()
        assert await pg.locator('.dw-editor').count() == 0
        await cell.dblclick()
        assert await pg.locator('.dw-editor').get_attribute('aria-label') == 'E2 수정'
        await pg.locator('.dw-editor').fill('150,000')
        await pg.locator('.dw-editor').dispatch_event('keydown', {'key': 'Enter', 'isComposing': True, 'keyCode': 229})
        assert await pg.locator('.dw-editor').get_attribute('aria-label') == 'E2 수정'
        await pg.locator('.dw-editor').press('Tab')
        assert await pg.locator('.dw-editor').get_attribute('aria-label') == 'F2 수정'
        assert await cell.inner_text() == '150,000'
        await pg.locator('.dw-editor').press('Enter')
        assert await pg.locator('.dw-editor').get_attribute('aria-label') == 'F3 수정'
        await pg.locator('.dw-editor').press('Shift+Enter')
        assert await pg.locator('.dw-editor').get_attribute('aria-label') == 'F2 수정'
        await pg.locator('.dw-editor').press('Shift+Tab')
        assert await pg.locator('.dw-editor').get_attribute('aria-label') == 'E2 수정'
        await pg.locator('.dw-editor').press('End')
        await pg.locator('.dw-editor').press('Alt+Enter')
        assert '\n' in await pg.locator('.dw-editor').input_value()
        await pg.locator('.dw-editor').press('Escape')
        assert await cell.inner_text() == '150,000'
        # 편집 밖에서도 Enter 이동, 마지막 열 Tab은 다음 행 첫 열로 이동.
        await pg.locator('.dw-scroll').press('Enter')
        assert await pg.locator('.dw-editor').get_attribute('aria-label') == 'E3 수정'
        await pg.locator('.dw-editor').press('Escape')
        await pg.locator('.dw-grid td[data-dwr="1"][data-dwc="8"]').dblclick()
        await pg.locator('.dw-editor').press('Tab')
        assert await pg.locator('.dw-editor').get_attribute('aria-label') == 'A3 수정'
        await pg.locator('.dw-editor').press('Shift+Tab')
        assert await pg.locator('.dw-editor').get_attribute('aria-label') == 'I2 수정'
        await pg.locator('.dw-editor').press('Escape')
        # 원본에 홀 색상이 남아 있어도 현재 입력값으로 즉시 색상을 결정.
        role_cell = pg.locator('.dw-grid td[data-dwr="1"][data-dwc="0"]')
        hall_color = await role_cell.evaluate('(e)=>getComputedStyle(e).backgroundColor')
        await role_cell.dblclick()
        await pg.locator('.dw-editor').fill('주방')
        await pg.locator('.dw-editor').press('Tab')
        assert await role_cell.evaluate('(e)=>getComputedStyle(e).textAlign') == 'center'
        assert await pg.evaluate('dwCellTheme(dwSheet(),1,0).align') == 'center'
        kitchen_color = await role_cell.evaluate('(e)=>getComputedStyle(e).backgroundColor')
        assert kitchen_color == 'rgb(131, 201, 154)' and kitchen_color != hall_color
        assert await pg.evaluate("dwCellTheme(dwSheet(),1,0).bg") == '#83c99a'
        await pg.locator('[data-dw=save]').click()
        await pg.wait_for_function('!DW.busy')
        assert WRITES[-1]['kind'] == 'pay' and WRITES[-1]['id'] == 'daily:2026-11'
        assert WRITES[-1]['data']['rows'][1][4] == '150,000'
        assert WRITES[-1]['data']['rows'][1][8] == SHEET['rows'][1][8]
        await pg.reload()
        await pg.locator('.dw-grid').wait_for()
        assert await cell.inner_text() == '150,000'
        assert await role_cell.inner_text() == '주방'
        assert await role_cell.evaluate('(e)=>getComputedStyle(e).backgroundColor') == kitchen_color
        await role_cell.dblclick()
        await pg.locator('.dw-editor').fill('홀')
        await pg.locator('.dw-editor').press('Tab')
        assert await role_cell.evaluate('(e)=>getComputedStyle(e).backgroundColor') == hall_color
        # 저장 실패·월 전환 후에도 수정 내용 보존.
        FAIL = True
        await cell.dblclick()
        await pg.locator('.dw-editor').fill('160,000')
        await pg.locator('.dw-editor').press('Enter')
        await pg.locator('[data-dw=save]').click()
        await pg.wait_for_function('!DW.busy')
        assert '수정됨' in await pg.locator('#dw-status').inner_text()
        await pg.locator('[data-dw-month="daily:2026-10"]').click()
        await pg.locator('[data-dw-month="daily:2026-11"]').click()
        assert await cell.inner_text() == '160,000'
        FAIL = False
        # 실제 마우스로 B2:E2만 선택. PDF에 그리는 문자도 검증.
        start = await pg.locator('.dw-grid td[data-dwr="1"][data-dwc="1"]').bounding_box()
        end = await cell.bounding_box()
        await pg.mouse.move(start['x']+20, start['y']+15)
        await pg.mouse.down()
        await pg.mouse.move(end['x']+20, end['y']+15, steps=12)
        await pg.wait_for_timeout(100)
        await pg.mouse.up()
        assert await pg.locator('#dw-range').inner_text() == 'B2:E2'
        assert await pg.locator('.dw-selected').count() == 4
        await pg.evaluate("()=>{window.pdfTexts=[]; const old=CanvasRenderingContext2D.prototype.fillText; CanvasRenderingContext2D.prototype.fillText=function(t,...a){pdfTexts.push(t); return old.call(this,t,...a)}}")
        async with pg.expect_download() as down:
            await pg.locator('[data-dw=pdf]').click()
        download = await down.value
        assert download.suggested_filename.endswith('_B2-E2.pdf')
        pdf_path = '/tmp/ilpum-daily-test.pdf'
        await download.save_as(pdf_path)
        pdf = open(pdf_path, 'rb').read()
        assert pdf.startswith(b'%PDF-1.4') and b'%%EOF' in pdf
        texts = await pg.evaluate('pdfTexts')
        assert '테스트가' in texts and '160,000' in texts
        assert '선택제외' not in texts and '테스트은행 001' not in texts and '근무형태' not in texts
        # 긴 표는 여러 페이지, 긴 셀은 줄을 나눠 마지막까지 보존.
        await pg.evaluate("window.longSheet=JSON.parse(JSON.stringify(dwSheet())); longSheet.rows=Array.from({length:100},(_,i)=>['행'+i,...Array(8).fill('긴 내용\\n두 번째 줄')]); DW.a={r:0,c:0};DW.b={r:99,c:8};")
        count = await pg.evaluate("(async()=>{const b=await dwMakePdf(longSheet,dwRange(),'테스트'); const t=await b.text(); return (t.match(/\\/Type \\/Page /g)||[]).length})()")
        assert count > 1
        await pg.locator('[data-dw=clear]').click()
        assert await pg.locator('[data-dw=pdf]').is_disabled()
        await pg.set_viewport_size({'width': 390, 'height': 844})
        assert await pg.evaluate('document.documentElement.scrollWidth <= innerWidth')
        await pg.locator('[data-a=paytog]').click()
        assert await pg.locator('.dw-grid').count() == 0
        await pg.reload()
        PAY = False
        await pg.reload()
        await pg.wait_for_function('APP.st !== null')
        assert await pg.locator('#nav [data-v=daily]').count() == 0
        assert await pg.locator('.dw-grid').count() == 0
        # 통합관리 메뉴와 iframe 간 이동·권한 표시.
        PAY = True
        shell = await ctx.new_page()
        shell.on('pageerror', lambda e: errors.append(str(e)))
        await shell.goto('http://localhost:8765/index.html#daily')
        frame = shell.frame_locator('iframe.fr[title="sch"]')
        await frame.locator('h1').filter(has_text='일용직근무자').wait_for()
        assert await shell.locator('#sub-sch [data-go=daily]').get_attribute('aria-current') == 'page'
        await shell.locator('#sub-sch [data-go=rules]').click()
        await frame.locator('h1').filter(has_text='기간 설정').wait_for()
        await shell.locator('#sub-sch [data-go=daily]').click()
        await frame.locator('h1').filter(has_text='일용직근무자').wait_for()
        PAY = False
        await shell.reload()
        await shell.wait_for_function("ME.mode==='in'")
        assert await shell.locator('#sub-sch [data-go=daily]').is_hidden()
        assert not errors, errors
        await browser.close()
        print('전체 OK: 일용직 원문·권한·저장/실패·드래그·선택 PDF·페이지 나눔·모바일')


if __name__ == '__main__':
    asyncio.run(main())
