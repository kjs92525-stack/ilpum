# 예약 붙여넣기 자동 입력(네이버 알림·손님 문자) + 빈 테이블 추천 (가짜 서버)
import asyncio, json, time, datetime
from playwright.async_api import async_playwright
NEW='bdqcrbnbuoujozlpttbe.supabase.co'; F1='ad2ffdae-f76b-44cd-a6c6-58514c4e4638'
TODAY='2026-10-10'   # 토요일
def item(i,name,tm,tb,pp="4"): return {"id":"i%d"%i,"c":TODAY,"u":1790900000000+i,"pp":pp,"req":"","done":False,"name":name,"time":tm,"phone":"","tnote":"","tables":tb}
DAY12=[item(1,"먼저온손님","18:00",["1"]),item(2,"큰자리손님","19:00",["6"],"6")]
SAVED=[]; URLS=[]
LAYOUT={"floors":[{"key":"1","name":"1층","groups":[{"title":"홀","cols":[["1","2","3"],["4","5"],["6","7"]]}]},{"key":"r","name":"룸","groups":[{"title":"룸","cols":[["R1-1","R1-2"]]}]}],"seats":{"6":6,"7":6}}
async def handler(r):
  u=r.request.url; URLS.append(u)
  if 'localhost' in u: return await r.continue_()
  if NEW not in u: return await r.fulfill(status=404,body='{}')
  J=lambda o,st=200: r.fulfill(status=st,content_type='application/json',body=json.dumps(o))
  if '/rpc/sch_my_stores' in u: return await J([{"id":F1,"name":"유천점","is_hq":False,"role":"owner","can_pay":True}])
  if '/rest/v1/sch_items' in u: return await J([{"data":LAYOUT}])
  if '/rest/v1/res_days' in u:
    if r.request.method=='GET':
      day='2026-10-12' if '2026-10-12' in u else TODAY
      items=DAY12 if day=='2026-10-12' else []
      return await J([{"id":day,"rev":3,"data":{"items":items}}] if 'select=data' in u else [{"rev":3}])
    SAVED.append(r.request.post_data or ''); return await J([{"rev":4}])
  await J([])
