"""Uniform screw-row infill versus the frozen split-center panel surrogate.

Reuse the checked independent S8 panels, eight actual hold datums, 20x20 mm
hypothetical pressure patches and projected 300 lb sensitivity loads. Both free
seam profiles, compliance and every ideal screw reaction undergo refinement.
These are ideal point-support diagnostics, not physical joint demands, plywood
capacity, a complete load envelope or construction qualification.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path

from fea import reuse_panel_job
from fea import split_center_panel_comparison as previous

prepare_panel, assess, run_panel = previous.prepare_panel, previous.assess, previous.run_panel
CASES, shell = previous.CASES, previous.shell


def reaction_refinement(coarse, fine):
    """Keep every signed support result; use a declared 0.5 N low-force absolute tolerance."""
    a, z = (r['ideal_screw_normal_reactions_n'] for r in (coarse, fine))
    if not a or set(a) != set(z):
        raise ValueError('Screw identities changed between mesh resolutions')
    if not all(math.isfinite(v) for row in (a, z) for v in row.values()):
        raise ValueError('Nonfinite ideal screw reaction')
    rows = []
    for name in sorted(a):
        change = abs(a[name]-z[name])
        tolerance = max(.5, .05*abs(z[name]))
        rows.append({'connection': name, 'coarse_signed_normal_n': a[name],
                     'fine_signed_normal_n': z[name], 'absolute_change_n': change,
                     'relative_change': change/abs(z[name]) if z[name] else None,
                     'numerical_tolerance_n': tolerance, 'passed': change <= tolerance})
    peak_a, peak_z = (max(row, key=lambda n: abs(row[n])) for row in (a, z))
    return {'individual_reactions': rows,
            'coarse_controlling_connection': peak_a, 'fine_controlling_connection': peak_z,
            'controlling_identity_changed': peak_a != peak_z,
            'coarse_max_abs_normal_n': abs(a[peak_a]), 'fine_max_abs_normal_n': abs(z[peak_z]),
            'all_individual_reactions_converged': all(r['passed'] for r in rows),
            'tolerance_basis': 'Numerical mesh comparison only: each signed reaction difference <= max(0.5 N, 5% of fine absolute reaction). Identity switches are recorded, not automatically failures.'}


def comparison_summary(cases, baseline, revised):
    sizes = sorted({r['mesh_mm'] for r in cases}, reverse=True)
    if len(sizes) != 2 or not all(math.isfinite(v) and v > 0 for v in sizes):
        raise ValueError('Require two positive finite distinct mesh sizes')
    expected = {(candidate, case[2], size) for candidate in (baseline, revised)
                for case in CASES for size in sizes}
    indexed = {(r['candidate'], r['case_id'], r['mesh_mm']): r for r in cases}
    if len(indexed) != len(cases) or set(indexed) != expected:
        raise ValueError('Require all 32 distinct variant/case/resolution rows')
    checks, displacement_checks, accepted = [], [], {}
    metrics = ('compliance_mm_per_n', 'max_abs_horizontal_seam_displacement_mm',
               'max_abs_vertical_seam_displacement_mm')
    for candidate in (baseline, revised):
        for _, _, label, _ in CASES:
            coarse, fine = (indexed[candidate, label, size] for size in sizes)
            changes = {key: abs(coarse[key]-fine[key])/max(abs(fine[key]), 1e-12) for key in metrics}
            displacement_passed = max(changes.values()) <= .05
            displacement_checks.append({'candidate': candidate, 'case_id': label,
                'relative_changes': changes, 'passes_5_percent_refinement': displacement_passed})
            check = reaction_refinement(coarse, fine)
            checks.append({'candidate': candidate, 'case_id': label, **check})
            accepted[candidate, label] = displacement_passed and check['all_individual_reactions_converged']
    ratios = []
    for _, _, label, _ in CASES:
        if accepted[baseline, label] and accepted[revised, label]:
            a, z = (indexed[candidate, label, min(sizes)] for candidate in (baseline, revised))
            old_peak, new_peak = (max(abs(v) for v in r['ideal_screw_normal_reactions_n'].values()) for r in (a, z))
            ratios.append({'case_id': label, 'revised_over_baseline_surrogate_ratios':
                {key: z[key]/a[key] if abs(a[key]) > 1e-12 else None for key in metrics},
                'revised_over_baseline_peak_ideal_reaction': new_peak/old_peak if old_peak else None})
    return {'mesh_sizes_mm': sizes, 'numerical_comparison_accepted': all(accepted.values()),
        'refinement_checks': displacement_checks, 'reaction_refinement_checks': checks,
        'accepted_case_surrogate_ratios': ratios, 'qualified_for_design': False,
        'actual_panel_qualified': False, 'gusset_force_reduction_established': False,
        'seam_interpretation': 'Each loaded panel is independent; its unloaded neighbor remains zero. Each profile is the same-case ideal seam displacement jump. Different load cases are not combined.',
        'ratio_policy': 'Ratios require both variants to pass compliance, both seam profiles and all signed ideal-reaction refinement checks. No actual connection resistance acceptance.'}


def source_hashes():
    result = previous.source_hashes()
    path = Path(__file__).resolve()
    result[str(path.relative_to(Path.cwd()))] = hashlib.sha256(path.read_bytes()).hexdigest()
    helper = Path(reuse_panel_job.__file__).resolve()
    result[str(helper.relative_to(Path.cwd()))] = hashlib.sha256(helper.read_bytes()).hexdigest()
    return result


def verify_reuse_solver(source_report):
    """A replay retains its source solver identity; it never upgrades the solver."""
    if source_report.get('solver_image') != shell.IMAGE:
        raise ValueError('Source solver image differs from current pinned solver image')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--reuse', type=Path, help='Authenticate and replay identical jobs from this report directory; never silently launch replacements')
    parser.add_argument('--mesh-sizes', nargs=2, type=float, default=list(shell.SIZES))
    args = parser.parse_args()
    sizes = sorted(set(args.mesh_sizes), reverse=True)
    if len(sizes) != 2 or not all(math.isfinite(v) and v > 0 for v in sizes):
        parser.error('Require two distinct positive finite mesh sizes')
    if args.output.exists():
        raise FileExistsError('Refusing to overwrite infill diagnostic evidence')
    from mini_moonboard import infill_panel_frame as revised
    from mini_moonboard import split_center_frame as baseline
    sources = source_hashes()
    reused_jobs = []
    if args.reuse:
        source_report_bytes = (args.reuse/'report.json').read_bytes()
        source_report = json.loads(source_report_bytes)
        verify_reuse_solver(source_report)
        source_report_sha = hashlib.sha256(source_report_bytes).hexdigest()

    def execute(record, directory):
        is_benchmark = record['candidate'] == 'cantilever-benchmark'
        if not args.reuse:
            return shell.run(record, directory) if is_benchmark else run_panel(record, directory)
        source_dir = args.reuse/directory.name
        saved = json.loads((source_dir/'result.json').read_text())
        expected = source_report['benchmark'] if is_benchmark else next(r for r in source_report['cases']
            if r['candidate'] == record['candidate'] and r['case_id'] == record['case_id']
            and r['mesh_mm'] == record['mesh_max_mm'])
        if saved['evidence_sha256'] != expected['evidence_sha256']:
            raise ValueError('Source job evidence differs from source report')
        result, provenance = reuse_panel_job.reuse(record, source_dir, directory,
                                                  shell.assess if is_benchmark else assess)
        reused_jobs.append({'job': directory.name, 'source_report_sha256': source_report_sha,
                            'regenerated_input_byte_identical': True, **provenance})
        return result

    report = {'limits': __doc__, 'source_sha256': sources, 'solver_image': shell.IMAGE,
              'baseline': baseline.KEY, 'revised': revised.KEY, 'mesh_sizes_mm': sizes, 'qualified_for_design': False,
              'actual_panel_qualified': False, 'gusset_force_reduction_established': False,
              'reused_jobs': reused_jobs, 'fresh_solver_jobs': 0 if args.reuse else 33,
              'benchmark': execute(shell.benchmark(), args.output/'benchmark'), 'cases': []}
    for module in (baseline, revised):
        for case in CASES:
            for size in sizes:
                record = prepare_panel(module, case, size)
                name = f'{module.KEY}-{case[2]}-{size:g}'
                result = execute(record, args.output/name)
                reactions = result['ideal_screw_normal_reactions_n']
                controller = max(reactions, key=lambda n: abs(reactions[n]))
                report['cases'].append({'candidate': module.KEY, 'case_id': case[2],
                    'panel': record['panel'], 'load_family': case[3], 'mesh_mm': size,
                    'patch_mm': record['patch_mm'], 'projected_load_cases': record['projected_load_cases'],
                    'applied_normal_force_n': record['applied_normal_force_n'],
                    'linear_250_over_300_scale': record['linear_250_over_300_scale'],
                    'controlling_ideal_screw': controller, 'controlling_signed_reaction_n': reactions[controller], **result})
                print(name, result['normal_patch_average_displacement_mm'], controller, reactions[controller], flush=True)
    report['comparison'] = comparison_summary(report['cases'], baseline.KEY, revised.KEY)
    if args.reuse and (args.reuse/'report.json').read_bytes() != source_report_bytes:
        raise ValueError('Source reuse report changed during replay')
    if source_hashes() != sources:
        raise ValueError('Source changed during infill comparison; results not accepted')
    (args.output/'report.json').write_text(json.dumps(report, indent=2, allow_nan=False)+'\n')


if __name__ == '__main__':
    main()
