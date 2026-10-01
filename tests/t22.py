# 전송량 점검: 가짜 시계로 몇 시간을 빨리 돌려서, 켜 둔 화면이 서버에 몇 번·몇 KB 요청하는지 센다 (가짜 서버)
# 실행 전: cd dist && python3 -m http.server 8765
import asyncio, json, time
from playwright.async_api import async_playwright
NEW='bdqcrbnbuoujozlpttbe.supabase.co'; F1='ad2ffdae-f76b-44cd-a6c6-58514c4e4638'
STAT={'n':0,'bytes':0,'by':{}}
BIG=[{"kind":"staff","id":f"s{i}","data":{"name":"직원"+str(i),"pos":"홀","type":"regular","off":[],"active":True,"order":i,"memo":"x"*300}} for i in range(150)]+[{"kind":"cfg","id":"positions","data":[{"name":"홀","color":"#2F6B3F","req":[0]*7}]}]
DAY={"data":{"items":[{"id":f"r{i}","name":"손님"+str(i),"time":"18:00","pp":"2","tables":[],"req":"메모"*20,"u":1} for i in range(40)]},"rev":7}
async def handler(r):
  u=r.request.url
  if 'localhost' in u: return await r.continue_()
  if NEW not in u: return await r.fulfill(status=404,body='{}')
  J=lambda o: r.fulfill(status=200,content_type='application/json',body=json.dumps(o))
  if '/rpc/sch_my_stores' in u: body=[{"id":F1,"name":"가맹점 1","is_hq":False,"role":"owner","can_pay":True}]
  elif '/sch_items' in u: body=[] if 'updated_at=gt' in u else BIG
  elif '/res_days' in u: body=[{"rev":7}] if 'select=rev' in u else [DAY]
  else: body=[]
  s=json.dumps(body); k=u.split('/rest/v1/')[-1].split('?')[0]; STAT['n']+=1; STAT['bytes']+=len(s)+700; STAT['by'][k]=STAT['by'].get(k,0)+1   # 700 = 헤더 대략
  await J(body)
S={"ses":{"access_token":"tok","refresh_token":"r","expires_at":int(time.time())+999999,"user":{"email":"x@ilpum.invalid"}}}
async def measure(b,page,hours,active_every_min):
  ctx=await b.new_context(viewport={'width':1200,'height':800}); pg=await ctx.new_page()
  await pg.route('**/*',handler)
  await pg.add_init_script(f"try{{ localStorage.setItem('ilpum-fr-conf',{json.dumps(json.dumps(S))}); }}catch(e){{}}")
  await pg.clock.install(); await pg.goto(f'http://localhost:8765/{page}'); await pg.wait_for_timeout(1500)
  STAT.update(n=0,bytes=0,by={})
  for m in range(hours*60):
    await pg.clock.run_for(60000)
    if active_every_min and m%active_every_min==0: await pg.mouse.click(5,5)
    await pg.wait_for_timeout(5)
  res=(STAT['n'],round(STAT['bytes']/1024), dict(STAT['by'])); await ctx.close(); return res
async def main():
  async with async_playwright() as p:
    b=await p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
    for page,label in [('index.html#dash','오늘 현황(통합 틀)'),('ilpum-schedule.html','근무표'),('reserve.html','예약')]:
      idle=await measure(b,page,3,0); busy=await measure(b,page,1,5)
      print(f'{label}: 3시간 켜 두고 아무도 안 만지면 → 요청 {idle[0]}번 / {idle[1]}KB {idle[2]}')
      print(f'{" "*len(label)}  1시간 계속 쓰면(5분마다 터치) → 요청 {busy[0]}번 / {busy[1]}KB {busy[2]}')
asyncio.run(main())
