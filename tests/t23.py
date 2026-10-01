# 예약 화면 실시간: 다른 기기에서 예약이 추가되면 바로 뜨는지 / 연결이 안 되면 예전처럼 30초 확인 / 연결되면 계속 묻지 않음 (가짜 서버+가짜 웹소켓)
# 실행 전: cd dist && python3 -m http.server 8765
import asyncio, json, time
from playwright.async_api import async_playwright
NEW='bdqcrbnbuoujozlpttbe.supabase.co'; F1='ad2ffdae-f76b-44cd-a6c6-58514c4e4638'
TODAY={'d':None}; DB={'rev':3,'items':[{"id":"a1","name":"원래손님","time":"18:00","pp":"2","tables":[],"req":"","u":1}]}; REQ=[]; WSLOG=[]; SOCKS=[]
async def handler(r):
  u=r.request.url; m=r.request.method
  if 'localhost' in u: return await r.continue_()
  if NEW not in u: return await r.fulfill(status=404,body='{}')
  J=lambda o,st=200: r.fulfill(status=st,content_type='application/json',body=json.dumps(o),headers={'access-control-allow-origin':'*'})
  if '/rpc/sch_my_stores' in u: return await J([{"id":F1,"name":"가맹점 1","is_hq":False,"role":"owner"}])
  if '/rest/v1/res_days' in u:
    REQ.append(u)
    if m=='GET': return await J([{"rev":DB['rev']}] if 'select=rev' in u else [{"data":{"items":DB['items']},"rev":DB['rev']}])
    return await J([{"rev":DB['rev']+1}])
  if '/rest/v1/sch_items' in u: return await J([])
  await J([])
S={"ses":{"access_token":"tok","refresh_token":"r","expires_at":int(time.time())+3000,"user":{"email":"x@ilpum.invalid"}}}
async def open_page(b,ws_ok):
  ctx=await b.new_context(viewport={'width':1300,'height':800}); pg=await ctx.new_page(); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
  await pg.route('**/*',handler); SOCKS.clear(); WSLOG.clear()
  if ws_ok:
    def on_ws(ws):
      SOCKS.append(ws)
      def on_msg(msg):
        m=json.loads(msg); WSLOG.append((m['event'],m['topic']))
        if m['event']=='phx_join': ws.send(json.dumps({"topic":m['topic'],"event":"phx_reply","payload":{"status":"ok","response":{"postgres_changes":[{"id":1}]}},"ref":m['ref']}))
        if m['event']=='heartbeat': ws.send(json.dumps({"topic":"phoenix","event":"phx_reply","payload":{"status":"ok"},"ref":m['ref']}))
      ws.on_message(on_msg)
    await pg.route_web_socket(f'wss://{NEW}/**',on_ws)
  else:
    await pg.route_web_socket(f'wss://{NEW}/**',lambda ws: asyncio.ensure_future(ws.close()))
  await pg.add_init_script(f"try{{ localStorage.setItem('ilpum-fr-conf',{json.dumps(json.dumps(S))}); }}catch(e){{}}")
  await pg.goto('http://localhost:8765/reserve.html'); await pg.wait_for_timeout(1500); return ctx,pg,errs
async def main():
  async with async_playwright() as p:
    b=await p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
    ctx,pg,errs=await open_page(b,True); d=await pg.evaluate("ui.date"); DB.update(rev=3,items=[{"id":"a1","name":"원래손님","time":"18:00","pp":"2","tables":[],"req":"","u":1}])
    await pg.evaluate("pullDay(ui.date)"); await pg.wait_for_timeout(600)
    print('1) 실시간 연결:', await pg.evaluate("rtOk"), '| 가입 요청:', [e for e,t in WSLOG if e=='phx_join'], '| 매장 구분 주제:', any(F1 in t for e,t in WSLOG))
    print('   처음 목록:', await pg.evaluate("items(ui.date).map(x=>x.name)"))
    DB['rev']=4; DB['items'].append({"id":"a2","name":"옆자리에서추가","time":"19:00","pp":"4","tables":[],"req":"","u":2}); REQ.clear()
    SOCKS[-1].send(json.dumps({"topic":SOCKS and [t for e,t in WSLOG if e=='phx_join'][0],"event":"postgres_changes","payload":{"ids":[1],"data":{"schema":"public","table":"res_days","type":"UPDATE","record":{"id":d,"store_id":F1,"rev":4},"old_record":{"id":d}}},"ref":None}))
    await pg.wait_for_timeout(1200)
    print('2) 다른 기기에서 추가 → 바로 뜸:', await pg.evaluate("items(ui.date).map(x=>x.name)"), '| 필요한 요청 수:', len(REQ), '(번호 확인 + 받기)')
    REQ.clear(); await pg.wait_for_timeout(34000)
    print('3) 연결돼 있으면 34초 동안 묻지 않음: 요청', len(REQ), '번 | 하트비트 보냄:', any(e=='heartbeat' for e,t in WSLOG) or '(25초 주기)')
    print('   errs', errs); await ctx.close()
    ctx,pg,errs=await open_page(b,False); REQ.clear(); await pg.wait_for_timeout(34000)
    print('4) 실시간이 안 될 때: 연결 상태', await pg.evaluate("rtOk"), '| 34초 동안 확인 요청', len(REQ), '번 (30초마다 확인으로 대체)'); print('   errs', errs); await ctx.close()
asyncio.run(main())
