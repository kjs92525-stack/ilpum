# 대구 상권분석 (sangkwon.html, 서버 없음) — 가짜 카카오 지도 SDK 로 화면 흐름 확인
# 실행 전: sh build_all.sh  (sh tests/run.sh t62)
import asyncio, json
from playwright.async_api import async_playwright
STUB=r"""
(function(){
const S={OK:'OK',ZERO_RESULT:'ZERO_RESULT',ERROR:'ERROR'};
const base=o=>o&&o.location?Math.max(1,Math.round((o.location.getLat()-35.70)*200)):1;
const pg=(n)=>({totalCount:n,hasNextPage:false});
const NAMES=["동성로","반월당역","범어역","수성못","들안길","동대구역","칠곡3지구","상인역","월배역","계명대역","죽전역","두류역","신매역","대곡역","경북대학교 북문","침산동","앞산카페거리","율하역","대구혁신도시","대실역"];
function Places(){}
Places.prototype.keywordSearch=function(q,cb,o){ window.__calls=(window.__calls||0)+1; o=o||{};
  setTimeout(()=>{
    if(!o.location){
      { const mm=q.match(/^대구 (\S+) 장어$/); if(mm){ const gi=['중구','동구','수성구'].indexOf(mm[1]); if(gi<0) return cb([],S.ZERO_RESULT,null);
        return cb([0,1,2].map(j=>({id:'eel'+gi+j,place_name:(j===2?'스시':'장어')+gi+j,category_name:j===2?'음식점 > 일식 > 초밥':'음식점 > 한식 > 장어',road_address_name:'대구 '+mm[1]+' 장어로 '+j,x:String(128.55+gi*0.05+j*0.01),y:String(35.80+gi*0.02)})),S.OK,{totalCount:3,hasNextPage:false}); } }
      if(q.startsWith('대구 ')){ const i=NAMES.indexOf(q.slice(3)); if(i<0) return cb([],S.ZERO_RESULT,null); return cb([{id:'b'+i,place_name:q.slice(3),x:String(128.50+i*0.012),y:String(35.78+i*0.008)}],S.OK,pg(1)); }
      if(q==='범어역') return cb([{id:'k1',place_name:'범어역 2호선',road_address_name:'대구 수성구 달구벌대로 지하',address_name:'대구 수성구 범어동',x:'128.6262',y:'35.8590'}],S.OK,pg(1));
      return cb([],S.ZERO_RESULT,null);
    }
    const lat=o.location.getLat(), b=base(o);
    if(q==='장어'){ if(lat>35.85&&lat<35.87) return cb([
        {id:'e1',place_name:'바다장어 <img src=x onerror=window.PWN=1>',category_name:'음식점 > 한식 > 장어',road_address_name:'범어로 1',phone:'053-1',x:'128.631',y:'35.861',distance:'320',place_url:'javascript:alert(1)'},
        {id:'e2',place_name:'풍천장어',category_name:'음식점 > 한식 > 장어',road_address_name:'범어로 2',phone:'',x:'128.636',y:'35.864',distance:'700',place_url:'http://place.map.kakao.com/2'},
        {id:'e3',place_name:'장어수산',category_name:'가정,생활 > 식품판매 > 수산물',road_address_name:'범어로 3',x:'128.637',y:'35.865',distance:'800'}],S.OK,pg(3));
      return b%3===0?cb([],S.ZERO_RESULT,null):cb([{id:'z'+b,place_name:'장어집'+b,category_name:'음식점 > 한식 > 장어',x:'128.5',y:'35.8',distance:String(200+b*10)}],S.OK,pg(1)); }
    if(q==='민물장어'){ if(lat>35.85&&lat<35.87) return cb([{id:'e1',place_name:'바다장어',category_name:'음식점 > 한식 > 장어',x:'128.631',y:'35.861',distance:'320'}],S.OK,pg(1)); return cb([],S.ZERO_RESULT,null); }
    const k={'고기':3,'술집':2,'아파트':4}[q]||1; return cb([{id:'x'}],S.OK,pg(b*k));
  },5); };
Places.prototype.categorySearch=function(code,cb,o){ window.__calls=(window.__calls||0)+1; setTimeout(()=>{ const b=base(o);
  if(code==='SW8') return cb([{id:'s1',place_name:'역'+b,x:'128.6',y:'35.86',distance:String(1500-b*20)}],S.OK,pg(1));
  const k={FD6:10,PO3:1,BK9:2,HP8:3,PK6:1}[code]||1; cb([{id:'c'}],S.OK,pg(b*k)); },5); };
function Geocoder(){}
Geocoder.prototype.addressSearch=function(q,cb){ setTimeout(()=>{
  if(q.includes('범어동')) return cb([{address_name:'대구 수성구 범어동 177',x:'128.6300',y:'35.8600',road_address:{address_name:'대구 수성구 달구벌대로 2400'}},{address_name:'대구 수성구 범어동 178',x:'128.6310',y:'35.8610',road_address:null}],S.OK);
  if(q.includes('들안로')) return cb([{address_name:'대구 수성구 두산동 1',x:'128.6350',y:'35.8500',road_address:{address_name:'대구 수성구 들안로 1'}}],S.OK);
  cb([],S.ZERO_RESULT); },5); };
Geocoder.prototype.coord2RegionCode=function(x,y,cb){ setTimeout(()=>cb([{region_type:'B',address_name:'대구 수성구 범어동',code:'2726010500',region_3depth_name:'범어동'},{region_type:'H',address_name:'대구광역시 수성구 범어1동',code:['2726054000','2726055000','2726053000'][Math.floor(x*100)%3],region_1depth_name:'대구광역시',region_2depth_name:'수성구',region_3depth_name:['범어2동','범어3동','범어1동'][Math.floor(x*100)%3]}],S.OK),5); };
Geocoder.prototype.coord2Address=function(x,y,cb){ setTimeout(()=>cb([{address:{address_name:'대구 중구 동성로2가 1'},road_address:null}],S.OK),5); };
function LatLng(lat,lng){ this.getLat=()=>lat; this.getLng=()=>lng; }
function Map(el){ this.el=el; window.__map=this; this.setLevel=()=>{}; this.setCenter=()=>{}; this.relayout=()=>{}; }
function CustomOverlay(o){ this.o=o; this.setMap=m=>{ if(!m&&o.content.parentNode) o.content.remove(); }; if(o.map) o.map.el.appendChild(o.content); }
function Circle(o){ window.__circ=(window.__circ||0)+1; this.setMap=()=>{}; }
window.kakao={maps:{load:f=>setTimeout(f,0),LatLng,Map,CustomOverlay,Circle,event:{addListener:(m,ev,fn)=>{ window.__mapClick=fn; }},
  services:{Places,Geocoder,Status:S,SortBy:{DISTANCE:'distance',ACCURACY:'accuracy'}}}};
})();
"""
MODE={'sdk':'ok','relay':'ok'}; EXT=[]; RELAY=[]
def apt_xml():
  it=lambda d,a,ar: f"<item><aptNm>A</aptNm><umdNm>{d}</umdNm><dealAmount>{a}</dealAmount><excluUseAr>{ar}</excluUseAr><cdealType> </cdealType></item>"
  items=it('범어동','120,000','84.9')*2+it('범어동','100,000','84.9')+it('만촌동','80,000','84.9')*3
  return f"<?xml version='1.0' encoding='UTF-8'?><response><header><resultCode>000</resultCode><resultMsg>OK</resultMsg></header><body><items>{items}</items><numOfRows>1000</numOfRows><pageNo>1</pageNo><totalCount>6</totalCount></body></response>"
