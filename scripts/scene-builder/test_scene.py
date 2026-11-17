import json,copy,unittest,hashlib,os
from pathlib import Path
from scene_html import validate,build
D=Path(__file__).parent
R=Path(os.environ.get('CHART_MOTION_RUNTIME',str(D.parents[1]/'assets/chart-motion.js')))
def rect(id,value,x,y,w,h=30):return {'id':id,'value':value,'geometry':{'x':x,'y':y,'width':w,'height':h,'lx':x+w+12,'ly':y+21}}
guides=[{'x1':140,'x2':740,'y1':65,'y2':65,'text':'不合格件 · 共同尺度 0–300'}, {'x1':140,'x2':140,'y1':65,'y2':280,'text':'0'}]
a={'title':'质量负担：保留对象，直接追踪变化','description':'合成验证数据。图形长度为不合格件数的两倍；新增/缺报与真零分开。','source':'合成验证，不代表真实工厂','width':980,'height':330,'marks':[{'id':'mill','kind':'rect','label':'精铣','unit':'件','color':'#b2633b'},{'id':'turn','kind':'rect','label':'车削','unit':'件','color':'#38796c'},{'id':'polish','kind':'rect','label':'抛光','unit':'件','color':'#617e91'}],'states':[{'id':'april','label':'4月','semanticSpace':'reject-count-axis300','description':'同单位、同对象、同尺度','guides':guides,'values':[rect('mill',80,140,100,160),rect('turn',180,140,160,360),rect('polish',100,140,220,200)]},{'id':'may','label':'5月','semanticSpace':'reject-count-axis300','description':'精铣变为300件；同一对象从当前绘制位置连续变化','guides':guides,'values':[rect('mill',300,140,100,600),rect('turn',120,140,160,240),rect('polish',165,140,220,330)]},{'id':'partial','label':'范围与缺报','semanticSpace':'reject-count-axis300','description':'精铣缺报、车削不在范围，抛光真零。缺报不补零。','guides':guides,'values':[{'id':'mill','value':None},rect('polish',0,140,100,0)]}]}
b={'title':'资金结构：移动边界，不重播整条','description':'两期同单位金额比较；占比视图改变坐标语义，因此立即切换。数字标签在过渡期间明确为目标值。','source':'合成公益筹款数据，单位万元','width':980,'height':300,'marks':[{'id':'free','kind':'rect','label':'非限定','unit':'万元','color':'#38796c'},{'id':'restricted','kind':'rect','label':'限定','unit':'万元','color':'#b2633b'}],'states':[]}
for id,label,f,r in [('h1','上半年',300,300),('h2','下半年',270,630)]:
 vals=[rect('free',f,100,100,f*.7,56),rect('restricted',r,100+f*.7,100,r*.7,56)]
 vals[0]['geometry'].update(lx=100,ly=195);vals[1]['geometry'].update(lx=470,ly=195)
 b['states'].append({'id':id,'label':label,'semanticSpace':'amount-axis900','description':'固定0–900万元坐标下，分段宽度和边界连续变化。','guides':[{'x1':100,'x2':730,'y1':70,'y2':70,'text':'0–900 万元共同尺度'}],'values':vals})
v=[rect('free',30,100,100,189,56),rect('restricted',70,289,100,441,56)]
for z in v:z['unit']='%'
v[0]['geometry'].update(lx=100,ly=195);v[1]['geometry'].update(lx=470,ly=195)
b['states'].append({'id':'ratio','label':'下半年占比','semanticSpace':'ratio-axis100','description':'单位改为百分比，坐标语义改变：即时切换，禁止金额到占比伪插值。','guides':[{'x1':100,'x2':730,'y1':70,'y2':70,'text':'0–100%'}],'values':v})
for name,s in [('manufacturing',a),('funding',b)]:
 (D/(name+'.json')).write_text(json.dumps(s,ensure_ascii=False,indent=2),encoding='utf-8');(D/(name+'.html')).write_text(build(s,R.read_text(encoding='utf-8')),encoding='utf-8')
class Contract(unittest.TestCase):
 def test_valid_and_value_swap(self):
  for s in [a,b]:validate(s)
  s=copy.deepcopy(a);s['states'][0]['values'][0]['value']=.00004;validate(s)
 def test_rejections(self):
  mutations=[lambda s:s['marks'][0].update(kind='path'),lambda s:s['states'][0]['values'][0]['geometry'].update(width=-1),lambda s:s['states'][0]['values'][0].update(value=True),lambda s:s['states'][0]['values'][0].update(value=float('nan')),lambda s:s['states'][0]['values'][0].update(value=10**1000),lambda s:s['states'][0]['values'][0].update(value=None),lambda s:s['states'][1]['values'][0].update(unit='%'),lambda s:s['states'][1].update(guides=[{'x1':140,'x2':740,'y1':65,'y2':65,'text':'different axis'}]),lambda s:s.update(unmapped_business='ignored'),lambda s:s['states'][1]['values'].append(s['states'][1]['values'][0])]
  for i,f in enumerate(mutations):
   with self.subTest(i=i):
    s=copy.deepcopy(a);f(s)
    with self.assertRaises(ValueError):validate(s)
 def test_marker_escape(self):
  s=copy.deepcopy(a);s['title']='@@RUNTIME@@ </script><script>window.bad=1</script>'
  out=build(s,'window.runtime=true;');self.assertNotIn('<script>window.bad',out);self.assertEqual(out.count('window.runtime=true;'),1)
 def test_edge(self):
  s=copy.deepcopy(a);s['marks'][0]['id']='__proto__'
  for st in s['states']:
   for v in st['values']:
    if v['id']=='mill':v['id']='__proto__'
  s['states'][0]['values'][0]['value']=-1e15;s['states'][1]['values'][0]['value']=1e15
  s['marks'] += [{'id':'point','kind':'circle','label':'点','unit':'件','color':'#38796c'},{'id':'rule','kind':'line','label':'线','unit':'件','color':'#617e91'}]
  for i,st in enumerate(s['states']):
   x=-1e6 if i==0 else 1e6
   st['values'] += [{'id':'point','value':.00004,'geometry':{'cx':x,'cy':20,'r':4,'lx':0,'ly':0}},{'id':'rule','value':0,'geometry':{'x1':x,'y1':0,'x2':100,'y2':100,'lx':0,'ly':0}}]
  (D/'edge.json').write_text(json.dumps(s),encoding='utf-8');(D/'edge.html').write_text(build(s,R.read_text(encoding='utf-8')),encoding='utf-8');validate(s)
if __name__=='__main__':unittest.main()
