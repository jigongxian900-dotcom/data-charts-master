"""Bounded renderer entry. No natural-language routing or business aggregation."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROUTES = {
    'ranking-states': ('scripts/motion_builder.py', 'ranking'),
    'attainment-states': ('scripts/motion_builder.py', 'attainment'),
    'metric-cards': ('scripts/kpi-builder/kpi_builder.py', None),
    'svg-scenes': ('scripts/scene-builder/scene_html.py', None),
}

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('request', type=Path)
    p.add_argument('output_dir', type=Path)
    p.add_argument('--skill-dir', type=Path, required=True)
    p.add_argument('--preflight', type=Path)
    p.add_argument('--contract', type=Path)
    a = p.parse_args()
    # Never leave an older successful HTML beside a newer rejection receipt.
    if a.output_dir.exists() and any(a.output_dir.iterdir()):
        p.error('output_dir must be new or empty; preserve prior attempts separately')
    a.output_dir.mkdir(parents=True, exist_ok=True)
    receipt = {'schema': 1, 'status': 'invalid_request', 'release_ready': False,
               'business_verified': False, 'visual_verified': False,
               'preflight': 'not_run', 'request_sha256': None,
               'scope': 'explicit preaggregated schema only; no automatic business reasoning'}
    def finish(status, code, reason=None):
        receipt['status'] = status
        if reason: receipt['reason'] = reason
        (a.output_dir/'route-receipt.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding='utf-8')
        print(json.dumps(receipt, ensure_ascii=False))
        return code
    try:
        receipt['request_sha256'] = sha(a.request)
        request = json.loads(a.request.read_text(encoding='utf-8-sig'))
        if not isinstance(request, dict): raise ValueError('request must be an object')
        allowed = {'intent', 'payload'}
        if set(request)-allowed: raise ValueError('unsupported request fields: '+', '.join(sorted(set(request)-allowed)))
        intent = request.get('intent')
        receipt['intent'] = intent
        if intent not in ROUTES:
            receipt['custom_next_steps'] = {'motion_reference': str(a.skill_dir/'references/motion-quickstart.md'), 'preflight_cli': 'node artifact_preflight.cjs --html CUSTOM.html --out preflight.json --contract contract.json', 'constraint': 'Do not force interpolation across units or incomparable populations; comparable retained objects should not replay entrance animation.'}
            return finish('custom_required', 3, 'No bounded renderer for this intent. Design a custom renderer and run artifact preflight; this is not a completed deliverable.')
        payload = request.get('payload')
        if not isinstance(payload, dict): raise ValueError('payload must be a preaggregated object')
        relative, required_chart_type = ROUTES[intent]
        if required_chart_type:
            charts = payload.get('charts')
            if not isinstance(charts, list) or not charts or any(not isinstance(c, dict) or c.get('type') != required_chart_type for c in charts):
                raise ValueError('intent requires only '+required_chart_type+' charts; mixed relationships require custom rendering')
        builder = a.skill_dir/relative
        if not builder.is_file(): raise ValueError('builder missing: '+relative)
        receipt['builder'] = relative
        receipt['builder_sha256'] = sha(builder)
        dependencies = (['assets/chart-motion.js', 'scripts/scene-builder/scene-template.html'] if intent == 'svg-scenes' else ['assets/chart-motion.js', 'assets/retained-motion.js'] if required_chart_type else ['scripts/kpi-builder/template.html'])
        receipt['dependency_sha256'] = {name: sha(a.skill_dir/name) for name in dependencies}
        input_path = a.output_dir/'payload.json'
        input_path.write_text(json.dumps(payload, ensure_ascii=False, allow_nan=False), encoding='utf-8')
        output = a.output_dir/'index.html'
        build_command = [sys.executable, str(builder.resolve()), str(input_path.resolve()), str(output.resolve())]
        if intent == 'svg-scenes': build_command += ['--runtime', str((a.skill_dir/'assets/chart-motion.js').resolve())]
        run = subprocess.run(build_command, capture_output=True, text=True, encoding='utf-8', errors='replace')
        (a.output_dir/'builder.log').write_text(run.stdout+'\n'+run.stderr, encoding='utf-8')
        receipt['builder_exit_code'] = run.returncode
        if run.returncode or not output.is_file():
            return finish('unsupported_or_invalid_payload', 2, 'Builder rejected input; see builder.log. Do not coerce data to pass its boundary.')
        receipt['html_sha256'] = sha(output)
        if not a.preflight:
            return finish('rendered_requires_preflight', 4, 'HTML exists, but runtime/keyboard verification has not run. Not ready for delivery.')
        if not a.preflight.is_file(): return finish('preflight_unavailable', 4, 'Specified preflight file is missing')
        receipt['preflight_script_sha256'] = sha(a.preflight)
        command = ['node', str(a.preflight.resolve()), '--html', str(output.resolve()), '--out', str((a.output_dir/'preflight.json').resolve())]
        if a.contract:
            command += ['--contract', str(a.contract.resolve())]
            receipt['contract_sha256'] = sha(a.contract)
        pf = subprocess.run(command, capture_output=True, text=True, encoding='utf-8', errors='replace')
        (a.output_dir/'preflight.log').write_text(pf.stdout+'\n'+pf.stderr, encoding='utf-8')
        receipt['preflight_exit_code'] = pf.returncode
        receipt['preflight'] = 'executed'
        report = a.output_dir/'preflight.json'
        if pf.returncode or not report.is_file(): return finish('preflight_failed_or_incomplete', 4, 'Read runtime evidence; a successful render does not clear this gate.')
        receipt['preflight_report_sha256'] = sha(report)
        gate = json.loads(report.read_text(encoding='utf-8-sig'))
        if not isinstance(gate, dict): raise ValueError('Preflight report must be an object')
        if gate.get('passed') is not True or gate.get('blocked') is not False:
            return finish('preflight_failed_or_incomplete', 4, 'Preflight report did not explicitly confirm passed=true and blocked=false.')
        receipt['untested'] = [c.get('name') for c in gate.get('checks', []) if c.get('status') == 'untested']
        return finish('rendered_preflight_executed', 0, 'Inspect preflight report, business meaning, intermediate geometry and visual result; this is not a quality score or release approval.')
    except (ValueError, OSError, TypeError) as exc:
        return finish('invalid_request', 2, str(exc))

if __name__ == '__main__':
    sys.exit(main())
