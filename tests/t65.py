# 상권분석: 장어집 자리 기준 · 생존율 · 3km 차량 상권 (t62 의 가짜 SDK·중계를 빌려 씀)
import asyncio
src=open('tests/t62.py',encoding='utf-8').read().rsplit('asyncio.run(main())',1)[0]
G={'__name__':'t62'}; exec(src,G)
from playwright.async_api import async_playwright
async def main():
  FAILS=G['FAILS']; ok=G['ok']
  async with async_playwright() as p:
    b=await p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
    pg=await (await b.new_context(viewport={'width':1300,'height':900})).new_page(); errs=[]
    pg.on('pageerror',lambda e:errs.append(str(e))); pg.on('dialog',lambda d: asyncio.ensure_future(d.accept()))
    await pg.route('**/*',G['handler']); await pg.goto('http://localhost:8765/sangkwon.html'); await pg.wait_for_timeout(600)
    await pg.click('[data-tab=set]'); await pg.wait_for_timeout(200)
    await pg.fill('[data-en]','10'); await pg.click('[data-act=bench]')
    await pg.wait_for_function("JSON.parse(localStorage.getItem('ilpum-sk-v1')||'{}').bench",timeout=120000)
    bench=await pg.evaluate("JSON.parse(localStorage.getItem('ilpum-sk-v1')).bench")
    names=[x['name'] for x in bench['points']]
    ok('1) 장어집 자리 기준: 일식(스시) 빼고 3개 구 장어집 6곳', bench['mode']=='eel' and len(names)==6 and not any('스시' in n for n in names) and all(x.get('selfId') for x in bench['points']), names)
    ok('   구마다 번갈아 고름(앞 3곳이 서로 다른 구)', len({n[2] for n in names[:3]})==3, names)
    t=await pg.inner_text('#pane'); ok('   설정에 "장어집 3곳 중"이 아니라 찾은 수 표시', '장어집 6곳 중 6곳 측정' in t, t[:0])
    await pg.click('[data-tab=list]'); await pg.fill('#q','대구 수성구 범어동 177'); await pg.click('[data-act=find]'); await pg.wait_for_timeout(300)
    await pg.click('[data-cand="0"]'); await pg.wait_for_function("document.querySelector('.scorebox')",timeout=60000); await pg.wait_for_timeout(300)
    body=await pg.inner_text('#pane')
    ok('2) 화면 문구가 "대구 장어집 자리"', '대구 장어집 자리' in body and '기준 상권' not in body)
    ok('3) 차량 상권(3km) 영역', '차량 상권 (3km)' in body)
    sv=await pg.evaluate("(()=>{const c=DB.cands[0]; return [c.m.eelSurv3,c.m.eelSurvN,c.m.eelDongOn,c.m.eelDongClose5]})()")
    ok('4) 장어집 3년 생존율 80% (5곳 중 4곳) · 범어동 영업 3곳', sv==[80,5,3,0], sv)
    ok('   SWOT 에 생존율 기회 문장', '3년 생존율이 80%' in body)
    ok('   오류 없음', not errs, errs)
    await b.close()
  print('모두 통과' if not FAILS else '실패 있음: '+', '.join(FAILS))
asyncio.run(main())
