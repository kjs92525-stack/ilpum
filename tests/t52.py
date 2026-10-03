# 직원 "이름 옆 표기": 편집 창에서 넣으면 카드·주간표·하루 화면에 이름 옆에 작게 뜸, 날짜 메모(memo)와는 별개 (체험 모드)
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
    sid=await pg.evaluate("(()=>{ const s=staffList(APP.D).find(x=>x.type==='regular'&&(x.off||[]).length<4); window.__s=s; return s.id; })()")
    name=await pg.evaluate("__s.name")
    await pg.evaluate("APP.view='staff'; render()"); await pg.wait_for_timeout(200)
    await pg.click(f'tr[data-sid="{sid}"]'); await pg.wait_for_timeout(300)
    chk('편집 창에 이름 옆 표기 칸', await pg.is_visible('#sfNote'))
    await pg.fill('#sfNote','신입'); await pg.click('[data-a="staffsave"]'); await pg.wait_for_timeout(300)
    chk('직원 목록에 표기', '신입' in await pg.inner_text(f'tr[data-sid="{sid}"]'))
    chk('데이터에 note 로 저장, 메모(dc)와 별개', await pg.evaluate(f"APP.D.staff['{sid}'].note")=='신입' and not await pg.evaluate("Object.values(APP.D.dc||{}).some(v=>v&&v.memo==='신입')"))
    # 근무하는 날 하나 찾아서 각 화면 확인
    key=await pg.evaluate("""(()=>{ for(let i=0;i<14;i++){ const d=addDays(new Date(),i); if(resolve(APP.D,d).list.some(x=>x.sid===__s.id)) return ds(d); } })()""")
    L=await pg.evaluate(f"resolve(APP.D, pd('{key}')).list.find(x=>x.sid==='{sid}').nl")
    chk('근무 계산 결과에 표기가 실림', L=='신입', L)
    for view in ('cards','week','day'):
      await pg.evaluate(f"APP.view='{view}'; render()"); await pg.wait_for_timeout(300)
      n=await pg.evaluate(f"[...document.querySelectorAll('#main .nl2')].filter(e=>e.textContent==='신입').length")
      chk(f'{view} 화면에 이름 옆 표기', n>=1, str(n))
    # 지우면 사라짐
    await pg.evaluate("APP.view='staff'; render()"); await pg.click(f'tr[data-sid="{sid}"]'); await pg.wait_for_timeout(300)
    await pg.fill('#sfNote',''); await pg.click('[data-a="staffsave"]'); await pg.wait_for_timeout(300)
    chk('비우면 note 삭제', 'note' not in await pg.evaluate(f"Object.keys(APP.D.staff['{sid}'])"))
    await pg.evaluate("APP.view='cards'; render()"); await pg.wait_for_timeout(200)
    chk('비우면 화면에서도 사라짐', await pg.evaluate("[...document.querySelectorAll('#main .nl2')].length")==0)
    chk('오류 없음', not errs, str(errs)); await b.close()
  print('전체 OK' if ok else '실패 있음')
asyncio.run(main())
