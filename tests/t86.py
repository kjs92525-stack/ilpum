"""급여 근무표 1000건 초과 조회: 뒤쪽 당일지급·수정 보존·캐시·부분 실패."""
import asyncio
import json
import shutil
import time
from urllib.parse import urlparse, parse_qs
from playwright.async_api import async_playwright

HOST = 'bdqcrbnbuoujozlpttbe.supabase.co'
BON = '0134d989-757a-4b60-9cb3-93245de2cac8'
DAY = '2026-11-25'
ITEMS = [
    {'kind': 'cfg', 'id': 'store', 'data': {'name': '일품집 본점', 'open': '11:00', 'close': '22:00', 'fullH': 10, 'pmH': 5}},
    {'kind': 'cfg', 'id': 'positions', 'data': [{'name': '홀', 'color': '#2F6B3F', 'req': [0]*7}]},
    {'kind': 'staff', 'id': 's1', 'data': {'id': 's1', 'name': '정규직', 'pos': '홀', 'type': 'regular', 'off': [], 'active': True}},
    {'kind': 'pay', 'id': 'staff:s1', 'data': {'k': 'hour', 'v': 12000}},
] + [{'kind': 'dc', 'id': f'2000-01-01|unused{i:04d}', 'data': {}} for i in range(1000)]
ITEMS += [{'kind': 'spot', 'id': f'p{i}', 'data': {'id': f'p{i}', 'date': DAY, 'name': f'일당알바{i}', 'pos': '홀', 'memo': memo}} for i, memo in enumerate(['6', '12', '6.5', '12'])]
ITEMS.sort(key=lambda r: (r['kind'], r['id']))
STATE = {'rows': ITEMS, 'fail': False}
READS, WRITES = [], []


async def handler(route):
    req = route.request
    if 'localhost' in req.url:
        return await route.continue_()
    if HOST not in req.url:
        return await route.abort()
    async def j(value, status=200):
        await route.fulfill(status=status, content_type='application/json', body=json.dumps(value))
    if '/rpc/sch_my_stores' in req.url:
        return await j([{'id': BON, 'name': '일품집 본점', 'role': 'hq', 'is_hq': True, 'can_pay': True}])
    if '/rpc/pay_pin_status' in req.url:
        return await j({'has': True, 'locked': 0})
    if '/rpc/pay_pin_check' in req.url:
        return await j('ok')
    if '/rest/v1/sch_items' in req.url:
        if req.method == 'POST':
            WRITES.append(json.loads(req.post_data))
            return await j([])
        q = parse_qs(urlparse(req.url).query)
        if q.get('select') != ['kind,id,data']:
            return await j([])
        assert q.get('store_id') == ['eq.'+BON]
        assert q.get('order') == ['kind,id']
        assert set(q.get('id', [])) == {'not.like.calc:*', 'not.like.daily:*'}
        assert q.get('kind') == ['neq.site']
        offset, limit = int(q.get('offset', ['0'])[0]), int(q.get('limit', ['1000'])[0])
        READS.append(offset)
        if STATE['fail'] and offset:
            return await j({'message': 'connection failed'}, 503)
        return await j(STATE['rows'][offset:offset+limit])
    await j([])


async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=shutil.which('chromium'), args=['--no-sandbox'])
        pg = await b.new_page(viewport={'width': 1400, 'height': 1000})
        errors = []
        pg.on('pageerror', lambda e: errors.append(str(e)))
        await pg.route('**/*', handler)
        conf = {'ses': {'access_token': 'test', 'refresh_token': 'test', 'expires_at': int(time.time())+10**7, 'user': {'email': 'test@ilpum.invalid'}}}
        await pg.add_init_script(f"localStorage.setItem('ilpum-fr-conf',{json.dumps(json.dumps(conf))});")
        await pg.add_init_script("(()=>{const D=Date;class Fixed extends D{constructor(...a){super(...(a.length?a:['2026-11-25T10:00:00+09:00']))}static now(){return new D('2026-11-25T10:00:00+09:00').getTime()}}window.Date=Fixed})();")
        await pg.goto('http://localhost:8765/pay.html')
        await pg.locator('.pinin').fill('test')
        await pg.locator('#pinForm button[type=submit]').click()
        await pg.wait_for_function("pay.months['2026-11']?.people['일당알바3']")
        assert READS == [0, 1000], READS
        await pg.locator('#dailyBtn').click()
        await pg.locator('.daily-row').first.wait_for()
        payouts = await pg.evaluate('dailyPayoutRows(view.daily).map(r=>r.amount)')
        assert sorted(payouts) == [60000, 65000, 120000, 120000], payouts
        # 같은 자료로 다른 달 계산을 해도 5분 캐시를 사용해 추가 조회하지 않음.
        await pg.evaluate("getSchedule(false)")
        assert READS == [0, 1000]
        # 다시 불러와도 직접 수정 금액·지급완료·사람 추가는 보존.
        await pg.evaluate("()=>{const m=pay.months[pay.cur];m.people['일당알바0'].days[view.daily].amount=77000;m.cash={[view.daily]:{'일당알바0':{paid:true,memo:'지급확인'}}};m.extra={[view.daily]:[{id:'manual',name:'직접추가',amount:30000}]};}")
        await pg.locator('#syncNowBtn').click()
        await pg.wait_for_function("document.querySelector('#toast').textContent.includes('근무를 불러왔어요')")
        assert READS == [0, 1000, 0, 1000]
        rows = await pg.evaluate('dailyPayoutRows(view.daily)')
        target = next(r for r in rows if r['name'] == '일당알바0')
        assert target['amount'] == 77000 and target['paid'] and target['memo'] == '지급확인'
        assert any(r['name'] == '직접추가' for r in rows)
        # 두 번째 페이지 실패 시 불완전한 자료로 기존 달을 덮어쓰지 않음.
        before = await pg.evaluate('JSON.stringify(pay.months[pay.cur])')
        STATE['fail'] = True
        await pg.locator('#syncNowBtn').click()
        await pg.wait_for_function("document.querySelector('#toast').textContent.includes('불러오기 실패')")
        assert await pg.evaluate('JSON.stringify(pay.months[pay.cur])') == before
        STATE['fail'] = False
        # 정확히 1000건일 때는 빈 다음 페이지를 확인하고 종료.
        STATE['rows'] = ITEMS[:1000]
        n = len(READS)
        await pg.evaluate('getSchedule(true)')
        assert READS[n:] == [0, 1000]
        assert not errors, errors
        await b.close()
        print('전체 OK: 1000건 초과·당일지급 4명·캐시·직접 수정 보존·부분 실패·정확히 1000건 종료')


if __name__ == '__main__':
    asyncio.run(main())
