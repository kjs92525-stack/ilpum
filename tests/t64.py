# 상권분석 도시 선택 (대구/부산/추가) — t62 의 가짜 SDK·중계를 그대로 빌려 씀
import asyncio, re
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
    await pg.click('[data-tab=set]'); await pg.wait_for_timeout(200)
    ok('2) 설정: 대구 기준 상권 제목·목록', '대구 기준 상권' in await pg.inner_text('#pane') and '동성로' in await pg.input_value('#benchNames'))
    await pg.select_option('#city','부산'); await pg.wait_for_timeout(300)
    ok('3) 부산으로 바꾸면 제목·목록이 부산 것', '부산 기준 상권' in await pg.inner_text('#pane') and '서면' in await pg.input_value('#benchNames') and '동성로' not in await pg.input_value('#benchNames'))
    await pg.select_option('#city','대구'); await pg.wait_for_timeout(300)
    ok('4) 대구로 돌아오면 대구 목록 그대로', '동성로' in await pg.input_value('#benchNames'))
    await pg.select_option('#city','__add'); await pg.wait_for_timeout(300)
    ok('5) 도시 추가(서울): 선택되고 기본 목록은 비어 있음', await pg.input_value('#city')=='서울' and (await pg.input_value('#benchNames')).strip()=='' and '기본 목록이 없어요' in await pg.inner_text('#pane'))
    await pg.reload(); await pg.wait_for_timeout(500)
    ok('6) 새로고침해도 도시 유지', await pg.input_value('#city')=='서울')
    ok('    오류 없음', not errs, errs)
    await b.close()
  print('모두 통과' if not FAILS else '실패 있음: '+', '.join(FAILS))
asyncio.run(main())