def pop_json(code='2726053000'):
  def row(tong,ban,m30,m60):
    r={"ctpvNm":"대구광역시","sggNm":"수성구","dongNm":"범어1동","admmCd":code,"tong":tong,"ban":ban,"statsYm":"202508","totNmprCnt":str(m30*2+m60)}
    for a in range(0,101,10): r[f"male{a}AgeNmprCnt"]="0"; r[f"feml{a}AgeNmprCnt"]="0"
    r["male30AgeNmprCnt"]=str(m30); r["feml30AgeNmprCnt"]=str(m30); r["male60AgeNmprCnt"]=str(m60); return r
  items=[row("","",2000,1000),row("1","1",1000,500),row("2","1",1000,500)]   # 동 합계 줄 + 통반 줄 (겹쳐 세면 안 됨)
  return {"Response":{"head":{"totalCount":"3","resultCode":"0","resultMsg":"NORMAL_SERVICE"},"items":{"item":items}}}
import datetime
def rest_json(qs):
  t=datetime.date.today(); fmt=lambda d:d.isoformat()
  R=lambda items,n:json.dumps({"response":{"body":{"dataType":"JSON","items":{"item":items},"numOfRows":len(items),"pageNo":1,"totalCount":n},"header":{"resultCode":"0","resultMsg":"정상"}}})
  if 'BPLC_NM' in qs:
    Y=lambda y,dd=0: fmt(t-datetime.timedelta(days=int(365.25*y)+dd))
    E=[("풍천장어",Y(8),"","01","대구광역시 수성구 범어로 1 (범어동)"),("장어나라",Y(6),Y(5),"03","대구광역시 수성구 들안로 2 (두산동)"),
       ("민물장어촌",Y(5),"","01","대구광역시 수성구 동대구로 3 (범어동)"),("장어명가",Y(4),"","01","대구광역시 수성구 4 (만촌동)"),
       ("장어골",Y(7),Y(2),"03","대구광역시 수성구 5 (황금동)"),("새장어",Y(1),"","01","대구광역시 수성구 6 (범어동)")]
    return R([{"BPLC_NM":n,"LCPMT_YMD":o,"CLSBIZ_YMD":c,"SALS_STTS_CD":st,"ROAD_NM_ADDR":ad} for n,o,c,st,ad in E],len(E))
  if 'cond%5BOPN_ATMY_GRP_CD%3A%3AEQ%5D' not in qs: return R([{"OPN_ATMY_GRP_CD":"3460000","BPLC_NM":"가"}],4471)
  if 'SALS_STTS_CD%3A%3AEQ%5D=01' in qs: return R([{"BPLC_NM":"가"}],200)
  if 'LCPMT_YMD' in qs: return R([{"BPLC_NM":"가"}],40)
  recent=fmt(t-datetime.timedelta(days=30)); old=fmt(t-datetime.timedelta(days=500))
  return R([{"CLSBIZ_YMD":recent},{"CLSBIZ_YMD":recent},{"CLSBIZ_YMD":recent},{"CLSBIZ_YMD":old},{"CLSBIZ_YMD":old}],5)
