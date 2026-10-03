# 매장 관리: 사용 중지 / 다시 사용 / 이름 바꾸기(중지 표시 유지) (가짜 서버)
import asyncio, json, time
from playwright.async_api import async_playwright
NEW='bdqcrbnbuoujozlpttbe.supabase.co'; BON='0134d989-757a-4b60-9cb3-93245de2cac8'; F1='ad2ffdae-f76b-44cd-a6c6-58514c4e4638'
ST={BON:"일품집 본점",F1:"유천점"}; CALLS=[]
async def handler(r):
  u=r.request.url
  if 'localhost' in u: return await r.continue_()
  if NEW not in u: return await r.fulfill(status=404,body='{}')
  J=lambda o,st=200: r.fulfill(status=st,content_type='application/json',body=json.dumps(o))
  if '/rpc/sch_my_stores' in u: return await J([{"id":i,"name":n,"is_hq":i==BON,"role":"hq","can_pay":i==BON} for i,n in ST.items()])
  if '/rpc/sch_rename_store' in u:
    b=json.loads(r.request.post_data); CALLS.append(('rename',b)); ST[b['p_store']]=b['p_name']; return await J('ok')
  if '/functions/v1/manage-stores' in u:
    b=json.loads(r.request.post_data); CALLS.append(('active',b)) if b['action']=='setactive' else None; M=' (사용 중지)'; n=ST[b['store']]; base=n[:-len(M)] if n.endswith(M) else n
    if b['action']=='delete':
      CALLS.append(('delete',b)); ST.pop(b['store']); return await J({"ok":True,"deleted":base})
    ST[b['store']]= base if b['on'] else base+M; return await J({"ok":True,"name":ST[b['store']],"accounts":2,"failed":0})
  await J([])
S={"ses":{"access_token":"tok","refresh_token":"r","expires_at":int(time.time())+3000,"user":{"email":"x@ilpum.invalid"}},"mode":"remote","url":"https://"+NEW,"key":"k"}
async def main():
  ok=True
  def chk(n,c,x=''):
    nonlocal ok; ok&=bool(c); print('OK  ' if c else 'FAIL',n,x)
  async with async_playwright() as p:
    b=await p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
    ctx=await b.new_context(viewport={'width':1300,'height':900}); pg=await ctx.new_page(); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
    ans=[]
    pg.on('dialog',lambda d: asyncio.ensure_future(d.accept(ans.pop(0) if (d.type=='prompt' and ans) else None) if d.type=='prompt' else d.accept()))
    await pg.route('**/*',handler); await pg.route_web_socket(f'wss://{NEW}/**',lambda ws: asyncio.ensure_future(ws.close()))
    await pg.add_init_script(f"try{{ localStorage.setItem('ilpum-fr-conf',{json.dumps(json.dumps(S))}); }}catch(e){{}}")
    await pg.goto('http://localhost:8765/ilpum-schedule.html?view=hq'); await pg.wait_for_timeout(2200)
    btns=await pg.evaluate("[...document.querySelectorAll('[data-a=storeactive]')].map(b=>b.dataset.id)")
    chk('본점에는 사용 중지 버튼 없음, 가맹점에만', btns==[F1], str(btns))
    await pg.click(f'[data-a=storeactive][data-id="{F1}"]'); await pg.wait_for_timeout(1200)
    chk('중지 호출', ('active',{'action':'setactive','store':F1,'on':False}) in CALLS, str(CALLS))
    t=await pg.inner_text('#main'); chk('카드에 (사용 중지) 표시', '유천점 (사용 중지)' in t)
    lab=await pg.evaluate(f"document.querySelector('[data-a=storeactive][data-id=\"{F1}\"]').textContent")
    chk('버튼이 다시 사용으로 바뀜', lab=='다시 사용', lab)
    ans.append('수성점')
    await pg.click(f'[data-a=storerename][data-id="{F1}"]'); await pg.wait_for_timeout(1200)
    chk('중지된 매장 이름을 바꿔도 중지 표시 유지', ST[F1]=='수성점 (사용 중지)', ST[F1])
    await pg.click(f'[data-a=storeactive][data-id="{F1}"]'); await pg.wait_for_timeout(1200)
    chk('다시 사용하면 표시가 사라짐', ST[F1]=='수성점', ST[F1])
    # 삭제: 중지된 매장에만 버튼이 있고, 이름을 쳐야 지워짐
    chk('사용 중인 매장엔 삭제 버튼 없음', not await pg.evaluate(f"!!document.querySelector('[data-a=storedel][data-id=\"{F1}\"]')"))
    await pg.click(f'[data-a=storeactive][data-id="{F1}"]'); await pg.wait_for_timeout(1000)
    chk('중지하면 삭제 버튼이 생김', await pg.evaluate(f"!!document.querySelector('[data-a=storedel][data-id=\"{F1}\"]')"))
    ans.append('수성점'); await pg.click(f'[data-a=storedel][data-id="{F1}"]'); await pg.wait_for_timeout(1200)
    chk('삭제 호출에 입력한 이름이 실림', ('delete',{'action':'delete','store':F1,'confirm':'수성점'}) in CALLS, str([c for c in CALLS if c[0]=='delete']))
    chk('삭제 뒤 카드가 사라짐', F1 not in ST and '수성점' not in await pg.inner_text('#main'))
    chk('오류 없음', not errs, str(errs)); await ctx.close(); await b.close()
  print('전체 OK' if ok else '실패 있음')
asyncio.run(main())
