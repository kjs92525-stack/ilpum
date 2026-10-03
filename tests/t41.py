# 유천점 이전 도구(yucheon-import.html): 본사 로그인 → 유천점 서버 읽기 → 새 서버 유천점 칸에 합쳐 넣기 (가짜 서버)
import asyncio, json
from playwright.async_api import async_playwright
NEW='bdqcrbnbuoujozlpttbe.supabase.co'; YC='yc.supabase.co'; BON='0134d989-757a-4b60-9cb3-93245de2cac8'; YU='ad2ffdae-f76b-44cd-a6c6-58514c4e4638'
SCH={"staff":[{"id":"s1","name":"김사장","pos":"홀","kind":"fixed","off":[1]}],"ex":[{"id":"e1","type":"당일알바","date":"2026-10-03","name":"알바","pos":"홀","memo":"6.5"}],"rules":[],"dc":{},"notes":{},"aw":{}}
RES=[{"id":"2026-10-03","rev":3,"data":{"items":[{"id":"a","u":5,"name":"새예약","time":"18:00","pp":"4","tables":["3"]},{"id":"b","u":2,"name":"예전쪽","time":"19:00","pp":"2","tables":[]}]}}]
EXIST_RES={"2026-10-03":{"id":"2026-10-03","rev":2,"data":{"items":[{"id":"b","u":9,"name":"새시스템에서수정","time":"19:00","pp":"2","tables":["5"]}]}}}
WR=[]
async def h(r):
  u=r.request.url; m=r.request.method
  if 'localhost' in u: return await r.continue_()
  J=lambda o,st=200: r.fulfill(status=st,content_type='application/json',body=json.dumps(o))
  if YC in u:
    if 'schedule_state' in u: return await J([{"data":SCH,"rev":4}])
    if 'reservations_day' in u: return await J(RES if 'offset=0' in u else [])
    return await J([],404)
  if NEW in u:
    if '/auth/v1/token' in u: return await J({"access_token":"tok","user":{"email":"ilpum@ilpum.invalid"}})
    if '/rpc/sch_my_stores' in u: return await J([{"id":BON,"name":"본점","is_hq":True,"role":"hq"},{"id":YU,"name":"유천점","is_hq":False,"role":"hq"}])
    if '/rest/v1/sch_items' in u:
      if m=='GET': return await J([])
      WR.append(('sch',json.loads(r.request.post_data))); return await r.fulfill(status=201,body='')
    if '/rest/v1/res_days' in u:
      if m=='GET': return await J(list(EXIST_RES.values()))
      WR.append(('res',json.loads(r.request.post_data))); return await r.fulfill(status=201,body='')
  await J([])
async def main():
  ok=True
  def chk(n,c):
    nonlocal ok; ok&=bool(c); print(('OK  ' if c else 'FAIL'),n)
  async with async_playwright() as p:
    b=await p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome'); ctx=await b.new_context(accept_downloads=True); pg=await ctx.new_page(); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
    await pg.route('**/*',h); await pg.goto('http://localhost:8766/yucheon-import.html')
    await pg.fill('#upw','x'); await pg.click('#bLogin'); await pg.wait_for_timeout(500)
    chk('로그인 → 가맹점(유천점)만 목록에', await pg.evaluate("[...document.querySelectorAll('#store option')].map(o=>o.textContent)")==['유천점'])
    await pg.fill('#yurl','https://yc.supabase.co'); await pg.fill('#ykey','eyJkey')
    async with pg.expect_download() as dl: await pg.click('#bRead')
    d=await dl.value; chk('읽은 내용이 백업 파일로 저장됨', d.suggested_filename.startswith('유천점_백업_'))
    await pg.wait_for_timeout(300); chk('요약: 직원 1명 · 예약 1일', '1명' in await pg.inner_text('#sum') and '1일' in await pg.inner_text('#sum'))
    await pg.click('#bGo'); await pg.wait_for_timeout(800)
    sch=[x for k,x in WR if k=='sch'][0]; res=[x for k,x in WR if k=='res'][0]
    chk('근무표가 유천점 칸(store_id)으로 들어감', all(x['store_id']==YU for x in sch) and {x['kind'] for x in sch}>={'staff','spot','cfg'})
    chk('본점 칸에는 아무것도 안 씀', not any(x['store_id']==BON for x in sch+res))
    items={i['id']:i for i in res[0]['data']['items']}
    chk('예약: 새 시스템에서 고친 b(u=9)는 유지, 예전에만 있던 a 추가', items['b']['name']=='새시스템에서수정' and 'a' in items and res[0]['rev']==3)
    chk('끝 안내', '끝났어요' in await pg.inner_text('#res'))
    chk('오류 없음', not errs)
  print('전체','OK' if ok else 'FAIL')
asyncio.run(main())
