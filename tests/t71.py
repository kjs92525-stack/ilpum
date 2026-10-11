# 태블릿 배터리 교체 알림: 휴지통 밑 '배터리', 누른 날+2일 저녁 7시에 빨간색 (가짜 서버)
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
    ctx,pg,errs=await run(b, '/tmp/batt.png' if len(sys.argv)>1 else None)
    pos=await pg.evaluate("(()=>{const a=document.getElementById('trashBtn').getBoundingClientRect(),c=document.getElementById('battBtn').getBoundingClientRect();return {below:c.top>=a.bottom-1,center:Math.abs((a.left+a.right)/2-(c.left+c.right)/2)<8,txt:document.getElementById('battBtn').textContent}})()")
    chk('휴지통 밑에 "배터리" 버튼', pos['below'] and pos['center'] and pos['txt']=='배터리', str(pos))
    due=await pg.evaluate("(()=>{localStorage.setItem('ilpum-battery',String(new Date(2026,9,12,18,0).getTime()));const d=battDue();return [d.getMonth()+1,d.getDate(),d.getHours(),d.getMinutes()]})()")
    chk('12일 오후 6시에 누르면 14일 저녁 7시', due==[10,14,19,0], str(due))
    await pg.evaluate("localStorage.setItem('ilpum-battery',String(Date.now()-3*864e5)); battPaint()")
    chk('기한 지나면 빨간색', await pg.evaluate("document.getElementById('battBtn').classList.contains('due')") and '교체' in await pg.inner_text('#battBtn'))
    await pg.click('#battBtn'); await pg.wait_for_timeout(300)
    chk('누르면 오늘/어제 고르는 창', await pg.is_visible('[data-batt="0"]') and await pg.is_visible('[data-batt="1"]'))
    await pg.click('[data-batt="0"]'); await pg.wait_for_timeout(300)
    st=await pg.evaluate("[document.getElementById('battBtn').classList.contains('due'), Date.now()-(+localStorage.getItem('ilpum-battery'))]")
    chk('오늘 → 다시 보통 색 + 지금 시각 기록', (not st[0]) and st[1]<5000, str(st))
    await pg.click('#battBtn'); await pg.wait_for_timeout(300); await pg.click('[data-batt="1"]'); await pg.wait_for_timeout(300)
    r=await pg.evaluate("(()=>{const d=battDue(),e=new Date();e.setDate(e.getDate()+1);return [d.getDate()===e.getDate(),d.getHours()]})()")
    chk('어제 뺐어요 → 내일 저녁 7시 (어제+2일)', r==[True,19], str(r))
    await pg.evaluate("localStorage.setItem('ilpum-battery','123')")
    await pg.click('#battBtn'); await pg.wait_for_timeout(300); await pg.click('#dlgBody [data-d="close"]'); await pg.wait_for_timeout(300)
    chk('닫기 누르면 기록 안 바뀜', await pg.evaluate("localStorage.getItem('ilpum-battery')")=='123')
    chk('오류 없음', not errs, str(errs)); await ctx.close(); await b.close()
  print('전체 OK' if ok else '실패 있음')
asyncio.run(main())
