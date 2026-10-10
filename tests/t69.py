# 예약 붙여넣기: 취소·변경 알림이면 기존 예약을 찾아 자동 처리 + 되돌리기 (가짜 서버, 저장까지 흉내)
import asyncio, json, datetime, re
from urllib.parse import unquote
from playwright.async_api import async_playwright
NEW='bdqcrbnbuoujozlpttbe.supabase.co'; F1='ad2ffdae-f76b-44cd-a6c6-58514c4e4638'
def item(i,name,tm,tb,pp="4",phone=""): return {"id":"i%d"%i,"c":"2026-10-01","u":1790900000000+i,"pp":pp,"req":"","done":False,"name":name,"time":tm,"phone":phone,"tnote":"","tables":tb}
DB={"2026-10-11":{"rev":1,"items":[item(1,"우상태","17:30",["3"]),item(2,"다른손님","19:00",["5"])]},
    "2026-10-13":{"rev":1,"items":[item(3,"김철수","12:00",["2"]),item(4,"김철수","18:00",["4"])]}}
LAYOUT={"floors":[{"key":"1","name":"1층","groups":[{"title":"홀","cols":[["1","2","3"],["4","5"],["6","7"]]}]}]}
async def handler(r):
  u=unquote(r.request.url)
  if 'localhost' in u: return await r.continue_()
  if NEW not in u: return await r.fulfill(status=404,body='{}')
  J=lambda o,st=200: r.fulfill(status=st,content_type='application/json',body=json.dumps(o))
  if '/rpc/sch_my_stores' in u: return await J([{"id":F1,"name":"유천점","is_hq":False,"role":"owner","can_pay":True}])
  if '/rest/v1/sch_items' in u: return await J([{"data":LAYOUT}])
  if '/rest/v1/res_days' in u:
    m=re.search(r'id=eq\.(\d{4}-\d{2}-\d{2})',u); d=m.group(1) if m else None; meth=r.request.method
    if meth=='GET':
      if d: return await J([{"id":d,"rev":DB[d]["rev"],"data":{"items":DB[d]["items"]}}] if d in DB else []) if 'data' in u else await J([{"rev":DB[d]["rev"]}] if d in DB else [])
      return await J([{"id":k,"data":{"items":v["items"]}} for k,v in DB.items()])
    body=json.loads(r.request.post_data or '{}')
    if meth=='PATCH':
      base=int(re.search(r'rev=eq\.(\d+)',u).group(1))
      if DB[d]["rev"]!=base: return await J([])
      DB[d]={"rev":body["rev"],"items":body["data"]["items"]}; return await J([{"rev":body["rev"]}])
    if meth=='POST':
      DB[body["id"]]={"rev":body["rev"],"items":body["data"]["items"]}; return await J([{"rev":body["rev"]}])
  await J([])
