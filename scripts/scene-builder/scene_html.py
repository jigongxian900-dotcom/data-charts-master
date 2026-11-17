import argparse,json,math,re
from pathlib import Path
ATTRS={'rect':['x','y','width','height','lx','ly'],'circle':['cx','cy','r','lx','ly'],'line':['x1','y1','x2','y2','lx','ly']}
def obj(x,allowed,where):
    if not isinstance(x,dict) or set(x)-set(allowed):raise ValueError(where+': unknown fields or not object')
def num(x,where,limit=1e6):
    if isinstance(x,bool) or not isinstance(x,(int,float)):raise ValueError(where+': finite number required')
    try: good=math.isfinite(x) and abs(x)<=limit
    except OverflowError:good=False
    if not good:raise ValueError(where+': number outside finite bounds')
def string(x,where):
    if not isinstance(x,str) or not x.strip() or len(x)>500:raise ValueError(where+': nonempty string <=500 required')
def validate(s):
    obj(s,['title','description','source','width','height','marks','states'],'root')
    for k in ['title','description','source']:string(s.get(k),k)
    for k in ['width','height']:
        num(s.get(k),k,5000)
        if s[k]<100:raise ValueError(k+': minimum 100')
    if not isinstance(s.get('marks'),list) or not 1<=len(s['marks'])<=100:raise ValueError('marks: 1..100 required')
    marks={}
    for m in s['marks']:
        obj(m,['id','kind','label','unit','color'],'mark')
        for k in ['id','label','unit']:string(m.get(k),'mark.'+k)
        if m['id'] in marks or m.get('kind') not in ATTRS:raise ValueError('duplicate ID or unsupported kind')
        if not re.fullmatch('#[0-9a-fA-F]{6}',m.get('color','')):raise ValueError('color must be hex')
        marks[m['id']]=m
    if not isinstance(s.get('states'),list) or not 2<=len(s['states'])<=20:raise ValueError('states: 2..20 required')
    ids=set();spaces={}
    for st in s['states']:
        obj(st,['id','label','semanticSpace','description','guides','values'],'state')
        for k in ['id','label','semanticSpace','description']:string(st.get(k),'state.'+k)
        if st['id'] in ids:raise ValueError('duplicate state ID')
        ids.add(st['id'])
        if not isinstance(st.get('guides'),list) or len(st['guides'])>60:raise ValueError('guides list <=60 required')
        for g in st['guides']:
            obj(g,['x1','y1','x2','y2','text'],'guide')
            for k in ['x1','y1','x2','y2']:num(g.get(k),'guide.'+k)
            if 'text' in g:string(g['text'],'guide.text')
        sig=json.dumps(st['guides'],sort_keys=True)
        old=spaces.setdefault(st['semanticSpace'],{'guides':sig,'units':{}})
        if old['guides']!=sig:raise ValueError('axes/guides change requires a different semanticSpace')
        if not isinstance(st.get('values'),list) or len(st['values'])>100:raise ValueError('values list <=100 required')
        seen=set()
        for v in st['values']:
            obj(v,['id','value','geometry','unit'],'value')
            if v.get('id') not in marks or v['id'] in seen:raise ValueError('unknown or duplicate value ID')
            seen.add(v['id']);m=marks[v['id']]
            unit=v.get('unit',m['unit']);string(unit,'value.unit')
            if old['units'].setdefault(v['id'],unit)!=unit:raise ValueError('unit change requires different semanticSpace')
            if 'value' not in v:raise ValueError('value missing; explicit null means missing')
            if v['value'] is None:
                if 'geometry' in v:raise ValueError('missing data cannot have geometry')
                continue
            num(v['value'],'value',1e15);g=v.get('geometry')
            if not isinstance(g,dict) or set(g)!=set(ATTRS[m['kind']]):raise ValueError('geometry must exactly match primitive contract')
            for k,x in g.items():
                num(x,'geometry.'+k)
                if k in ['width','height','r'] and x<0:raise ValueError('negative extent')
    return s

def build(spec,runtime):
    validate(spec)
    template=Path(__file__).with_name('scene-template.html').read_text(encoding='utf-8')
    # Single replacement pass: hostile marker strings in user data are inert.
    replacements={'@@SPEC@@':json.dumps(json.dumps(spec,ensure_ascii=False),ensure_ascii=False).replace('<','\\u003c'),'@@RUNTIME@@':runtime}
    return re.sub(r'@@SPEC@@|@@RUNTIME@@',lambda m:replacements[m.group()],template)
if __name__=='__main__':
    p=argparse.ArgumentParser(description='Bounded authored numeric SVG scene; no aggregation or automatic chart selection.')
    p.add_argument('spec',type=Path);p.add_argument('output',type=Path);p.add_argument('--runtime',type=Path,required=True)
    a=p.parse_args()
    try:result=build(json.loads(a.spec.read_text(encoding='utf-8-sig')),a.runtime.read_text(encoding='utf-8'))
    except (ValueError,TypeError,KeyError) as e:p.error(str(e))
    a.output.write_text(result,encoding='utf-8')
