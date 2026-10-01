import asyncio, json, datetime
from playwright.async_api import async_playwright
OLD='https://fmzpmekypmjuydgxpnlu.supabase.co'; NEW='https://bdqcrbnbuoujozlpttbe.supabase.co'; BON='0134d989-757a-4b60-9cb3-93245de2cac8'
items=json.load(open('/home/claude/imp/items.json'))
ROWS=[{"kind":"cfg","id":"store","data":{"name":"일품집 본점"},"deleted":False},
      {"kind":"cfg","id":"positions","data":[{"name":n,"color":c,"req":[0]*7} for n,c in [('카운터','#3C5A86'),('홀','#2F6B3F'),('그릴','#B8621B'),('주방','#8A2E2E'),('장치','#5B3F86'),('주차','#55605A'),('장잡','#1F6F78'),('배송','#8A6A12')]],"deleted":False}]
for kind in ['staff','dc','spot','aw']:
    for k,v in items[kind].items(): ROWS.append({"kind":kind,"id":k,"data":v,"deleted":False})
RES={"2026-10-01":{"items":[
 {"id":"a1","name":"홍길동","phone":"010-1111-2222","time":"18:30","pp":"5+1","tables":["33","34"],"req":"창가 자리","done":False},
 {"id":"a2","name":"김철수","phone":"010-3333-4444","time":"12:00","pp":"4","tables":["5"],"done":True},
 {"id":"a3","name":"취소손님","time":"19:00","pp":"2","tables":["R1-1"],"tnote":"취소 (노쇼)"},
 {"id":"a4","name":"삭제됨","time":"20:00","pp":"2","deleted":True}]}}
