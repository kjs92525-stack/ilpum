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
    r0=await pg.evaluate("scoreOf(DB.cands[0].m,DB.cands[0]).d.n1k")
    await pg.check('[data-cx=e1]'); await pg.wait_for_timeout(300)
    r1=await pg.evaluate("scoreOf(DB.cands[0].m,DB.cands[0]).d.n1k"); ex=await pg.evaluate("DB.cands[0].compEx")
    ok('5) 경쟁 아님 체크 → 장어집 수에서 빠지고 저장', r1==r0-1 and ex=={'e1':1}, (r0,r1,ex))
    ok('   빠진 줄은 흐리게', await pg.evaluate("document.querySelector('[data-cx=e1]').closest('tr').style.opacity")=='0.45')
    await pg.fill('[data-f=rent]','300'); await pg.fill('[data-f=area]','40'); await pg.wait_for_timeout(500)
    fr=await pg.inner_text('#finres')
    ok('6) 새 기본 가정(원가 47%·감가상각 60개월): 손익분기 3,333만 · 비수기 보정 안내', '3,333만' in fr and '감가상각 월 167만원' in fr and '연평균 월매출 약' in fr, fr[:200])
    await pg.fill('[data-f=target]','3000'); await pg.wait_for_timeout(500)
    fr=await pg.inner_text('#finres')
    ok('7) 목표 3,000만 → 계절 막대: 적자 달 10개월 · 1년 합계 -800만', '적자 달 10개월' in fr and '-800만원' in fr, fr[fr.find('계절'):fr.find('계절')+120])
    ok('   오류 없음', not errs, errs)
    await b.close()
  print('모두 통과' if not FAILS else '실패 있음: '+', '.join(FAILS))
asyncio.run(main())
