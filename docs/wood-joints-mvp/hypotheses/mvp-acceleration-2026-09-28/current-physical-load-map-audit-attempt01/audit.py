"""Audit separated source loads and the preserved projection-map label error."""
from pathlib import Path
import hashlib
import json
import math
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
BASE = HERE.parent


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def resultant(loads):
    return [math.fsum(v[d] for v in loads.values()) for d in range(3)]


def collect(body_maps):
    out = {}
    for body, nodes in body_maps.items():
        for node, value in nodes.items():
            assert node not in out, (body, node)
            assert len(value) == 3 and all(math.isfinite(x) for x in value)
            out[node] = value
    return out


def audit():
    maps_path = BASE / 'current-frame-pure-solid-matrix-export-preflight-attempt01/source-load-maps.json'
    old_path = BASE / 'current-frame-physical-connector-projection-contract-attempt01/source-gravity-nodal-map.json'
    proposal_pins_path = BASE / 'current-frame-pure-solid-matrix-export-preflight-attempt01/source-pins.json'
    maps = json.loads(maps_path.read_text())
    assert digest(maps_path) == '9cd59d7bbafd65c740d2b0200e3dd88a6a49e6dca0bead0a38bc7826e337548c'
    old = collect(json.loads(old_path.read_text()))
    rows = []
    sources = {str(p.relative_to(ROOT)): digest(p) for p in [maps_path, old_path, proposal_pins_path, Path(__file__)]}
    for case in maps['cases']:
        model_path = ROOT / case['source_input_model_path']
        assert digest(model_path) == case['source_input_model_sha256']
        sources[str(model_path.relative_to(ROOT))] = digest(model_path)
        model = json.loads(model_path.read_text())
        total = collect(model['physical_body_loads'])
        gravity = case['gravity_nodal_map']
        climber = case['climber_nodal_map']
        physical = {str(n) for nodes in model['physical_body_nodes'].values() for n in nodes}
        assert set(total) | set(gravity) | set(climber) <= physical
        errors = []
        for node in set(total) | set(gravity) | set(climber):
            g, c, t = gravity.get(node, [0.,0.,0.]), climber.get(node, [0.,0.,0.]), total.get(node, [0.,0.,0.])
            errors.extend(abs(g[d] + c[d] - t[d]) for d in range(3))
        error = max(errors)
        assert error <= 1e-9
        rows.append({'case_id': case['case_id'],
                     'source_model_sha256': digest(model_path),
                     'gravity_resultant_N': resultant(gravity),
                     'climber_resultant_N': resultant(climber),
                     'combined_resultant_N': resultant(total),
                     'max_nodal_recomposition_error_N': error,
                     'physical_node_map_coverage': True,
                     'preserved_mislabeled_map_equals_case_combined_map': old == total})
    assert len(rows) == 6
    a12 = next(row for row in rows if row['case_id'] == 'a12-rear')
    assert a12['preserved_mislabeled_map_equals_case_combined_map']
    assert abs(a12['gravity_resultant_N'][2] + 2200.816009515055) <= 1e-8
    assert abs(resultant(old)[1] - 300.) <= 1e-8
    return {'schema': 'current_physical_load_map_label_audit/v1',
            'status': 'PASS_SIX_CASE_SEPARATED_LOAD_RECOMPOSITION_WITH_EXPLICIT_LABEL_ERRATUM',
            'source_sha256': sources,
            'cases': rows,
            'preserved_mislabeled_file': str(old_path.relative_to(ROOT)),
            'preserved_mislabeled_file_actual_semantics': 'A12-rear combined gravity and climber source load; not a gravity-only map',
            'gravity_stage_source': str(maps_path.relative_to(ROOT)) + ': cases[case_id].gravity_nodal_map',
            'climber_ramp_source': str(maps_path.relative_to(ROOT)) + ': gravity_nodal_map + alpha*climber_nodal_map',
            'existing_unloaded_native_operator_affected': False,
            'response_or_contact_state_computed': False,
            'claim_boundary': 'This audits nodal source-load identity, not physical self-weight distribution, contact history or frame acceptance.'}


if __name__ == '__main__':
    result = audit()
    out = HERE / 'audit.json'
    if '--verify' in sys.argv:
        assert result == json.loads(out.read_text())
    else:
        out.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(result['status'])
