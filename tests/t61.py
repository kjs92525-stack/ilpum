# 발주: "물건 직접 적기" — 직원·발주 전용은 품목 저장 칸 없이 이번 발주에만 담겨 발주가 들어감(예전엔 품목 저장이 거부돼 발주 전체 실패),
#        점주는 "품목에 바로 등록"으로 목록에 생기고 수량이 담김 (가짜 서버, 품목 쓰기는 점주·매니저·본사만 허용)
import asyncio, json, time
from playwright.async_api import async_playwright
NEW='bdqcrbnbuoujozlpttbe.supabase.co'; F1='ad2ffdae-f76b-44cd-a6c6-58514c4e4638'
ROLE={'v':'order'}; ITEMS={}; ORDERS={}
ITEMS['a']={"store_id":F1,"id":"a","category":"주방","name":"깨","stock":"3kg","links":[],"sort":0}
async def handler(r):
  u=r.request.url; m=r.request.method
  if 'localhost' in u: return await r.continue_()
  J=lambda o,st=200: r.fulfill(status=st,content_type='application/json',body=json.dumps(o))
  if '/rpc/sch_my_stores' in u: return await J([{"id":F1,"name":"유천점","is_hq":False,"role":ROLE['v']}])
  if '/rest/v1/wh_' in u:
    tab='wh_items' if 'wh_items' in u else 'wh_orders'; D=ITEMS if tab=='wh_items' else ORDERS
    if m=='GET': return await J(list(D.values()))
    if m=='POST':
      if tab=='wh_items' and ROLE['v'] not in ('hq','owner','manager'): return await J({"message":"new row violates row-level security policy"},403)
      b=json.loads(r.request.post_data); b=b if isinstance(b,list) else [b]
      for x in b: x.setdefault('created_at','2026-10-06T05:00:00+00:00'); x.setdefault('status','open'); D[x.get('id') or x['code']]=x
      return await r.fulfill(status=201,body='')
  await J([])
S={"ses":{"access_token":"tok","refresh_token":"r","expires_at":int(time.time())+3000,"user":{"email":"x@ilpum.invalid"}}}
async def run(b,role):
  ROLE['v']=role; ORDERS.clear(); [ITEMS.pop(k) for k in list(ITEMS) if k!='a']
  ctx=await b.new_context(viewport={'width':1100,'height':900}); pg=await ctx.new_page(); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
  await pg.route('**/*',handler); await pg.add_init_script(f"try{{ localStorage.setItem('ilpum-fr-conf',{json.dumps(json.dumps(S))}); }}catch(e){{}}")
  await pg.goto('http://localhost:8765/order.html'); await pg.wait_for_timeout(1200)
  await pg.click('[data-act=xadd]'); await pg.wait_for_timeout(200)
  hasSave=await pg.is_visible('#xSave')
  await pg.fill('#xName','깻잎'); await pg.fill('#xQty','3'); await pg.fill('#xUnit','박스'); await pg.click('#dOk'); await pg.wait_for_timeout(800)
  await pg.click('#send'); await pg.wait_for_timeout(1000)
  return ctx,pg,errs,hasSave
async def main():
  ok=True
  def chk(n,c,x=''):
    nonlocal ok; ok&=bool(c); print('OK  ' if c else 'FAIL',n,x)
  async with async_playwright() as p:
    b=await p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
    for role in ('order','staff'):
      ctx,pg,errs,hasSave=await run(b,role)
      lines=[l for o in ORDERS.values() for l in o['lines']]
      chk(f'[{role}] 품목 저장 칸 안 보임', not hasSave)
      chk(f'[{role}] 직접 적은 물건이 발주에 들어감', any(l['name']=='깻잎' and l['qty']==3 and l['unit']=='박스' for l in lines), str(lines))
      chk(f'[{role}] 품목 목록은 그대로', set(ITEMS)=={'a'}); chk(f'[{role}] 오류 없음', not errs, str(errs)); await ctx.close()
    ctx,pg,errs,hasSave=await run(b,'owner')
    lines=[l for o in ORDERS.values() for l in o['lines']]
    chk('[owner] 품목 저장 칸 보임', hasSave)
    chk('[owner] 품목에 바로 등록됨', any(x['name']=='깻잎' for x in ITEMS.values()), str(list(ITEMS.values())))
    chk('[owner] 발주에도 들어감(단위 박스)', any(l['name']=='깻잎' and l['qty']==3 and l['unit']=='박스' for l in lines), str(lines))
    chk('[owner] 오류 없음', not errs, str(errs)); await ctx.close(); await b.close()
  print('전체 OK' if ok else '실패 있음')
asyncio.run(main())
