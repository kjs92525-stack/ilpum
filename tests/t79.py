# 손님용 현황판(display.html) "앞뒤 2시간" (2026-11-07): 지금 시각 ±2시간 예약만, 글자 더 크게, 버튼·N 키·기억 (가짜 서버, 시계 18:00 고정)
import asyncio, json, time, datetime
from playwright.async_api import async_playwright
NEW='bdqcrbnbuoujozlpttbe.supabase.co'; HQ='0134d989-757a-4b60-9cb3-93245de2cac8'
TODAY=datetime.date.today().isoformat()
def it(i,n,tm,tb,pp): return {"id":"i%d"%i,"name":n,"time":tm,"tables":tb,"pp":pp,"tnote":"","req":"","done":False}
ITEMS=[it(1,"점심손님","12:00",["1"],"2"),it(2,"이른손님","15:30",["2"],"2"),it(3,"사시반","16:00",["3"],"4"),it(4,"여섯시","18:00",["4"],"4"),
       it(5,"일곱시","19:30",["5"],"3"),it(6,"여덟시","20:00",["6"],"2"),it(7,"늦은손님","20:30",["7"],"2")]
async def handler(r):
  u=r.request.url
  if 'localhost' in u: return await r.continue_()
  if NEW not in u: return await r.fulfill(status=404,body='{}')
  J=lambda o: r.fulfill(status=200,content_type='application/json',body=json.dumps(o))
  if '/rpc/sch_my_stores' in u: return await J([{"id":HQ,"name":"일품집 본점","is_hq":True,"role":"hq","can_pay":True}])
  if '/rest/v1/res_days' in u:
    if 'select=data' in u: return await J([{"rev":5,"data":{"items":ITEMS}}])
    return await J([{"rev":5}])
  await J([])
S={"ses":{"access_token":"tok","refresh_token":"r","expires_at":int(time.time())+10**8,"user":{"email":"x@ilpum.invalid"}}}
FIX="""(()=>{const _D=Date;const fx=new _D(new _D().getFullYear(),new _D().getMonth(),new _D().getDate(),18,0,0).getTime();class FD extends _D{constructor(...a){if(a.length===0)super(fx);else super(...a);}static now(){return fx;}}window.Date=FD;})();"""
async def main():
  ok=True
  def chk(n,c,x=''):
    nonlocal ok; ok&=bool(c); print('OK  ' if c else 'FAIL',n,x)
  async with async_playwright() as p:
    b=await p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
    ctx=await b.new_context(viewport={'width':1280,'height':800}); pg=await ctx.new_page(); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
    await pg.route('**/*',handler); await pg.route_web_socket(f'wss://{NEW}/**',lambda ws: None)
    await pg.add_init_script(FIX)
    await pg.add_init_script(f"try{{ localStorage.setItem('ilpum-fr-conf',{json.dumps(json.dumps(S))}); }}catch(e){{}}")
    await pg.goto('http://localhost:8765/display.html'); await pg.wait_for_timeout(2000)
    names=lambda: pg.evaluate("[...document.querySelectorAll('.row .nm')].map(e=>e.firstChild.textContent)")
    all_=await names(); fs0=await pg.evaluate("parseInt(getComputedStyle(document.getElementById('grid')).getPropertyValue('--fs'))")
    chk('처음엔 오늘 전부(7팀)', len(all_)==7, all_)
    await pg.evaluate("showCtl()"); await pg.click('#ctlNear'); await pg.wait_for_timeout(400)
    nn=await names(); fs1=await pg.evaluate("parseInt(getComputedStyle(document.getElementById('grid')).getPropertyValue('--fs'))")
    chk('앞뒤 2시간(16:00~20:00)만', nn==['사시반','여섯시','일곱시','여덟시'], nn)
    chk(f'글자가 더 커짐 {fs0}→{fs1}px', fs1>fs0)
    chk('제목·버튼 표시', '앞뒤 2시간' in await pg.inner_text('#title') and '✓' in await pg.inner_text('#ctlNear'))
    await pg.reload(); await pg.wait_for_timeout(2000)
    chk('다시 열어도 기억', len(await names())==4)
    await pg.keyboard.press('n'); await pg.wait_for_timeout(300)
    chk('N 키로 끄면 전부', len(await names())==7)
    chk('오류 없음', not errs, errs); await b.close()
  print('전체 OK' if ok else '실패 있음')
asyncio.run(main())
