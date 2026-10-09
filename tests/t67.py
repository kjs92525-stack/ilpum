# 요청사항(메모)에 '10%' 가 있으면 현황판 칸 왼쪽 위에 작은 10% 꼬리표 (칸 배치·자유 배치, 100%·10명 등은 제외) (가짜 서버)
import asyncio, json, time, datetime, sys
from playwright.async_api import async_playwright
NEW='bdqcrbnbuoujozlpttbe.supabase.co'; F1='ad2ffdae-f76b-44cd-a6c6-58514c4e4638'
TODAY=datetime.date.today().isoformat()
def item(i,name,tm,tb,req="",u=0): return {"id":"i%d"%i,"c":TODAY,"u":1790900000000+i,"pp":"4","req":req,"done":False,"name":name,"time":tm,"phone":"010-1111-2222","tnote":"","tables":tb}
ITEMS=[item(1,"할인손님","18:00",["3"],"10% 이벤트"),item(2,"붙여씀","18:30",["4"],"생일 10%할인"),item(3,"메모없음","19:00",["5"]),
       item(4,"백퍼","19:30",["7"],"100% 환불"),item(5,"열명","20:00",["8"],"10명 단체"),item(6,"전각","18:00",["9"],"10 ％"),item(7,"도착손님","18:15",["10"],"10%"),item(8,"예약금도","18:20",["11"],"예약금 5만원(입완) 10%")]
ITEMS[6]["done"]=True
MODE={'v':'grid'}
GRID={"floors":[{"key":"1","name":"1층","groups":[{"title":"홀","cols":[[3,4,5],[7,8],[9,10],[11,12],[13,14]]}]}]}
FREE={"floors":[{"key":"1","mode":"free","name":"홀","tables":[{"id":str(i),"x":20+(i-3)*100,"y":60,"w":100,"h":100,"shape":"round"} for i in (3,4,5,7,8,9,10,11,12,13,14)]}]}
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
      await pg.click('.res .rtime'); await pg.wait_for_timeout(800)
      if len(sys.argv)>1: await pg.screenshot(path=f'/tmp/pct_{mode}.png')
      cells=await pg.evaluate("[...document.querySelectorAll('#boardPanel .cell')].filter(c=>c.querySelector('.cn')).map(c=>{ const b=c.querySelector('.pctb'), r=b&&b.getBoundingClientRect(), cr=c.getBoundingClientRect(); return {n:c.querySelector('.cn').textContent.trim(),p:b?b.textContent:'',inside:!!b&&r.left>=cr.left-1&&r.right<=cr.right+1&&r.top>=cr.top-1&&r.bottom<=cr.bottom+1,left:!!b&&(r.left-cr.left)<cr.width/2}; })")
      c={x['n']:x for x in cells}
      yes=['할인손님','붙여씀','전각','도착손님','예약금도']; no=['메모없음','백퍼','열명']
      chk(f'[{mode}] 10% 칸에만 꼬리표', all(c.get(n,{}).get('p')=='10%' for n in yes) and not any(c.get(n,{}).get('p') for n in no), str(cells))
      chk(f'[{mode}] 꼬리표가 칸 안에 있음', all(c[n]['inside'] for n in yes), str([(n,c[n]) for n in yes]))
      if mode=='grid': chk('[grid] 왼쪽에 붙음', all(c[n]['left'] for n in yes))
      chk(f'[{mode}] 오류 없음', not errs, str(errs)); await ctx.close()
    await b.close()
  print('전체 OK' if ok else '실패 있음')
asyncio.run(main())
