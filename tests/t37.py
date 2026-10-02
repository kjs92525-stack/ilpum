# 직원 검색: 한글 조합 중에는 화면을 다시 그리지 않아 글자가 안 풀림 (실제 IME 대신 CDP insertText/조합 이벤트로 확인)
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
    await pg.evaluate("APP.view='staff'; render()"); await pg.wait_for_timeout(300)
    await pg.focus('#staffQ')
    cdp=await pg.context.new_cdp_session(pg)
    # 조합 중(ㅇ→이→읻→이재): 입력칸이 다시 그려지면 요소가 바뀜
    await pg.evaluate("window.__el=document.querySelector('#staffQ')")
    for txt in ['ㅇ','이','읻','이ㅈ','이재']:
      await cdp.send('Input.imeSetComposition',{'text':txt,'selectionStart':len(txt),'selectionEnd':len(txt)}); await pg.wait_for_timeout(120)
    same=await pg.evaluate("window.__el===document.querySelector('#staffQ')"); chk('조합 중에는 입력칸이 그대로(다시 안 그려짐)', same)
    await cdp.send('Input.insertText',{'text':'이재'}); await pg.wait_for_timeout(300)
    chk('조합이 끝나면 글자가 이재로 들어감', await pg.input_value('#staffQ')=='이재' and await pg.evaluate("APP.q")=='이재')
    chk('입력칸에 포커스 유지', await pg.evaluate("document.activeElement&&document.activeElement.id")=='staffQ')
    chk('오류 없음', not errs)
  print('전체','OK' if ok else 'FAIL')
asyncio.run(main())