S={"ses":{"access_token":"tok","refresh_token":"r","expires_at":int(datetime.datetime(2026,10,10,15,0).timestamp())+3000,"user":{"email":"x@ilpum.invalid"}}}
CXL="일품집 본점, 예약취소\n우상태님, 일품집 본점 예약, 2026.10.11.(일) 오후 5:30, 4명 (성인4), 예약이 취소되었습니다."
CHG="일품집 본점, 예약변경\n우상태님, 일품집 본점 예약, 2026.10.12.(월) 오후 6:00, 5명 (성인5), 예약이 변경되었습니다."
def live(d): return [x for x in DB.get(d,{"items":[]})["items"] if not x.get("deleted")]
async def main():
  ok=True
  def chk(n,c,x=''):
    nonlocal ok; ok&=bool(c); print('OK  ' if c else 'FAIL',n,x)
  async with async_playwright() as p:
    b=await p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
    ctx=await b.new_context(viewport={'width':1500,'height':900}); pg=await ctx.new_page(); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
    await pg.add_init_script("{ const _D=Date; const T=new _D('2026-10-10T15:00:00').getTime(); const st=_D.now(); class D extends _D{ constructor(...a){ if(!a.length) super(T+(_D.now()-st)); else super(...a); } static now(){ return T+(_D.now()-st); } } window.Date=D; }")
    await pg.route('**/*',handler); await pg.route_web_socket(f'wss://{NEW}/**',lambda ws: asyncio.ensure_future(ws.close()))
    await pg.add_init_script(f"try{{ localStorage.setItem('ilpum-fr-conf',{json.dumps(json.dumps(S))}); }}catch(e){{}}")
    await pg.goto('http://localhost:8765/reserve.html'); await pg.wait_for_timeout(2500)
    async def paste(t):
      await pg.evaluate("()=>{ const d=document.getElementById('qPasteBox'); if(d) d.open=true; }")
      await pg.fill('#qPaste',''); await pg.fill('#qPaste',t); await pg.wait_for_timeout(2500)
      return await pg.inner_text('#qPasteRes')
    # 1) 취소
    m=await paste(CXL)
    w=[x for x in live("2026-10-11") if x["name"]=="우상태"]
    chk('취소 알림 → 서버 예약에 취소 표시', w and '취소' in w[0]["tnote"], str(w)+' | '+m)
    chk('다른 손님은 그대로', [x["tnote"] for x in live("2026-10-11") if x["name"]=="다른손님"]==[""])
    chk('입력 칸은 안 채움(새 예약 아님)', await pg.input_value('#qName')=='')
    chk('그 날짜로 이동', await pg.evaluate("ui.date")=='2026-10-11')
    await pg.click('[data-nundo]'); await pg.wait_for_timeout(1500)
    w=[x for x in live("2026-10-11") if x["name"]=="우상태"]
    chk('되돌리기 → 취소 풀림', w and '취소' not in w[0]["tnote"], str(w))
    # 2) 변경 (날짜 이동 + 인원·시간)
    m=await paste(CHG)
    old=[x for x in live("2026-10-11") if x["name"]=="우상태"]; new=[x for x in live("2026-10-12") if x["name"]=="우상태"]
    chk('변경 → 10/11에서 빠지고 10/12 18:00 5명으로', not old and new and new[0]["time"]=='18:00' and new[0]["pp"]=='5', str(new)+' | '+m)
    m2=await paste(CHG+" ")
    chk('같은 변경을 다시 붙이면 "이미 반영"', '이미 반영' in m2 and len([x for x in live("2026-10-12") if x["name"]=="우상태"])==1, m2)
    # 3) 후보 여러 개 → 고르기
    m=await paste("김철수님, 일품집 본점 예약, 2026.10.13.(화), 예약이 취소되었습니다.")
    n=await pg.evaluate("document.querySelectorAll('#qPasteRes [data-ncand]').length")
    chk('같은 날 김철수 2건 → 고르기 버튼 2개, 자동 취소 안 함', n==2 and all('취소' not in x["tnote"] for x in live("2026-10-13")), m)
    await pg.click('#qPasteRes [data-ncand="1"]'); await pg.wait_for_timeout(1500)
    chk('고른 18:00 예약만 취소', [(x["time"],'취소' in x["tnote"]) for x in live("2026-10-13")]==[("12:00",False),("18:00",True)], str(live("2026-10-13")))
    # 4) 요청사항에 "취소" 글자가 있어도 새 예약으로 처리
    r=await pg.evaluate("t=>parseResText(t,'2026-10-10')", "박영희님 10/20 6시 2명\n요청사항 : 늦으면 취소될 수 있나요")
    chk('요청사항 속 "취소"는 무시', not r['cancel'] and not r['change'] and r['req']=='늦으면 취소될 수 있나요', str(r))
    # 5) 없는 예약 취소
    m=await paste("없는사람님, 일품집 본점 예약, 2026.10.11.(일) 오후 5:30, 예약이 취소되었습니다.")
    chk('못 찾으면 안내만', '찾지 못했어요' in m, m)
    chk('오류 없음', not errs, str(errs)); await ctx.close(); await b.close()
  print('전체 OK' if ok else '실패 있음')
asyncio.run(main())
