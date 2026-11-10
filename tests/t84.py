"""신고금액 숨기기·편집 보존·PDF 신고 불가 제외 (가짜 서버)."""
import asyncio
import json
import shutil
import time
from playwright.async_api import async_playwright
import t82 as fixture

async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox'])
        ctx=await b.new_context(viewport={'width':1500,'height':1050})
        await ctx.route('**/*',fixture.handler)
        await ctx.route_web_socket(f'wss://{fixture.HOST}/**',lambda ws:asyncio.ensure_future(ws.close()))
        ses={'mode':'remote','ses':{'access_token':'test','refresh_token':'test','expires_at':int(time.time())+3000,'user':{'email':'test@ilpum.invalid'}}}
        await ctx.add_init_script(f"localStorage.setItem('ilpum-fr-conf',{json.dumps(json.dumps(ses))});sessionStorage.setItem('fr-pay','1');")
        pg=await ctx.new_page()
        errors=[]
        downloads=[]
        pg.on('pageerror',lambda e:errors.append(str(e)))
        pg.on('download',lambda d:downloads.append(d))
        await pg.goto('http://localhost:8765/ilpum-schedule.html?view=daily')
        await pg.locator('.dw-grid').wait_for()
        # 머리글 전체 선택과 키보드 선택, 왼쪽 메뉴 숨김/복원.
        await pg.locator('[data-dw-row="1"]').click()
        assert await pg.locator('.dw-selected').count()==9
        assert await pg.evaluate('dwRange()')=={'r0':1,'r1':1,'c0':0,'c1':8}
        await pg.locator('[data-dw-col="2"]').click()
        assert await pg.locator('.dw-selected').count()==3
        await pg.locator('[data-dw-row="2"]').press('Enter')
        assert await pg.evaluate('dwRange().r0')==2
        await pg.locator('[data-dw=menu]').click()
        assert not await pg.locator('.side').is_visible()
        await pg.locator('[data-dw=menu]').click()
        assert await pg.locator('.side').is_visible()
        assert await pg.locator('[data-dwr="1"][data-dwc="1"]').evaluate('(e)=>getComputedStyle(e).fontSize')=='17px'
        await pg.evaluate("()=>{window.pdfTexts=[];const old=CanvasRenderingContext2D.prototype.fillText;CanvasRenderingContext2D.prototype.fillText=function(t,...a){pdfTexts.push(t);return old.call(this,t,...a)}}")
        await pg.locator('[data-dw=all]').click()
        async with pg.expect_download():
            await pg.locator('[data-dw=pdf]').click()
        await pg.wait_for_function('!DW.busy')
        texts=await pg.evaluate('pdfTexts')
        assert '테스트가' in texts and '120,000' in texts
        assert '선택제외' not in texts and '현찰' not in texts
        # 상태 열을 선택하지 않아도 원본 행 상태로 제외.
        await pg.locator('[data-dwr="2"][data-dwc="1"]').click()
        before=len(downloads)
        await pg.locator('[data-dw=pdf]').click()
        await pg.wait_for_function("!DW.busy && document.querySelector('#toast').textContent.includes('신고 가능한 사람이 없어요')")
        assert len(downloads)==before
        await pg.locator('[data-dw=amount]').click()
        assert await pg.locator('[data-dwc="4"]').count()==0
        assert await pg.locator('[data-dwc="3"]').count()==3
        assert await pg.locator('[data-dwc="5"]').count()==3
        # Tab/화살표는 숨긴 신고금액을 건너뜀.
        await pg.locator('[data-dwr="1"][data-dwc="3"]').dblclick()
        await pg.locator('.dw-editor').press('Tab')
        assert await pg.locator('.dw-editor').get_attribute('aria-label')=='F2 수정'
        await pg.locator('.dw-editor').press('Escape')
        await pg.locator('.dw-scroll').press('ArrowLeft')
        assert await pg.evaluate('DW.b.c')==3
        await pg.locator('[data-dw=all]').click()
        assert '120,000' not in await pg.evaluate('dwCopyData().text')
        await pg.evaluate('pdfTexts=[]')
        async with pg.expect_download():
            await pg.locator('[data-dw=pdf]').click()
        await pg.wait_for_function('!DW.busy')
        texts=await pg.evaluate('pdfTexts')
        assert '테스트가' in texts and '테스트은행 001' in texts
        assert '신고금액' not in texts and '120,000' not in texts and '선택제외' not in texts
        # 숨긴 열을 포함한 선택 범위에 붙여넣기/삭제해도 금액은 보존.
        await pg.evaluate("DW.a={r:1,c:3};DW.b=DW.a;dwPasteRows([['가능','3']])")
        assert await pg.evaluate('dwSheet().rows[1].slice(3,6)')==['가능','120,000','3']
        await pg.evaluate('DW.a={r:1,c:3};DW.b={r:1,c:5};dwPaint()')
        await pg.locator('.dw-scroll').press('Delete')
        assert await pg.evaluate('dwSheet().rows[1][4]')=='120,000'
        await pg.locator('[data-dw=amount]').click()
        assert await pg.locator('[data-dwr="1"][data-dwc="4"]').inner_text()=='120,000'
        await pg.set_viewport_size({'width':390,'height':844})
        assert await pg.evaluate('document.documentElement.scrollWidth<=innerWidth')
        assert not errors,errors
        await b.close()
        print('전체 OK: 신고 불가 행 PDF 제외·불가만 선택 시 다운로드 없음·신고금액 숨김·키보드·붙여넣기·삭제·모바일')

if __name__=='__main__':
    asyncio.run(main())
