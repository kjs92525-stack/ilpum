# 근무·급여 집계기(pay.html): 칸 해석 규칙 검증 + 시트 불러오기(가짜 Apps Script) + 설정이 서버(calc:agg)에 저장돼 다른 기기에서도 보임 (가짜 서버)
import asyncio, json, time, urllib.parse
from playwright.async_api import async_playwright
NEW='bdqcrbnbuoujozlpttbe.supabase.co'; BON='0134d989-757a-4b60-9cb3-93245de2cac8'
SHEET='https://script.google.com/macros/s/TEST/exec'
SRV={}; LOG=[]; SHEETREQ=[]
def row(a,b,*c): return [a,b]+list(c)+['']*(14-2-len(c))
VALUES=[row('날짜','포지션','이름'),
 row('2026-10-05(월)','카운터','황거만(오후)6.5','박미화(종일)13','서은미7.0','강윤선오후)'),
 row('','홀','준성','홍준성','민호(5시출)','민혁(5~7당일지급'),
 row('','주방','민호휴무','민혁장치금지','규하씨 16일 출근x','진현 : X','연순 19,20 오후 24 토요일 종일'),
 row('','장치','장잡 : 실장,2팀 / 배송 : 이황우 / 달서지원 : 김지수'),
 row('2026-10-06(화)','카운터','황거만(오후)6.5','3','=COUNTA','1팀장'),
 row('','홀','','','','','','','','','','엘열씨'),
 ]
VALUES[6][12]='메모무시'; VALUES[6][13]='김무시'      # M열·N열은 읽지 않음, L열(index 11)은 읽음
async def handler(r):
  u=urllib.parse.unquote(r.request.url); m=r.request.method
  if 'localhost' in u: return await r.continue_()
  if 'script.google.com' in u:
    SHEETREQ.append(u); return await r.fulfill(status=200,content_type='application/json',headers={'access-control-allow-origin':'*'},body=json.dumps({"ok":True,"values":VALUES}))
  if NEW not in u: return await r.fulfill(status=404,body='{}')
  J=lambda o,sv=200: r.fulfill(status=sv,content_type='application/json',body=json.dumps(o))
  if '/rpc/pay_pin_status' in u: return await J({"has":True,"locked":0})
  if '/rpc/pay_pin_check' in u: return await J('ok')
  if '/rpc/sch_my_stores' in u: return await J([{"id":BON,"name":"일품집 본점","is_hq":True,"role":"hq","can_pay":True}])
  if '/rest/v1/sch_items' in u:
    if m=='POST':
      rows=json.loads(r.request.post_data)
      for x in rows: SRV[x['id']]={"data":x['data']}; LOG.append(x['id'])
      return await J([],201)
    if 'id=eq.calc:agg' in u: return await J([SRV['calc:agg']] if 'calc:agg' in SRV else [])
    return await J([])
  await J([])
S={"ses":{"access_token":"tok","refresh_token":"r","expires_at":int(time.time())+10**8,"user":{"email":"x@ilpum.invalid"}}}
async def open_dev(b):
  ctx=await b.new_context(viewport={'width':420,'height':900}); pg=await ctx.new_page(); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
  await pg.route('**/*',handler)
  await pg.add_init_script(f"try{{ if(!sessionStorage.getItem('__i')){{ sessionStorage.setItem('__i','1'); localStorage.setItem('ilpum-fr-conf',{json.dumps(json.dumps(S))}); }} }}catch(e){{}}")
  await pg.goto('http://localhost:8765/pay.html'); await pg.wait_for_selector('#pinForm'); await pg.fill('.pinin','1234'); await pg.press('.pinin','Enter')
  await pg.wait_for_selector('#ui:not([hidden])'); await pg.wait_for_timeout(300)
  return ctx,pg,errs
