# 급여 계산기 기록을 서버에 보관: 처음엔 이 기기 기록을 올림 / 다른 기기에서 그대로 열림 / 바뀐 줄만 올림·받음 / 서버 오류 때 점점 느리게 (가짜 서버)
import asyncio, json, time, urllib.parse
from playwright.async_api import async_playwright
NEW='bdqcrbnbuoujozlpttbe.supabase.co'; BON='0134d989-757a-4b60-9cb3-93245de2cac8'
ITEMS=[{"kind":"cfg","id":"store","data":{"name":"일품집 본점","open":"11:00","close":"22:00","fullH":10,"pmH":5}},
  {"kind":"cfg","id":"positions","data":[{"name":"홀","color":"#2F6B3F","req":[0]*7}]}]
SRV={}; LOG=[]; FAIL={'v':False}; CLK={'t':1}
def stamp(): CLK['t']+=1; return '2026-10-07T01:00:%02d.000Z'%CLK['t']
async def handler(r):
  u=urllib.parse.unquote(r.request.url); m=r.request.method
  if 'localhost' in u: return await r.continue_()
  if NEW not in u: return await r.fulfill(status=404,body='{}')
  J=lambda o,sv=200: r.fulfill(status=sv,content_type='application/json',body=json.dumps(o))
  if '/rpc/pay_pin_status' in u: return await J({"has":True,"locked":0})
  if '/rpc/pay_pin_check' in u: return await J('ok')
  if '/rpc/sch_my_stores' in u: return await J([{"id":BON,"name":"일품집 본점","is_hq":True,"role":"hq","can_pay":True}])
  if '/rest/v1/sch_items' in u:
    if m=='POST':
      if FAIL['v']: LOG.append(('POST-FAIL',[])); return await J({"message":"boom"},500)
      rows=json.loads(r.request.post_data); out=[]
      for x in rows:
        at=stamp(); SRV[x['id']]={"id":x['id'],"data":x['data'],"deleted":x['deleted'],"updated_at":at}; out.append(SRV[x['id']])
      LOG.append(('POST',[x['id'] for x in rows],len(r.request.post_data))); return await J(out,201)
    if 'id=like.calc:' in u:
      LOG.append(('LIST',)); return await J([{"id":v['id'],"updated_at":v['updated_at'],"deleted":v['deleted']} for v in SRV.values()])
    if 'id=in.(' in u:
      ids=[s.strip('"') for s in u.split('id=in.(')[1].split(')')[0].split(',')]
      LOG.append(('GET',ids)); return await J([SRV[i] for i in ids if i in SRV])
    return await J([{**x,"deleted":False} for x in ITEMS])
  await J([])
S={"ses":{"access_token":"tok","refresh_token":"r","expires_at":int(time.time())+10**8,"user":{"email":"x@ilpum.invalid"}}}
FIX="""(()=>{const _D=Date;const fixed=new _D('2026-10-07T10:00:00+09:00').getTime();class FD extends _D{constructor(...a){if(a.length===0)super(fixed);else super(...a);}static now(){return _D.now()-(_D.now()-fixed)+(performance.now());}}window.Date=FD;})();"""
LOCAL={"fullH":10,"pmH":5,"rates":{"홍길동":12000},"drates":{},"cycle":{},"fullHs":{},"accts":{"홍길동":"농협 111-22"},"showAcct":True,
  "months":{"2026-09":{"people":{"홍길동":{"days":{"2026-09-03":{"base":True,"hours":8}}}}}},"cur":"2026-09"}
async def open_dev(b,local=None,meta=None):
  ctx=await b.new_context(viewport={'width':1300,'height':900}); pg=await ctx.new_page(); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
  await pg.route('**/*',handler); await pg.add_init_script(FIX)
  init=f"try{{ if(!sessionStorage.getItem('__init')){{ sessionStorage.setItem('__init','1'); localStorage.setItem('ilpum-fr-conf',{json.dumps(json.dumps(S))});"
  if local: init+=f" localStorage.setItem('ilpum-pay-v1',{json.dumps(json.dumps(local))});"
  if meta: init+=f" localStorage.setItem('ilpum-pay-v1-srv',{json.dumps(json.dumps(meta))});"
  init+=" } }catch(e){}"
  await pg.add_init_script(init)
  await pg.goto('http://localhost:8765/pay.html'); await pg.wait_for_timeout(1500)
  await pg.locator('.pinin').nth(0).fill('abcd'); await pg.locator('#pinForm button[type=submit]').click(); await pg.wait_for_timeout(3500)
  return ctx,pg,errs
