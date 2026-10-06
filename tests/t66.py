# 직원명부 붙여넣기: 시트 12명 → 미리보기, 기존 이름은 날짜만 갱신, 새 이름은 추가, 임시 입사일은 기본으로 무시 (체험 모드)
import asyncio
from playwright.async_api import async_playwright
ROWS=[("점장","공태건","2026-09-10"),("주방","이숙희","2026-05-27"),("홀","금영희","2025-11-04"),("홀","한수정","2026-08-05"),("홀","박자영","2026-09-15"),("홀","백승욱","2026-09-15"),("홀","김경자","2025-10-22"),("장치.그릴","김세훈","2025-11-28"),("장치.그릴","이지후","2026-01-26"),("홀","신주양","2026-01-01"),("홀","백예진","2026-01-01"),("홀","여나현","2026-01-01")]
def exp(k):
  import datetime; d=datetime.date.fromisoformat(k); return d.replace(year=d.year+1)-datetime.timedelta(days=1)
TXT="구분\t성명\t입사일\t입사 1년\t퇴사일\t보건증시작일\t보건증만료일\t근로계약서 작성여부\t연차 대상\n"+"\n".join(f"{g}\t{n}\t2026-01-01\t2027-01-01\t\t{h}\t{exp(h)}\tO/X\tO/X" for g,n,h in ROWS)
async def main():
  ok=True
  def chk(n,c,x=''):
    nonlocal ok; ok&=bool(c); print(('OK  ' if c else 'FAIL'),n,x)
  async with async_playwright() as p:
    b=await p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome'); pg=await b.new_page(viewport={'width':1500,'height':900}); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
    await pg.route('**/*', lambda r: r.abort() if 'jsdelivr' in r.request.url or 'supabase' in r.request.url else r.continue_())
    await pg.goto('http://localhost:8765/ilpum-schedule.html')
    await pg.evaluate("localStorage.clear(); localStorage.setItem('ilpum-fr-conf', JSON.stringify({mode:'local'}))"); await pg.reload(); await pg.wait_for_timeout(1200)
    exist=await pg.evaluate("staffList(APP.D)[0].name"); before=await pg.evaluate("staffList(APP.D,true).length")
    await pg.evaluate("APP.view='staff'; render()"); await pg.click('[data-a="rosteropen"]'); await pg.wait_for_timeout(200)
    txt=TXT.replace("공태건",exist,1)   # 첫 줄은 기존 직원 이름으로 바꿔 '갱신' 경로 확인
    await pg.fill('#rosterTx',txt); await pg.click('[data-a="rosterprev"]'); await pg.wait_for_timeout(200)
    out=await pg.inner_text('#rosterOut')
    n=await pg.evaluate("document.querySelectorAll('#rosterOut tbody tr').length"); chk('미리보기 12줄', n==12, str(n))
    chk('기존 1명 갱신·11명 추가', '1명 갱신 · 11명 새로 추가' in out)
    await pg.click('[data-a="rosterapply"]'); await pg.wait_for_timeout(400)
    after=await pg.evaluate("staffList(APP.D,true).length"); chk('직원 11명 늘어남', after==before+11, f'{before}->{after}')
    s=await pg.evaluate("(n=>{const x=staffList(APP.D,true).find(s=>s.name===n); return {hcIss:x.hcIss,hcExp:x.hcExp,join:x.join,contract:x.contract,annual:x.annual,pos:x.pos};})('이숙희')")
    chk('이숙희 보건증 시작일·만료 자동', s['hcIss']=='2026-05-27' and not s.get('hcExp'), str(s))
    chk('임시 입사일(2026-01-01)은 안 들어감', s.get('join') is None and s.get('contract') is None and s.get('annual') is None)
    ex=await pg.evaluate(f"(()=>{{const x=staffList(APP.D,true).find(s=>s.name==='{exist}'); return {{h:x.hcIss, pos:x.pos}};}})()")
    chk('기존 직원은 포지션 그대로, 보건증만 채움', ex['h']=='2026-09-10', str(ex))
    row=await pg.inner_text('tr[data-sid]:has-text("이숙희")'); chk('목록에 보건증 날짜 표시', '2026-05-27' in row and '2027-05-26' in row, row.replace('\n',' | ')[:100])
    # 입사일 가져오기 켜면 들어감
    await pg.click('[data-a="rosteropen"]'); await pg.fill('#rosterTx',"홀\t테스트\t2025-03-02\t\t2027-02-03\t\t\tO\tX"); await pg.check('#rosterJoin'); await pg.click('[data-a="rosterapply"]'); await pg.wait_for_timeout(300)
    t=await pg.evaluate("(()=>{const x=staffList(APP.D,true).find(s=>s.name==='테스트'); return {j:x.join,l:x.last,c:x.contract,a:x.annual};})()")
    chk('입사일 가져오기 켜면 입사·퇴사·O/X 저장', t=={'j':'2025-03-02','l':'2027-02-03','c':'O','a':'X'}, str(t))
    chk('오류 없음', not errs, str(errs)); await b.close()
  print('전체 OK' if ok else '실패 있음')
asyncio.run(main())