S={"ses":{"access_token":"tok","refresh_token":"r","expires_at":int(datetime.datetime(2026,10,10,15,0).timestamp())+3000,"user":{"email":"x@ilpum.invalid"}}}
NAVER="""[네이버 예약] 새로운 예약이 접수되었습니다.
예약자명 : 홍길동
예약번호 : 1234567890
이용일시 : 2026.10.12.(월) 오후 6:30
상품명 : 장어 정식
인원 : 성인 4명, 어린이 1명
요청사항 : 아기의자 부탁드려요
연락처 : 010-1234-5678
결제금액 : 0원"""
CASES=[
 (NAVER, dict(date='2026-10-12',time='18:30',pp='4+1',name='홍길동',phone='010-1234-5678',req='아기의자 부탁드려요')),
 ("안녕하세요 10/12 저녁 7시에 4명 예약 가능할까요? 김철수 01098765432", dict(date='2026-10-12',time='19:00',pp='4',name='김철수',phone='010-9876-5432')),
 ("내일 6시반 3명 이영희입니다 010 2222 3333", dict(date='2026-10-11',time='18:30',pp='3',name='이영희',phone='010-2222-3333')),
 ("10월 15일 18시 성인6 아이2 박민수님", dict(date='2026-10-15',time='18:00',pp='6+2',name='박민수')),
 ("다음주 수요일 12시 2명 최지훈 010-5555-6666", dict(date='2026-10-14',time='12:00',pp='2',name='최지훈',phone='010-5555-6666')),
 ("일품집 본점, 예약신청\n우상태님, 일품집 본점 예약, 2026.10.11.(일) 오후 5:30, 4명 (성인4), 새로운 예약이 접수되었습니다.", dict(date='2026-10-11',time='17:30',pp='4',name='우상태',phone='',cancel=False)),
 ("일품집 본점, 예약취소\n우상태님, 일품집 본점 예약, 2026.10.11.(일) 오후 5:30, 4명 (성인4), 예약이 취소되었습니다.", dict(cancel=True,name='우상태',time='17:30')),
 ("일품집 본점, 예약신청\n김영수님, 일품집 본점 예약, 2026.10.12.(월) 오후 7:00, 6명 (성인4, 아동2), 새로운 예약이 접수되었습니다.", dict(date='2026-10-12',time='19:00',pp='4+2',name='김영수')),
 ("[네이버 예약] 예약이 취소되었습니다\n예약자명 : 홍길동\n이용일시 : 2026.10.12.(월) 오후 6:30", dict(cancel=True,name='홍길동')),
]
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
    # 1) 해석기
    for i,(txt,want) in enumerate(CASES):
      got=await pg.evaluate("t=>parseResText(t,'2026-10-10')", txt)
      bad={k:(got.get(k),v) for k,v in want.items() if got.get(k)!=v}
      chk(f'해석 {i+1}', not bad, str(bad) if bad else '')
    # 2) 화면: 붙여넣기 → 칸 채움·날짜 이동
    await pg.click('#qPasteBox summary'); await pg.fill('#qPaste', NAVER); await pg.wait_for_timeout(1200)
    v=await pg.evaluate("({n:qName.value,t:qTime.value,p:qPP.value,ph:qPhone.value,r:qReq.value,d:ui.date})")
    chk('칸 채움 + 날짜 10/12로 이동', v=={'n':'홍길동','t':'1830','p':'4+1','ph':'010-1234-5678','r':'아기의자 부탁드려요','d':'2026-10-12'}, str(v))
    res=await pg.inner_text('#qPasteRes'); chk('읽은 내용 안내', '10/12' in res and '옮겼어요' in res, res)
    # 3) 추천: 5명, 18:30 → 1번은 18:00 예약이라 제외, 6번은 19:00 예약이라 제외, 6인석 7번 추천
    sg=await pg.evaluate("[...document.querySelectorAll('#qprev .sugchip')].map(b=>b.dataset.sug)")
    chk('추천 칩에 바쁜 자리 없음', sg and '1' not in [x for s in sg for x in s.split()] and '6' not in [x for s in sg for x in s.split()], str(sg))
    chk('5명이면 6인석 7번이 먼저', sg and sg[0]=='7', str(sg))
    await pg.click('#qprev .sugchip >> nth=0'); await pg.wait_for_timeout(300)
    chk('칩 누르면 테이블 칸에 들어감', await pg.input_value('#qTables')=='7')
    chk('테이블 넣으면 추천 사라짐', await pg.evaluate("document.querySelectorAll('#qprev .sugchip').length")==0)
    # 2명이면 큰 자리(6·7) 대신 작은 자리 추천
    await pg.fill('#qTables',''); await pg.fill('#qPP','2'); await pg.wait_for_timeout(300)
    sg2=await pg.evaluate("[...document.querySelectorAll('#qprev .sugchip')].map(b=>b.dataset.sug)")
    chk('2명이면 작은 자리, 큰 자리·룸은 뒤로', sg2 and all(s in ('2','3','4','5') for s in sg2), str(sg2))
    await pg.fill('#qPP','4+1'); await pg.wait_for_timeout(200); await pg.click('#qprev .sugchip >> nth=0'); await pg.wait_for_timeout(200)
    n0=len(SAVED); await pg.press('#qName','Enter'); await pg.wait_for_timeout(1500)
    items=await pg.evaluate("items('2026-10-12').map(x=>[x.name,x.time,x.pp,x.tables.join(),x.phone,x.req])")
    chk('Enter로 10/12에 추가됨', ['홍길동','18:30','4+1','7','010-1234-5678','아기의자 부탁드려요'] in items, str(items))
    chk('추가 뒤 붙여넣기 칸 비움', await pg.input_value('#qPaste')=='' )
    # 4) 취소 문자 경고
    await pg.fill('#qPaste', [c for c in CASES if c[1].get('cancel')][-1][0]); await pg.wait_for_timeout(1000)
    chk('취소 문자 경고', '취소 안내' in await pg.inner_text('#qPasteRes'))
    await pg.fill('#qPaste', NAVER); await pg.wait_for_timeout(800)
    chk('이미 있는 예약 경고', '이미 있는 예약' in await pg.inner_text('#qPasteRes'), await pg.inner_text('#qPasteRes'))
    chk('오류 없음', not errs, str(errs)); await ctx.close(); await b.close()
  print('전체 OK' if ok else '실패 있음')
asyncio.run(main())
