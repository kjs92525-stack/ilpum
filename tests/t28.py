# 현황판 자유 배치: 칸 배치→자유 배치, 끌어서 옮기기, 모양·크기·번호, 원형 배치, 저장·다시 열기 (가짜 서버)
# 실행 전: cd dist && python3 -m http.server 8765
import asyncio, json, time, os
from playwright.async_api import async_playwright
NEW='bdqcrbnbuoujozlpttbe.supabase.co'; F1='ad2ffdae-f76b-44cd-a6c6-58514c4e4638'
LAYOUT={}; POSTS=[]
async def handler(r):
  u=r.request.url; m=r.request.method
  if 'localhost' in u: return await r.continue_()
  if NEW not in u: return await r.fulfill(status=404,body='{}')
  J=lambda o,st=200: r.fulfill(status=st,content_type='application/json',body=json.dumps(o))
  if '/rpc/sch_my_stores' in u: return await J([{"id":F1,"name":"유천점","is_hq":False,"role":"owner"}])
  if '/rest/v1/sch_items' in u:
    if m=='POST': b=json.loads(r.request.post_data); POSTS.append(b); LAYOUT['d']=b['data']; return await r.fulfill(status=201,body='')
    return await J([{"data":LAYOUT['d']}] if 'd' in LAYOUT else [])
  if '/rest/v1/res_days' in u: return await J([] if m=='GET' else [{"rev":1}])
  await J([])
S={"ses":{"access_token":"tok","refresh_token":"r","expires_at":int(time.time())+3000,"user":{"email":"x@ilpum.invalid"}}}
async def open_page(b,prompts):
  ctx=await b.new_context(viewport={'width':1500,'height':900}); pg=await ctx.new_page(); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
  def on_dialog(d):
    v=prompts.pop(0) if (d.type=='prompt' and prompts) else None
    asyncio.ensure_future(d.accept(v) if d.type=='prompt' else d.accept())
  pg.on('dialog',on_dialog)
  await pg.route('**/*',handler); await pg.route_web_socket(f'wss://{NEW}/**',lambda ws: asyncio.ensure_future(ws.close()))
  await pg.add_init_script(f"try{{ localStorage.setItem('ilpum-fr-conf',{json.dumps(json.dumps(S))}); }}catch(e){{}}")
  await pg.goto('http://localhost:8765/reserve.html'); await pg.wait_for_timeout(1300); return ctx,pg,errs
async def main():
  async with async_playwright() as p:
    b=await p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
    prompts=['12','8','1']   # fcircle 개수, 시작 번호는 아래서 따로
    ctx,pg,errs=await open_page(b,[])
    n0=await pg.evaluate("ALL_TABLES.length")
    await pg.click('[data-led="start"]'); await pg.wait_for_timeout(200)
    await pg.click('[data-led="tofree"]'); await pg.wait_for_timeout(300)
    print('1) 자유 배치로 바꿈: 모드', await pg.evaluate("editFloor().mode"), '| 테이블 수 그대로:', await pg.evaluate("tablesOf(layoutEdit.floors).length")==n0, '| 캔버스 보임:', await pg.is_visible('#fcanvas'))
    # 끌어서 옮기기
    el=pg.locator('.fedit .fpos').first; bb=await el.bounding_box(); before=await pg.evaluate("[editFloor().tables[0].x,editFloor().tables[0].y]")
    await pg.mouse.move(bb['x']+bb['width']/2,bb['y']+bb['height']/2); await pg.mouse.down(); await pg.mouse.move(bb['x']+bb['width']/2+200,bb['y']+bb['height']/2+120,steps=8); await pg.mouse.up(); await pg.wait_for_timeout(300)
    print('2) 끌어서 옮김:', before, '→', await pg.evaluate("[editFloor().tables[0].x,editFloor().tables[0].y]"), '| 눌러서 고른 테이블:', await pg.evaluate("layoutSel"), '| 선택 막대:', await pg.is_visible('.fselbar b'))
    await pg.click('[data-led="fshape"][data-v="round"]'); w0=await pg.evaluate("editFloor().tables[0].w"); await pg.click('[data-led="fsize"][data-v="1"]'); await pg.wait_for_timeout(100)
    print('3) 모양 원·크게:', await pg.evaluate("[editFloor().tables[0].shape,editFloor().tables[0].w>%s]"%w0))
    await pg.click('[data-led="ffadd"]'); await pg.wait_for_timeout(100)
    await pg.close(); await ctx.close()
    # 원형 배치는 새 페이지에서 prompt 값을 줘서
    ctx,pg,errs=await open_page(b,['홀','8','60'])
    await pg.click('[data-led="start"]'); await pg.click('[data-led="ffadd"]'); await pg.wait_for_timeout(200)     # 새 자유 층 '홀'
    await pg.click('[data-led="fcircle"]'); await pg.wait_for_timeout(300)
    t=await pg.evaluate("editFloor().tables.map(t=>[t.id,t.x,t.y,t.w,t.shape])")
    print('4) 원형 배치 8개(60번부터):', [x[0] for x in t], '| 모양:', {x[4] for x in t}, '| 위치가 원 모양으로 퍼짐: 가운데 기준 거리', sorted({round(((x[1]+x[3]/2-500)/380)**2+((x[2]+x[3]/2-300)/200)**2,1) for x in t}))
    await pg.screenshot(path='free_edit.png')
    await pg.click('[data-led="save"]'); await pg.wait_for_timeout(700)
    d=POSTS[-1]['data']['floors']; print('5) 저장:', len(POSTS),'번 | 층:', [(f['name'],f.get('mode','칸')) for f in d], '| 매장:', POSTS[-1]['store_id']==F1)
    print('   보기 화면: 자유 층 선택 →'); await pg.click('.ftabs button >> nth=-1'); await pg.wait_for_timeout(300)
    print('   현황판에 원형 테이블:', await pg.evaluate("document.querySelectorAll('.floor .fpos.round').length"), '| 데이터 있는 칸 클릭 가능(data-cell):', await pg.evaluate("document.querySelectorAll('.floor .fpos .cell[data-cell]').length"))
    await pg.screenshot(path='free_view.png'); print('   errs', errs); await ctx.close()
    ctx,pg,errs=await open_page(b,[]); await pg.click('.ftabs button >> nth=-1'); await pg.wait_for_timeout(300)
    print('6) 새로고침 후에도 자유 배치 유지:', await pg.evaluate("document.querySelectorAll('.floor .fpos.round').length"), '| 번호 인식:', await pg.evaluate("parseTables('60 63')"))
    await pg.evaluate("saveItem(ui.date,{id:'z1',name:'원형손님',time:'18:00',pp:'4',tables:['60'],req:'',u:Date.now()})"); await pg.wait_for_timeout(400)
    print('   예약을 60번 원형 테이블에 넣으면 그 칸에 표시:', await pg.evaluate("document.querySelector('.fpos[data-ft=\"60\"] .cell').innerText.replace(/\\s+/g,' ')"), '| errs', errs); await ctx.close()
asyncio.run(main())
