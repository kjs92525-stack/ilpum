# 손님용 예약 현황판(display.html): 오늘 예약을 시간순·테이블 번호 크게, 취소는 빼고, 실시간 알림이 오면 서버에 다시 묻지 않고 바로 바뀜, 한 화면에 다 들어감 (가짜 서버)
import asyncio, json, time, datetime, sys
from playwright.async_api import async_playwright
NEW='bdqcrbnbuoujozlpttbe.supabase.co'; HQ='0134d989-757a-4b60-9cb3-93245de2cac8'
TODAY=datetime.date.today().isoformat()
def it(i,n,tm,tb,pp,**k): d={"id":"i%d"%i,"name":n,"time":tm,"tables":tb,"pp":pp,"tnote":"","req":"","done":False}; d.update(k); return d
# 사진 속 (토) 칠판 그대로 25팀
RAW=[("홍혜원","11:30",["7"],"6"),("강수연","13:00",["10"],"6"),("김태희","13:00",["31","32"],"8"),("이채의","13:00",["13"],"4"),("오창현","16:00",["8"],"5"),("이수연","16:30",["12"],"4"),
("김연지","17:00",["14"],"4"),("허지현","17:00",["R1"],"8"),("황인자","17:00",["13"],"3"),("금동하","17:30",["33","34"],"10"),("강동현","18:00",["9"],"5"),("윤상목","18:00",["4"],"4"),("임재우","18:00",["6"],"6"),
("차수자","18:00",["7"],"5"),("김효미","18:30",["49","53"],"11"),("한정현","18:30",["R2-1","R2-2","R3-1"],"20"),("김지영","19:00",["31","32"],"8"),("이지훈","19:00",["8"],"5"),("조하영","18:00",["17"],"3"),
("김기민","20:00",["13"],"3"),("금수돈","11:20",["15"],"5"),("김유정","12:30",["14"],"4"),("조진철","17:15",["21"],"2"),("김준우","17:30",["18"],"3"),("김상훈","19:00",["23"],"5")]
ITEMS=[it(i,*r) for i,r in enumerate(RAW)]+[it(99,"취소손님","18:00",["2"],"2",tnote="네이버취소"),it(98,"지운손님","18:00",["3"],"2",deleted=True)]
REQ={'n':0,'full':0}
async def handler(r):
  u=r.request.url
  if 'localhost' in u: return await r.continue_()
  if NEW not in u: return await r.fulfill(status=404,body='{}')
  REQ['n']+=1
  J=lambda o: r.fulfill(status=200,content_type='application/json',body=json.dumps(o))
  if '/rpc/sch_my_stores' in u: return await J([{"id":HQ,"name":"일품집 본점","is_hq":True,"role":"hq","can_pay":True}])
  if '/rest/v1/res_days' in u:
    if 'select=data' in u: REQ['full']+=1; return await J([{"rev":5,"data":{"items":ITEMS}}])
    return await J([{"rev":5}])
  await J([])
WS={}
def on_ws(ws):
  WS['ws']=ws
  def msg(m):
    m=json.loads(m)
    if m['event']=='phx_join': WS['topic']=m['topic']; ws.send(json.dumps({"topic":m['topic'],"event":"phx_reply","payload":{"status":"ok","response":{}},"ref":m['ref']}))
  ws.on_message(msg)
