# 당일알바 이름 옆 표기(당일지급): 넣을 때·고칠 때 입력, 카드에 표시, 메모(memo)와 별개 (체험 모드)
import asyncio
from playwright.async_api import async_playwright
async def main():
  ok=True
  def chk(n,c,x=''):
    nonlocal ok; ok&=bool(c); print(('OK  ' if c else 'FAIL'),n,x)
  async with async_playwright() as p:
    b=await p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome'); pg=await b.new_page(viewport={'width':1300,'height':900}); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
    await pg.route('**/*', lambda r: r.abort() if 'jsdelivr' in r.request.url or 'supabase' in r.request.url else r.continue_())
    await pg.goto('http://localhost:8765/ilpum-schedule.html')
    await pg.evaluate("localStorage.clear(); localStorage.setItem('ilpum-fr-conf', JSON.stringify({mode:'local'}))"); await pg.reload(); await pg.wait_for_timeout(1200)
    key=await pg.evaluate("ds(new Date())")
    await pg.evaluate(f"dAdd(APP.D.positions[0].name,'{key}')"); await pg.wait_for_timeout(300)
    await pg.fill('#aName','테스트알바'); await pg.click('[data-t=aNote]'); chk('버튼이 칸을 채움', await pg.input_value('#aNote')=='당일지급')
    await pg.click('[data-a=addspot]'); await pg.wait_for_timeout(400)
    x=await pg.evaluate("Object.values(APP.D.spot).find(s=>s.name==='테스트알바')")
    chk('spot 에 note 저장, memo 와 별개', x['note']=='당일지급' and not x.get('memo'), str(x))
    chk('resolve 에 nl 로 실림', await pg.evaluate(f"resolve(APP.D,pd('{key}')).list.find(l=>l.name==='테스트알바').nl")=='당일지급')
    await pg.evaluate("APP.view='cards'; render()"); await pg.wait_for_timeout(300)
    chk('카드에 표시', await pg.evaluate("[...document.querySelectorAll('#main .nl2')].some(e=>e.textContent==='당일지급')"))
    await pg.evaluate(f"dSpot('{x['id']}')"); await pg.wait_for_timeout(300)
    chk('편집 창에 값 유지', await pg.input_value('#spNote')=='당일지급')
    await pg.fill('#spNote',''); await pg.click('[data-a=spotsave]'); await pg.wait_for_timeout(300)
    chk('비우면 note 삭제', 'note' not in await pg.evaluate(f"APP.D.spot['{x['id']}']"))
    chk('오류 없음', not errs, str(errs)); await b.close()
  print('전체 OK' if ok else '실패 있음')
asyncio.run(main())
