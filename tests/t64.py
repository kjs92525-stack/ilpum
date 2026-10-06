# 상권분석 도시 선택 (대구/부산/추가) — t62 의 가짜 SDK·중계를 빌려 씀
import asyncio
src=open('tests/t62.py',encoding='utf-8').read().rsplit('asyncio.run(main())',1)[0]
G={'__name__':'t62'}; exec(src,G)
from playwright.async_api import async_playwright
async def main():
  FAILS=G['FAILS']; ok=G['ok']
  async with async_playwright() as p:
    b=await p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
    pg=await (await b.new_context(viewport={'width':1300,'height':900})).new_page(); errs=[]
    pg.on('pageerror',lambda e:errs.append(str(e))); pg.on('dialog',lambda d: asyncio.ensure_future(d.accept('서울')))
    await pg.route('**/*',G['handler']); await pg.goto('http://localhost:8765/sangkwon.html'); await pg.wait_for_timeout(600)
    ok('1) 도시 선택: 대구·부산·추가', await pg.evaluate("[...document.querySelectorAll('#city option')].map(o=>o.textContent).join()")=='대구,부산,+ 도시 추가…')
    ph=await pg.get_attribute('#q','placeholder'); ok('2) 검색 예시가 대구', '대구' in ph, ph)
    await pg.select_option('#city','부산'); await pg.wait_for_timeout(300)
    ph=await pg.get_attribute('#q','placeholder'); ok('3) 부산으로 바꾸면 검색 예시가 부산', '부산' in ph, ph)
    await pg.fill('#q','대구 수성구 범어동 177'); await pg.click('[data-act=find]'); await pg.wait_for_timeout(300); await pg.click('[data-cand="0"]')
    await pg.wait_for_function("document.querySelector('.scorebox')",timeout=60000)
    ok('4) 부산을 골랐는데 대구 후보지 → 도시 밖 경고', '부산 밖 주소예요' in await pg.inner_text('#pane'))
    await pg.select_option('#city','대구'); await pg.wait_for_timeout(300)
    ok('5) 대구로 돌아오면 경고 사라짐', '밖 주소예요' not in await pg.inner_text('#pane'))
    await pg.select_option('#city','__add'); await pg.wait_for_timeout(300)
    ok('6) 도시 추가(서울): 선택됨', await pg.input_value('#city')=='서울')
    await pg.reload(); await pg.wait_for_timeout(500)
    ok('7) 새로고침해도 도시 유지', await pg.input_value('#city')=='서울')
    ok('    오류 없음', not errs, errs)
    await b.close()
  print('모두 통과' if not FAILS else '실패 있음: '+', '.join(FAILS))
asyncio.run(main())
