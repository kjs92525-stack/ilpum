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
  ok=True
  def chk(n,c):
    nonlocal ok; ok&=bool(c); print(('OK  ' if c else 'FAIL'),n)
  for i,(c,n) in enumerate([('위생','장갑'),('위생','앞치마'),('주방','숯')]):
    ITEMS['t%d'%i]={'id':'t%d'%i,'category':c,'name':n,'stock':'3box','buy_url':None,'links':[],'sort':i}
  ORDERS['ZZ']={'code':'ZZ','created_at':'2026-10-01T05:00:00+00:00','status':'open','lines':[{'id':'t0','qty':2,'done':True,'name':'장갑','unit':'box','links':[]},{'id':'t2','qty':1,'done':False,'name':'숯','unit':'box','links':[]}]}
  async with async_playwright() as p:
    b=await p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
    ctx,pg,errs=await open_page(b)
    await pg.click('[data-tab="hist"]'); await pg.wait_for_timeout(300)
    chk('발주 카드에 수정 버튼', await pg.is_visible('[data-oedit="ZZ"]'))
    await pg.click('[data-oedit="ZZ"]'); await pg.wait_for_timeout(200)
    chk('수정 창에 2줄', await pg.locator('#dlgBody [data-lq]').count()==2)
    await pg.locator('[data-lq="1"]').fill('5')
    await pg.select_option('#oAdd','t1'); await pg.fill('#oQty','4'); await pg.click('#oAddBtn'); await pg.wait_for_timeout(150)
    chk('물건 더하기 → 3줄', await pg.locator('#dlgBody [data-lq]').count()==3)
    await pg.click('[data-lx="0"]'); await pg.wait_for_timeout(150); chk('줄 빼기 → 2줄', await pg.locator('#dlgBody [data-lq]').count()==2)
    await pg.click('#dOk'); await pg.wait_for_timeout(500)
    L=ORDERS['ZZ']['lines']; chk('저장됨: 숯 5, 앞치마 4, 장갑 빠짐', [(l['name'],l['qty']) for l in L]==[('숯',5),('앞치마',4)])
    chk('상태는 진행 중으로 유지', ORDERS['ZZ']['status']=='open')
    await pg.click('[data-oedit="ZZ"]'); await pg.wait_for_timeout(200)
    for _ in range(2): await pg.click('[data-lx="0"]'); await pg.wait_for_timeout(100)
    await pg.click('#dOk'); await pg.wait_for_timeout(300); chk('0줄은 저장 거절', len(ORDERS['ZZ']['lines'])==2)
    chk('오류 없음', not errs)
  print('전체','OK' if ok else 'FAIL')
asyncio.run(main())
