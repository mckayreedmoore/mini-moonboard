"""Conditional axial reference comparisons, never assembly resistance approval."""
import argparse
import hashlib
import json
from pathlib import Path

REFERENCE = Path('docs/infill-panel-hardware-reference.json')
LBF_N = .45359237*9.80665


def assess(report, reference):
    """Compare tensile ideal reactions; compression is not screw withdrawal."""
    if report['revised'] != 'infill-panel-development':
        raise ValueError('Require the current infill candidate')
    withdrawal = reference['table_10']['unadjusted_withdrawal_n']
    heads = {key: value*LBF_N for key, value in reference['table_6'].items()
             if key.endswith('_pullthrough_lbf')}
    checks = {(r['candidate'], r['case_id']): r for r in
              report['comparison']['reaction_refinement_checks']}
    rows = []
    fine = min(c['mesh_mm'] for c in report['cases'])
    for case in report['cases']:
        if case['candidate'] != report['revised'] or case['mesh_mm'] != fine:
            continue
        refinements = {r['connection']: r for r in
                       checks[case['candidate'], case['case_id']]['individual_reactions']}
        for name, reaction in case['ideal_screw_normal_reactions_n'].items():
            # Shell normal load is positive; negative support reaction resists
            # outward separation. A positive support reaction is compression.
            tension300 = max(0., -reaction)
            tension250 = tension300*case['linear_250_over_300_scale']
            rows.append({'case_id': case['case_id'], 'panel': case['panel'], 'connection': name,
                         'signed_300lb_normal_reaction_n': reaction,
                         'ideal_tension_300lb_n': tension300, 'ideal_tension_250lb_n': tension250,
                         'reaction_refinement_passed': refinements[name]['passed'],
                         'conditional_withdrawal_reference_n': withdrawal,
                         'normal_only_250lb_over_unadjusted_withdrawal': tension250/withdrawal,
                         'normal_only_250lb_over_conditional_head_references': {
                             key: tension250/value for key, value in heads.items()},
                         'qualified_connection': False})
    if {r['case_id'] for r in rows} != {'D6', 'D7', 'H6', 'H7', 'F3', 'F10', 'G3', 'G10'}:
        raise ValueError('Require all eight current fine-mesh hold cases')
    peak = max(rows, key=lambda r: r['ideal_tension_250lb_n'])
    return {'candidate': report['revised'], 'qualified_for_design': False,
            'joint_strength_passed': False, 'actual_demands_available': False,
            'material_applicability_verified': False,
            'reference': reference, 'rows': rows, 'maximum_ideal_tension': peak,
            'individual_reaction_refinement_passed': all(r['reaction_refinement_passed'] for r in rows),
            'rows_above_unadjusted_withdrawal_reference': sum(
                r['normal_only_250lb_over_unadjusted_withdrawal'] > 1 for r in rows),
            'limits': 'Unadjusted product references with conditional material applicability. '
                      'Negative shell support reaction is interpreted as ideal axial tension only. '
                      'No equal sharing, NDS adjustment increases, screw group, cyclic or combined '
                      'action credit. Normal-only forces omit tangential force and hold-offset moment; '
                      'ideal rigid point restraints are not physical demand bounds. Ratios are '
                      'diagnostics, not actual utilization or proof of construction adequacy/failure. '
                      'Plywood assigned specific gravity and installed conditions remain unverified.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    report = json.loads(args.report.read_text())
    for path, sha in report['source_sha256'].items():
        if hashlib.sha256(Path(path).read_bytes()).hexdigest() != sha:
            raise ValueError('Panel evidence source differs: '+path)
    result = assess(report, json.loads(REFERENCE.read_text()))
    paths = (Path(__file__).resolve(), REFERENCE.resolve())
    result['source_sha256'] = {**report['source_sha256'], **{
        str(p.relative_to(Path.cwd())): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}}
    result['panel_report_sha256'] = hashlib.sha256(args.report.read_bytes()).hexdigest()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write('\n')


if __name__ == '__main__':
    main()
