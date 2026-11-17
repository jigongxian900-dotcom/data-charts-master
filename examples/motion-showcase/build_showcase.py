from pathlib import Path
import json,argparse,re
HERE=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--skill-root',type=Path,default=HERE.parents[1]);p.add_argument('--assets',type=Path);p.add_argument('--rows',type=Path);a=p.parse_args()
data=json.loads((HERE/'data.json').read_text(encoding='utf-8-sig'))
assert data['synthetic'] is True
assert [sum(x['values'][i] for x in data['stores']) for i in range(3)]==[sum(x['values'][i] for x in data['channels']) for i in range(3)]
assets=a.assets or a.skill_root/'assets'
runtime=(assets/'chart-motion.js').read_text(encoding='utf-8-sig');retained=(assets/'retained-motion.js').read_text(encoding='utf-8-sig');rows=(a.rows or assets/'retained-rows.js').read_text(encoding='utf-8-sig')
parts={'__DATA__':json.dumps(data,ensure_ascii=False).replace('<','\\u003c'),'__RUNTIME__':runtime,'__RETAINED__':retained,'__ROWS__':rows}
s=re.sub(r'__DATA__|__RUNTIME__|__RETAINED__|__ROWS__',lambda m:parts[m.group()],(HERE/'template.html').read_text(encoding='utf-8-sig'))
(HERE/'index.html').write_text(s,encoding='utf-8');print('Built single-file showcase; synthetic totals verified')
