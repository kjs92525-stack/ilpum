# 보건증 발급일·만료일(직원 편집·목록, 만료 30일 전부터 경고) + 통합 틀 오른쪽 위 종 알림(보건증·발주·공지·게시판) (가짜 서버 + 체험 모드)
import asyncio, json, time, datetime
from playwright.async_api import async_playwright
NEW='bdqcrbnbuoujozlpttbe.supabase.co'; BON='0134d989-757a-4b60-9cb3-93245de2cac8'; F1='ad2ffdae-f76b-44cd-a6c6-58514c4e4638'
T=datetime.date.today(); D=lambda n:(T+datetime.timedelta(days=n)).isoformat()
ROLE={'v':'hq'}
STAFF=[(BON,'s1',{"name":"김만료","pos":"홀","hcExp":D(-3)}),(BON,'s2',{"name":"이임박","pos":"홀","hcIss":(datetime.date(T.year-1,T.month,T.day)+datetime.timedelta(days=10)).isoformat()}),
       (F1,'s3',{"name":"박여유","pos":"홀","hcExp":D(200)}),(F1,'s4',{"name":"최그만","pos":"홀","hcExp":D(-10),"active":False}),(F1,'s5',{"name":"정유천","pos":"주방","hcExp":D(20)})]
def stores():
  if ROLE['v']=='hq': return [{"id":BON,"name":"일품집 본점","is_hq":True,"role":"hq","can_pay":True},{"id":F1,"name":"유천점","is_hq":False,"role":"hq","can_pay":False}]
  return [{"id":F1,"name":"유천점","is_hq":False,"role":ROLE['v'],"can_pay":True}]
async def handler(r):
  u=r.request.url
  if 'localhost' in u: return await r.continue_()
  if NEW not in u: return await r.fulfill(status=404,body='{}')
  J=lambda o,st=200: r.fulfill(status=st,content_type='application/json',body=json.dumps(o))
  if '/rpc/sch_my_stores' in u: return await J(stores())
  if '/rest/v1/sch_items' in u and 'kind=eq.staff' in u:
    ids=u.split('store_id=in.(')[1].split(')')[0].split(',')
    return await J([{"store_id":s,"id":i,"data":d} for s,i,d in STAFF if s in ids])
  if '/rest/v1/wh_orders' in u: return await J([{"store_id":F1,"code":"AB12","created_at":"2026-10-06T01:00:00+00:00"}])
  if '/rest/v1/board_msgs' in u: return await J([{"id":1},{"id":2}])
  await J([])
