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
Geocoder.prototype.coord2RegionCode=function(x,y,cb){ setTimeout(()=>cb([{region_type:'B',address_name:'법정동'},{region_type:'H',address_name:'대구광역시 수성구 범어1동'}],S.OK),5); };
Geocoder.prototype.coord2Address=function(x,y,cb){ setTimeout(()=>cb([{address:{address_name:'대구 중구 동성로2가 1'},road_address:null}],S.OK),5); };
function LatLng(lat,lng){ this.getLat=()=>lat; this.getLng=()=>lng; }
function Map(el){ this.el=el; window.__map=this; this.setLevel=()=>{}; this.setCenter=()=>{}; this.relayout=()=>{}; }
function CustomOverlay(o){ this.o=o; this.setMap=m=>{ if(!m&&o.content.parentNode) o.content.remove(); }; if(o.map) o.map.el.appendChild(o.content); }
function Circle(o){ window.__circ=(window.__circ||0)+1; this.setMap=()=>{}; }
window.kakao={maps:{load:f=>setTimeout(f,0),LatLng,Map,CustomOverlay,Circle,event:{addListener:(m,ev,fn)=>{ window.__mapClick=fn; }},
  services:{Places,Geocoder,Status:S,SortBy:{DISTANCE:'distance',ACCURACY:'accuracy'}}}};
})();
"""
MODE={'sdk':'ok'}; EXT=[]
async def handler(r):
  u=r.request.url
  if 'localhost' in u: return await r.continue_()
  if 'dapi.kakao.com/v2/maps/sdk.js' in u:
    if MODE['sdk']=='fail': return await r.fulfill(status=404,body='')
    assert 'appkey=7ed6cf4a57f04e78dab3bf66a095dcd2' in u and 'libraries=services' in u
    return await r.fulfill(status=200,content_type='application/javascript',body=STUB)
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
    ok('1) 처음: 대구 기준 상권 안내', '대구 기준 상권' in await pg.inner_text('#pane'))
    await pg.click('[data-tab=set]'); await pg.fill('#sname','본점'); await pg.fill('#saddr','대구 수성구 들안로 1'); await pg.click('[data-act=sadd]'); await pg.wait_for_timeout(200)
    db=await pg.evaluate("JSON.parse(localStorage.getItem('ilpum-sk-v1'))")
    ok('2) 우리 매장 저장', db['stores'][0]['name']=='본점' and db['stores'][0]['x']==128.635, db['stores'])
    await pg.click('[data-act=bench]'); await pg.wait_for_function("JSON.parse(localStorage.getItem('ilpum-sk-v1')||'{}').bench",timeout=60000)
    db=await pg.evaluate("JSON.parse(localStorage.getItem('ilpum-sk-v1'))")
    pts=db['bench']['points']; ok('3) 기준 상권 20곳 측정', len(pts)==20 and all(x.get('m') for x in pts), len(pts))
    ok('   기준 상권 점수 표', await pg.evaluate("document.querySelectorAll('details tbody tr').length")==20)
    await pg.click('[data-tab=list]'); await pg.fill('#q','대구 수성구 범어동 177'); await pg.click('[data-act=find]'); await pg.wait_for_timeout(200)
    ok('4) 주소 후보 2곳', await pg.evaluate("document.querySelectorAll('[data-cand]').length")==2)
    await pg.click('[data-cand="0"]'); await pg.wait_for_function("document.querySelector('.score .n')",timeout=15000)
    sc=int(await pg.inner_text('.score .n')); g=await pg.inner_text('.score .gr')
    ok('5) 점수·등급', 0<=sc<=100 and g==('A' if sc>=70 else 'B' if sc>=55 else 'C' if sc>=40 else 'D'), (sc,g))
    ok('   기준 상권 중 순위 표시', '20곳 중' in await pg.inner_text('.score'))
    rows=await pg.evaluate("[...document.querySelectorAll('#rcard table')[1].querySelectorAll('tbody tr')].map(r=>r.innerText)")
    ok('6) 장어집 2곳 (중복·수산물 가게 빠짐)', len(rows)==2, rows)
    ok('   이름 안전하게 표시 · javascript 링크 없음', await pg.evaluate("!window.PWN && !document.querySelector('#rcard img') && ![...document.querySelectorAll('#rcard a')].some(a=>a.href.startsWith('javascript'))"))
    w=await pg.inner_text('#rcard'); ok('7) 본점 2km 안 → 영업지역 경고', '영업지역 2km 안에 우리 매장: 본점' in w)
    ok('   행정동 표시', '범어1동' in w)
    await pg.fill('[data-f=rent]','300'); await pg.fill('[data-f=area]','40'); await pg.fill('[data-f=memo]','주차 10대'); await pg.select_option('[data-f=status]','현장 확인'); await pg.wait_for_timeout(100)
    c=(await pg.evaluate("JSON.parse(localStorage.getItem('ilpum-sk-v1'))"))['cands'][0]
    ok('8) 매물 정보 바로 저장', c['rent']==300 and c['area']==40 and c['memo']=='주차 10대' and c['status']=='현장 확인' and c['m']['food500']>0, {k:c[k] for k in ('rent','area','status')})
    ok('   평당 월세', '평당 월세 7.5만원' in await pg.inner_text('#rcard'))
    await pg.click('[data-tab=list]'); await pg.fill('#q','범어역'); await pg.click('[data-act=find]'); await pg.wait_for_function("document.querySelector('.score .n')",timeout=15000)
    ok('9) 주소 아니면 장소 이름으로, 1곳이면 바로 분석', '범어역 2호선' in await pg.inner_text('#rcard'))
    await pg.click('[data-tab=list]'); await pg.wait_for_timeout(100)
    ok('   목록 2곳', await pg.evaluate("document.querySelectorAll('#clist tbody tr').length")==2)
    await pg.click('#clist tbody tr:nth-child(1) [data-sel]'); await pg.click('#clist tbody tr:nth-child(2) [data-sel]')
    await pg.click('[data-act=cmpSel]'); await pg.wait_for_timeout(100)
    ok('10) 비교표 2열 + 가장 좋은 칸 표시', await pg.evaluate("document.querySelectorAll('thead th').length")==3 and await pg.evaluate("document.querySelectorAll('td.best').length")>0)
    await pg.click('[data-tab=list]'); await pg.click('[data-act=pick]')
    await pg.evaluate("window.__mapClick({latLng:new kakao.maps.LatLng(35.869,128.596)})"); await pg.wait_for_function("document.querySelector('.score .n')",timeout=15000); await pg.wait_for_timeout(200)
    ok('11) 지도에서 찍기 → 주소 채움', '동성로2가' in await pg.inner_text('#rcard'))
    ok('    지도 표시(후보지·장어집·역·매장)', await pg.evaluate("document.querySelectorAll('#map .mk').length")>=4)
    dump=await pg.evaluate("localStorage.getItem('ilpum-sk-v1')")
    await pg.evaluate("localStorage.clear()"); await pg.reload(); await pg.wait_for_timeout(500)
    ok('12) 지우면 빈 목록', '후보지 0곳' in await pg.inner_text('#pane'))
    open('/tmp/claude-0/-home-user-ilpum/84939bee-6935-52c6-a313-b33888ccf60e/scratchpad/bk.json','w').write(dump)
    await pg.click('[data-tab=set]'); await pg.set_input_files('#imp','/tmp/claude-0/-home-user-ilpum/84939bee-6935-52c6-a313-b33888ccf60e/scratchpad/bk.json'); await pg.wait_for_timeout(400)
    ok('    백업 불러오기 → 3곳 복원', len((await pg.evaluate("JSON.parse(localStorage.getItem('ilpum-sk-v1'))"))['cands'])==3)
    ok('    외부 요청은 카카오 SDK 만', not EXT, EXT[:3])
    ok('    오류 없음', not errs, errs); await ctx.close()
    MODE['sdk']='fail'; ctx=await b.new_context(); pg=await ctx.new_page(); await pg.route('**/*',handler)
    await pg.goto('http://localhost:8765/sangkwon.html'); await pg.wait_for_timeout(800)
    ok('13) 카카오 못 열면 안내', '카카오 지도를 열지 못했어요' in await pg.inner_text('#map')); await ctx.close()
    await b.close()
  print('모두 통과' if not FAILS else '실패 있음: '+', '.join(FAILS))
asyncio.run(main())
