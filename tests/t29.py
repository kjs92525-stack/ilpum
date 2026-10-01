# 공지사항·게시판(점주↔본사 1:1) + 메뉴 순서 + 빨간 숫자 (가짜 서버)
# 실행 전: cd dist && python3 -m http.server 8765
import asyncio, json, time
from playwright.async_api import async_playwright
NEW='bdqcrbnbuoujozlpttbe.supabase.co'; BON='0134d989-757a-4b60-9cb3-93245de2cac8'; YU='ad2ffdae-f76b-44cd-a6c6-58514c4e4638'; AB='aaaaaaaa-0000-0000-0000-000000000002'
NOTICES=[{"id":"n1","title":"추석 연휴 안내","body":"10/5 휴무","pinned":False,"created_at":"2026-09-30T01:00:00+00:00"}]
MSGS=[{"id":"m1","store_id":YU,"from_hq":False,"hq_read":False,"store_read":False,"body":"유천점 문의입니다","created_at":"2026-10-01T01:00:00+00:00","author_id":"u"},
      {"id":"m2","store_id":AB,"from_hq":False,"hq_read":False,"store_read":False,"body":"다른점 비밀 글","created_at":"2026-10-01T02:00:00+00:00","author_id":"u2"}]
ROLE={'v':'hq'}; CALLS=[]; WRITES=[]
STORES={'hq':[{"id":BON,"name":"일품집 본점","is_hq":True,"role":"hq","can_pay":True},{"id":YU,"name":"유천점","is_hq":False,"role":"hq","can_pay":False},{"id":AB,"name":"다른점","is_hq":False,"role":"hq","can_pay":False}],
        'owner':[{"id":YU,"name":"유천점","is_hq":False,"role":"owner","can_pay":True}],
        'staff':[{"id":YU,"name":"유천점","is_hq":False,"role":"staff","can_pay":False}]}
async def handler(r):
  u=r.request.url; m=r.request.method
  if 'localhost' in u: return await r.continue_()
  if NEW not in u: return await r.fulfill(status=404,body='{}')
  J=lambda o,st=200: r.fulfill(status=st,content_type='application/json',body=json.dumps(o))
  if '/rpc/sch_my_stores' in u: return await J(STORES[ROLE['v']])
  if '/rpc/board_mark_read' in u:
    sid=json.loads(r.request.post_data)['p_store']; CALLS.append(('mark',ROLE['v'],sid))
    for x in MSGS:
      if x['store_id']==sid:
        if ROLE['v']=='hq' and not x['from_hq']: x['hq_read']=True
        if ROLE['v']!='hq' and x['from_hq']: x['store_read']=True
    return await J(None)
  if '/rest/v1/board_notices' in u:
    if m=='GET': return await J(NOTICES)
    if m=='POST': b=json.loads(r.request.post_data); WRITES.append(('notice',b)); NOTICES.insert(0,{"id":"n"+str(len(NOTICES)+1),"pinned":False,"created_at":"2026-10-01T05:00:00+00:00",**b}); return await r.fulfill(status=201,body='')
  if '/rest/v1/board_msgs' in u:
    allowed={'hq':{BON,YU,AB},'owner':{YU},'staff':set()}[ROLE['v']]
    if m=='POST':
      b=json.loads(r.request.post_data); WRITES.append(('msg',b)); MSGS.append({"id":"m"+str(len(MSGS)+1),"hq_read":False,"store_read":False,"created_at":"2026-10-01T06:00:00+00:00","author_id":"me",**b}); return await r.fulfill(status=201,body='')
    rows=[x for x in MSGS if x['store_id'] in allowed]
    if 'store_id=eq.' in u: sid=u.split('store_id=eq.')[1].split('&')[0]; rows=[x for x in rows if x['store_id']==sid]
    if 'from_hq=eq.false' in u: rows=[x for x in rows if not x['from_hq']]
    if 'from_hq=eq.true' in u: rows=[x for x in rows if x['from_hq']]
    if 'hq_read=eq.false' in u: rows=[x for x in rows if not x['hq_read']]
    if 'store_read=eq.false' in u: rows=[x for x in rows if not x['store_read']]
    rows=sorted(rows,key=lambda x:x['created_at'],reverse='order=created_at.desc' in u)
    return await J(rows)
  if '/rest/v1/' in u: return await J([])
  await J([])
S={"ses":{"access_token":"tok","refresh_token":"r","expires_at":int(time.time())+3000,"user":{"email":"x@ilpum.invalid"}}}
async def open_page(b,url,seed=True):
  ctx=await b.new_context(viewport={'width':1300,'height':900}); pg=await ctx.new_page(); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
  pg.on('dialog',lambda d: asyncio.ensure_future(d.accept()))
  await pg.route('**/*',handler); await pg.route_web_socket(f'wss://{NEW}/**',lambda ws: asyncio.ensure_future(ws.close()))
  await pg.add_init_script(f"try{{ if(!localStorage.getItem('s')){{ localStorage.setItem('s','1'); localStorage.setItem('ilpum-fr-conf',{json.dumps(json.dumps(S))}); }} }}catch(e){{}}")
  await pg.goto('http://localhost:8765/'+url); await pg.wait_for_timeout(1500); return ctx,pg,errs
