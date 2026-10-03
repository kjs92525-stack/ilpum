# (t25 복사) 급여 계산기: 새 서버에서 불러오기 / 메모 6.5 = 그 날 일급만 / 일급 없는 사람 = 시급×시간 주급 / 기간별 계산 / 일급 = 일한 날 수 (가짜 서버)
# 실행 전: cd dist && python3 -m http.server 8765
import asyncio, json, time, urllib.parse
from playwright.async_api import async_playwright
NEW='bdqcrbnbuoujozlpttbe.supabase.co'; BON='0134d989-757a-4b60-9cb3-93245de2cac8'
def st(i,name,off=(0,6)): return {"kind":"staff","id":i,"data":{"id":i,"name":name,"pos":"홀","type":"regular","off":list(off),"active":True,"order":1}}
ITEMS=[{"kind":"cfg","id":"store","data":{"name":"일품집 본점","open":"11:00","close":"22:00","fullH":10,"pmH":5}},
  {"kind":"cfg","id":"positions","data":[{"name":"홀","color":"#2F6B3F","req":[0]*7}]},
  st('sA','시급맨'),st('sB','일급맨'),st('sC','메모시급'),st('sD','메모일급'),st('sE','추가금'),
  {"kind":"pay","id":"staff:sA","data":{"k":"hour","v":12000}},{"kind":"pay","id":"staff:sB","data":{"k":"day","v":130000}},
  {"kind":"pay","id":"staff:sC","data":{"k":"hour","v":12000}},{"kind":"pay","id":"staff:sD","data":{"k":"day","v":130000}},
  {"kind":"pay","id":"staff:sE","data":{"k":"hour","v":12000}},{"kind":"pay","id":"dc:2026-10-06|sE","data":{"k":"bonus","v":20000}},
  st('sF','현금맨'),{"kind":"pay","id":"staff:sF","data":{"k":"hour","v":12000}},{"kind":"pay","id":"dc:2026-10-07|sF","data":{"k":"day","v":100000,"cash":True}},
  {"kind":"spot","id":"p1","data":{"id":"p1","date":"2026-10-07","name":"당일메모","pos":"홀","memo":"6.5"}},
  {"kind":"spot","id":"p2","data":{"id":"p2","date":"2026-10-07","name":"당일무메모","pos":"홀","memo":""}},
  {"kind":"dc","id":"2026-10-07|sC","data":{"memo":"6.5"}},{"kind":"dc","id":"2026-10-08|sD","data":{"memo":"6.5"}}]
REQ=[]; CANPAY={'v':True}; PIN={'v':None,'fails':0,'locked':False}
async def handler(r):
  u=r.request.url; m=r.request.method
  if 'localhost' in u: return await r.continue_()
  if NEW not in u: return await r.fulfill(status=404,body='{}')
  J=lambda o,sv=200: r.fulfill(status=sv,content_type='application/json',body=json.dumps(o))
  if '/rpc/pay_pin_status' in u: return await J({"has":PIN['v'] is not None,"locked":600 if PIN['locked'] else 0})
  if '/rpc/pay_pin_set' in u:
    b=json.loads(r.request.post_data)
    if len(b['p_new'].strip())<4: return await J('short')
    if PIN['v'] is not None and b.get('p_old')!=PIN['v']: return await J('bad_old')
    PIN['v']=b['p_new']; return await J('ok')
  if '/rpc/pay_pin_check' in u:
    b=json.loads(r.request.post_data)
    if PIN['locked']: return await J('locked')
    if b['p_pin']==PIN['v']: PIN['fails']=0; return await J('ok')
    PIN['fails']+=1
    if PIN['fails']>=5: PIN['locked']=True
    return await J('bad')
  if '/rpc/sch_my_stores' in u: return await J([{"id":BON,"name":"일품집 본점","is_hq":True,"role":"hq","can_pay":CANPAY['v']}])
  if '/rest/v1/sch_items' in u:
    REQ.append(u); rows=[x for x in ITEMS if CANPAY['v'] or x['kind']!='pay']
    return await J([{**x,"deleted":False} for x in rows])
  await J([])
