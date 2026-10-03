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
    pg.on('dialog',lambda d: asyncio.ensure_future(d.accept()))
    await pg.click('#dailyBtn'); await pg.wait_for_timeout(800)
    chk('일당 지급 화면에 사람 추가 카드', await pg.is_visible('#xAddCard'))
    base=await pg.evaluate("dailyPayoutRows(view.daily).length")
    # 1) 3일치 × 하루 금액
    await pg.fill('#xName','김철수'); await pg.fill('#xDays','3'); await pg.fill('#xPer','110000'); await pg.dispatch_event('#xPer','change'); await pg.wait_for_timeout(200)
    chk('합계가 자동 계산(3 × 110,000)', await pg.input_value('#xTotal')=='330,000', await pg.input_value('#xTotal'))
    await pg.click('[data-act=xadd]'); await pg.wait_for_timeout(500)
    rows=await pg.evaluate("dailyPayoutRows(view.daily).filter(r=>r.eid)")
    chk('추가한 줄이 목록에 들어감', len(rows)==1 and rows[0]['name']=='김철수' and rows[0]['amount']==330000 and rows[0]['tag']=='3일치' and rows[0]['memo']=='3일치', str(rows))
    t=await pg.inner_text('.daily-card')
    chk('화면에 이름·3일치·금액', '김철수' in t and '3일치' in t and '330,000' in t)
    tot=await pg.evaluate("dailyPayoutRows(view.daily).reduce((a,r)=>a+r.amount,0)")
    chk('합계에 포함', f'{tot:,}' in await pg.inner_text('.daily-total'), str(tot))
    txt=await pg.evaluate("dailyText(view.daily)"); chk('텍스트 복사에 포함', '김철수 330,000원' in txt and '비고: 3일치' in txt, txt[:120])
    # 2) 지급완료·비고·금액 수정
    eid=rows[0]['eid']
    await pg.check(f'[data-xpaid="{eid}"]'); await pg.wait_for_timeout(300)
    chk('지급완료 체크 저장', await pg.evaluate(f"dailyPayoutRows(view.daily).find(r=>r.eid==='{eid}').paid"))
    await pg.fill(f'[data-xmemo="{eid}"]','10/5~10/7 3일치 계좌이체'); await pg.dispatch_event(f'[data-xmemo="{eid}"]','change'); await pg.wait_for_timeout(300)
    chk('비고 수정', await pg.evaluate(f"dailyPayoutRows(view.daily).find(r=>r.eid==='{eid}').memo")=='10/5~10/7 3일치 계좌이체')
    await pg.fill(f'[data-xamt="{eid}"]','300,000'); await pg.dispatch_event(f'[data-xamt="{eid}"]','change'); await pg.wait_for_timeout(300)
    chk('금액 수정', await pg.evaluate(f"dailyPayoutRows(view.daily).find(r=>r.eid==='{eid}').amount")==300000)
    # 3) 같은 이름을 한 번 더 / 근무표에 있는 사람 기간 합계 불러오기
    who=await pg.evaluate("Object.keys(pay.months[pay.cur].people).find(n=>n==='시급맨')")
    await pg.fill('#xName',who); await pg.fill('#xFrom','2026-10-05'); await pg.fill('#xTo','2026-10-07'); await pg.click('[data-act=xcalc]'); await pg.wait_for_timeout(1500)
    calc=await pg.evaluate("personRange('시급맨','2026-10-05','2026-10-07').tot")
    chk('근무표 기간 합계를 불러옴', await pg.input_value('#xTotal')==calc['sum'].toLocaleString('ko-KR') if False else (await pg.input_value('#xTotal')).replace(',','')==str(calc['sum']), f"{await pg.input_value('#xTotal')} vs {calc}")
    await pg.click('[data-act=xadd]'); await pg.wait_for_timeout(500)
    chk('두 번째 추가(근무표 기반)', await pg.evaluate("dailyPayoutRows(view.daily).filter(r=>r.eid).length")==2)
    # 4) 달을 다시 열어도 유지(저장), 지우기
    stored=await pg.evaluate("JSON.parse(localStorage.getItem(KEY)).months[pay.cur].extra[view.daily].length")
    chk('저장소에 남음', stored==2, str(stored))
    await pg.click(f'[data-xdel="{eid}"]'); await pg.wait_for_timeout(500)
    chk('이 줄 삭제', await pg.evaluate("dailyPayoutRows(view.daily).filter(r=>r.eid).length")==1)
    # 5) 입력 검증
    await pg.fill('#xName',''); await pg.click('[data-act=xadd]'); await pg.wait_for_timeout(300)
    chk('이름이 비면 추가 안 됨', await pg.evaluate("dailyPayoutRows(view.daily).filter(r=>r.eid).length")==1)
    chk('오류 없음', not errs, str(errs)); await ctx.close(); await b.close()
  print('전체 OK' if ok else '실패 있음')
asyncio.run(main())