async def main():
  async with async_playwright() as p:
    b=await p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
    ctx=await b.new_context(viewport={'width':1440,'height':900},timezone_id='Asia/Seoul')
    await ctx.add_init_script("(()=>{const R=Date; const fixed=new R('2026-10-01T12:40:00+09:00').getTime(); const off=fixed-R.now(); class D extends R{constructor(...a){ if(a.length===0) super(R.now()+off); else super(...a);} static now(){ return R.now()+off; }} window.Date=D; })()")
    await ctx.add_init_script("try{ if(!localStorage.getItem('ilpum-fr-conf')) localStorage.setItem('ilpum-fr-conf', JSON.stringify({mode:'remote',openOnly:true})); }catch(e){}")
    pg=await ctx.new_page(); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
    async def route(r):
      u=r.request.url; J=lambda o: r.fulfill(status=200,content_type='application/json',body=json.dumps(o))
      if u.startswith('file:') or u.startswith('http://localhost'): return await r.continue_()
      if u.startswith(OLD):
        if 'reservations_day' in u:
          for k,v in RES.items():
            if 'id=eq.'+k in u: return await J([{"data":v}])
          return await J([])
        return await J([])
      if u.startswith(NEW):
        if '/rpc/sch_open_store' in u: return await J([{"id":BON,"name":"일품집 본점","has_pin":False}])
        if '/rpc/sch_my_stores' in u: return await J([{"id":BON,"name":"일품집 본점","is_hq":True,"role":"hq","can_pay":True,"staff_id":None}])
        if '/sch_items' in u: return await J([] if 'updated_at=gt' in u else ROWS)
        return await J([])
      await r.abort()
    await pg.route('**/*', route)
    await pg.goto('http://localhost:8765/index.html#dash'); await pg.wait_for_timeout(1500)
    print('메뉴:', await pg.evaluate("[...document.querySelectorAll('#menu > .mi')].map(b=>b.textContent.trim()).join(' / ')"))
    print('테이블 현황 메뉴 없음:', '테이블 현황' not in await pg.inner_text('#menu'))
    k=await pg.evaluate("[...document.querySelectorAll('.kpi')].map(k=>k.querySelector('.k').textContent+'='+k.querySelector('.v').textContent.trim()).join(' | ')"); print('KPI:', k)
    print('오늘의 예약 행:', await pg.evaluate("[...document.querySelectorAll('.panel')[0].querySelectorAll('tbody tr')].map(r=>r.innerText.replace(/\\s+/g,' ').slice(0,60)).join(' || ')"))
    print('곧 들어올 예약(12:30~15:00):', await pg.evaluate("[...document.querySelectorAll('.panel')[2].querySelectorAll('tbody tr')].length"), '건 | 기준시각', await pg.evaluate("document.querySelector('#soonSel').selectedOptions[0].textContent"))
    print('출근 직원 수:', await pg.evaluate("document.querySelectorAll('.st').length"), '| 예:', await pg.evaluate("[...document.querySelectorAll('.st')].slice(0,3).map(s=>s.innerText.replace(/\\s+/g,' ')).join(' / ')"))
    await pg.screenshot(path='sh1.png')
    # 숨기기
    w=lambda: pg.evaluate("Math.round(document.getElementById('main').getBoundingClientRect().left)")
    print('펼친 상태 본문 시작 x:', await w())
    await pg.click('#tog'); await pg.wait_for_timeout(400); print('숨김 → 본문 시작 x:', await w(), '| 저장:', await pg.evaluate("localStorage.getItem('ilpum-nav')"))
    await pg.reload(); await pg.wait_for_timeout(900); print('새로고침 후에도 숨김 유지:', await w()==0)
    await pg.keyboard.press('Control+b'); await pg.wait_for_timeout(400); print('Ctrl+B 로 다시 펼침:', await w()>200)
    await pg.screenshot(path='sh1b.png')
    # 근무 스케줄 연동
    await pg.click('#menu [data-g="sch"]'); await pg.wait_for_timeout(2500)
    fr=pg.frame_locator('iframe[title="sch"]'); 
    inner=await pg.evaluate("(()=>{const w=document.querySelector('iframe[title=sch]').contentWindow; return {embed:w.document.documentElement.classList.contains('embed'), view:w.eval('APP.view'), sideShown:w.getComputedStyle(w.document.querySelector('.side')).display, role:w.eval('role()')}})()")
    print('근무 스케줄 안쪽:', inner, '| 제목:', await pg.inner_text('#ttl'), '| 하위메뉴 열림:', await pg.evaluate("document.getElementById('sub-sch').classList.contains('on')"))
    await pg.click('#sub-sch [data-go="week"]'); await pg.wait_for_timeout(600); print('주간표 클릭 → 안쪽 화면:', await pg.evaluate("document.querySelector('iframe[title=sch]').contentWindow.eval('APP.view')"), '| 강조된 하위메뉴:', await pg.evaluate("document.querySelector('#sub-sch [aria-current]').textContent"))
    await pg.click('#menu [data-m="staff"]'); await pg.wait_for_timeout(600); print('직원 관리 → 안쪽 화면:', await pg.evaluate("document.querySelector('iframe[title=sch]').contentWindow.eval('APP.view')"), '| 같은 창 재사용(iframe 수):', await pg.evaluate("document.querySelectorAll('iframe[title=sch]').length"))
    # 안쪽에서 화면을 바꾸면 왼쪽 메뉴도 따라감
    await pg.click('#menu [data-g="sch"]'); await pg.wait_for_timeout(500)
    await pg.evaluate("document.querySelector('iframe[title=sch]').contentDocument.querySelector('[data-a=\"view\"][data-v=\"day\"]').click()"); await pg.wait_for_timeout(700)
    print('안쪽에서 하루로 바꿈 → 왼쪽 메뉴 강조:', await pg.evaluate("document.querySelector('#sub-sch [aria-current]').textContent"), '| 제목:', await pg.inner_text('#ttl'))
    await pg.screenshot(path='sh2.png')
    # 나머지 화면
    for id,label in [('res','예약 관리'),('pay','급여 관리')]:
      await pg.click(f'#menu [data-m="{id}"]'); await pg.wait_for_timeout(1200)
      print(label, '→ 창:', await pg.evaluate(f"(()=>{{const f=[...document.querySelectorAll('iframe')].find(x=>!x.hidden); return decodeURIComponent(f.getAttribute('src'))}})()"), '| 제목:', await pg.inner_text('#ttl'))
    await pg.click('#menu [data-go="ord"]'); await pg.wait_for_timeout(400); print('발주 관리 → 창:', await pg.evaluate("[...document.querySelectorAll('iframe')].find(x=>!x.hidden).getAttribute('src')"))
    # 해시 주소로 바로 열기
    await pg.goto('http://localhost:8765/index.html#rules'); await pg.wait_for_timeout(2500); print('#rules 주소로 열기 → 제목:', await pg.inner_text('#ttl'), '| 안쪽 화면:', await pg.evaluate("document.querySelector('iframe[title=sch]').contentWindow.eval('APP.view')"))
    print('errs',errs[:3]); await b.close()
asyncio.run(main())