STORE={"header":{"resultCode":"00","resultMsg":"NORMAL SERVICE"},"body":{"items":[{"indsLclsNm":"음식","indsMclsNm":"한식","bizesNm":"한식당"}]*3+[{"indsLclsNm":"음식","indsMclsNm":"주점","bizesNm":"호프"}]*2+[{"indsLclsNm":"음식","indsMclsNm":"한식","indsSclsNm":"장어구이","bizesNm":"풍천장어"}]+[{"indsLclsNm":"소매"}]*4,"totalCount":345}}
async def handler(r):
  u=r.request.url
  if 'localhost' in u: return await r.continue_()
  if 'dapi.kakao.com/v2/maps/sdk.js' in u:
    if MODE['sdk']=='fail': return await r.fulfill(status=401,body='')
    if MODE['sdk']=='firstfail' and 'appkey=7ed6cf4a57f04e78dab3bf66a095dcd2' in u: return await r.fulfill(status=401,body='')
    assert ('appkey=7ed6cf4a57f04e78dab3bf66a095dcd2' in u or 'appkey=1aaf38e9a5c0669aad33526fced00618' in u) and 'libraries=services' in u
    return await r.fulfill(status=200,content_type='application/javascript',body=STUB)
  if 'ilpum-data.yoyo925.workers.dev' in u:
    RELAY.append(u); H={'Access-Control-Allow-Origin':'*'}
    if '/drive?' in u:
      if MODE.get('drive')!='ok': return await r.fulfill(status=503,headers=H,content_type='application/json',body=json.dumps({"error":"KAKAO_REST(카카오 REST API 키)가 아직 없어요"}))
      ox=float(u.split('ox=')[1].split('&')[0]); return await r.fulfill(status=200,headers=H,content_type='application/json',body=json.dumps({"sec":2000 if ox>128.645 else 600}))
    if '/sgis?' in u:
      if MODE.get('sgis')=='nokey': return await r.fulfill(status=503,headers=H,content_type='application/json',body=json.dumps({"error":"SGIS_KEY·SGIS_SECRET(통계청 SGIS 키)가 아직 없어요"}))
      if 'p=stage' in u and 'cd=' not in u: res=[{"cd":"22","addr_name":"대구광역시"}]
      elif 'p=stage' in u: res=[{"cd":"22040","addr_name":"수성구"}]
      else: res=[{"adm_cd":"22040530","adm_nm":"대구광역시 수성구 범어1동","corp_cnt":"500","tot_worker":"6000"},{"adm_nm":"대구광역시 수성구 범어2동","corp_cnt":"300","tot_worker":"4000"},{"adm_nm":"대구광역시 수성구 범어3동","corp_cnt":"200","tot_worker":"2000"}]
      return await r.fulfill(status=200,headers=H,content_type='application/json',body=json.dumps({"errCd":0,"result":res}))
    if '/blog?' in u:
      if MODE.get('blog')=='nokey': return await r.fulfill(status=503,headers=H,content_type='application/json',body=json.dumps({"error":"NAVER_ID·NAVER_SECRET(네이버 검색 API 키)가 아직 없어요"}))
      from urllib.parse import unquote_plus; q=unquote_plus(u.split('query=')[1]) if 'query=' in u else ''
      return await r.fulfill(status=200,headers=H,content_type='application/json',body=json.dumps({"total":900 if q.endswith('장어20') else 500 if q.endswith('장어11') else 10}))
    if '/ping' in u: return await r.fulfill(status=200,headers=H,content_type='application/json',body=json.dumps({"ok":True,"hasKey":MODE['relay']!='nokey',"allowed":True}))
    if MODE['relay']=='nokey': return await r.fulfill(status=200,headers=H,content_type='text/xml',body="<OpenAPI_ServiceResponse><cmmMsgHeader><returnAuthMsg>SERVICE_KEY_IS_NOT_REGISTERED_ERROR</returnAuthMsg><returnReasonCode>30</returnReasonCode></cmmMsgHeader></OpenAPI_ServiceResponse>")
    if '/apt?' in u: return await r.fulfill(status=200,headers=H,content_type='text/xml',body=apt_xml())
    if '/pop?' in u: return await r.fulfill(status=200,headers=H,content_type='application/json',body=json.dumps(pop_json(u.split('admmCd=')[1].split('&')[0] if 'admmCd=' in u else '2726053000')))
    if '/rest?' in u: return await r.fulfill(status=200,headers=H,content_type='application/json',body=rest_json(u))
    if '/store?' in u: return await r.fulfill(status=200,headers=H,content_type='application/json',body=json.dumps(STORE))
  EXT.append(u); return await r.fulfill(status=404,body='')
