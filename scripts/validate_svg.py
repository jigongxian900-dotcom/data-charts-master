"""Check self-contained analytical SVG structure. Not a data or visual validator."""
import argparse
import json
import math
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

def check(path):
    errors=[]
    try:
        root=ET.parse(path).getroot()
    except (ET.ParseError,OSError) as exc:
        return {'path':str(path),'passed':False,'errors':[str(exc)]}
    name=lambda s:s.rsplit('}',1)[-1]
    if name(root.tag)!='svg':errors.append('root must be svg')
    view=root.get('viewBox','').split()
    try:
        nums=[float(v) for v in view]
        if len(nums)!=4 or not all(math.isfinite(v) for v in nums) or nums[2]<=0 or nums[3]<=0:raise ValueError()
    except ValueError:errors.append('finite positive viewBox required')
    ids=[];refs=[];texts=0
    for node in root.iter():
        tag=name(node.tag)
        if tag in {'script','foreignObject'}:errors.append('unsupported active/container element: '+tag)
        if node.get('id'):ids.append(node.get('id'))
        if tag=='text' and ''.join(node.itertext()).strip():texts+=1
        for key,value in node.attrib.items():
            key=name(key)
            if key.lower().startswith('on'):errors.append('event attribute: '+key)
            if key=='href':
                if value.startswith('#'):refs.append(value[1:])
                elif not value.startswith('data:'):errors.append('external href')
            if re.search(r'url\((?![\s\'\"]*#)',value,re.I):errors.append('external url()')
            refs.extend(re.findall(r'url\([\s\'\"]*#([^\s\)\'\"]+)',value))
            if re.search(r'\b(?:NaN|Infinity)\b',value):errors.append('non-finite value')
            if key in {'width','height','r','rx','ry','stroke-width'}:
                try:
                    if float(value)<0:errors.append('negative '+key)
                except ValueError:pass
        if tag=='style':
            css=node.text or ''
            if '@import' in css or re.search(r'url\((?![\s\'\"]*#|[\s\'\"]*data:)',css,re.I):errors.append('external stylesheet resource')
    if len(ids)!=len(set(ids)):errors.append('duplicate ids')
    for ref in set(refs)-set(ids):errors.append('unresolved reference: '+ref)
    for tag in ('title','desc'):
        if not any(name(n.tag)==tag and ''.join(n.itertext()).strip() for n in root):errors.append('missing '+tag)
    if not texts:errors.append('no editable text')
    return {'path':str(path),'passed':not errors,'text_elements':texts,'errors':sorted(set(errors))}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('svg',type=Path,nargs='+');a=p.parse_args()
    results=[check(f) for f in a.svg];print(json.dumps(results,ensure_ascii=False,indent=2));sys.exit(0 if all(r['passed'] for r in results) else 1)
