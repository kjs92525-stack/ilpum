# 예약금 메모가 있는 예약은 목록과 현황판(칸 배치·자유 배치)에서 눈에 띔 / 없는 예약은 그대로 (가짜 서버)
import asyncio, json, time, datetime, sys
from playwright.async_api import async_playwright
NEW='bdqcrbnbuoujozlpttbe.supabase.co'; F1='ad2ffdae-f76b-44cd-a6c6-58514c4e4638'
TODAY=datetime.date.today().isoformat()
def item(i,name,tm,tb,req="",u=0): return {"id":"i%d"%i,"c":TODAY,"u":1790900000000+i,"pp":"4","req":req,"done":False,"name":name,"time":tm,"phone":"010-1111-2222","tnote":"","tables":tb}
ITEMS=[item(1,"예약금손님","18:00",["3"],"예약금 5만원(입완)"),item(2,"일반손님","18:30",["4"],"창가 자리"),item(3,"메모없음","19:00",["5"]),
       item(4,"둘다","19:30",["7"],"초1+아기2, 예약금(입완)"),item(5,"취소손님","20:00",["8"],"예약금 5만원"),
       item(6,"입금대기","18:00",["9"],"예약금 5만원 입금대기"),item(7,"입완만","18:15",["10"],"입완")]
ITEMS[4]["tnote"]="취소"
MODE={'v':'grid'}
GRID={"floors":[{"key":"1","name":"1층","groups":[{"title":"홀","cols":[[3,4,5],[7,8],[9,10]]}]}]}
FREE={"floors":[{"key":"1","mode":"free","name":"홀","tables":[{"id":str(i),"x":20+(i-3)*100,"y":60,"w":100,"h":100,"shape":"round"} for i in (3,4,5,7,8,9,10)]}]}
async def handler(r):
  u=r.request.url
  if 'localhost' in u: return await r.continue_()
  if NEW not in u: return await r.fulfill(status=404,body='{}')
  J=lambda o,st=200: r.fulfill(status=st,content_type='application/json',body=json.dumps(o))
  if '/rpc/sch_my_stores' in u: return await J([{"id":F1,"name":"유천점","is_hq":False,"role":"owner","can_pay":True}])
  if '/rest/v1/sch_items' in u: return await J([{"data":GRID if MODE['v']=='grid' else FREE}])
  if '/rest/v1/res_days' in u:
    if r.request.method=='GET': return await J([{"id":TODAY,"rev":3,"data":{"items":ITEMS}}] if 'select=data' in u else [{"rev":3}])
    return await J([{"rev":4}])
  await J([])
S={"ses":{"access_token":"tok","refresh_token":"r","expires_at":int(time.time())+3000,"user":{"email":"x@ilpum.invalid"}}}
async def run(b,shot=None):
  ctx=await b.new_context(viewport={'width':1500,'height':900}); pg=await ctx.new_page(); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
  await pg.route('**/*',handler); await pg.route_web_socket(f'wss://{NEW}/**',lambda ws: asyncio.ensure_future(ws.close()))
  await pg.add_init_script(f"try{{ localStorage.setItem('ilpum-fr-conf',{json.dumps(json.dumps(S))}); }}catch(e){{}}")
  await pg.goto('http://localhost:8765/reserve.html'); await pg.wait_for_timeout(2500)
  if shot: await pg.screenshot(path=shot)
  return ctx,pg,errs
async def main():
  ok=True
  def chk(n,c,x=''):
    nonlocal ok; ok&=bool(c); print('OK  ' if c else 'FAIL',n,x)
  async with async_playwright() as p:
    b=await p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
    for mode in ('grid','free'):
      MODE['v']=mode; ctx,pg,errs=await run(b, f'/tmp/dep_{mode}.png' if len(sys.argv)>1 else None)
      rows=await pg.evaluate("[...document.querySelectorAll('.res')].map(r=>({n:r.querySelector('.nm')?r.querySelector('.nm').textContent.trim():'',dep:r.classList.contains('dep'),q:!!r.querySelector('.rq.depq')}))")
      d={x['n']:x for x in rows}
      chk(f'[{mode}] 목록: 예약금 예약만 강조', d.get('예약금손님',{}).get('dep') and d.get('예약금손님',{}).get('q') and d.get('둘다',{}).get('dep') and not d.get('일반손님',{}).get('dep') and not d.get('메모없음',{}).get('dep') and not d.get('입금대기',{}).get('dep') and not d.get('입완만',{}).get('dep') and not d.get('취소손님',{}).get('dep'), str(rows))
      await pg.click('.res .rtime'); await pg.wait_for_timeout(800)
      if len(sys.argv)>1: await pg.screenshot(path=f'/tmp/dep_{mode}.png')
      cells=await pg.evaluate("[...document.querySelectorAll('#boardPanel .cell')].filter(c=>c.querySelector('.cn')).map(c=>({n:c.querySelector('.cn').textContent.trim(),dep:c.classList.contains('dep'),b:!!c.querySelector('.depb')}))")
      c={x['n']:x for x in cells}
      chk(f'[{mode}] 현황판: 예약금 칸만 강조', c.get('예약금손님',{}).get('dep') and c.get('예약금손님',{}).get('b') and c.get('둘다',{}).get('b') and not c.get('일반손님',{}).get('dep') and not c.get('메모없음',{}).get('dep') and not c.get('입금대기',{}).get('dep') and not c.get('입완만',{}).get('dep'), str(cells))
      chk(f'[{mode}] 오류 없음', not errs, str(errs)); await ctx.close()
    await b.close()
  print('전체 OK' if ok else '실패 있음')
asyncio.run(main())
