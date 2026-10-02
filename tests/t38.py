# 직원 "마지막 근무일": 그 다음 날부터 근무표에서 빠지고, 지난 날은 그대로 (체험 모드)
import asyncio
from playwright.async_api import async_playwright
async def main():
  ok=True
  def chk(n,c):
    nonlocal ok; ok&=bool(c); print(('OK  ' if c else 'FAIL'),n)
  async with async_playwright() as p:
    b=await p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome'); pg=await b.new_page(viewport={'width':1300,'height':900}); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
    await pg.route('**/*', lambda r: r.abort() if 'jsdelivr' in r.request.url or 'supabase' in r.request.url else r.continue_())
    await pg.goto('http://localhost:8765/ilpum-schedule.html')
    await pg.evaluate("localStorage.clear(); localStorage.setItem('ilpum-fr-conf', JSON.stringify({mode:'local'}))"); await pg.reload(); await pg.wait_for_timeout(1200)
    sid=await pg.evaluate("(()=>{ const s=staffList(APP.D).find(x=>x.type==='regular'&&(x.off||[]).length<5); window.__s=s; return s.id; })()")
    name=await pg.evaluate("__s.name")
    day=lambda k: pg.evaluate(f"resolve(APP.D, pd('{k}')).list.some(x=>x.sid==='{sid}')")
    # 일주일 중 이 사람이 일하는 날 찾기
    days=await pg.evaluate("""(()=>{ const out=[]; for(let i=1;i<=14;i++){ const d=addDays(new Date(),i); if(resolve(APP.D,d).list.some(x=>x.sid===__s.id)) out.push(ds(d)); } return out; })()""")
    chk('마지막 근무일 설정 전: 앞으로 근무일이 여러 날', len(days)>=4)
    last=days[1]
    await pg.evaluate("APP.view='staff'; render()"); await pg.wait_for_timeout(200)
    await pg.evaluate(f"openStaff('{sid}')") if False else None
    await pg.click(f'tr[data-sid="{sid}"]'); await pg.wait_for_timeout(300)
    await pg.fill('#sfLast',last); await pg.click('[data-a="staffsave"]'); await pg.wait_for_timeout(300)
    after=[d for d in days if d>last]; before=[d for d in days if d<=last]
    chk('마지막 근무일까지는 근무', all([await day(d) for d in before]))
    chk('그 다음 날부터는 근무표에서 빠짐', not any([await day(d) for d in after]) and len(after)>0)
    chk('직원 목록에 "~까지" 표시', '까지' in await pg.inner_text(f'tr[data-sid="{sid}"]'))
    # 다시 비우면 복구
    await pg.click(f'tr[data-sid="{sid}"]'); await pg.wait_for_timeout(300); await pg.fill('#sfLast',''); await pg.click('[data-a="staffsave"]'); await pg.wait_for_timeout(300)
    chk('비우면 다시 계속 근무', all([await day(d) for d in days]) and 'last' not in await pg.evaluate("Object.keys(APP.D.staff['%s'])"%sid))
    chk('오류 없음', not errs)
  print('전체','OK' if ok else 'FAIL')
asyncio.run(main())
