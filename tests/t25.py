# 급여 계산기: 새 서버에서 불러오기 / 메모 6.5 = 그 날 일급만 / 일급 없는 사람 = 시급×시간 주급 / 기간별 계산 / 일급 = 일한 날 수 (가짜 서버)
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
  async with async_playwright() as p:
    b=await p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
    ctx,pg,errs=await open_page(b)
    print('0) 처음엔 비밀번호 만들기 화면:', await pg.inner_text('#lockBox h2'), '| 근무표·금액 요청 아직 없음:', len(REQ)==0, '| 화면 비어 있음:', (await pg.inner_text('#app')).strip()=='')
    ins=pg.locator('.pinin'); await ins.nth(0).fill('12'); await ins.nth(1).fill('12'); await pg.locator('#pinForm button[type=submit]').click(); await pg.wait_for_timeout(300); print('   짧은 비번:', await pg.inner_text('#pinMsg'))
    await ins.nth(0).fill('abcd1234'); await ins.nth(1).fill('abcd9999'); await pg.locator('#pinForm button[type=submit]').click(); await pg.wait_for_timeout(300); print('   두 칸 다름:', await pg.inner_text('#pinMsg'))
    await unlock(pg)
    print('   만든 뒤 열림:', not await pg.is_visible('#lockBox'), '| 비번이 서버에 저장됨:', PIN['v'] is not None)
    print('1) 매장:', await pg.inner_text('#storeBox'), '| 자동으로 이번 달 불러옴:', await pg.evaluate("pay.cur"), '| 서버 요청:', len(REQ))
    print('   시급/일급이 근무표에서 들어옴:', await pg.evaluate("[pay.rates['시급맨'],pay.drates['일급맨'],pay.rates['메모시급'],pay.drates['메모일급']]"))
    print('2) 지급 주기 기본값:', await pg.evaluate("['시급맨','일급맨'].map(n=>n+':'+cycleOf(n))"), '(시급=주급, 일급=월급)')
    print('3) 이번 주(10/5~10/11) 기간 계산 [시급맨 600,000 / 일급맨 650,000 / 메모시급 545,000 / 메모일급 585,000 / 추가금 620,000 / 현금맨 580,000]:'); [print('   ',r) for r in await rows(pg)]
    print('   합계:', await pg.inner_text('#periodCard tfoot'))
    await pg.click('[data-act="pset"][data-v="prev"]'); await pg.wait_for_timeout(1200)
    print('4) 이전 주(9/28~10/4): 달이 달라도 자동으로 불러옴 →', await pg.evaluate("[view.pf,view.pt,Object.keys(pay.months)]")); [print('   ',r) for r in await rows(pg)]
    print('   서버 요청 합계(캐시로 한 번만 읽음):', len(REQ))
    await pg.click('[data-act="pset"][data-v="month"]'); await pg.wait_for_timeout(500); print('5) 이번 달 시급맨:', [r for r in await rows(pg) if r.startswith('시급맨')])
    await pg.click('[data-act="pset"][data-v="this"]'); await pg.wait_for_timeout(300); await pg.click('[data-act="pcopy"]'); print('6) 텍스트 복사 안내:', await pg.inner_text('#toast'))
    print('   메모일급 7일 상세:', await pg.evaluate("(()=>{const c=dayCalc('메모시급',pay.months['2026-10'].people['메모시급'].days['2026-10-07']);const d=dayCalc('메모일급',pay.months['2026-10'].people['메모일급'].days['2026-10-08']);return {시급메모날:[c.amount,c.base,c.bonus,c.memoDay],일급메모날:[d.amount,d.base,d.bonus,d.memoDay]}})()"))
    # 일당 지급: 메모에 일당이 있는 사람 / 그날 현금만
    await pg.click('#dailyBtn'); await pg.wait_for_timeout(300)
    print('7) 일당 지급 10/7:', await pg.evaluate("dailyPayoutRows(view.daily).map(r=>r.name+' '+r.amount+' ['+r.tag+']')"))
    print('   (당일무메모·정규 출근자는 안 나와야 함) 나온 이름:', await pg.evaluate("dailyPayoutRows(view.daily).map(r=>r.name)"))
    await pg.evaluate("window.pullNow()"); await pg.wait_for_timeout(600)
    print('8) 통합관리에서 다시 열면 다시 잠김:', await pg.is_visible('#lockBox'), '| 화면 비움:', (await pg.inner_text('#app')).strip()=='')
    await pg.locator('.pinin').nth(0).fill('틀림'); await pg.locator('#pinForm button[type=submit]').click(); await pg.wait_for_timeout(500); print('   틀린 비번:', await pg.inner_text('#pinMsg'), '| 여전히 잠김:', await pg.is_visible('#lockBox'))
    for i in range(4):
      await pg.locator('.pinin').nth(0).fill('x'+str(i)); await pg.locator('#pinForm button[type=submit]').click(); await pg.wait_for_timeout(300)
    print('   5번 틀리면:', await pg.inner_text('#pinMsg')); PIN['locked']=False; PIN['fails']=0
    print('   errs', errs); await ctx.close()
    ctx,pg,errs=await open_page(b); await unlock(pg); print('9) 다시 열고 맞는 비번으로 열림:', not await pg.is_visible('#lockBox'), '| 사람 수:', await pg.evaluate("Object.keys(pay.months[pay.cur].people).length")); await ctx.close()
    CANPAY['v']=False; ctx,pg,errs=await open_page(b); await unlock(pg)
    print('10) 금액 권한 없는 계정: 안내', await pg.inner_text('#toast'), '| 금액:', [r for r in await rows(pg)][:2], '| errs', errs); await ctx.close()
asyncio.run(main())
