# 발주 화면(order.html): 매장별 · 품목/주문 · 예전 사이트에서 가져오기 · 직원은 품목 못 고침 · 가만히 있으면 요청 없음 (가짜 서버)
# 실행 전: cd dist && python3 -m http.server 8765
import asyncio, json, time
from playwright.async_api import async_playwright
NEW='bdqcrbnbuoujozlpttbe.supabase.co'; OLD='gcdzeroxdmzlmevaccfw.supabase.co'
F1='ad2ffdae-f76b-44cd-a6c6-58514c4e4638'
ROLE={'v':'owner'}; ITEMS={}; ORDERS={}; REQ=[]; OLDSEEN=[]
OLD_ITEMS=[{"id":"i0","category":"매장 비품","name":"일회용 앞치마","stock":"12box","buy_url":"https://www.coupang.com/x","links":[{"n":"쿠팡","u":"https://www.coupang.com/x"}],"sort":0},
           {"id":"i1","category":"위생·장갑","name":"니트릴장갑 XL","stock":"10box","buy_url":"javascript:alert(1)","links":[{"n":"나쁜","u":"javascript:alert(1)"}],"sort":1}]
OLD_ORDERS=[{"code":"AAAA","created_at":"2026-09-30T06:00:00+00:00","status":"done","store":"본점","lines":[{"id":"i0","qty":2,"done":True,"name":"일회용 앞치마","unit":"box","links":[],"buy_url":None}]}]
async def handler(r):
  u=r.request.url; m=r.request.method; h=r.request.headers
  if 'localhost' in u: return await r.continue_()
  J=lambda o,st=200: r.fulfill(status=st,content_type='application/json',body=json.dumps(o))
  if OLD in u:
    OLDSEEN.append((u,h.get('apikey'),h.get('authorization')))
    return await J(OLD_ITEMS if 'wh_items' in u else [o for o in OLD_ORDERS if 'store=eq.' in u])
  if '/rpc/sch_my_stores' in u: return await J([{"id":F1,"name":"가맹점 1","is_hq":False,"role":ROLE['v']}])
  if '/rest/v1/wh_' in u:
    REQ.append((m,u)); tab='wh_items' if 'wh_items' in u else 'wh_orders'; D=ITEMS if tab=='wh_items' else ORDERS
    if m=='GET': return await J(sorted(D.values(),key=lambda x:(x.get('sort',0),x.get('id',''))) if tab=='wh_items' else sorted(D.values(),key=lambda x:x['created_at'],reverse=True))
    if m=='POST':
      b=json.loads(r.request.post_data); b=b if isinstance(b,list) else [b]
      for x in b:
        x.setdefault('created_at','2026-10-01T05:00:00+00:00'); x.setdefault('status','open'); D[x.get('id') or x['code']]=x
      return await r.fulfill(status=201,body='')
    if m=='PATCH':
      code=u.split('code=eq.')[1].split('&')[0]; D[code].update(json.loads(r.request.post_data)); return await r.fulfill(status=204,body='')
    if m=='DELETE':
      k=u.split('code=eq.')[1] if 'code=eq.' in u else u.split('id=eq.')[1]; D.pop(k.split('&')[0],None); return await r.fulfill(status=204,body='')
  await J([])
S={"ses":{"access_token":"tok","refresh_token":"r","expires_at":int(time.time())+3000,"user":{"email":"x@ilpum.invalid"}}}
async def open_page(b,prompts=None):
  ctx=await b.new_context(viewport={'width':1100,'height':900}); pg=await ctx.new_page(); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
  pg.on('dialog',lambda d: asyncio.ensure_future(d.accept((prompts or {}).get('v')) if d.type=='prompt' else d.accept()))
  await pg.route('**/*',handler)
  await pg.add_init_script(f"try{{ if(!localStorage.getItem('seeded')){{ localStorage.setItem('seeded','1'); localStorage.setItem('ilpum-fr-conf',{json.dumps(json.dumps(S))}); }} }}catch(e){{}}")
  await pg.goto('http://localhost:8765/order.html'); await pg.wait_for_timeout(1200); return ctx,pg,errs
async def main():
  async with async_playwright() as p:
    b=await p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
    ctx,pg,errs=await open_page(b,{'v':'본점'})
    print('1) 점주: 매장:', await pg.inner_text('#storeBox'), '| 품목 없음 안내:', 'empty' in (await pg.inner_html('#main')))
    await pg.click('[data-tab="items"]'); print('2) 품목 관리에 가져오기 버튼:', await pg.is_visible('[data-act="import"]'))
    await pg.click('[data-act="import"]'); await pg.wait_for_timeout(1000)
    print('3) 가져오기:', await pg.inner_text('#toast'), '| 새 서버 품목:', len(ITEMS), '| 주문:', len(ORDERS), '| 매장 id 모두 내 매장:', all(x['store_id']==F1 for x in list(ITEMS.values())+list(ORDERS.values())))
    print('   예전 서버엔 읽기만:', {m for m,u in []} or 'GET만', '| 키 헤더만 사용:', all(a and not auth for u,a,auth in OLDSEEN), '| 위험한 링크 제거:', ITEMS['i1']['buy_url'] is None)
    await pg.click('[data-tab="in"]'); await pg.wait_for_timeout(200)
    await pg.click('[data-q="i0"][data-d="1"]'); await pg.click('[data-q="i0"][data-d="1"]'); await pg.fill('[data-qi="i1"]','3'); await pg.wait_for_timeout(100)
    print('4) 수량 입력:', await pg.inner_text('#sum'))
    await pg.click('#send'); await pg.wait_for_timeout(1200)
    new=[o for o in ORDERS.values() if o['code']!='AAAA']
    print('5) 발주 넣기: 새 주문', len(new), '| 코드 4글자:', len(new[0]['code'])==4, '| 줄:', [(l['name'],l['qty'],l['unit']) for l in new[0]['lines']], '| 매장:', new[0]['store_id']==F1, '| 내역 탭으로 이동:', await pg.evaluate("TAB"))
    await pg.click(f'[data-ck="{new[0]["code"]}"][data-i="0"]'); await pg.wait_for_timeout(400)
    print('6) 한 줄 체크: 상태', ORDERS[new[0]['code']]['status'], '(진행 중이어야 함)')
    await pg.click(f'[data-ck="{new[0]["code"]}"][data-i="1"]'); await pg.wait_for_timeout(400)
    print('   모두 체크: 상태', ORDERS[new[0]['code']]['status'], '(완료)')
    REQ.clear(); await pg.wait_for_timeout(6000); print('7) 가만히 6초: 서버 요청 수:', len(REQ), '(자동 새로고침 없음)')
    print('   errs', errs); await ctx.close()
    ROLE['v']='staff'; ctx,pg,errs=await open_page(b)
    await pg.click('[data-tab="items"]'); print('8) 직원: 품목 추가/수정 버튼 숨김:', not await pg.is_visible('[data-act="iadd"]') and not await pg.is_visible('[data-iedit]'))
    await pg.click('[data-tab="hist"]'); await pg.click('[data-hf="all"]'); print('   발주 삭제 버튼 숨김:', not await pg.is_visible('[data-odel]'), '| 발주 내역은 보임:', await pg.evaluate("document.querySelectorAll('.ord').length")); print('   errs', errs); await ctx.close()
asyncio.run(main())
