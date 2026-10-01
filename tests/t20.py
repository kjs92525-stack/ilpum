# 예약 화면: 현황판 배치 수정(수정 버튼을 눌러야만, 저장해야 반영) + 촘촘한 목록 (가짜 서버)
# 실행 전: cd dist && python3 -m http.server 8765
import asyncio, json, time
from playwright.async_api import async_playwright
NEW='https://bdqcrbnbuoujozlpttbe.supabase.co'; F1='ad2ffdae-f76b-44cd-a6c6-58514c4e4638'
ROLE={'v':'owner'}; LAYOUT={}; POSTS=[]; DAYS={}
async def handler(r):
  u=r.request.url; m=r.request.method; h=r.request.headers
  if 'localhost' in u: return await r.continue_()
  J=lambda o,st=200: r.fulfill(status=st,content_type='application/json',body=json.dumps(o))
  if '/rpc/sch_my_stores' in u: return await J([{"id":F1,"name":"가맹점 1","is_hq":False,"role":ROLE['v']}])
  if '/rest/v1/sch_items' in u:
    if m=='POST': b=json.loads(r.request.post_data); POSTS.append(b); LAYOUT['d']=b['data']; return await r.fulfill(status=201,body='')
    return await J([{"data":LAYOUT['d']}] if 'd' in LAYOUT else [])
  if '/rest/v1/res_days' in u:
    if m=='GET': return await J([])
    if m=='POST': b=json.loads(r.request.post_data); return await J([{"rev":b['rev']}],201)
  await J([])
S=lambda: {"ses":{"access_token":"tok","refresh_token":"r","expires_at":int(time.time())+3000,"user":{"email":"x@ilpum.invalid"}}}
async def open_page(b):
  ctx=await b.new_context(viewport={'width':1500,'height':900}); pg=await ctx.new_page(); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
  pg.on('dialog',lambda d: asyncio.ensure_future(d.accept(PROMPT.get('v')) if d.type=='prompt' else d.accept()))
  await pg.route('**/*',handler)
  await pg.add_init_script(f"try{{ if(!localStorage.getItem('seeded')){{ localStorage.setItem('seeded','1'); localStorage.setItem('ilpum-fr-conf',{json.dumps(json.dumps(S()))}); }} }}catch(e){{}}")
  await pg.goto('http://localhost:8765/reserve.html'); await pg.wait_for_timeout(1200); return ctx,pg,errs
PROMPT={'v':''}
async def main():
  async with async_playwright() as p:
    b=await p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
    ctx,pg,errs=await open_page(b)
    print('1) 점주: 배치 수정 버튼 보임:', await pg.is_visible('[data-led="start"]'), '| 수정 중 표시 없음:', not await pg.is_visible('.ledbar'))
    print('   수정 버튼 누르기 전 테이블 수:', await pg.evaluate("ALL_TABLES.length"))
    await pg.click('[data-led="start"]'); await pg.wait_for_timeout(300)
    print('2) 수정 모드 켜짐:', await pg.is_visible('.ledbar'), '| 저장 호출 아직 없음:', len(POSTS)==0)
    PROMPT['v']='60'; await pg.click('.cell.addc >> nth=0'); await pg.wait_for_timeout(200)
    print('3) 60번 추가(임시):', await pg.evaluate("tablesOf(layoutEdit.floors).includes('60')"), '| 실제 배치엔 아직 없음:', await pg.evaluate("!ALL_TABLES.includes('60')"), '| 서버 저장 없음:', len(POSTS)==0)
    PROMPT['v']='5'; await pg.click('.cell.addc >> nth=0'); await pg.wait_for_timeout(200); print('   이미 있는 번호는 거절:', await pg.inner_text('#toast'))
    a=await pg.evaluate("layoutEdit.floors[0].groups[0].cols[0].slice(0,2)"); await pg.click('.cell.ed >> nth=0'); await pg.click('.cell.ed >> nth=1'); await pg.wait_for_timeout(200)
    c=await pg.evaluate("layoutEdit.floors[0].groups[0].cols[0].slice(0,2)"); print('4) 두 칸 눌러서 자리 바꿈:', a, '→', c)
    await pg.click('.cell.ed >> nth=2 >> .x'); await pg.wait_for_timeout(200)
    print('5) 테이블 지우기(임시): 개수', await pg.evaluate("tablesOf(layoutEdit.floors).length"), '(실제', await pg.evaluate("ALL_TABLES.length"), ')')
    await pg.click('[data-led="cancel"]'); await pg.wait_for_timeout(200)
    print('6) 취소 → 원래대로:', await pg.evaluate("ALL_TABLES.length"), '| 수정 모드 꺼짐:', not await pg.is_visible('.ledbar'), '| 서버 저장 없음:', len(POSTS)==0)
    await pg.click('[data-led="start"]'); PROMPT['v']='60'; await pg.click('.cell.addc >> nth=0'); await pg.click('[data-led="save"]'); await pg.wait_for_timeout(500)
    print('7) 저장 → 서버에 1번 전송:', len(POSTS), '| 종류:', POSTS[-1]['kind'], POSTS[-1]['id'], '| 매장:', POSTS[-1]['store_id']==F1, '| 실제 배치에 60:', await pg.evaluate("ALL_TABLES.includes('60')"), '| 60번 입력 인식:', await pg.evaluate("parseTables('60')"))
    await pg.evaluate("saveItem(ui.date,{id:'a1',name:'테스트손님',time:'18:00',pp:'2',tables:['60'],req:'',u:Date.now()})"); await pg.wait_for_timeout(500)
    print('8) 목록 이름 글자 크기:', await pg.evaluate("getComputedStyle(document.querySelector('.res .nm')).fontSize"), '| 한 줄 높이:', await pg.evaluate("Math.round(document.querySelector('.res').getBoundingClientRect().height)"), 'px')
    print('   errs', errs); await ctx.close()
    ctx,pg,errs=await open_page(b)
    print('9) 새로고침 후에도 60번 있음:', await pg.evaluate("ALL_TABLES.includes('60')"), '| 현황판에 보임:', await pg.is_visible('.floor .cell[data-cell="60"]'), '| errs', errs); await ctx.close()
    ROLE['v']='staff'; ctx,pg,errs=await open_page(b); print('10) 직원 계정: 배치 수정 버튼 숨김:', not await pg.is_visible('[data-led="start"]')); await ctx.close()
asyncio.run(main())