S={"ses":{"access_token":"tok","refresh_token":"r","expires_at":int(time.time())+3000,"user":{"email":"x@ilpum.invalid"}}}
async def main():
  ok=True
  def chk(n,c,x=''):
    nonlocal ok; ok&=bool(c); print('OK  ' if c else 'FAIL',n,x)
  async with async_playwright() as p:
    b=await p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
    for vw,vh in ((1920,1080),(1280,720)):
      ctx=await b.new_context(viewport={'width':vw,'height':vh}); pg=await ctx.new_page(); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
      await pg.route('**/*',handler); await pg.route_web_socket(f'wss://{NEW}/**',on_ws)
      await pg.add_init_script(f"try{{ localStorage.setItem('ilpum-fr-conf',{json.dumps(json.dumps(S))}); }}catch(e){{}}")
      await pg.goto('http://localhost:8765/display.html'); await pg.wait_for_timeout(2500)
      if len(sys.argv)>1: await pg.screenshot(path=f'/tmp/disp_{vw}.png')
      rows=await pg.evaluate("[...document.querySelectorAll('.row')].map(r=>[r.querySelector('.nm').firstChild.textContent,r.querySelector('.tb').textContent,r.querySelector('.tm').textContent])")
      chk(f'[{vw}] 25팀, 취소·지운 예약 빠짐', len(rows)==25 and not any(r[0] in ('취소손님','지운손님') for r in rows), str(len(rows)))
      chk(f'[{vw}] 시간순 (11:20 금수돈 먼저)', rows[0][0]=='금수돈' and rows[0][2]=='11:20', str(rows[:2]))
      d=dict((r[0],r[1]) for r in rows)
      chk(f'[{vw}] 테이블 표기 (7 / 31·32 / 룸1 / 룸2 룸3)', d['홍혜원']=='7' and d['김태희']=='31·32' and d['허지현']=='룸1' and d['한정현']=='룸2 룸3', str(d))
      fitok=await pg.evaluate("(()=>{const g=document.getElementById('grid'),H=g.clientHeight,W=g.clientWidth;return [...g.children].every(c=>c.offsetTop-g.offsetTop+c.offsetHeight<=H+1&&c.offsetLeft-g.offsetLeft+c.offsetWidth<=W+1)&&document.documentElement.scrollHeight<=innerHeight+1})()")
      fs=await pg.evaluate("parseInt(getComputedStyle(document.getElementById('grid')).getPropertyValue('--fs'))")
      chk(f'[{vw}] 스크롤 없이 한 화면, 글자 {fs}px', fitok and fs>=(28 if vw==1920 else 18), str(fs))
      chk(f'[{vw}] 실시간 표시', '실시간' in await pg.inner_text('#st'))
      if vw==1920:
        full0=REQ['full']; n0=REQ['n']
        new=ITEMS[:5]+[it(77,"새손님","19:30",["16"],"4")]
        WS["ws"].send(json.dumps({"topic":WS['topic'],"event":"postgres_changes","payload":{"data":{"type":"UPDATE","record":{"id":TODAY,"store_id":HQ,"rev":6,"data":{"items":new}}}},"ref":None}))
        await pg.wait_for_timeout(600)
        names=await pg.evaluate("[...document.querySelectorAll('.row .nm')].map(e=>e.firstChild.textContent)")
        chk('실시간 알림 → 바로 바뀜(새손님 보이고 6팀)', '새손님' in names and len(names)==6, str(names))
        chk('알림 내용을 그대로 써서 서버에 다시 안 물어봄', REQ['full']==full0 and REQ['n']==n0, f"{REQ}")
        WS["ws"].send(json.dumps({"topic":WS['topic'],"event":"postgres_changes","payload":{"data":{"type":"UPDATE","record":{"id":"2000-01-01","store_id":HQ,"rev":1,"data":{"items":[]}}}},"ref":None}))
        await pg.wait_for_timeout(300)
        chk('다른 날짜 알림은 무시', len(await pg.query_selector_all('.row'))==6)
      chk(f'[{vw}] 오류 없음', not errs, str(errs)); await ctx.close()
    # 로그인 안 된 기기
    ctx=await b.new_context(); pg=await ctx.new_page(); await pg.route('**/*',handler)
    await pg.goto('http://localhost:8765/display.html'); await pg.wait_for_timeout(800)
    chk('로그인 안 했으면 안내', '로그인이 필요해요' in await pg.inner_text('body')); await ctx.close()
    await b.close()
  print('전체 OK' if ok else '실패 있음')
asyncio.run(main())
