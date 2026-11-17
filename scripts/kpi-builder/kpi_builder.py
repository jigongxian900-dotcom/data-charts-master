"""Bounded KPI cards: validated input -> offline HTML. No business aggregation."""
import argparse
import json
import math
from pathlib import Path


def validate(data):
    def text(value, path):
        if not isinstance(value, str) or not value.strip() or len(value) > 500:
            raise ValueError(f'{path}: expected nonempty string <=500 chars')
    def number(value, path):
        if value is not None and (isinstance(value, bool) or not isinstance(value, (int, float)) or abs(value)>1e15 or not math.isfinite(value)):
            raise ValueError(f'{path}: expected finite number/null, magnitude <=1e15')
    if not isinstance(data, dict):
        raise ValueError('input must be an object')
    for key in ('title', 'scope', 'source'):
        text(data.get(key), key)
    states=data.get('states')
    if not isinstance(states,list) or not 1<=len(states)<=50:
        raise ValueError('states: expected 1..50 entries')
    baseline=None; state_ids=set()
    for state in states:
        if not isinstance(state,dict): raise ValueError('state must be object')
        for key in ('id','label'): text(state.get(key),key)
        if state['id'] in state_ids: raise ValueError('duplicate state id')
        state_ids.add(state['id'])
        metrics=state.get('metrics')
        if not isinstance(metrics,list) or not 1<=len(metrics)<=8: raise ValueError('metrics: expected 1..8 entries')
        identities=[]
        for m in metrics:
            if not isinstance(m,dict): raise ValueError('metric must be object')
            for key in ('id','label','unit','period','definition'): text(m.get(key), key)
            if m.get('kind') not in ('number','percent'): raise ValueError('kind must be number or percent')
            if m.get('polarity') not in ('higher','lower','neutral'): raise ValueError('polarity must be higher/lower/neutral')
            if m.get('precision',1) not in range(0,7) or isinstance(m.get('precision',1),bool): raise ValueError('precision must be 0..6')
            if 'value' not in m: raise ValueError('value is required, null for missing')
            number(m['value'],'value')
            if m['kind']=='percent' and m['unit']!='%': raise ValueError('percent kind uses unit %, value in percentage points e.g.5.1')
            if 'comparison' in m:
                c=m['comparison']
                if not isinstance(c,dict) or 'value' not in c: raise ValueError('comparison requires value')
                text(c.get('label'),'comparison label'); number(c['value'],'comparison value')
            if 'target' in m:
                number(m['target'],'target'); text(m.get('targetPeriod'),'targetPeriod')
                if m['targetPeriod']!=m['period']: raise ValueError('targetPeriod must equal period')
                if m['target'] is not None and m['target']<0: raise ValueError('negative targets are not supported')
            trend=m.get('trend',[])
            if not isinstance(trend,list) or len(trend)>120: raise ValueError('trend expected 0..120 observations')
            dates=set()
            for p in trend:
                if not isinstance(p,dict) or 'value' not in p: raise ValueError('trend point requires date/value')
                text(p.get('date'),'trend date'); number(p['value'],'trend value')
                if p['date'] in dates: raise ValueError('duplicate trend date')
                dates.add(p['date'])
            if trend: text(m.get('trendLabel'),'trendLabel')
            identities.append((m['id'],m['label'],m['unit'],m['kind'],m['polarity']))
        if len(set(m['id'] for m in metrics))!=len(metrics): raise ValueError('duplicate metric id')
        if baseline is None: baseline=identities
        elif identities!=baseline: raise ValueError('states must retain metric identity, order, unit, kind and polarity')
    return data


def build(data):
    validate(data)
    raw=json.dumps(data,ensure_ascii=False,allow_nan=False).replace('<','\\u003c').replace('>','\\u003e').replace('&','\\u0026')
    return Path(__file__).with_name('template.html').read_text(encoding='utf-8').replace('__DATA__', raw)


if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('input'); p.add_argument('output'); a=p.parse_args()
    data=json.loads(Path(a.input).read_text(encoding='utf-8-sig'))
    Path(a.output).write_text(build(data),encoding='utf-8')
