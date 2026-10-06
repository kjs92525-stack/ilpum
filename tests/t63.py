# 유천점처럼 룸마다 작은 테이블 수가 다를 때(룸2 = 2-1·2-2·2-3) 입력·표시가 그 매장 배치를 따르는지 (가짜 서버)
import asyncio, json, time, datetime
from playwright.async_api import async_playwright
NEW='bdqcrbnbuoujozlpttbe.supabase.co'; F1='ad2ffdae-f76b-44cd-a6c6-58514c4e4638'
mk=lambda i,x,y:{"id":i,"x":x,"y":y,"w":80,"h":60,"shape":"rect"}
T=[mk(str(i),20+i*40,20) for i in range(1,6)]+[mk("R1-1",20,200),mk("R1-2",110,200),mk("R2-1",20,300),mk("R2-2",110,300),mk("R2-3",200,300),mk("R3-1",20,400)]
LAYOUT={"v":1,"floors":[{"key":"1","mode":"free","name":"1층","tables":T}]}
async def handler(r):
  u=r.request.url; m=r.request.method
  if 'localhost' in u: return await r.continue_()
  if NEW not in u: return await r.fulfill(status=404,body='{}')
  J=lambda o,st=200: r.fulfill(status=st,content_type='application/json',body=json.dumps(o))
  if '/rpc/sch_my_stores' in u: return await J([{"id":F1,"name":"유천점","is_hq":False,"role":"owner"}])
  if '/rest/v1/sch_items' in u: return await J([{"data":LAYOUT}])
  if '/rest/v1/res_days' in u: return await J([{"rev":0}] if m=='GET' else [{"rev":1}])
  await J([])
S={"ses":{"access_token":"tok","refresh_token":"r","expires_at":int(time.time())+3000,"user":{"email":"x@ilpum.invalid"}}}
FAILS=[]
def ok(n,c,x=''):
  print(('  ok ' if c else 'FAIL ')+n,x)
  if not c: FAILS.append(n)
async def main():
  async with async_playwright() as p:
    b=await p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
    ctx=await b.new_context(viewport={'width':1500,'height':900}); pg=await ctx.new_page(); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
    await pg.route('**/*',handler); await pg.route_web_socket(f'wss://{NEW}/**',lambda ws: asyncio.ensure_future(ws.close()))
    await pg.add_init_script(f"try{{ localStorage.setItem('ilpum-fr-conf',{json.dumps(json.dumps(S))}); }}catch(e){{}}")
    await pg.goto('http://localhost:8765/reserve.html'); await pg.wait_for_timeout(2000)
    ev=lambda js: pg.evaluate(js)
    ok('1) 룸별 작은 테이블은 그 매장 배치에서: 룸1 2개·룸2 3개·룸3 1개', await ev("JSON.stringify(ROOM_SUBS)")=='{"1":[1,2],"2":[1,2,3],"3":[1]}', await ev("JSON.stringify(ROOM_SUBS)"))
    ok('2) "r2" → 룸2 세 칸 전부', await ev("parseTables('r2').join()")=='R2-1,R2-2,R2-3')
    ok('3) "r2-3" → 룸2-3 한 칸', await ev("parseTables('r2-3').join()")=='R2-3')
    ok('4) "r2-1,3" → 룸2-1·2-3', await ev("parseTables('r2-1,3').join()")=='R2-1,R2-3')
    ok('5) 룸2 세 칸이면 "룸2", 두 칸이면 "룸2-1·2"', await ev("tablesText(['R2-1','R2-2','R2-3']).join()")=='룸2' and await ev("tablesText(['R2-1','R2-2']).join()")=='룸2-1·2')
    ok('6) 없는 칸은 무시 (룸1-3, 룸9)', await ev("parseTables('r1-3').length")==0 and await ev("parseTables('r9').length")==0)
    ok('7) 룸3 은 한 칸뿐 → "r3" = 룸3-1', await ev("parseTables('r3').join()")=='R3-1')
    ok('8) 숫자 테이블과 섞어도 됨 "3 r2"', await ev("parseTables('3 r2').join()")=='3,R2-1,R2-2,R2-3')
    ok('   오류 없음', not errs, errs); await ctx.close()
  print('모두 통과' if not FAILS else '실패 있음: '+', '.join(FAILS))
asyncio.run(main())
