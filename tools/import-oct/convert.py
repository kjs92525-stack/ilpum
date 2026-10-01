import json, re, datetime as dt, hashlib
expected=json.load(open('expected.json')); staff_raw=json.load(open('staff.json')); ex=json.load(open('ex.json'))
D=lambda s: dt.date.fromisoformat(s)
WD={'일':0,'월':1,'화':2,'수':3,'목':4,'금':5,'토':6}
def sid(name): return 's'+hashlib.md5(name.encode()).hexdigest()[:8]
# ---- 직원
staff=[]; fixed=set()
for i,s in enumerate(staff_raw):
    raw=s['raw']; isfix=raw.endswith(' (고정알바)'); name=raw.replace(' (고정알바)','')
    off=[] if (isfix or s['off'] in ('없음','주간 입력')) else sorted(WD[x.strip()] for x in s['off'].split(','))
    staff.append(dict(id=sid(name),name=name,pos=s['pos'],type='weekly' if isfix else 'regular',off=off,active=True,order=i))
    if isfix: fixed.add(name)
byname={s['name']:s for s in staff}
# ---- 예외 → dc / spot
dc={}; spot=[]; pay={}
def dck(date,name): return f"{date}|{byname[name]['id']}"
def parse_alba(memo,pm):
    m=(memo or '').strip(); sh={'k':'pm'} if pm else None; pv=None; note=m
    mm=re.match(r'^일급\s*([\d,]+)$',m)
    if mm: pv=int(mm.group(1).replace(',','')); note=''
    elif re.match(r'^\d+(\.\d+)?$',m): pv=round(float(m)*10000); note=''
    elif (mm:=re.match(r'^일당백\s*(\d+(\.\d+)?)$',m)): pv=round(float(mm.group(1))*10000); note='일당백'
    elif (mm:=re.match(r'^(\d{1,2})-(\d{1,2})시$',m)):
        a,b=int(mm.group(1)),int(mm.group(2)); sh={'k':'t','s':f'{a:02d}:00','e':f'{b:02d}:00' if b!=22 else ''}; note=''
    elif (mm:=re.match(r'^(.*?)\s*/\s*(\d{1,2})시\s*출근$',m)):
        sh={'k':'t','s':f'{int(mm.group(2)):02d}:00','e':''}; note=mm.group(1).strip()
    return sh,pv,note
for i,e in enumerate(ex):
    t=e['type']; date=e['date']; name=e['name']
    if t.startswith('당일알바'):
        pm=t.endswith('(오후)'); sh,pv,note=parse_alba(e['memo'],pm)
        x=dict(id='a'+hashlib.md5(f'{date}{name}{i}'.encode()).hexdigest()[:8],date=date,name=name,pos=e['pos'])
        if sh: x['sh']=sh
        if note: x['memo']=note
        spot.append(x)
        if pv: pay['spot:'+x['id']]=dict(k='day',v=pv)
        continue
    k=dck(date,name); o=dc.setdefault(k,{})
    if t=='휴무': o['st']='off'
    elif t=='월차': o['st']='annual'
    elif t=='휴무지급': o['st']='paidoff'
    elif t=='추가근무': o['st']='extra'; o['pos']=e['pos']
    elif t=='근무변경': o['pos']=e['pos']
    elif t=='오후출근': o.setdefault('sh',{'k':'pm'})
    if e['memo'] and t not in ('오후출근',): o['memo']=e['memo']
# ---- 고정알바 주간 입력(aw) 역산: 스케줄에서 보이는 날 - (예외로 설명되는 날)
def strip_pm(tok): return (tok[:-4],True) if tok.endswith('(오후)') else (tok,False)
presence={}   # (date,name)->list of pm flags (staff+spot 구분 없이)
for date,v in expected.items():
    for p,toks in v['pos'].items():
        for t in toks:
            n,pm=strip_pm(t); presence.setdefault((date,n),[]).append(pm)
spot_names={}
for x in spot: spot_names.setdefault((x['date'],x['name']),[]).append(x)
dcmap={(k.split('|')[0],k.split('|')[1]):v for k,v in dc.items()}
aw={}
def weekstart(d): return d-dt.timedelta(days=d.weekday())
weeks=sorted({weekstart(D(d)) for d in expected})
def plain_off(date,f):   # 휴무 줄에 '이름'만 있으면 = 그 주 주간 입력이 있고 그날 쉬는 사람
    return any(t==f for t in expected[date]['off'])
for f in fixed:
    s=byname[f]
    for w in weeks:
        on=[]; pm=[]; offs=[]; has=False
        for i in range(7):
            d=(w+dt.timedelta(days=i)).isoformat()
            if d not in expected: continue
            flags=list(presence.get((d,f),[]))
            for x in spot_names.get((d,f),[]):            # 같은 이름의 당일알바 몫은 제외
                pmx=(x.get('sh') or {}).get('k')=='pm'
                if pmx in flags: flags.remove(pmx)
                elif flags: flags.pop()
            ex_dc=dcmap.get((d,s['id']),{})
            if plain_off(d,f): has=True; offs.append(i); continue
            if not flags: continue
            if ex_dc.get('st')=='extra': continue          # 추가근무로 설명됨
            has=True; on.append(i)
            if flags[0] and not ex_dc.get('sh'): pm.append(i)
        if has:
            # 예외로 쉬는 날(휴무)은 주간 입력상으로는 근무일로 둠 (예외가 덮어씀)
            aw.setdefault(w.isoformat(),{})[s['id']]=dict(off=sorted(offs),pm=pm)
items={'staff':{s['id']:s for s in staff},'dc':dc,'spot':{x['id']:x for x in spot},'aw':aw,'pay':pay}
json.dump(items,open('items.json','w'),ensure_ascii=False,indent=1)
print('staff',len(staff),'fixed',len(fixed),'dc',len(dc),'spot',len(spot),'pay',len(pay),'aw weeks',{k:len(v) for k,v in aw.items()})