MENU_JS="[...document.querySelectorAll('#menu > .mi')].filter(b=>!b.hidden).map(b=>b.querySelector('span').textContent.trim())"
async def main():
  async with async_playwright() as p:
    b=await p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
    ctx,pg,errs=await open_page(b,'index.html#dash')
    print('1) 본사 메뉴 순서:', await pg.evaluate(MENU_JS))
    print('   게시판 빨간 숫자(점주 글 안 읽음):', await pg.evaluate("(document.querySelector('#menu [data-m=board] .bdg')||{}).textContent"), '| errs', errs); await ctx.close()
    ctx,pg,errs=await open_page(b,'notice.html')
    print('2) 본사 공지: 글쓰기 버튼', await pg.is_visible('[data-act=new]'), '| 목록:', await pg.evaluate("[...document.querySelectorAll('.nt h3')].map(h=>h.innerText)"))
    await pg.click('[data-act=new]'); await pg.fill('#nTitle','새 공지'); await pg.fill('#nBody','내용입니다'); await pg.check('#nPin'); await pg.click('#dOk'); await pg.wait_for_timeout(600)
    print('   공지 저장:', [w for w in WRITES if w[0]=='notice'], '| 목록 맨 위:', await pg.evaluate("document.querySelector('.nt h3').innerText"), '| errs', errs); await ctx.close()
    ROLE['v']='owner'
    ctx,pg,errs=await open_page(b,'notice.html')
    print('3) 점주 공지: 글쓰기 버튼 없음', not await pg.is_visible('[data-act=new]'), '| 수정/삭제 버튼 없음', await pg.evaluate("document.querySelectorAll('[data-edit],[data-del]').length")==0, '| 새 글 표시:', await pg.evaluate("document.querySelectorAll('.newb').length"), '| errs', errs); await ctx.close()
    ctx,pg,errs=await open_page(b,'index.html#dash')
    print('4) 점주 메뉴 순서:', await pg.evaluate(MENU_JS))
    print('   공지 빨간 숫자(안 본 공지):', await pg.evaluate("(document.querySelector('#menu [data-m=notice] .bdg')||{}).textContent"), '| errs', errs); await ctx.close()
    ctx,pg,errs=await open_page(b,'board.html')
    th=await pg.evaluate("[...document.querySelectorAll('.msg')].map(m=>m.innerText.replace(/\\s+/g,' '))")
    print('5) 점주 게시판: 내 글만 보임', th, '| 다른 점 글 안 보임:', not any('비밀' in t for t in th), '| 안내:', await pg.inner_text('.privacy'))
    await pg.fill('#body','야간 영업 문의'); await pg.click('#send'); await pg.wait_for_timeout(600)
    w=[x for x in WRITES if x[0]=='msg'][-1][1]; print('   보낸 글:', w, '| 화면에 추가:', await pg.evaluate("document.querySelectorAll('.msg').length"), '| errs', errs); await ctx.close()
    ROLE['v']='staff'
    ctx,pg,errs=await open_page(b,'index.html#dash'); print('6) 직원 계정 메뉴에 게시판:', '게시판' in await pg.evaluate(MENU_JS), '| errs', errs); await ctx.close()
    ROLE['v']='hq'
    ctx,pg,errs=await open_page(b,'board.html')
    print('7) 본사 게시판: 매장 목록', await pg.evaluate("[...document.querySelectorAll('.stbtn')].map(b=>b.innerText.replace(/\\s+/g,' '))"))
    await pg.click('[data-st=\"%s\"]'%YU); await pg.wait_for_timeout(700)
    print('   유천점 대화:', await pg.evaluate("[...document.querySelectorAll('.msg')].map(m=>m.innerText.replace(/\\s+/g,' '))"), '| 읽음 처리 호출:', CALLS[-1])
    await pg.fill('#body','본사 답글입니다'); await pg.click('#send'); await pg.wait_for_timeout(600)
    print('   답글 전송:', [x for x in WRITES if x[0]=='msg'][-1][1], '| errs', errs); await ctx.close()
    ROLE['v']='owner'
    ctx,pg,errs=await open_page(b,'index.html#dash'); print('8) 점주 메뉴: 게시판 빨간 숫자(본사 답글):', await pg.evaluate("(document.querySelector('#menu [data-m=board] .bdg')||{}).textContent"), '| errs', errs); await ctx.close()
asyncio.run(main())