S={"ses":{"access_token":"tok","refresh_token":"r","expires_at":int(time.time())+3000,"user":{"email":"x@ilpum.invalid"}},"mode":"remote","url":"https://"+NEW,"key":"k"}
async def main():
  ok=True
  def chk(n,c,x=''):
    nonlocal ok; ok&=bool(c); print('OK  ' if c else 'FAIL',n,x)
  async with async_playwright() as p:
    b=await p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
    # 1) 근무표(체험): 직원 편집 창에 보건증 칸, 목록·경고
    pg=await b.new_page(viewport={'width':1300,'height':900}); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
    await pg.route('**/*', lambda r: r.abort() if 'supabase' in r.request.url else r.continue_())
    await pg.goto('http://localhost:8765/ilpum-schedule.html')
    await pg.evaluate("localStorage.clear(); localStorage.setItem('ilpum-fr-conf', JSON.stringify({mode:'local'}))"); await pg.reload(); await pg.wait_for_timeout(1200)
    sid=await pg.evaluate("staffList(APP.D).find(s=>s.type==='regular').id")
    await pg.evaluate("APP.view='staff'; render()"); await pg.click(f'tr[data-sid="{sid}"]'); await pg.wait_for_timeout(300)
    chk('편집 창에 보건증 발급일·만료일 칸', await pg.is_visible('#sfHcIss') and await pg.is_visible('#sfHcExp'))
    iss=(datetime.date(T.year-1,T.month,T.day)+datetime.timedelta(days=15)).isoformat()
    await pg.fill('#sfHcIss',iss); await pg.click('[data-a="staffsave"]'); await pg.wait_for_timeout(300)
    s=await pg.evaluate(f"APP.D.staff['{sid}']")
    chk('발급일 저장, 만료일 비우면 저장 안 함', s.get('hcIss')==iss and 'hcExp' not in s, str(s))
    h=await pg.evaluate(f"hcState(APP.D.staff['{sid}'],todayStr)")
    chk('만료일 = 발급일+1년 (하루 전), 30일 이내라 soon', h['lv']=='soon' and h['days']==14, str(h))
    t=await pg.inner_text('#main')
    chk('목록 위에 보건증 확인 안내', '보건증 확인' in t and '14일 남음' in t)
    await pg.click(f'tr[data-sid="{sid}"]'); await pg.fill('#sfHcExp',D(100)); await pg.click('[data-a="staffsave"]'); await pg.wait_for_timeout(300)
    chk('만료일 직접 넣으면 그 날짜 우선, 경고 사라짐', await pg.evaluate(f"hcState(APP.D.staff['{sid}'],todayStr).lv")=='ok' and '보건증 확인' not in await pg.inner_text('#main'))
    chk('근무표 오류 없음', not errs, str(errs)); await pg.close()
    # 2) 통합 틀: 종 알림
    for role in ('hq','owner'):
      ROLE['v']=role
      ctx=await b.new_context(viewport={'width':1400,'height':900}); pg=await ctx.new_page(); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
      await pg.route('**/*',handler); await pg.route_web_socket(f'wss://{NEW}/**',lambda ws: asyncio.ensure_future(ws.close()))
      await pg.add_init_script(f"try{{ localStorage.setItem('ilpum-fr-conf',{json.dumps(json.dumps(S))}); }}catch(e){{}}")
      await pg.goto('http://localhost:8765/index.html#dash'); await pg.wait_for_timeout(2500)
      chk(f'[{role}] 종 버튼 보임', await pg.is_visible('#bell'))
      n=await pg.inner_text('#bellN')
      await pg.click('#bell'); await pg.wait_for_timeout(800)
      items=await pg.evaluate("[...document.querySelectorAll('#nList .ni b')].map(e=>e.textContent)")
      if role=='hq':
        chk('[hq] 숫자 = 알림 수(만료1·임박2·발주·게시판)', n=='5', n)
        chk('[hq] 만료·임박 순서, 그만둔 사람·여유 있는 사람 제외', items[0]=='김만료 보건증 만료됨' and any('이임박' in x for x in items) and any('정유천' in x for x in items) and not any('최그만' in x or '박여유' in x for x in items), str(items))
        chk('[hq] 발주·게시판도 함께', any('발주 1건' in x for x in items) and any('점주 글 2건' in x for x in items), str(items))
      else:
        chk('[owner] 자기 매장 보건증만', any('정유천' in x for x in items) and not any('김만료' in x or '이임박' in x for x in items), str(items))
      await pg.click('#nList .ni'); await pg.wait_for_timeout(800)
      chk(f'[{role}] 누르면 직원 관리로 가고 창 닫힘', await pg.evaluate("location.hash")=='#staff' and await pg.is_hidden('#npanel'))
      chk(f'[{role}] 오류 없음', not errs, str(errs)); await ctx.close()
    await b.close()
  print('전체 OK' if ok else '실패 있음')
asyncio.run(main())
# 입사일 · 1년 되는 날 (알림 없음)
async def join_test():
  async with async_playwright() as p:
    b=await p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome'); pg=await b.new_page(viewport={'width':1300,'height':900}); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
    await pg.route('**/*', lambda r: r.abort() if 'supabase' in r.request.url else r.continue_())
    await pg.goto('http://localhost:8765/ilpum-schedule.html')
    await pg.evaluate("localStorage.clear(); localStorage.setItem('ilpum-fr-conf', JSON.stringify({mode:'local'}))"); await pg.reload(); await pg.wait_for_timeout(1200)
    sid=await pg.evaluate("staffList(APP.D).find(s=>s.type==='regular').id")
    await pg.evaluate("APP.view='staff'; render()"); await pg.click(f'tr[data-sid="{sid}"]'); await pg.wait_for_timeout(300)
    await pg.fill('#sfJoin','2025-03-02'); await pg.dispatch_event('#sfJoin','input')
    h=await pg.inner_text('#sfJoin1'); await pg.click('[data-a="staffsave"]'); await pg.wait_for_timeout(300)
    row=await pg.inner_text(f'tr[data-sid="{sid}"]')
    r=[await pg.evaluate(f"APP.D.staff['{sid}'].join")=='2025-03-02', '2026-03-02' in h, '2025-03-02' in row and '2026-03-02' in row, await pg.evaluate("oneYear('2024-02-29')")=='2025-03-01', not errs]
    print(('OK  ' if all(r) else 'FAIL'),'입사일 저장·1년 되는 날 표시',r,h,row.replace('\n',' | ')); await b.close()
asyncio.run(join_test())
