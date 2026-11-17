import copy,json,unittest
from pathlib import Path
from kpi_builder import validate,build
ROOT=Path(__file__).parent
def metric(id,label,value,unit='万元',**extra):
    return dict(id=id,label=label,value=value,unit=unit,kind='number',polarity='higher',period='2026-10',definition='合成验证数据，不代表真实业务',**extra)
def fixture():
    a=metric('revenue','营业额',120,target=100,targetPeriod='2026-10',comparison={'label':'去年同期','value':100})
    b=metric('cost','每单配送成本',8,unit='元/单',trendLabel='近6期 · 单期值',trend=[{'date':str(i),'value':v} for i,v in enumerate([10,9,None,10,9,8])],comparison={'label':'去年同期','value':10});b['polarity']='lower'
    c=metric('margin','利润率',5.1,unit='%',comparison={'label':'去年同期','value':13.5});c['kind']='percent'
    d=metric('missing','待核验指标',None,target=None,targetPeriod='2026-10')
    first={'id':'oct','label':'10月（合成）','metrics':[a,b,c,d]}
    second=copy.deepcopy(first);second.update(id='sep',label='9月（合成）')
    for m in second['metrics']:
        m['period']='2026-09'
        if 'targetPeriod'in m:m['targetPeriod']='2026-09'
    second['metrics'][0]['value']=60;second['metrics'][1]['value']=11
    second['metrics'][3]['value']=0
    return dict(title='配送业务指标 · 合成验证',scope='同一配送业务范围；数值均为验证用构造，不作经营结论',source='本地合成夹具',states=[first,second])
def edge_fixture():
    d=fixture();d['title']='边界数据验证 </script><img src=x onerror=alert(1)>'
    m=d['states'][0]['metrics'];m[0].update(value=-25,target=100);m[0]['comparison']['value']=0
    m[1]['trend']=[{'date':'2026-09','value':None},{'date':'2026-10','value':8}]
    m[2].update(value=5.1,target=10,targetPeriod='2026-10');m[3].update(value=5,target=0)
    big=metric('big','极长中文指标名称用于检验换行保留完整单位与真实读数',123456789012345,unit='人民币元',trendLabel='恒定序列',trend=[{'date':str(i),'value':1} for i in range(3)])
    empty=metric('empty','全部缺报趋势',None,trendLabel='全部缺报',trend=[{'date':str(i),'value':None} for i in range(3)])
    m.extend([big,empty]);d['states']=d['states'][:1]
    return d
def second_business():
    d=fixture();d.update(title='水处理厂 · 合成月度验证',scope='同一厂区；预先聚合的合成月度读数，不代表实际监测')
    for index,state in enumerate(d['states']):
        ms=state['metrics'];ms[0].update(label='处理水量',unit='万立方米',definition='月处理水量；目标与实际同月同范围')
        ms[1].update(label='单位处理电耗',unit='千瓦时/立方米',definition='总耗电÷处理水量；不平均每日比率')
        ms[2].update(label='出水达标率',definition='达标检测次数÷有效检测次数；缺测不计为达标')
        ms[3].update(label='复核中的污泥处理量',unit='吨',definition='待复核，不以缺报代替零')
        ms[0].update(value=[96,104][index],target=100,comparison={'label':'去年同期','value':[90,95][index]})
        values=[.45,.44,.43,None,.42,.38] if index==0 else [.47,.46,.45,None,.44,.42]
        ms[1].update(value=[.38,.42][index],precision=2,comparison={'label':'去年同期','value':.44},trend=[{'date':f'2026-{i+5-index:02d}','value':v} for i,v in enumerate(values)])
        ms[2].update(value=[98.4,97.9][index],comparison={'label':'去年同期','value':97.5})
    return d
class Tests(unittest.TestCase):
    def test_valid(self):validate(fixture());validate(edge_fixture());validate(second_business())
    def test_script_safety(self):self.assertNotIn('</script><img',build(edge_fixture()))
    def test_giant_integer_rejected(self):
        d=fixture();d['states'][0]['metrics'][0]['value']=10**400
        with self.assertRaises(ValueError):validate(d)
    def test_rejects(self):
        changes=[lambda d:d['states'][0]['metrics'][0].update(value=True),lambda d:d['states'][0]['metrics'][0].update(value=float('nan')),lambda d:d['states'][0]['metrics'][0].update(target=-1),lambda d:d['states'][0]['metrics'][0].update(targetPeriod='bad'),lambda d:d['states'][1]['metrics'][0].update(unit='元'),lambda d:d['states'][0]['metrics'][0].update(value='10'),lambda d:d['states'][0]['metrics'][0].pop('value'),lambda d:d['states'][0]['metrics'][1]['trend'].append({'date':'0','value':2}),lambda d:d['states'][0]['metrics'][0].update(precision=8)]
        for change in changes:
            d=fixture();change(d)
            with self.subTest(change=change),self.assertRaises(ValueError):validate(d)
if __name__=='__main__':
    for name,data in [('demo',fixture()),('edge',edge_fixture()),('water',second_business())]:
        (ROOT/f'{name}.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
        (ROOT/f'{name}.html').write_text(build(data),encoding='utf-8')
    d=fixture();d['states']=d['states'][:1];ms=d['states'][0]['metrics']
    ms[0].update(value=5,target=10,polarity='lower')
    ms[1].update(value=.004,precision=1,target=1,targetPeriod='2026-10',polarity='neutral')
    ms[1]['trend'][0]['value']=.0004
    ms[2].update(value=1e15,target=1e-300,targetPeriod='2026-10',kind='number',unit='元')
    ms[3].update(value=.004,comparison={'label':'极小基期','value':1e-300})
    (ROOT/'review-cases.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
    (ROOT/'review-cases.html').write_text(build(d),encoding='utf-8')
    unittest.main()