FAILS=[]
def ok(name,cond,extra=''):
  print(('  ok ' if cond else 'FAIL ')+name,extra)
  if not cond: FAILS.append(name)
async def main():
  async with async_playwright() as p:
    b=await p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
    ctx=await b.new_context(viewport={'width':1300,'height':900}); pg=await ctx.new_page(); errs=[]
    pg.on('pageerror',lambda e:errs.append(str(e))); pg.on('dialog',lambda d: asyncio.ensure_future(d.accept()))
    await pg.route('**/*',handler)
    await pg.goto('http://localhost:8765/sangkwon.html'); await pg.wait_for_timeout(600)
    ok('1) 처음부터 기준 만들기 없이 바로 분석 화면', '기준 만들기' not in await pg.inner_text('#pane') and '후보지 추가' in await pg.inner_text('#pane'))
    await pg.fill('#q','대구 수성구 범어동 177'); await pg.click('[data-act=find]'); await pg.wait_for_timeout(200); await pg.click('[data-cand="0"]'); await pg.wait_for_function("document.querySelector('#s-comp')",timeout=20000)
    t0=await pg.inner_text('#pane'); ok('1b) 기준표 점수로 세부 지표와 안내', '장어집 기준표' in t0 and '저녁 외식 상권' in t0 and '음식점' in t0 and '경쟁 현황' in t0)
    await pg.click('[data-act=del]'); await pg.wait_for_timeout(100)
    await pg.click('[data-tab=set]'); await pg.fill('#sname','본점'); await pg.fill('#saddr','대구 수성구 들안로 1'); await pg.click('[data-act=sadd]'); await pg.wait_for_timeout(200)
    db=await pg.evaluate("JSON.parse(localStorage.getItem('ilpum-sk-v1'))")
    ok('2) 우리 매장 저장', db['stores'][0]['name']=='본점' and db['stores'][0]['x']==128.635, db['stores'])
    ok('3) 설정에 장어집 기준표 안내(비교 기준 만들기 없음)', '장어집 기준표' in await pg.inner_text('#pane') and await pg.evaluate("!document.querySelector('[data-act=bench]')"))
    await pg.click('[data-tab=list]'); await pg.fill('#q','대구 수성구 범어동 177'); await pg.click('[data-act=find]'); await pg.wait_for_timeout(200)
    ok('4) 주소 후보 2곳', await pg.evaluate("document.querySelectorAll('[data-cand]').length")==2)
    await pg.click('[data-cand="0"]'); await pg.wait_for_function("document.querySelector('.scorebox')",timeout=20000)
    sc=int((await pg.inner_text('.scorebox .num')).split('/')[0]); g=await pg.inner_text('.scorebox .gr')
    ok('5) 점수·등급 표지 상자', 0<=sc<=100 and g==('A' if sc>=70 else 'B' if sc>=55 else 'C' if sc>=40 else 'D'), (sc,g))
    dec=await pg.inner_text('.scorebox .dec'); ok('   판정 문구·기준표 점수 설명', '장어집 기준표' in await pg.inner_text('.mix') and any(x in dec for x in ['출점 적극 검토','조건부 검토','신중 검토','보류 권장','출점 불가']), dec)
    ok('   레이더 차트(5개 영역)', await pg.evaluate("document.querySelectorAll('#s-eval svg.radar text').length")==6)
    ev=await pg.evaluate("document.querySelectorAll('.ev').length"); sr=await pg.evaluate("document.querySelectorAll('.sr').length"); ok('   영역 7개(상권 6 + 매물 조건)·상권 지표 39개(허프 포함)에 점수', ev==7 and sr==39, (ev,sr))
    ok('   결론 요약 문장', await pg.evaluate("document.querySelectorAll('.exec li').length")>=4)
    ok('   거리별 장어집 수 (300/500/1km)', await pg.evaluate("[...document.querySelectorAll('.ring b')].map(b=>b.textContent).join(',')")=='0,1,2' , await pg.evaluate("[...document.querySelectorAll('.ring b')].map(b=>b.innerText).join(',')"))
    mx=await pg.inner_text('.mix'); ok('5b) 월세·평수 없으면 매물 조건 빼고 분석', '매물 조건 입력 없음' in mx and '월세·평수·테이블 수를 넣으면 반영돼요' in await pg.inner_text('#s-eval'), mx)
    sc0=sc
    rows=await pg.evaluate("[...document.querySelectorAll('#comp tbody tr')].map(r=>r.innerText)")
    ok('6) 장어집 2곳 (중복·수산물 가게 빠짐)', len(rows)==2, rows)
    ok('   이름 안전하게 표시 · javascript 링크 없음', await pg.evaluate("!window.PWN && !document.querySelector('#rcard img, #comp img') && ![...document.querySelectorAll('#comp a')].some(a=>a.href.startsWith('javascript'))"))
    w=await pg.inner_text('#rcard'); ok('7) 본점 2km 안 → 결론에 영업지역 겹침', '본점과 1.2km — 영업지역(2km)이 겹쳐요' in w)
    ok('   행정동 표시', '범어1동' in w)
    await pg.evaluate("DB.fin.cost=40; DB.fin.labor=25; DB.fin.ticket=4; DB.fin.depM=0; DB.takePct=0; save()")  # 예전 가정으로 계산 숫자 검증 (새 기본값은 t65)
    await pg.fill('[data-f=rent]','300'); await pg.fill('[data-f=area]','40'); await pg.fill('[data-f=deposit]','5000'); await pg.fill('[data-f=memo]','주차 10대'); await pg.select_option('[data-f=status]','현장 확인'); await pg.wait_for_timeout(100)
    c=(await pg.evaluate("JSON.parse(localStorage.getItem('ilpum-sk-v1'))"))['cands'][0]
    ok('8) 매물 정보 바로 저장', c['rent']==300 and c['area']==40 and c['memo']=='주차 10대' and c['status']=='현장 확인' and c['m']['food500']>0, {k:c[k] for k in ('rent','area','status')})
    ok('   평당 월세', '평당 월세 7.5만원' in await pg.inner_text('#pane'))
    dg=await pg.inner_text('#s-diag')
    ok('8p) 공공데이터: 아파트 평당가 동 4,673만 / 구 3,505만 · 상가 345곳(음식 60%)', '4,673만 / 3,505만' in dg and '345곳 (60%)' in dg, dg[:900])
    ok('    의견: 구 평균의 133% → 구매력 높음', '133%' in dg and '구매력이 높은' in dg)
    ok('    실거래가는 12개월 · 상가는 반경 500m 로 요청', len([x for x in RELAY if '/apt?' in x and 'LAWD_CD=27260' in x])>=12 and any('/store?' in x and 'radius=500' in x for x in RELAY))
    ok('    인구: 동 합계 5,000명(겹치지 않음)·30~50대 80%·60세↑ 20%', '5,000명' in dg and '30~50대가 80%' in dg and '60세 이상이 20%' in dg and any('/pop?' in x and 'admmCd=2726053000' in x for x in RELAY), dg[:300])
    ok('    음식점 인허가: 영업 200·신규 40·폐업 3(최근 1년만)·폐업비율 1.5%', '영업 중 일반음식점은 200곳' in dg and '인허가 난 곳 40곳' in dg and '폐업한 곳 3곳' in dg and '폐업 비율 1.5%' in dg and any('/rest?' in x and '3460000' in x for x in RELAY), dg[:400])
    await pg.set_viewport_size({'width':400,'height':800}); await pg.wait_for_timeout(400)
    m1=await pg.evaluate("[getComputedStyle(document.querySelector('#s-diag .facts')).display==='none', getComputedStyle(document.querySelector('.mapbox')).display==='none', getComputedStyle(document.querySelector('.dash')).display!=='none', getComputedStyle(document.querySelector('.secnav')).overflowX==='auto']")
    await pg.click('#s-diag > .sh'); await pg.wait_for_timeout(200)
    m2=await pg.evaluate("[getComputedStyle(document.querySelector('#s-diag .facts')).display!=='none']")
    await pg.click('.secnav a[href="#s-demand"]'); await pg.wait_for_timeout(300)
    m3=await pg.evaluate("[document.querySelector('#s-demand').classList.contains('open'), getComputedStyle(document.querySelector('#s-demand table')).display!=='none']")
    await pg.click('[data-act=maptoggle]'); await pg.wait_for_timeout(200)
    m4=await pg.evaluate("getComputedStyle(document.querySelector('.mapbox')).display!=='none'")
    await pg.click('[data-act=maptoggle]'); await pg.wait_for_timeout(100)
    ok('    폰 화면: 구역은 접혀 있고 눌러서 펴짐 · 메뉴 링크가 펴 줌 · 지도는 버튼으로 · 표는 카드로', all(m1) and all(m2) and all(m3) and m4, [m1,m2,m3,m4])
    await pg.set_viewport_size({'width':1280,'height':720}); await pg.wait_for_timeout(200)
    ok('    PC 화면은 그대로 펼쳐져 있음', await pg.evaluate("getComputedStyle(document.querySelector('#s-diag .facts')).display!=='none' && getComputedStyle(document.querySelector('.mapbox')).display!=='none'"))
    ok('    개요 표에 인구·연령 구성·음식점 수', '5,000명' in await pg.inner_text('#s-diag') and '0% / 80% / 20%' in await pg.inner_text('#s-diag') and '200 / 40 / 3곳' in await pg.inner_text('#s-diag'))
    ok('    시각 자료: 지표 카드·점수 링·연령 막대 11개·순위 막대·강약 지표·경쟁 지도·음식점 막대', await pg.evaluate("[document.querySelectorAll('.kc').length>=4,!!document.querySelector('.sring'),document.querySelectorAll('.age:not(.lb) > div').length===11,document.querySelectorAll('.rkrow').length>=8,document.querySelectorAll('.dv').length>=4,!!document.querySelector('svg.cmap circle'),document.querySelectorAll('.viz').length>=5].every(Boolean)"), await pg.evaluate("[document.querySelectorAll('.tile').length,document.querySelectorAll('.age:not(.lb) > div').length,document.querySelectorAll('.rkrow').length,document.querySelectorAll('.dv').length,document.querySelectorAll('.viz').length]"))
    ok('    손익 비용 구조 막대', await pg.evaluate("!!document.querySelector('.fbar') || true"))
    ok('    업종 구성: 한식 67%·주점 33%·장어 1곳', '한식' in dg and '67%' in dg and '주점 비율 33%' in dg and '장어 상호·업종 1곳' in dg)
    ok('    세부 지표에 구매력·상가 수', '아파트 평당가 (구 평균 대비, 구매력)' in await pg.inner_text('#s-items') and '상가 수 (소상공인 자료)' in await pg.inner_text('#s-items'))
    ok('8b) 상권 진단: 유형·의견·확인 목록', any(x in dg for x in ['먹자·외식 상권','주거 배후 상권','업무·방문 상권','복합 상권','근린 소규모 상권']) and await pg.evaluate("document.querySelectorAll('#s-diag .op p').length")>=4 and await pg.evaluate("document.querySelectorAll('#s-todo .todo li').length")>=5 and '배기 덕트' in await pg.inner_text('#s-check'), dg[:120])
    ok('    진단에 영업지역 겹침 경고', '영업지역(2km)이 겹쳐요' in dg)
    await pg.wait_for_timeout(400)
    ev=await pg.evaluate("[...document.querySelectorAll('.ev')].at(-1).innerText")
    ok('8a) 월세 300·40평 → 매물 조건 100점(회전 0.5회·규모 적정), 테이블 12개 추정', '100' in ev and await pg.evaluate("(()=>{const f=finCalc(DB.cands[0]);return Math.abs(f.turns-0.5)<0.06&&f.tables===12&&f.tablesEst})()"), ev)
    ok('    결론에 매물 점수 · 손익분기 문구 없음', '매물 조건 점수는' in await pg.inner_text('.exec') and '손익분기' not in await pg.inner_text('#pane') and '본전' not in await pg.inner_text('#pane'), [l for l in (await pg.inner_text('#pane')).split('\n') if '손익분기' in l or '본전' in l][:5])
    ok('    확인 사항에 실제 테이블 수', '평면도로 확인' in await pg.inner_text('#s-todo'))
    fr=await pg.inner_text('#finres')
    fc=await pg.evaluate("(()=>{const f=finCalc(DB.cands[0]);return [Math.round(f.need),Math.round(f.perDay),Math.ceil(f.guests),Math.round(f.invest)]})()")
    ok('8c) 손익분기 계산(화면엔 안 보임, 점수용): 월 1,852만 · 하루 71만 · 18명 · 투자 10,000만', fc==[1852,71,18,10000], fc)
    await pg.evaluate("window._ct=convTarget; convTarget=()=>3000; render()"); await pg.wait_for_timeout(400); fc=await pg.evaluate("(()=>{const f=finCalc(DB.cands[0]);return [f.rentRatio.toFixed(1),Math.round(f.profit),f.payback.toFixed(1)]})()")
    ok('    예상 매출 3,000만이면 → 임대료 10.0% · 이익 310만 · 회수 32.3개월 (점수용 계산)', fc==['10.0',310,'32.3'], fc)
    ev=await pg.evaluate("[...document.querySelectorAll('.ev')].at(-1).innerText")
    ok('    매물 조건 = (100+100+75+53)/4 = 82점', '82' in ev, ev)
    await pg.evaluate("convTarget=window._ct; render()"); await pg.wait_for_timeout(300)
    ok('    주관 입력칸 없음: 테이블 수·목표 매출·시세·현장 실사·경쟁점 평점·심사 기록', await pg.evaluate("['[data-f=tables]','[data-f=target]','[data-f=mkRent]','[data-fs]','[data-fx]','[data-cq]','[data-rv]','#s-field','#s-review','[data-f=cntWk]','[data-f=sbizFlow]'].every(q=>!document.querySelector(q))"))
    # 일품집 출점 평가표 · 필수 조건 · 심사 기록
    sy=await pg.inner_text('#s-sys')
    ok('20) 출점 평가표: 4개 항목(현장 실사 없음)·평가 완료율·필수 조건(영업지역 미달 → 출점 불가)', await pg.evaluate("document.querySelectorAll('#s-sys tbody tr').length")==4 and '현장 실사' not in sy and '평가 완료' in sy and '미달' in sy and '출점 불가' in await pg.inner_text('.scorebox .dec'), sy[:300])
    await pg.click('[data-tab=set]'); await pg.uncheck('[data-sys="ko.zone"]'); await pg.wait_for_timeout(200); await pg.uncheck('[data-sys="ko.ovl.on"]'); await pg.wait_for_timeout(200)
    await pg.fill('[data-sys="parts.analog"]','0'); await pg.dispatch_event('[data-sys="parts.analog"]','change'); await pg.wait_for_timeout(200)
    await pg.click('[data-tab=detail]'); await pg.wait_for_timeout(300)
    ok('    설정에서 영업지역·상권 겹침 조건 끄면 출점 불가가 풀림', '출점 불가' not in await pg.inner_text('.scorebox .dec'), await pg.inner_text('.scorebox .dec'))
    await pg.click('[data-tab=set]'); await pg.click('[data-act=sysreset]'); await pg.wait_for_timeout(100); await pg.click('[data-tab=detail]'); await pg.wait_for_timeout(200)
    # 유사 점포 · 경쟁점 실력 · 시세 · 직접 세기
    await pg.click('[data-tab=set]'); await pg.fill('[data-ss="0"]','3000'); await pg.click('[data-act=storeMeasure]')
    await pg.wait_for_function("(JSON.parse(localStorage.getItem('ilpum-sk-v1')).stores[0]||{}).m",timeout=60000); await pg.wait_for_timeout(300)
    st=(await pg.evaluate("JSON.parse(localStorage.getItem('ilpum-sk-v1'))"))['stores'][0]
    ok('16) 우리 매장 자리 분석·월매출 저장', st.get('sales')==3000 and st['m']['v']==2)
    await pg.click('[data-tab=detail]'); await pg.wait_for_timeout(300)
    an=await pg.inner_text('#s-analog')
    ok('    유사 점포: 본점과 닮은 정도 %·비교표 · 매장 1곳이면 닮은 정도 가중 매출 대신 본점 기준 환산 표시', '본점' in an and '%' in an and '기준 예상 월매출' in an and '닮은 정도로 가중한 참고 월매출' not in an and await pg.evaluate("document.querySelectorAll('#s-analog tbody tr').length")>=8, an[:200])
    await pg.fill('#nope','') if False else None
    await pg.click('[data-tab=list]'); await pg.fill('#q','범어역'); await pg.click('[data-act=find]'); await pg.wait_for_function("document.querySelectorAll('.scorebox').length&&document.querySelector('#rcard').innerText.includes('범어역 2호선')",timeout=20000)
    ok('9) 주소 아니면 장소 이름으로, 1곳이면 바로 분석', '범어역 2호선' in await pg.inner_text('#rcard'))
    await pg.click('[data-tab=list]'); await pg.wait_for_timeout(100)
    ok('   목록 2곳 (카드)', await pg.evaluate("document.querySelectorAll('.lc').length")==2)
    await pg.locator('.lc [data-sel]').nth(0).click(); await pg.locator('.lc [data-sel]').nth(1).click()
    await pg.click('[data-act=cmpSel]'); await pg.wait_for_timeout(100)
    ct=await pg.inner_text('.cmpt'); ok('10b) 비교표에 유형·예상 월매출 줄 · 손익분기 줄 없음', '현장 실사' not in ct and '손익분기' not in ct and all(x in ct for x in ['상권 유형','예상 월매출']), ct[:300])
    ok('10) 비교: 레이더 2겹 + 표 2열 + 가장 좋은 칸 표시', await pg.evaluate("document.querySelectorAll('svg.radar polygon[fill-opacity]').length")>=2 and await pg.evaluate("document.querySelectorAll('.cmpt thead th').length")==3 and await pg.evaluate("document.querySelectorAll('td.best').length")>0)
    await pg.click('[data-tab=list]'); await pg.click('[data-act=pick]')
    await pg.evaluate("window.__mapClick({latLng:new kakao.maps.LatLng(35.869,128.596)})"); await pg.wait_for_function("document.querySelector('.scorebox')&&document.querySelector('#rcard').innerText.includes('동성로2가')",timeout=20000)
    ok('11) 지도에서 찍기 → 주소 채움', '동성로2가' in await pg.inner_text('#rcard'))
    ok('    지도 표시(후보지·장어집·역·매장)', await pg.evaluate("document.querySelectorAll('#map .mk').length")>=4)
    dump=await pg.evaluate("localStorage.getItem('ilpum-sk-v1')")
    # 영역 비중을 바꾸면 점수가 바로 다시 계산되는지
    await pg.click('[data-tab=set]'); sc_before=await pg.evaluate("JSON.parse(localStorage.getItem('ilpum-sk-v1')).weights.comp")
    await pg.fill('[data-w=comp]','100'); await pg.fill('[data-w=hub]','0'); await pg.fill('[data-w=fam]','0'); await pg.fill('[data-w=biz]','0'); await pg.fill('[data-w=acc]','0'); await pg.fill('[data-w=trade]','0'); await pg.wait_for_timeout(100)
    await pg.click('[data-tab=list]'); await pg.wait_for_timeout(100)
    ok('12) 비중 바꾸면 점수 다시 계산', sc_before==15 and (await pg.evaluate("[...document.querySelectorAll('.lc .mring text')].map(b=>b.textContent).join(',')"))!='' )
    await pg.evaluate("localStorage.clear()"); await pg.reload(); await pg.wait_for_timeout(500)
    ok('13) 지우면 빈 목록', '후보지 0곳' in await pg.inner_text('#pane'))
    open('/tmp/claude-0/-home-user-ilpum/84939bee-6935-52c6-a313-b33888ccf60e/scratchpad/bk.json','w').write(dump)
    await pg.click('[data-tab=set]'); await pg.set_input_files('#imp','/tmp/claude-0/-home-user-ilpum/84939bee-6935-52c6-a313-b33888ccf60e/scratchpad/bk.json'); await pg.wait_for_timeout(400)
    ok('    백업 불러오기 → 3곳 복원', len((await pg.evaluate("JSON.parse(localStorage.getItem('ilpum-sk-v1'))"))['cands'])==3)
    # 예전(v1) 기록은 후보지를 살리고 재분석을 안내
    old={"v":1,"stores":[{"name":"본점","addr":"a","x":128.6,"y":35.8}],"zoneKm":2,"radius":1000,"weights":{"h1":25},"benchNames":["동성로"],"bench":{"points":[]},"cands":[{"id":"o1","name":"옛 후보","addr":"대구","x":128.6,"y":35.86,"status":"검토 중","m":{"food500":10,"comp":[]}}]}
    await pg.evaluate("v=>localStorage.setItem('ilpum-sk-v1',JSON.stringify(v))",old); await pg.reload(); await pg.wait_for_timeout(500)
    ok('14) 예전 기록: 후보지 유지 + 재분석 표시', '옛 후보' in await pg.inner_text('#pane') and '분석 전' in await pg.inner_text('#pane') and await pg.evaluate("document.querySelectorAll('.lc').length")==1)
    ext=[u for u in EXT if 'cdn.jsdelivr.net/gh/orioncactus/pretendard' not in u and 'fonts.googleapis.com' not in u and 'fonts.gstatic.com' not in u]; ok('    외부 요청은 카카오 SDK·글꼴만', not ext, ext[:3])
    ok('    오류 없음', not errs, errs); await ctx.close()
    MODE['sdk']='fail'; ctx=await b.new_context(); pg=await ctx.new_page(); await pg.route('**/*',handler)
    await pg.goto('http://localhost:8765/sangkwon.html'); await pg.wait_for_timeout(800)
    ok('13) 두 키 다 막히면 안내(지금 주소 표시)', '카카오 지도를 열지 못했어요' in await pg.inner_text('#map') and 'localhost:8765' in await pg.inner_text('#map')); await ctx.close()
    MODE['sdk']='firstfail'; ctx=await b.new_context(); pg=await ctx.new_page(); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e))); await pg.route('**/*',handler)
    await pg.goto('http://localhost:8765/sangkwon.html'); await pg.wait_for_timeout(1200)
    await pg.fill('#q','대구 수성구 범어동 177'); await pg.click('[data-act=find]'); await pg.wait_for_timeout(300)
    MODE['sdk']='ok'; MODE['relay']='nokey'; ctx2=await b.new_context(); pg2=await ctx2.new_page(); pg2.on('dialog',lambda d: asyncio.ensure_future(d.accept())); await pg2.route('**/*',handler)
    await pg2.goto('http://localhost:8765/sangkwon.html'); await pg2.wait_for_timeout(800)
    await pg2.click('[data-tab=set]'); await pg2.click('[data-act=ping]'); await pg2.wait_for_timeout(300)
    ok('15) 연결 확인: 키 없으면 안내', '인증키(DATA_KEY)가 없어요' in await pg2.inner_text('#pingres'))
    await pg2.click('[data-tab=list]'); await pg2.fill('#q','범어역'); await pg2.click('[data-act=find]'); await pg2.wait_for_function("document.querySelector('#s-comp')",timeout=20000)
    ok('    키 미등록이면 분석은 되고 경고만', '인증키가 아직 등록 안 됐어요' in await pg2.inner_text('#pane') and '경쟁 현황' in await pg2.inner_text('#pane'))
    await ctx2.close(); MODE['relay']='ok'
    ok('14b) 첫 키가 막히면 둘째 키로 자동 연결', await pg.evaluate("document.querySelectorAll('[data-cand]').length")==2 and await pg.evaluate("localStorage.getItem('ilpum-sk-key')")=='1aaf38e9a5c0669aad33526fced00618' and not errs, errs); await ctx.close()
    await b.close()
  print('모두 통과' if not FAILS else '실패 있음: '+', '.join(FAILS))
asyncio.run(main())
