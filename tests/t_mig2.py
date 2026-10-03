import asyncio, json
from playwright.async_api import async_playwright
OLD='https://fmzpmekypmjuydgxpnlu.supabase.co'; NEW='https://bdqcrbnbuoujozlpttbe.supabase.co'; BON='0134d989-757a-4b60-9cb3-93245de2cac8'
old_state=json.load(open('old_state.json'))
old_res=[{"id":"2026-10-01","data":{"items":[
  {"id":"a1","name":"홍길동","phone":"010-1111-2222","time":"18:30","pp":"5+1","tables":["33","34"],"req":"창가","done":True,"u":1},
  {"id":"a2","name":"김철수","time":"19:00","pp":"4","tables":["R1-1"],"tnote":"취소 (노쇼)","u":1},
  {"id":"a3","name":"삭제","time":"12:00","pp":"2","deleted":True,"u":1}]}},
  {"id":"2026-10-02","data":{"items":[{"id":"b1","name":"박영희","phone":"01099998888","time":"12:00","pp":"2","tables":["5"],"u":1},{"id":"b2","name":"이시간없음","time":"","pp":"3","u":1}]}}]
DB={'sch':{}, 'res':{}}
seed=[("staff","sTEMP1",{"name":"임시직원"},False),("dc","2026-10-01|sTEMP1",{"st":"off"},False),("pay","spot:sTEMP1",None,False),("sales","2026-10-01",{"v":1},False),
      ("cfg","positions",[{"name":n,"color":"#000","req":[0]*7} for n in ['카운터','홀','그릴','주방','장치','주차','장잡','배송']],False)]
for k,i,d,dl in seed: DB['sch'][(k,i)]={"kind":k,"id":i,"data":d,"deleted":dl}
STATE={'open':True}; CALLS=[]
async def main():
  async with async_playwright() as p:
    b=await p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
    ctx=await b.new_context(viewport={'width':900,'height':1100},accept_downloads=True); pg=await ctx.new_page(); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
    dls=[]; pg.on('download',lambda d: dls.append(d.suggested_filename))
    async def route(r):
      u=r.request.url; m=r.request.method; h=r.request.headers
      J=lambda o,st=200: r.fulfill(status=st,content_type='application/json',body=json.dumps(o))
      if u.startswith('file:'): return await r.continue_()
      if u.startswith(OLD):
        assert m=='GET'
        if 'schedule_state' in u: return await J([{"data":old_state,"rev":7}])
        if 'reservations_day' in u: return await J(old_res)
      if u.startswith(NEW):
        assert '/auth/' not in u, '로그인 요청이 나감!'
        assert h.get('authorization','').startswith('Bearer eyJ') and 'rpc/' in u
        body=json.loads(r.request.post_data or '{}'); fn=u.split('/rpc/')[1]; CALLS.append(fn)
        if fn=='sch_mig_state': return await J([{"is_open":STATE['open'],"store_id":BON,"store_name":"일품집 본점","until":"2026-10-01T03:00:00Z"}])
        if not STATE['open']: return await J('closed') if fn.startswith('sch_mig_put') else await J(None)
        if fn=='sch_mig_existing': return await J(list(DB['sch'].values()))
        if fn=='sch_mig_put_items':
          for row in body['p_rows']: DB['sch'][(row['kind'],row['id'])]={"kind":row['kind'],"id":row['id'],"data":row.get('data'),"deleted":row['deleted']}
          return await J('ok')
        if fn=='sch_mig_put_reservations':
          for row in body['p_rows']: assert row['size']>0 and row['rtime'] and row['name']; DB['res'][row['id']]=row
          return await J('ok')
        if fn=='sch_mig_counts':
          c={}
          for v in DB['sch'].values():
            if not v['deleted']: c[v['kind']]=c.get(v['kind'],0)+1
          return await J({"items":c,"reservations":len(DB['res'])})
      await r.fulfill(status=404,body='{}')
    await pg.route('**/*', route)
    await pg.goto('http://localhost:8766/ilpum-migrate.html'); await pg.wait_for_timeout(700)
    print('로그인 입력칸 없음:', await pg.evaluate("!document.getElementById('pw')&&!document.getElementById('bLogin')"), '| 창구:', (await pg.inner_text('#winMsg')).replace('\n',' '))
    print('처음 옮기기 버튼 비활성:', await pg.is_disabled('#bGo'))
    await pg.click('#bRead'); await pg.wait_for_timeout(900); print('읽기 후 옮기기 활성:', not await pg.is_disabled('#bGo'))
    await pg.click('#bGo'); await pg.wait_for_timeout(1500)
    print('결과:', (await pg.inner_text('#result')).replace('\n',' | ').replace('\t',': '))
    print('파일:', dls)
    cnt={}
    for v in DB['sch'].values():
      if not v['deleted']: cnt[v['kind']]=cnt.get(v['kind'],0)+1
    print('새 서버(가짜):', cnt, '| 임시직원 정리됨:', DB['sch'][('staff','sTEMP1')]['deleted'], '| 임시 금액 정리됨:', DB['sch'][('pay','spot:sTEMP1')]['deleted'], '| 매출 보존:', not DB['sch'][('sales','2026-10-01')]['deleted'])
    print('예약:', sorted((v['rdate'],v['rtime'],v['name'],v['size'],v['table_no']) for v in DB['res'].values()))
    n0=len(DB['res']); await pg.click('#bGo'); await pg.wait_for_timeout(1200); print('다시 실행 예약 수:', n0,'→',len(DB['res']))
    # 창구가 닫힌 경우
    STATE['open']=False; await pg.reload(); await pg.wait_for_timeout(600); print('닫힌 창구 안내:', (await pg.inner_text('#winMsg')).replace('\n',' '), '| 버튼 비활성:', await pg.is_disabled('#bGo'))
    print('errs',errs); await b.close()
asyncio.run(main())
