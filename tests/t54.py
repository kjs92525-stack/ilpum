# (t25 복사) 급여 계산기: 새 서버에서 불러오기 / 메모 6.5 = 그 날 일급만 / 일급 없는 사람 = 시급×시간 주급 / 기간별 계산 / 일급 = 일한 날 수 (가짜 서버)
# 실행 전: cd dist && python3 -m http.server 8765
import asyncio, json, time, urllib.parse, sys
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
async def main():
  ok=True
  def chk(n,c,x=''):
    nonlocal ok; ok&=bool(c); print('OK  ' if c else 'FAIL',n,x)
  async with async_playwright() as p:
    b=await p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
    ctx,pg,errs=await open_page(b); await unlock(pg); await pg.wait_for_timeout(1500)
    # 1) 기간 카드는 위 표에서 체크한 사람만
    names=await pg.evaluate("Object.keys(pay.months[pay.cur].people)")
    sel=await pg.evaluate("Object.keys(pay.months[pay.cur].people).filter(isSel)")
    uns=[n for n in names if n not in sel]
    chk('체크 안 된 사람이 있음(테스트 전제)', len(uns)>0 and len(sel)>0, f'체크 {sel} / 안 한 {uns}')
    await pg.evaluate("view.pf='2026-09-28'; view.pt='2026-10-10'; render()"); await pg.wait_for_timeout(400)
    inperiod=await pg.evaluate("periodData().rows.map(r=>r.n)")
    chk('기간 카드에는 체크한 사람만', set(inperiod)<=set(sel) and not (set(inperiod)&set(uns)), str(inperiod))
    # 다른 달에만 금액이 있는 사람이 체크 없이 끼어들지 않음 (예전 isSelAny 동작)
    await pg.evaluate("pay.sel={}; Object.keys(pay.months[pay.cur].people).forEach(n=>pay.sel[n]=false); save(); render()"); await pg.wait_for_timeout(300)
    chk('아무도 체크 안 하면 기간 카드에 안내', '체크' in await pg.inner_text('#periodCard') and await pg.evaluate("periodData().rows.length")==0)
    # 2) 사람 이름을 눌러 들어간 화면에서 기간 설정
    await pg.evaluate("pay.sel={}; save(); render()"); await pg.wait_for_timeout(300)
    who=sel[0]
    await pg.click(f'button.name[data-person="{who}"]'); await pg.wait_for_timeout(800)
    chk('개인 화면에 기간 카드', await pg.is_visible('#periodCard') and who in await pg.inner_text('#periodCard h3'))
    await pg.fill('#pFrom','2026-09-28'); await pg.dispatch_event('#pFrom','change'); await pg.wait_for_timeout(300)
    await pg.fill('#pTo','2026-10-03'); await pg.dispatch_event('#pTo','change'); await pg.wait_for_timeout(2500)
    if len(sys.argv)>1: await pg.screenshot(path='/tmp/person_period.png')
    t=await pg.inner_text('#periodCard'); h=await pg.inner_text('#periodCard h3')
    chk('개인 기간 표시 9/28~10/3', '9/28' in h and '10/3' in h and '6일' in h, h)
    r=await pg.evaluate(f"(()=>{{ const R=personRange('{who}',view.pf,view.pt); return {{yms:R.yms,days:R.days.length,sum:R.tot.sum,miss:R.missing}}; }})()")
    chk('9월·10월 두 달에 걸쳐 날짜별로 합침', r['yms']==['2026-09','2026-10'] and r['days']>0 and not r['miss'], str(r))
    parts=await pg.evaluate(f"(()=>{{ const f=(a,b)=>personRange('{who}',a,b).tot; const A=f('2026-09-28','2026-09-30'),B=f('2026-10-01','2026-10-03'),T=f('2026-09-28','2026-10-03'); return {{ok:T.sum===A.sum+B.sum&&T.days===A.days+B.days&&T.h===A.h+B.h,T}}; }})()")
    chk('개인 합계 = 9월 부분 + 10월 부분', parts['ok'] and parts['T']['sum']>0, str(parts))
    # 전체 목록의 기간 카드와 같은 숫자인지 (체크한 사람 기준)
    await pg.evaluate(f"pay.sel={{'{who}':true}}; save()"); 
    same=await pg.evaluate(f"(()=>{{ const P=periodData(); const row=P.rows.find(r=>r.n==='{who}'); const R=personRange('{who}',view.pf,view.pt); return row&&row.sum===R.tot.sum&&row.days===R.tot.days; }})()")
    chk('전체 기간 카드와 개인 기간 계산이 같은 값', same)
    await pg.click('[data-act=pcopy]'); await pg.wait_for_timeout(300)
    chk('텍스트 복사 내용(개인)', who in await pg.evaluate(f"personPeriodText('{who}')"))
    chk('오류 없음', not errs, str(errs)); await ctx.close(); await b.close()
  print('전체 OK' if ok else '실패 있음')
asyncio.run(main())
