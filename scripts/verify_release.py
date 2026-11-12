"""Verify the public package structure, links, synthetic-data contract and SVG safety."""
from pathlib import Path
import json,re,sys
from urllib.parse import unquote
from validate_svg import check

ROOT=Path(__file__).resolve().parents[1]
errors=[]
data=json.loads((ROOT/'examples/dashboard-atlas/source-data.json').read_text(encoding='utf-8'))
charts=data['charts']
assert len(charts)==54 and len({c['id'] for c in charts})==54
assert data['synthetic'] is True
assert all(c['source'].startswith('原创') for c in charts)
assert all(c['dataKind']=='原创合成数据' for c in charts)
assert len(json.loads((ROOT/'assets/color-system.json').read_text(encoding='utf-8'))['themes'])==7
svgfiles=sorted((ROOT/'examples/dashboard-atlas/svg').glob('*.svg'))
assert len(svgfiles)==54
for p in svgfiles:
    result=check(p)
    errors.extend(f'{p.name}: {x}' for x in result['errors'])
assert (ROOT/'docs/index.html').read_text(encoding='utf-8').replace('href="labs/','href="../interaction-lab/')==(ROOT/'examples/dashboard-atlas/atlas.html').read_text(encoding='utf-8')
assert (ROOT/'docs/source-data.json').read_bytes()==(ROOT/'examples/dashboard-atlas/source-data.json').read_bytes()
for p in ROOT.rglob('*'):
    if not p.is_file() or any(x in {'.git','__pycache__','node_modules','.test-output'} for x in p.parts):continue
    if p.suffix not in {'.md','.html','.json','.js','.py','.yml','.svg'}:continue
    s=p.read_text(encoding='utf-8-sig')
    # The public package uses neutral, general-purpose palette names.
    for prohibited in [''.join(map(chr,[0x871c,0x96ea])),''.join(map(chr,[109,105,120,117,101]))]:
        if prohibited in s.lower():errors.append(f'{p.relative_to(ROOT)}: non-generic brand reference')
    # Do not publish host-specific absolute filesystem paths or common credentials.
    for pattern in [r'[A-Za-z]:[\\/](?:Users|Desktop|Temp)',r'gh[pousr]_[A-Za-z0-9]{20,}',r'github_pat_[A-Za-z0-9_]{20,}',r'-----BEGIN (?:RSA |OPENSSH )?PRIVATE KEY-----']:
        if re.search(pattern,s):errors.append(f'{p.relative_to(ROOT)}: private path/credential pattern')
    if p.suffix=='.md':
        for href in re.findall(r'!?\[[^\]]*\]\(([^\s)]+)(?:\s+[^)]*)?\)',s):
            if re.match(r'(?:https?:|mailto:|#)',href):continue
            target=unquote(href.split('#')[0])
            if target and not (p.parent/target).exists():errors.append(f'{p.relative_to(ROOT)}: broken link {href}')
        for href in re.findall(r'(?:src|srcset)="([^"\s]+)"',s):
            if not re.match(r'https?:',href) and not (p.parent/href).exists():errors.append(f'{p.relative_to(ROOT)}: missing preview {href}')
for key in ['rankedbar','dumbbell','waterfall']:
    c=next(c for c in charts if c['id']==key)
    assert c['source']=='原创合成数据，仅用于图表选型与效果演示'
bar=next(c for c in charts if c['id']=='rankedbar')
assert bar['rows'][0][1]-bar['rows'][1][1]==108
wf=next(c for c in charts if c['id']=='waterfall')
assert sum(r[1] for r in wf['rows'])==194
if errors:
    print('\n'.join(errors));sys.exit(1)
print('PASS: 54 original synthetic cases, 54 self-contained SVGs, seven palettes, mirrored gallery, local links and publication hygiene.')
