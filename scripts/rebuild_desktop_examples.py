"""Rebuild three fixed synthetic desktop works using only their bundled files."""
from pathlib import Path
import hashlib
import json
import runpy
import sys

ROOT=Path(__file__).resolve().parents[1]
SLUGS=('receivables-reconciliation','tenant-unit-allocation','civic-request-overlap')
records=[]
for slug in SLUGS:
    folder=ROOT/'examples/autonomous-desktop'/slug
    before={p.relative_to(folder).as_posix():p.read_bytes() for p in (folder/'input').iterdir() if p.is_file()}
    prior=sys.argv
    sys.argv=[str(folder/'producer.py')]
    try:
        runpy.run_path(str(folder/'producer.py'),run_name='__main__')
    finally:
        sys.argv=prior
    for name in ('artifact.html','computed.json'):
        p=folder/name
        p.write_bytes(p.read_bytes().replace(b'\r\n',b'\n').replace(b'\r',b'\n'))
    for name,data in before.items():
        if (folder/name).read_bytes()!=data:
            raise RuntimeError('Original input was modified: '+name)
    manifest=json.loads((folder/'provenance.json').read_text(encoding='utf-8'))
    digest=hashlib.sha256((folder/'artifact.html').read_bytes()).hexdigest()
    if digest!=manifest['public_artifact_sha256']:
        raise RuntimeError('Rebuild differs from the published fixed example: '+slug)
    computed_digest=hashlib.sha256((folder/'computed.json').read_bytes()).hexdigest()
    if computed_digest!=manifest['public_computed_sha256']:
        raise RuntimeError('Computed output differs: '+slug)
    mirror=ROOT/'docs/desktop'/(slug+'.html')
    mirror.parent.mkdir(parents=True,exist_ok=True)
    mirror.write_bytes((folder/'artifact.html').read_bytes())
    records.append({'example':slug,'artifact_sha256':digest,'computed_sha256':computed_digest,'input_preserved':True})
print(json.dumps({'fixed_examples_rebuilt':len(records),'results':records},indent=2))
