# 근무표 실시간: 연결·표시 / 다른 기기에서 바뀌면 바로 반영 / 연결돼 있으면 묻지 않음 / 안 되면 60초 확인 / 매장 바꾸면 새로 연결 (가짜 서버+가짜 웹소켓)
# 실행 전: cd dist && python3 -m http.server 8765
import asyncio, json, time
from playwright.async_api import async_playwright
NEW='bdqcrbnbuoujozlpttbe.supabase.co'; BON='0134d989-757a-4b60-9cb3-93245de2cac8'; F1='ad2ffdae-f76b-44cd-a6c6-58514c4e4638'
ROWS={'v':[{"kind":"cfg","id":"positions","data":[{"name":"홀","color":"#2F6B3F","req":[0]*7}],"deleted":False,"updated_at":"2026-09-30T00:00:00Z"},
           {"kind":"staff","id":"s1","data":{"name":"김원래","pos":"홀","type":"regular","off":[],"active":True,"order":1},"deleted":False,"updated_at":"2026-09-30T00:00:00Z"}]}
NEWROW={"kind":"staff","id":"s2","data":{"name":"박새직원","pos":"홀","type":"regular","off":[],"active":True,"order":2},"deleted":False,"updated_at":"2026-10-01T05:00:00Z"}
REQ=[]; WSLOG=[]; SOCKS=[]; PENDING={'rows':[]}
async def handler(r):
  u=r.request.url; m=r.request.method
  if 'localhost' in u: return await r.continue_()
  if NEW not in u: return await r.fulfill(status=404,body='{}')
  J=lambda o,st=200: r.fulfill(status=st,content_type='application/json',body=json.dumps(o))
  if '/rpc/sch_my_stores' in u: return await J([{"id":BON,"name":"일품집 본점","is_hq":True,"role":"hq","can_pay":True},{"id":F1,"name":"가맹점 1","is_hq":False,"role":"hq","can_pay":False}])
  if '/rest/v1/sch_items' in u:
    if m=='GET':
      if 'updated_at=gt' in u: REQ.append('since'); out=PENDING['rows']; PENDING['rows']=[]; return await J(out)
      REQ.append('items'); return await J(ROWS['v'])
    return await r.fulfill(status=201,body='')
  await J([])
S={"ses":{"access_token":"tok","refresh_token":"r","expires_at":int(time.time())+3000,"user":{"email":"x@ilpum.invalid"}}}
async def open_page(b,ws_ok):
  ctx=await b.new_context(viewport={'width':1300,'height':800}); pg=await ctx.new_page(); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
  await pg.route('**/*',handler); SOCKS.clear(); WSLOG.clear(); REQ.clear()
  if ws_ok:
    def on_ws(ws):
      SOCKS.append(ws)
      def on_msg(msg):
        m=json.loads(msg); WSLOG.append((m['event'],m['topic']))
        if m['event']=='phx_join': ws.send(json.dumps({"topic":m['topic'],"event":"phx_reply","payload":{"status":"ok","response":{"postgres_changes":[{"id":1}]}},"ref":m['ref']}))
      ws.on_message(on_msg)
    await pg.route_web_socket(f'wss://{NEW}/**',on_ws)
  else: await pg.route_web_socket(f'wss://{NEW}/**',lambda ws: asyncio.ensure_future(ws.close()))
  await pg.add_init_script(f"try{{ localStorage.setItem('ilpum-fr-conf',{json.dumps(json.dumps({**S,'mode':'remote','url':'https://'+NEW,'key':'k'}))}); }}catch(e){{}}")
  await pg.goto('http://localhost:8765/ilpum-schedule.html'); await pg.wait_for_timeout(1800); return ctx,pg,errs
async def main():
  async with async_playwright() as p:
    b=await p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
    ctx,pg,errs=await open_page(b,True)
    print('1) 실시간 연결:', await pg.evaluate("rtOk"), '| 매장 구분 주제:', [t for e,t in WSLOG if e=='phx_join'], '| 상태 표시:', await pg.evaluate("APP.sync[0]"))
    print('   처음 직원 수:', await pg.evaluate("Object.keys(APP.D.staff).length"))
    PENDING['rows']=[NEWROW]; REQ.clear()
    SOCKS[-1].send(json.dumps({"topic":[t for e,t in WSLOG if e=='phx_join'][0],"event":"postgres_changes","payload":{"ids":[1],"data":{"schema":"public","table":"sch_items","type":"INSERT","record":{"kind":"staff","id":"s2","store_id":BON}}},"ref":None}))
    await pg.wait_for_timeout(1500)
    print('2) 다른 기기에서 직원 추가 → 바로 반영:', await pg.evaluate("Object.values(APP.D.staff).map(s=>s.name)"), '| 요청:', REQ)
    REQ.clear(); await pg.wait_for_timeout(34000); print('3) 연결돼 있으면 34초 동안 묻지 않음: 요청', len(REQ), '번')
    n=len([1 for e,t in WSLOG if e=='phx_join'])
    await pg.evaluate("openStore(APP.stores.find(s=>s.id!==APP.sid).id).then(()=>{renderShell();render();})"); await pg.wait_for_timeout(1500)
    joins=[t for e,t in WSLOG if e=='phx_join']; print('4) 매장 바꾸면 새 주제로 다시 연결:', joins[-1].endswith(F1), '| 가입 횟수', len(joins), '| 이전 연결은 닫힘:', SOCKS[0] is not SOCKS[-1])
    print('   errs', errs); await ctx.close()
    ctx,pg,errs=await open_page(b,False); REQ.clear(); await pg.wait_for_timeout(64000)
    print('5) 실시간이 안 될 때: 연결', await pg.evaluate("rtOk"), '| 64초 동안 확인 요청', len(REQ), '번 (60초마다 확인으로 대체)'); print('   errs', errs); await ctx.close()
asyncio.run(main())
