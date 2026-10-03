# 본사가 점주 비밀번호를 바꾸면: 점주 화면(설정·오늘 현황)에 알림, "내 비밀번호 바꾸기" 후 알림이 사라짐 / 본사 계정 목록에 표시 (가짜 서버)
import asyncio, json, time
from playwright.async_api import async_playwright
NEW='bdqcrbnbuoujozlpttbe.supabase.co'; BON='0134d989-757a-4b60-9cb3-93245de2cac8'; F1='ad2ffdae-f76b-44cd-a6c6-58514c4e4638'
ROLE={'v':'owner'}; PUTS=[]
HQAT='2026-10-03T01:00:00.000Z'
async def handler(r):
  u=r.request.url
  if 'localhost' in u: return await r.continue_()
  if NEW not in u: return await r.fulfill(status=404,body='{}')
  J=lambda o,st=200: r.fulfill(status=st,content_type='application/json',body=json.dumps(o))
  if '/auth/v1/user' in u and r.request.method=='PUT':
    b=json.loads(r.request.post_data); PUTS.append(b)
    return await J({"id":"u1","email":"yucheon@ilpum.invalid","app_metadata":{"pw_by_hq":HQAT},"user_metadata":b.get('data',{})})
  if '/rpc/sch_my_stores' in u:
    if ROLE['v']=='hq': return await J([{"id":BON,"name":"일품집 본점","is_hq":True,"role":"hq","can_pay":True}])
    return await J([{"id":F1,"name":"유천점","is_hq":False,"role":"owner","can_pay":True}])
  if '/functions/v1/manage-accounts' in u:
    return await J({"ok":True,"rows":[{"id":"yucheon","hq":False,"me":False,"links":[{"store":"유천점","role":"owner","pay":True}],"last":None,"banned":False,"pwByHq":HQAT}]})
  await J([])
def conf():
  return {"ses":{"access_token":"tok","refresh_token":"r","expires_at":int(time.time())+3000,
    "user":{"id":"u1","email":"yucheon@ilpum.invalid","app_metadata":{"pw_by_hq":HQAT} if ROLE['v']=='owner' else {},"user_metadata":{}}},"mode":"remote","url":"https://"+NEW,"key":"k"}
async def open_page(b,url):
  ctx=await b.new_context(viewport={'width':1200,'height':900}); pg=await ctx.new_page(); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
  ans=iter(['newpass123','newpass123'])
  pg.on('dialog',lambda d: asyncio.ensure_future(d.accept(next(ans,'')) if d.type=='prompt' else d.accept()))
  await pg.route('**/*',handler); await pg.route_web_socket(f'wss://{NEW}/**',lambda ws: asyncio.ensure_future(ws.close()))
  await pg.add_init_script(f"try{{ localStorage.setItem('ilpum-fr-conf',{json.dumps(json.dumps(conf()))}); }}catch(e){{}}")
  await pg.goto(url); await pg.wait_for_timeout(1800); return ctx,pg,errs
async def main():
  ok=True
  def chk(name,cond,extra=''):
    nonlocal ok; ok&=bool(cond); print('OK  ' if cond else 'FAIL',name,extra)
  async with async_playwright() as p:
    b=await p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
    ctx,pg,errs=await open_page(b,'http://localhost:8765/ilpum-schedule.html?view=set')
    t=await pg.inner_text('#main')
    chk('점주 설정에 경고', '본사가 비밀번호를 바꿨어요' in t)
    await pg.click('[data-a=mypw]'); await pg.wait_for_timeout(800)
    chk('내 비밀번호 바꾸기 호출', PUTS and PUTS[-1].get('password')=='newpass123' and PUTS[-1]['data'].get('pw_self_at'), str(PUTS[-1:] and {k:v for k,v in PUTS[-1].items() if k!='password'}))
    chk('바꾼 뒤 경고 사라짐', '본사가 비밀번호를 바꿨어요' not in await pg.inner_text('#main'))
    saved=await pg.evaluate("JSON.parse(localStorage.getItem('ilpum-fr-conf')).ses.user.user_metadata.pw_self_at||''")
    chk('새 사용자 정보 저장', bool(saved)); chk('오류 없음', not errs, str(errs)); await ctx.close()
    ctx,pg,errs=await open_page(b,'http://localhost:8765/index.html'); await pg.wait_for_timeout(1500)
    chk('오늘 현황에 경고', '비밀번호를 바꿨어요' in await pg.inner_text('body')); chk('오류 없음(통합 틀)', not errs, str(errs)); await ctx.close()
    ROLE['v']='hq'; ctx,pg,errs=await open_page(b,'http://localhost:8765/ilpum-schedule.html?view=acct')
    t=await pg.inner_text('#main')
    chk('본사 계정 목록에 표시', '본사가 비밀번호 바꿈' in t); chk('본사 화면엔 경고 없음', '본사가 비밀번호를 바꿨어요' not in t); chk('오류 없음(본사)', not errs, str(errs)); await ctx.close()
    await b.close()
  print('전체 OK' if ok else '실패 있음')
asyncio.run(main())
