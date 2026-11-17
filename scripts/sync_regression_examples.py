"""Verify and mirror six frozen HTML regression records; no data/producer rebuild."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
SLUGS = (
    'intercity-delivery-scheduling',
    'factorial-outreach-experiment',
    'perishable-inventory-expiry',
    'recruitment-waiting-load',
    'service-error-budget-latency',
    'venue-booking-capacity',
)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    verified = []
    # Validate every source before writing any mirror.
    for slug in SLUGS:
        folder = ROOT/'examples/regression'/slug
        manifest = json.loads((folder/'provenance.json').read_text(encoding='utf-8'))
        if manifest.get('class') != 'regression' or manifest.get('synthetic') is not True:
            raise RuntimeError('Invalid regression scope: '+slug)
        for name, expected in manifest['files_sha256'].items():
            if digest(folder/name) != expected:
                raise RuntimeError('Provenance hash mismatch: '+slug+'/'+name)
        for name, expected in manifest['original_input_sha256'].items():
            if digest(folder/name) != expected:
                raise RuntimeError('Original input bytes differ: '+slug+'/'+name)
        if digest(folder/'artifact.html') != manifest['public_artifact_sha256']:
            raise RuntimeError('Public HTML hash mismatch: '+slug)
        if digest(folder/'computed.json') != manifest['original_computed_sha256']:
            raise RuntimeError('Frozen computed bytes differ: '+slug)
        verified.append((slug, folder, manifest))
    records = []
    for slug, folder, manifest in verified:
        mirror = ROOT/'docs/regression'/(slug+'.html')
        mirror.parent.mkdir(parents=True, exist_ok=True)
        mirror.write_bytes((folder/'artifact.html').read_bytes())
        if digest(mirror) != manifest['public_artifact_sha256']:
            raise RuntimeError('Mirror hash mismatch: '+slug)
        records.append({'example': slug, 'public_artifact_sha256': digest(mirror), 'original_input_preserved': True})
    print(json.dumps({'frozen_regression_pages_synced': len(records), 'business_data_rebuilt': False, 'producer_executed': False, 'results': records}, indent=2))


if __name__ == '__main__':
    main()
