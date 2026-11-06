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

def sp2(i,name,memo='',sh=None,pay=None):
  d={"id":i,"date":"2026-10-07","name":name,"pos":"주방","memo":memo}
  if sh: d["sh"]=sh
  ITEMS.append({"kind":"spot","id":i,"data":d})
  if pay: ITEMS.append({"kind":"pay","id":"spot:"+i,"data":pay})
sp2('e1','오전알바','',{"k":"am"}); sp2('e2','오후알바','',{"k":"pm"}); sp2('e3','시간알바','',{"k":"t","s":"14:00","e":"20:00"}); sp2('e4','오전메모','11',{"k":"am"})
async def main():
  ok=True
  def chk(n,c,x=''):
    nonlocal ok; ok&=bool(c); print('OK  ' if c else 'FAIL',n,x)
  async with async_playwright() as p:
    b=await p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
    ctx,pg,errs=await open_page(b); await unlock(pg); await pg.wait_for_timeout(1500)
    await pg.evaluate("['오전알바','오후알바','시간알바','오전메모'].forEach(n=>pay.rates[n]=12000)")
    r=await pg.evaluate("Object.fromEntries(['오전알바','오후알바','시간알바','오전메모'].map(n=>{const d=pay.months[pay.cur].people[n].days['2026-10-07'];const c=dayCalc(n,d);return [n,{h:c.hours,a:c.amount,t:c.type}]}))")
    chk('오전 = 5시간 × 시급', r['오전알바']['h']==5 and r['오전알바']['a']==60000 and r['오전알바']['t']=='am', str(r['오전알바']))
    chk('오후 = 5시간', r['오후알바']['h']==5 and r['오후알바']['a']==60000, str(r['오후알바']))
    chk('시간 지정 14~20 = 6시간', r['시간알바']['h']==6 and r['시간알바']['a']==72000, str(r['시간알바']))
    chk('메모 11 = 하루 11만 (시급 더하지 않음)', r['오전메모']['a']==110000, str(r['오전메모']))
    # 사람 직접 고친 시급이 있어도 메모가 하루 전체
    r2=await pg.evaluate("(()=>{const d={...pay.months[pay.cur].people['오전메모'].days['2026-10-07'],rate:15000};return dayCalc('오전메모',d).amount})()")
    chk('시급 직접 입력해도 메모 11 이면 11만', r2==110000, str(r2))
    await pg.click('#dailyBtn'); await pg.wait_for_timeout(600)
    async def val(i): return await pg.input_value('#'+i)
    await pg.fill('#xName','새사람'); await pg.fill('#xRate','12000'); await pg.select_option('#xShift','pm'); await pg.dispatch_event('#xShift','change'); await pg.wait_for_timeout(200)
    chk('사람 추가: 오후 → 5시간×12,000 = 60,000', await val('xPer')=='60,000', await val('xPer'))
    await pg.select_option('#xShift','am'); await pg.dispatch_event('#xShift','change'); chk('오전 → 60,000', await val('xPer')=='60,000')
    await pg.select_option('#xShift','t'); await pg.fill('#xT1','2'); await pg.fill('#xT2','8'); await pg.dispatch_event('#xT2','change'); await pg.wait_for_timeout(200)
    chk('시간 지정 2~8시 = 6시간 → 72,000', await val('xPer')=='72,000', await val('xPer'))
    await pg.fill('#xMemo','11'); await pg.dispatch_event('#xMemo','change'); await pg.wait_for_timeout(200)
    chk('비고 11 → 하루 110,000 (시급 더하지 않음)', await val('xPer')=='110,000', await val('xPer'))
    await pg.fill('#xDays','3'); await pg.dispatch_event('#xDays','change'); await pg.wait_for_timeout(200)
    chk('3일치 합계 330,000', await val('xTotal')=='330,000', await val('xTotal'))
    chk('오류 없음', not errs, str(errs)); await ctx.close(); await b.close()
  print('전체 OK' if ok else '실패 있음')
asyncio.run(main())
