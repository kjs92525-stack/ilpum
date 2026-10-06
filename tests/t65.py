# 직원 목록이 스프레드시트(직원명부) 열 순서대로 나옴 + 근로계약서·연차 대상 O/X 저장 (체험 모드)
import asyncio
from playwright.async_api import async_playwright
async def main():
  ok=True
  def chk(n,c,x=''):
    nonlocal ok; ok&=bool(c); print(('OK  ' if c else 'FAIL'),n,x)
  async with async_playwright() as p:
    b=await p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome'); pg=await b.new_page(viewport={'width':1500,'height':900}); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
    await pg.route('**/*', lambda r: r.abort() if 'jsdelivr' in r.request.url or 'supabase' in r.request.url else r.continue_())
    await pg.goto('http://localhost:8765/ilpum-schedule.html')
    await pg.evaluate("localStorage.clear(); localStorage.setItem('ilpum-fr-conf', JSON.stringify({mode:'local'}))"); await pg.reload(); await pg.wait_for_timeout(1200)
    sid=await pg.evaluate("staffList(APP.D)[0].id")
    await pg.evaluate("APP.view='staff'; render()"); await pg.wait_for_timeout(200)
    heads=await pg.evaluate("[...document.querySelectorAll('#main table.t thead th')].map(x=>x.textContent)")
    want=['구분','성명','입사일','입사 1년','퇴사일','보건증 시작일','보건증 만료일','근로계약서','연차 대상']
    chk('열 순서가 직원명부와 같음', heads[:9]==want, str(heads))
    await pg.click(f'tr[data-sid="{sid}"]'); await pg.wait_for_timeout(300)
    await pg.fill('#sfJoin','2026-01-01'); await pg.fill('#sfLast','2027-02-03'); await pg.fill('#sfHcIss','2026-09-10')
    await pg.select_option('#sfContract','O'); await pg.select_option('#sfAnnual','X')
    await pg.click('[data-a="staffsave"]'); await pg.wait_for_timeout(300)
    row=await pg.inner_text(f'tr[data-sid="{sid}"]')
    for t in ['2026-01-01','2027-01-01','2027-02-03','2026-09-10','2027-09-09']: chk('행에 '+t, t in row, row.replace('\n',' | '))
    st=await pg.evaluate(f"({{c:APP.D.staff['{sid}'].contract,a:APP.D.staff['{sid}'].annual}})")
    chk('O/X 저장', st=={'c':'O','a':'X'}, str(st))
    cells=await pg.evaluate(f"[...document.querySelectorAll('tr[data-sid=\"{sid}\"] td')].slice(7,9).map(x=>x.textContent.trim())")
    chk('목록에 O / X 표시', cells==['O','X'], str(cells))
    await pg.click(f'tr[data-sid="{sid}"]'); await pg.wait_for_timeout(300)
    await pg.select_option('#sfContract',''); await pg.click('[data-a="staffsave"]'); await pg.wait_for_timeout(300)
    chk('미정으로 되돌리면 필드 삭제', 'contract' not in await pg.evaluate(f"Object.keys(APP.D.staff['{sid}'])"))
    chk('오류 없음', not errs, str(errs)); await b.close()
  print('전체 OK' if ok else '실패 있음')
asyncio.run(main())
