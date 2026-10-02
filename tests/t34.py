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
  ok=True
  def chk(n,c):
    nonlocal ok; ok&=bool(c); print(('OK  ' if c else 'FAIL'),n)
  async with async_playwright() as p:
    b=await p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
    ctx,pg,errs=await open_page(b,['6','8','3'])
    chk('처음엔 큰 자리 안내(인원 미지정)', '몇 인석인지' in await pg.evaluate("freeHtml(ui.t)"))
    await pg.click('[data-led="start"]'); await pg.wait_for_timeout(200)
    btns=pg.locator('[data-led="tseat"]'); n=await btns.count(); chk('칸 배치 수정 중 테이블마다 인원 버튼', n>5)
    await btns.nth(0).click(); await btns.nth(0).wait_for(state='attached'); await pg.wait_for_timeout(150)
    await pg.locator('[data-led="tseat"]').nth(1).click(); await pg.wait_for_timeout(150)
    await pg.locator('[data-led="tseat"]').nth(2).click(); await pg.wait_for_timeout(150)
    seats=await pg.evaluate("layoutEdit.seats"); chk('인원이 임시 저장됨', sorted(seats.values())==[3,6,8])
    await pg.click('[data-led="save"]'); await pg.wait_for_timeout(500)
    chk('저장 내용에 seats 포함', POSTS and set(POSTS[-1]['data']['seats'].values())=={3,6,8})
    chk('현황판 칸에 배지 표시', await pg.locator('.seatb').count()==3)
    html=await pg.evaluate("freeHtml(ui.t)"); chk('큰 자리 줄: 6인석·8인석 나옴(3인은 제외)', '6인석' in html and '8인석' in html and '3인석' not in html)
    st=await pg.inner_text('#seatStat'); chk('예약 목록 위에 남은 6인석·8인석 표시', '6인석' in st and '8인석' in st and '3인석' not in st and '/1' in st)
    await ctx.close()
    ctx,pg,errs=await open_page(b,[])   # 다시 열기
    chk('다시 열어도 유지', await pg.evaluate("Object.keys(SEATS).length")==3 and await pg.locator('.seatb').count()==3)
    # 자유 배치에서도
    await pg.click('[data-led="start"]'); await pg.click('[data-led="tofree"]'); await pg.wait_for_timeout(300)
    await pg.locator('.fedit .fpos').first.click(); await pg.wait_for_timeout(200)
    chk('자유 배치: 선택 막대에 인원수 버튼', await pg.is_visible('.fselbar [data-led="tseat"]'))
    chk('오류 없음', not errs)
  print('전체','OK' if ok else 'FAIL')
asyncio.run(main())
