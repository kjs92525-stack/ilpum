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
async def main():
  ok=True
  def chk(n,c,x=''):
    nonlocal ok; ok&=bool(c); print('OK  ' if c else 'FAIL',n,x)
  async with async_playwright() as p:
    b=await p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
    ctx,pg,errs=await open_page(b); await unlock(pg); await pg.wait_for_timeout(1500)
    chk('월 급여 카드에 "기간 정해서 계산" 버튼', await pg.is_visible('[data-act=pgo]'))
    await pg.click('[data-act=pgo]'); await pg.wait_for_timeout(500)
    chk('눌러서 기간 카드로 이동(제목)', '기간 정해서 계산' in await pg.inner_text('#periodCard h2'))
    # 9월 말 ~ 10월 초 직접 입력
    await pg.fill('#pFrom','2026-09-28'); await pg.dispatch_event('#pFrom','change'); await pg.wait_for_timeout(300)
    await pg.fill('#pTo','2026-10-03'); await pg.dispatch_event('#pTo','change'); await pg.wait_for_timeout(2500)
    h=await pg.inner_text('#periodCard h2'); t=await pg.inner_text('#periodCard')
    chk('기간 표시(9/28~10/3, 6일)', '9/28' in h and '10/3' in h and '6일' in h, h)
    chk('두 달에 걸쳐 계산된 행이 있음', len(await rows(pg))>0 and '합계' in t, str(len(await rows(pg))))
    both=await pg.evaluate("(()=>{ const P=periodData(); return {yms:P.yms, miss:P.missing}; })()")
    chk('9월·10월 두 달을 모두 불러옴', both['yms']==['2026-09','2026-10'] and not both['miss'], str(both))
    # 이전 기간 / 다음 기간: 같은 길이(6일)만큼 이동
    await pg.click('[data-act=pset][data-v=prev]'); await pg.wait_for_timeout(1500)
    r=await pg.evaluate("[view.pf,view.pt]"); chk('이전 기간 = 9/22~9/27', r==['2026-09-22','2026-09-27'], str(r))
    await pg.click('[data-act=pset][data-v=next]'); await pg.click('[data-act=pset][data-v=next]'); await pg.wait_for_timeout(1500)
    r=await pg.evaluate("[view.pf,view.pt]"); chk('다음 기간 두 번 = 10/4~10/9', r==['2026-10-04','2026-10-09'], str(r))
    await pg.click('[data-act=pset][data-v=lastmonth]'); await pg.wait_for_timeout(1500)
    r=await pg.evaluate("[view.pf,view.pt]"); chk('지난 달 = 9/1~9/30', r==['2026-09-01','2026-09-30'], str(r))
    await pg.click('[data-act=pset][data-v=lastweek]'); await pg.wait_for_timeout(1500)
    r=await pg.evaluate("[view.pf,view.pt]"); chk('지난 주 = 9/28~10/4 (월~일, 달이 걸침)', r==['2026-09-28','2026-10-04'], str(r))
    # 달이 걸친 기간의 합 = 9월 부분 + 10월 부분
    tot=await pg.evaluate("(()=>{ const f=(a,b)=>{ view.pf=a; view.pt=b; const P=periodData(); return {sum:P.tot.sum,days:P.tot.days,h:P.tot.h}; }; return {all:f('2026-09-28','2026-10-03'),a:f('2026-09-28','2026-09-30'),b:f('2026-10-01','2026-10-03')}; })()")
    chk('걸친 기간 합계 = 9월 부분 + 10월 부분', tot['all']['sum']==tot['a']['sum']+tot['b']['sum'] and tot['all']['days']==tot['a']['days']+tot['b']['days'] and tot['all']['sum']>0, str(tot))
    chk('오류 없음', not errs, str(errs)); await ctx.close(); await b.close()
  print('전체 OK' if ok else '실패 있음')
asyncio.run(main())
