"""Rebuild D01 with Python standard library: python producer.py [source-data.json]."""
import json, pathlib, sys, hashlib
from collections import defaultdict
ROOT = pathlib.Path(__file__).resolve().parent
src = pathlib.Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'source-data.json'
d = json.loads(src.read_text('utf-8'))
credits=defaultdict(int); paid=defaultdict(int); used=defaultdict(int); fx=defaultdict(int)
iv={i['invoice_id']:i for i in d['invoices']}; rp={p['receipt_id']:p for p in d['receipts']}
for c in d['credit_notes']: credits[c['invoice_id']]+=c['amount_minor']
alloc=[]
for a in d['allocations']:
    i=iv[a['invoice_id']];p=rp[a['receipt_id']]
    assert i['currency']==p['currency']
    paid[a['invoice_id']]+=a['amount_minor'];used[a['receipt_id']]+=a['amount_minor']
    v=a['amount_minor']*(p['receipt_fx']-i['invoice_fx']);fx[a['invoice_id']]+=v
    alloc.append(dict(a,customer=i['customer'],currency=i['currency'],invoice_fx=i['invoice_fx'],receipt_fx=p['receipt_fx'],settled_fx=v))
inv=[]
for i in d['invoices']:
    k=i['invoice_id'];net=i['face_minor']-credits[k];op=net-paid[k];age=max(0,d['snapshot_day']-i['due_day'])
    assert 0<=i['disputed_minor']<=op
    inv.append(dict(i,credits=credits[k],net=net,allocated=paid[k],open=op,age=age,overdue=i['due_day']<d['snapshot_day'],bucket='未到期' if i['due_day']>=d['snapshot_day'] else '1–15日' if age<=15 else '16–30日' if age<=30 else '31日以上',book=op*i['invoice_fx'],current=op*d['current_fx'][i['currency']],revaluation=op*(d['current_fx'][i['currency']]-i['invoice_fx']),settled_fx=fx[k]))
rec=[dict(p,allocated=used[p['receipt_id']],unallocated=p['received_minor']-used[p['receipt_id']],net_cash=p['received_minor']-p['bank_fee_minor']) for p in d['receipts']]
assert all(p['unallocated']>=0 for p in rec)
# Independent event-ledger algorithm: debit faces, credit notes and allocation events.
balance={k:i['face_minor'] for k,i in iv.items()}
cash={k:p['received_minor'] for k,p in rp.items()}
for event in d['credit_notes']:balance[event['invoice_id']]-=event['amount_minor']
for event in d['allocations']:
    balance[event['invoice_id']]-=event['amount_minor'];cash[event['receipt_id']]-=event['amount_minor']
assert balance=={i['invoice_id']:i['open'] for i in inv}
assert cash=={p['receipt_id']:p['unallocated'] for p in rec}
checks={}
for cur in d['current_fx']:
    ii=[i for i in inv if i['currency']==cur];pp=[p for p in rec if p['currency']==cur]
    checks[cur]={'face_less_credits_equals_allocations_plus_open':sum(i['net'] for i in ii)==sum(i['allocated']+i['open'] for i in ii),'receipts_equal_allocations_plus_unallocated':sum(p['received_minor'] for p in pp)==sum(p['allocated']+p['unallocated'] for p in pp),'fee_only_reduces_net_cash':sum(p['net_cash']+p['bank_fee_minor'] for p in pp)==sum(p['received_minor'] for p in pp)}
out={'source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'units':'synthetic currency minor units; FX integer LC minor / original minor','snapshot_day':d['snapshot_day'],'invoices':inv,'receipts':rec,'allocations':alloc,'credit_notes':d['credit_notes'],'invariants':checks,'independent_event_ledger':'PASS'}
(ROOT/'computed.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),'utf-8', newline='\n')
template=(ROOT/'template.html').read_text('utf-8')
html=template.replace('__SOURCE_JSON__',json.dumps(d,ensure_ascii=False).replace('</','<\\/')).replace('__COMPUTED_JSON__',json.dumps(out,ensure_ascii=False).replace('</','<\\/'))
(ROOT/'artifact.html').write_text(html,'utf-8',newline='\n')
print(json.dumps({'artifact_sha256':hashlib.sha256((ROOT/'artifact.html').read_bytes()).hexdigest(),'invoice_rows':len(inv),'receipt_rows':len(rec),'allocation_rows':len(alloc),'invariants':checks},ensure_ascii=False))