async def main():
  ok=True
  def chk(n,c,x=''):
    nonlocal ok; ok&=bool(c); print('OK  ' if c else 'FAIL',n,x)
  async with async_playwright() as p:
    b=await p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
    # 1) 기기 A: 이 기기에만 기록이 있고 서버는 비어 있음 → 올림
    ctxA,A,errs=await open_dev(b,LOCAL)
    posts=[x for x in LOG if x[0]=='POST']; ids=set(i for x in posts for i in x[1])
    chk('A: 처음 열 때 이 기기 기록을 서버에 올림', {'calc:cfg','calc:m:2026-09'}<=ids, str(posts))
    chk('A: 서버에 계좌·시급 보관', SRV.get('calc:cfg',{}).get('data',{}).get('accts',{}).get('홍길동')=='농협 111-22')
    metaA=await A.evaluate("localStorage.getItem('ilpum-pay-v1-srv')"); chk('A: 오류 없음',not errs,str(errs)); await ctxA.close()
    # 2) 기기 B: 아무 기록 없음 → 서버에서 받아서 그대로
    LOG.clear(); ctxB,B,errs=await open_dev(b)
    acct=await B.evaluate("pay.accts['홍길동']||''"); sep=await B.evaluate("!!pay.months['2026-09']")
    chk('B: 다른 기기에서도 계좌·지난달 기록이 열림', acct=='농협 111-22' and sep, acct)
    # B 에서 계좌만 바꿈 → 설정 줄만 올라가야 함
    LOG.clear(); await B.evaluate("pay.accts['홍길동']='국민 999'; save()"); await B.wait_for_timeout(2500)
    posts=[x for x in LOG if x[0]=='POST']
    chk('B: 바꾼 줄(설정)만 올림', posts and all('calc:m:2026-09' not in x[1] for x in posts) and any('calc:cfg' in x[1] for x in posts), str(posts))
    chk('B: 오류 없음',not errs,str(errs)); await ctxB.close()
    # 3) 기기 A 다시 열기(예전 기록·메타 그대로) → 바뀐 설정 줄만 받아 옴
    LOG.clear(); ctxA,A,errs=await open_dev(b,LOCAL,json.loads(metaA))
    gets=[x for x in LOG if x[0]=='GET']; acct=await A.evaluate("pay.accts['홍길동']")
    got=[i for x in gets for i in x[1]]
    chk('A: 다시 열면 바뀐 줄(설정)과 이 기기에 없는 달만 받음, 있는 9월은 안 받음', 'calc:cfg' in got and 'calc:m:2026-09' not in got, str(gets))
    chk('A: B에서 바꾼 계좌가 보임', acct=='국민 999', acct)
    chk('A: 다시 열어도 쓸데없이 올리지 않음', not [x for x in LOG if x[0]=='POST'], str([x for x in LOG if x[0]=='POST']))
    await ctxA.close()
    # 3-2) 빈 기기 C 가 먼저 열려 기본값을 올린 뒤, 진짜 기록이 있는 기기 D 를 처음 열어도 D 의 시급·계좌가 지켜지고 합쳐져야 함
    SRV.clear(); LOG.clear(); ctxC,C,_=await open_dev(b); await ctxC.close()
    D_LOCAL=json.loads(json.dumps(LOCAL)); D_LOCAL['accts']={'김철수':'우리 555'}; D_LOCAL['rates']={'김철수':11000}
    ctxD,Dp,errs=await open_dev(b,D_LOCAL); await Dp.wait_for_timeout(2500)
    chk('D: 처음 연결해도 이 기기 계좌·시급이 안 지워짐', await Dp.evaluate("pay.accts['김철수']")=='우리 555' and await Dp.evaluate("pay.rates['김철수']")==11000)
    chk('D: 합친 결과가 서버에 올라감', SRV.get('calc:cfg',{}).get('data',{}).get('accts',{}).get('김철수')=='우리 555')
    chk('D: 오류 없음',not errs,str(errs)); await ctxD.close()
    ctxA,A,errs=await open_dev(b,LOCAL,json.loads(metaA))
    # 4) 서버가 계속 500 이면 점점 느리게 (20초에 몇 번?)
    FAIL['v']=True; LOG.clear(); await A.evaluate("pay.accts['홍길동']='신한 1'; save()"); await A.wait_for_timeout(20000)
    n=len([x for x in LOG if x[0]=='POST-FAIL']); note=await A.inner_text('#srvNote')
    chk('A: 서버 오류 때 20초 동안 시도 5번 이하', 1<=n<=5, f'{n}번'); chk('A: 저장 실패 안내 표시', '저장하지 못했어요' in note)
    FAIL['v']=False; await A.wait_for_timeout(26000)
    chk('A: 서버가 돌아오면 결국 올라감', SRV['calc:cfg']['data']['accts']['홍길동']=='신한 1')
    chk('A: 오류 없음',not errs,str(errs)); await ctxA.close(); await b.close()
  print('전체 OK' if ok else '실패 있음')
asyncio.run(main())
