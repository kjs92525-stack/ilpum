# 오전 출근: 스케줄에서 고를 수 있고 5시간으로 계산됨, 라벨 '오전' (체험 모드)
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
    chk('출근 시간에 오전 버튼', await pg.is_visible('[data-a=shk][data-p=a][data-v=am]'))
    await pg.fill('#aName','오전알바'); await pg.click('[data-a=shk][data-p=a][data-v=am]'); await pg.click('[data-a=addspot]'); await pg.wait_for_timeout(400)
    x=await pg.evaluate("Object.values(APP.D.spot).find(s=>s.name==='오전알바')")
    chk('sh=am 저장', x['sh']=={'k':'am'}, str(x))
    chk('5시간', await pg.evaluate("hoursOf(APP.D.store,{k:'am'})")==5)
    chk('span 12~17시', await pg.evaluate("spanOf(APP.D.store,{k:'am'})")==[720,1020])
    await pg.evaluate("APP.view='cards'; render()"); await pg.wait_for_timeout(300)
    chk('카드에 오전 표시', await pg.evaluate("[...document.querySelectorAll('#main .chip i')].some(e=>e.textContent==='오전')"))
    chk('오류 없음', not errs, str(errs)); await b.close()
  print('전체 OK' if ok else '실패 있음')
asyncio.run(main())
