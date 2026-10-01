# 공지사항 사진·동영상 (가짜 서버): 올리기(사진 자동 축소)·보기(서명 주소)·빼기/삭제 시 파일 정리·점주는 올리기 버튼 없음
# 실행 전: cd dist && python3 -m http.server 8765
import asyncio, json, time, re
from playwright.async_api import async_playwright
NEW='bdqcrbnbuoujozlpttbe.supabase.co'; BON='0134d989-757a-4b60-9cb3-93245de2cac8'
NOTICES=[{"id":"n1","title":"사진 공지","body":"본문","pinned":False,"created_at":"2026-09-30T01:00:00+00:00","media":[{"path":"2026-09/a.jpg","type":"image","name":"a.jpg"},{"path":"2026-09/b.mp4","type":"video","name":"b.mp4"}]}]
ROLE={'v':'hq'}; UP=[]; DEL=[]; SIGN=[]; WR=[]
async def handler(r):
  u=r.request.url; m=r.request.method
  if 'localhost' in u: return await r.continue_()
  J=lambda o,st=200: r.fulfill(status=st,content_type='application/json',body=json.dumps(o))
  if '/rpc/sch_my_stores' in u: return await J([{"id":BON,"name":"본점","is_hq":True,"role":ROLE['v'],"can_pay":False}])
  if '/storage/v1/object/sign/' in u and m=='POST':
    ps=json.loads(r.request.post_data)['paths']; SIGN.extend(ps); return await J([{"path":p,"signedURL":"/object/sign/notice-media/"+p+"?token=t"} for p in ps])
  if '/storage/v1/object/notice-media' in u and m=='POST': UP.append((u.split('notice-media/')[1],r.request.headers.get('content-type'),len(r.request.post_data_buffer or b''))); return await J({"Key":"x"})
  if '/storage/v1/object/notice-media' in u and m=='DELETE': DEL.extend(json.loads(r.request.post_data)['prefixes']); return await J([])
  if '/storage/v1/object/sign' in u: return await r.fulfill(status=200,content_type='image/png',body=b'')
  if '/rest/v1/board_notices' in u:
    if m=='GET': return await J(NOTICES)
    if m=='POST': b=json.loads(r.request.post_data); WR.append(('post',b)); NOTICES.insert(0,{"id":"n2","pinned":False,"created_at":"2026-10-01T05:00:00+00:00",**b}); return await r.fulfill(status=201,body='')
    if m=='PATCH': b=json.loads(r.request.post_data); WR.append(('patch',b)); NOTICES[-1].update(b); return await r.fulfill(status=204,body='')
    if m=='DELETE': WR.append(('del',u)); NOTICES.pop(); return await r.fulfill(status=204,body='')
  await J([])
S={"ses":{"access_token":"tok","refresh_token":"r","expires_at":int(time.time())+3000,"user":{"email":"x@ilpum.invalid"}}}
async def open_page(b):
  ctx=await b.new_context(viewport={'width':1000,'height':900}); pg=await ctx.new_page(); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
  pg.on('dialog',lambda d: asyncio.ensure_future(d.accept()))
  await pg.route('**/*',handler)
  await pg.add_init_script(f"try{{ localStorage.setItem('ilpum-fr-conf',{json.dumps(json.dumps(S))}); }}catch(e){{}}")
  await pg.goto('http://localhost:8765/notice.html'); await pg.wait_for_timeout(1200); return ctx,pg,errs
async def main():
  ok=True
  def chk(n,c):
    nonlocal ok; ok&=bool(c); print(('OK  ' if c else 'FAIL'),n)
  async with async_playwright() as p:
    b=await p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
    ctx,pg,errs=await open_page(b)
    chk('기존 공지의 사진·동영상 주소가 채워짐', await pg.evaluate("[...document.querySelectorAll('[data-mp]')].every(e=>e.src.includes('/storage/v1/object/sign/notice-media/'))") and len(SIGN)==2)
    chk('동영상은 눌러야 받음(preload none)', await pg.evaluate("document.querySelector('video').preload")=='none')
    await pg.click('[data-act="new"]'); await pg.fill('#nTitle','새 공지')
    await pg.set_input_files('#nFiles',['/tmp/big.png','/tmp/v.mp4']); await pg.wait_for_timeout(300)
    chk('고른 파일 2개 표시', await pg.locator('#nMg .mi2').count()==2)
    await pg.click('#dOk'); await pg.wait_for_timeout(2500)
    chk('올린 파일 2개 (사진은 jpeg 로 줄임, 동영상 그대로)', len(UP)==2 and UP[0][1]=='image/jpeg' and UP[0][0].endswith('.jpg') and UP[1][1]=='video/mp4')
    import os; chk('사진이 원본보다 작음', UP[0][2]<os.path.getsize('/tmp/big.png'))
    chk('공지에 media 2개 저장', WR and WR[-1][0]=='post' and len(WR[-1][1]['media'])==2 and {x['type'] for x in WR[-1][1]['media']}=={'image','video'})
    # 수정: 기존 사진 1개 빼기 → 저장 후 저장소 파일 지움
    await pg.click('[data-edit="n1"]'); await pg.wait_for_timeout(500)
    chk('수정 창에 기존 2개', await pg.locator('#nMg .mi2').count()==2)
    await pg.click('#nMg button[data-k="0"]'); await pg.click('#dOk'); await pg.wait_for_timeout(1200)
    chk('빼면 저장소에서 지움', DEL==['2026-09/a.jpg'] and len(WR[-1][1]['media'])==1)
    # 삭제
    DEL.clear(); await pg.click('[data-del="n1"]'); await pg.wait_for_timeout(800)
    chk('공지 삭제 시 파일도 지움', '2026-09/b.mp4' in DEL)
    # 50MB 초과 동영상 거부
    await pg.click('[data-act="new"]'); await pg.evaluate("""()=>{ const f=new File([new Uint8Array(10)],'big.mp4',{type:'video/mp4'}); Object.defineProperty(f,'size',{value:60*1024*1024}); const dt=new DataTransfer(); dt.items.add(f); const i=document.querySelector('#nFiles'); i.files=dt.files; i.dispatchEvent(new Event('change')); }""")
    await pg.wait_for_timeout(300); chk('50MB 넘는 동영상은 안 담김', await pg.locator('#nMg .mi2').count()==0)
    chk('오류 없음', not errs); await ctx.close()
    ROLE['v']='owner'; ctx,pg,errs=await open_page(b)
    chk('점주: 공지 쓰기 버튼 없음', await pg.locator('[data-act="new"]').count()==0)
    await ctx.close()
  print('전체', 'OK' if ok else 'FAIL')
asyncio.run(main())