async def main():
  ok=True
  def chk(n,c,x=''):
    nonlocal ok; ok&=bool(c); print('OK  ' if c else 'FAIL',n,x)
  async with async_playwright() as p:
    b=await p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
    ctx,pg,errs=await open_dev(b)
    # 1) 칸 해석 규칙
    def case(txt):
      return pg.evaluate("t=>parseCell(t).map(e=>({name:e.name,kind:e.kind,hours:e.hours,won:e.won,tags:e.tags,list:e.list}))",txt)
    c=await case("황거만(오후)6.5"); chk('황거만(오후)6.5 → 오후 65,000',c[0]['kind']=='h' and c[0]['won']==65000 and c[0]['name']=='황거만',c)
    c=await case("박미화(종일)13"); chk('박미화(종일)13 → 종일 130,000',c[0]['kind']=='f' and c[0]['won']==130000,c)
    c=await case("서은미7.0"); chk('서은미7.0 → 오후 70,000',c[0]['kind']=='h' and c[0]['won']==70000 and c[0]['name']=='서은미',c)
    c=await case("민호(5시출)"); chk('민호(5시출) → 5시간',c[0]['hours']==5,c)
    c=await case("민호(12시출"); chk('민호(12시출 → 종일 10시간',c[0]['kind']=='f' and c[0]['hours']==10,c)
    c=await case("민호(오후)6시출"); chk('민호(오후)6시출 → 오후 4시간',c[0]['kind']=='h' and c[0]['hours']==4,c)
    c=await case("민혁(5~7당일지급"); chk('민혁(5~7당일지급 → 2시간 당일지급',c[0]['hours']==2 and '당일지급' in c[0]['tags'],c)
    c=await case("권민서(11~7"); chk('권민서(11~7 → 8시간',c[0]['hours']==8,c)
    c=await case("김재민(종일)8시퇴근"); chk('김재민(종일)8시퇴근 → 9시간',c[0]['hours']==9 and c[0]['kind']=='f',c)
    c=await case("승엽(휴무지급)"); chk('승엽(휴무지급) → 휴무지급 0시간(시간 없음)',c[0]['kind']=='off' and not c[0]['hours'],c)
    c=await case("김재민(달서지급"); chk('김재민(달서지급 → 달서지급 태그',c[0]['tags']==['달서지급'],c)
    c=await case("정미옥(오후6.5(17:10도착)"); chk('정미옥(오후6.5(17:10도착) → 오후 65,000 (17:10 무시)',c[0]['kind']=='h' and c[0]['won']==65000 and c[0]['hours'] is None,c)
    c=await case("한수연(오후금일괄)"); chk('한수연(오후금일괄) → 오후 일괄',c[0]['kind']=='h' and '일괄' in c[0]['tags'] and c[0]['name']=='한수연',c)
    c=await case("강윤선오후)"); chk('강윤선오후) → 이름 강윤선 + 오후',c[0]['name']=='강윤선' and c[0]['kind']=='h',c)
    c=await case("1팀장"); chk('1팀장 → 1팀',c[0]['name']=='1팀',c)
    c=await case("17:10도착"); chk('17:10도착만 있으면 무시',c==[],c)
    for memo in ["민호휴무","민혁장치금지","규하씨 16일 출근x","강윤선:원,수 오후/토,일 종일","진현 : X","연순 19,20 오후 24 토요일 종일"]:
      chk('메모 건너뜀: '+memo, await case(memo)==[])
    c=await case("장잡 : 실장,2팀 / 배송 : 이황우 / 달서지원 : 김지수")
    chk('장잡·배송·달서지원 칸 → 실장,2팀,이황우,김지수',sorted(x['name'] for x in c)==sorted(['실장','2팀','이황우','김지수']) and {x['list'] for x in c}=={'장잡','배송','달서지원'},c)
    c=await case("장잡 : 실장,2팀\n배송 : 이황우\n달서지원 : 김지수"); chk('줄바꿈으로 쓴 같은 칸도 읽음',len(c)==4,c)
    # 2) 시트 불러오기
    await pg.click('#btnSheet'); await pg.wait_for_timeout(300)
    chk('주소 없이 누르면 안내(요청 없음)', not SHEETREQ and await pg.evaluate("document.getElementById('setDet').open"))
    await pg.fill('#sUrl',SHEET); await pg.press('#sUrl','Tab'); await pg.click('#btnSheet'); await pg.wait_for_timeout(800)
    chk('action=schedule 로 요청', SHEETREQ and 'action=schedule' in SHEETREQ[0] and SHEETREQ[0].startswith(SHEET), SHEETREQ)
    chk('기간 카드·결과가 뜸', await pg.is_visible('#periodCard') and await pg.is_visible('#resCard'))
    d=await pg.evaluate("[dFrom.value,dTo.value]"); chk('기간 = 시트의 첫~마지막 날짜', d==['2026-10-05','2026-10-06'], d)
    names=await pg.evaluate("results.map(r=>r.name).sort()")
    chk('M열 이후 메모·수식 숫자는 안 읽고 L열은 읽음', '김무시' not in names and '메모무시' not in names and '엘열' in names, names)
    chk('이름 모음', set(['황거만','박미화','서은미','강윤선','준성','홍준성','민호','민혁','실장','2팀','이황우','김지수','1팀'])<=set(names), names)
    sug=await pg.inner_text('#sugs'); chk('준성 = 홍준성 합치기 제안', '준성' in sug and '홍준성' in sug)
    cards=await pg.inner_text('#cards'); chk('요약 카드 6개', await pg.locator('#cards .sc').count()==6, cards)
    # 황거만: 이틀 다 오후 6.5 → 130,000
    h=await pg.evaluate("(()=>{const r=results.find(x=>x.name==='황거만');return [r.type,r.total,r.cnt,r.h]})()"); chk('황거만 일당 130,000 (2일, 오후2)', h==['일당',130000,2,2], h)
    # 3) 합치기·지급방식 저장 → 서버 calc:agg
    await pg.click('#sugs button.primary'); await pg.wait_for_timeout(300)
    chk('합치기 후 홍준성 한 사람', await pg.evaluate("results.filter(r=>r.name==='홍준성').length==1 && !results.some(r=>r.name==='준성')"))
    await pg.evaluate("setP('민호','type','시급')"); await pg.evaluate("compute()")
    await pg.fill('#sWage','11000'); await pg.press('#sWage','Tab'); await pg.fill('#sCol','K'); await pg.press('#sCol','Tab'); await pg.wait_for_timeout(300)
    chk('마지막 열 K 로 바꾸면 L열 이름 빠짐', '엘열' not in await pg.evaluate("results.map(r=>r.name)"))
    await pg.wait_for_timeout(2500)
    sv=SRV.get('calc:agg',{}).get('data',{})
    chk('서버(calc:agg)에 저장됨', sv.get('alias')=={'준성':'홍준성'} and sv.get('people',{}).get('민호',{}).get('type')=='시급' and sv.get('wage')==11000 and sv.get('url')==SHEET and sv.get('col')=='K', sv)
    chk('localStorage 에는 집계기 설정 안 둠', not await pg.evaluate("Object.keys(localStorage).some(k=>/payagg|ilpum-pay/.test(k))"))
    # 4) 복사 텍스트
    st=await pg.evaluate("summaryText()"); dt=await pg.evaluate("dayText()")
    chk('요약 복사 머리글', st.split('\n')[1]=='이름\t지급방식\t근무일\t종일\t오후\t오전\t휴무지급\t총시간\t일당합계\t시급지급\t총지급액\t금액없는날', st[:200])
    chk('일자별 복사 머리글', dt.split('\n')[0]=='날짜\t이름\t지급방식\t구분\t시간\t지급액\t근거\t스케줄 원문' and '2026-10-05\t황거만\t일당\t오후' in dt, dt[:300])
    chk('시급 민호: 5시간×11,000 = 55,000', await pg.evaluate("results.find(r=>r.name==='민호').total")==55000)
    chk('오류 없음', not errs, errs); await ctx.close()
    # 5) 다른 기기: 서버 설정이 그대로 보임
    ctx2,pg2,errs2=await open_dev(b)
    v=await pg2.evaluate("[S.alias,S.people['민호'],S.wage,S.url,document.getElementById('sUrl').value]")
    chk('다른 기기에서도 같은 설정', v[0]=={'준성':'홍준성'} and v[1]['type']=='시급' and v[2]==11000 and v[3]==SHEET and v[4]==SHEET, v)
    await pg2.click('#btnSheet'); await pg2.wait_for_timeout(700)
    chk('다른 기기에서 시트 불러오면 시급 설정 적용', await pg2.evaluate("results.find(r=>r.name==='민호').type")=='시급')
    chk('오류 없음(2)', not errs2, errs2); await ctx2.close(); await b.close()
  print('전체 OK' if ok else '실패 있음')
asyncio.run(main())
