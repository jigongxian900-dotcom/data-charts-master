import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

HERE=Path(__file__).parent
SKILL=Path(os.environ.get('CHART_SKILL_TEST_ROOT', str(HERE.parent)))
EVIDENCE=SKILL/'.test-output'/'router'
class RouterTests(unittest.TestCase):
    def run_case(self, req):
        folder=Path(tempfile.mkdtemp(prefix='route-test-',dir=EVIDENCE))
        path=folder/'request.json'; path.write_text(json.dumps(req, ensure_ascii=False),encoding='utf-8')
        run=subprocess.run([sys.executable,str(HERE/'bounded_build.py'),str(path),str(folder/'result'),'--skill-dir',str(SKILL)],capture_output=True,text=True,encoding='utf-8',errors='replace')
        receipt=json.loads((folder/'result/route-receipt.json').read_text(encoding='utf-8'))
        return run.returncode,receipt,folder
    def chart(self, typ='ranking', value=15):
        return {'title':'Reusable business example','source':'Synthetic QA', 'charts':[{'type':typ,'title':'Two periods','unit':'%' if typ=='attainment' else '件','definition':'Same population and period length','comparable':True,'scale_max':100,'states':{'P1':[{'id':'A','label':'Alpha','value':10}],'P2':[{'id':'A','label':'Alpha','value':value}]}}]}
    def test_ranking_renders_but_not_ready(self):
        code,r,p=self.run_case({'intent':'ranking-states','payload':self.chart()})
        self.assertEqual(code,4);self.assertEqual(r['status'],'rendered_requires_preflight');self.assertFalse(r['release_ready']);self.assertTrue((p/'result/index.html').is_file())
    def test_attainment_renders(self):
        code,r,p=self.run_case({'intent':'attainment-states','payload':self.chart('attainment')})
        self.assertEqual(code,4); self.assertIn('html_sha256',r)
    def test_kpi_renders(self):
        payload=json.loads((SKILL/'scripts/kpi-builder/demo.json').read_text(encoding='utf-8-sig'))
        code,r,p=self.run_case({'intent':'metric-cards','payload':payload})
        self.assertEqual(code,4);self.assertIn('html_sha256',r)
    def test_svg_scene_renders(self):
        payload=json.loads((SKILL/'scripts/scene-builder/manufacturing.json').read_text(encoding='utf-8-sig'))
        code,r,p=self.run_case({'intent':'svg-scenes','payload':payload})
        self.assertEqual(code,4);self.assertTrue((p/'result/index.html').is_file());self.assertIn('scripts/scene-builder/scene-template.html',r['dependency_sha256'])
    def test_custom_is_not_success(self):
        code,r,p=self.run_case({'intent':'bump-trajectories','payload':{}})
        self.assertEqual(code,3);self.assertEqual(r['status'],'custom_required');self.assertFalse((p/'result/index.html').exists())
    def test_over_target_is_rejected(self):
        code,r,p=self.run_case({'intent':'attainment-states','payload':self.chart('attainment',120)})
        self.assertEqual(code,2);self.assertEqual(r['status'],'unsupported_or_invalid_payload');self.assertFalse((p/'result/index.html').exists())
    def test_mixed_intent_is_rejected(self):
        code,r,p=self.run_case({'intent':'ranking-states','payload':self.chart('attainment')})
        self.assertEqual(code,2);self.assertEqual(r['status'],'invalid_request')
    def test_unmapped_requirements_are_not_ignored(self):
        code,r,p=self.run_case({'intent':'ranking-states','payload':self.chart(),'joins':['quality']})
        self.assertEqual(code,2);self.assertEqual(r['status'],'invalid_request')
    def test_stale_output_is_not_overwritten(self):
        code,r,p=self.run_case({'intent':'ranking-states','payload':self.chart()})
        before=(p/'result/route-receipt.json').read_bytes()
        repeated=subprocess.run([sys.executable,str(HERE/'bounded_build.py'),str(p/'request.json'),str(p/'result'),'--skill-dir',str(SKILL)],capture_output=True)
        self.assertEqual(repeated.returncode,2);self.assertEqual(before,(p/'result/route-receipt.json').read_bytes())
if __name__=='__main__':
    (EVIDENCE).mkdir(parents=True, exist_ok=True)
    unittest.main(verbosity=2)