S={"ses":{"access_token":"tok","refresh_token":"r","expires_at":int(time.time())+10**8,"user":{"email":"x@ilpum.invalid"}}}
FIX="""(()=>{const _D=Date;const fixed=new _D('2026-10-07T10:00:00+09:00').getTime();class FD extends _D{constructor(...a){if(a.length===0)super(fixed);else super(...a);}static now(){return fixed;}}window.Date=FD;})();"""
async def open_page(b):
  ctx=await b.new_context(viewport={'width':1300,'height':900}); pg=await ctx.new_page(); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
  await pg.route('**/*',handler); REQ.clear()
  await pg.add_init_script(FIX); await pg.add_init_script(f"try{{ localStorage.setItem('ilpum-fr-conf',{json.dumps(json.dumps(S))}); }}catch(e){{}}")
  await pg.goto('http://localhost:8765/pay.html'); await pg.wait_for_timeout(2000); return ctx,pg,errs
async def unlock(pg,pin='abcd1234'):
  if PIN['v'] is None:
    ins=pg.locator('.pinin'); await ins.nth(0).fill(pin); await ins.nth(1).fill(pin)
  else: await pg.locator('.pinin').nth(0).fill(pin)
  await pg.locator('#pinForm button[type=submit]').click(); await pg.wait_for_timeout(1800)
async def rows(pg):
  return await pg.evaluate("[...document.querySelectorAll('#periodCard tbody tr')].map(tr=>{const c=[...tr.children].map(x=>x.innerText.replace(/\\s+/g,' ').trim());return c.join(' | ')})")

def sp(i,name,memo,pay=None):
  ITEMS.append({"kind":"spot","id":i,"data":{"id":i,"date":"2026-10-07","name":name,"pos":"주방","memo":memo}})
  if pay: ITEMS.append({"kind":"pay","id":"spot:"+i,"data":{"k":"day","v":pay}})
sp('k1','주방일치','7',70000); sp('k2','주방다름','7',65000); sp('k3','주방일당백','일당백7',65000); sp('k4','주방금액만','',130000); sp('k5','주방열셋','13',130000); sp('k6','주방메모만','8')
async def main():
  ok=True
  def chk(n,c,x=''):
    nonlocal ok; ok&=bool(c); print('OK  ' if c else 'FAIL',n,x)
  async with async_playwright() as p:
    b=await p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
    ctx,pg,errs=await open_page(b); await unlock(pg); await pg.wait_for_timeout(1500)
    await pg.click('#dailyBtn'); await pg.wait_for_timeout(800)
    rows=await pg.evaluate("dailyPayoutRows(view.daily).map(r=>({n:r.name,a:r.amount,t:r.tag,w:!!r.warn}))")
    d={r['n']:r for r in rows}
    # 금액 직접 수정 → 원래대로
    await pg.fill('[data-cashamt="주방다름"]','70000'); await pg.dispatch_event('[data-cashamt="주방다름"]','change'); await pg.wait_for_timeout(400)
    r=await pg.evaluate("dailyPayoutRows(view.daily).find(r=>r.name==='주방다름')")
    chk('금액을 7만으로 고침(주황 확인 사라지고 직접 수정 표시)', r['amount']==70000 and r['tag']=='직접 수정' and not r['warn'], str(r))
    chk('합계에 반영', '70,000' in await pg.inner_text('.daily-card'))
    await pg.click('[data-cashamtreset="주방다름"]'); await pg.wait_for_timeout(400)
    r=await pg.evaluate("dailyPayoutRows(view.daily).find(r=>r.name==='주방다름')")
    chk('원래대로 누르면 6.5만 + 확인 표시 복귀', r['amount']==65000 and r['warn'], str(r))
    chk('오류 없음', not errs, str(errs)); await ctx.close(); await b.close()
  print('전체 OK' if ok else '실패 있음')

asyncio.run(main())
