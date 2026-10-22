"""Publish the retained 2x6 revision as a small patch on its preserved viewer.

Reuse the preceding table/mesh publisher, changing only authenticated inputs,
censuses and the incremental scene composition. No mechanical result is copied.
"""
from __future__ import annotations

import builtins
from pathlib import Path

from scripts.eoere_paired_frame_basis import ROOT

OWN = Path(__file__).resolve()
SOURCE = OWN.with_name('publish_eoere_paired_frame.py')
CODE = SOURCE.read_text()


def replace(before, after):
    global CODE
    assert CODE.count(before) == 1, before
    CODE = CODE.replace(before, after)


replace("GEOMETRY = WORK/'upper-leg-up15-geometry-v1/geometry.json'",
        "GEOMETRY = WORK/'retained-2x6-A574-geometry-v2/geometry.json'")
replace("INPUT = WORK/'upper-leg-up15-cases-v1/geometry-preparation/inputs.json'",
        "INPUT = WORK/'retained-2x6-A574-cases-v2/geometry-preparation/inputs.json'")
replace("OLD = Path('docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/leg-header-v3/geometry.json')",
        "OLD = Path('docs/bolted-frame-development/paired-frame-v1/geometry.json')")
replace("SCENE = Path('site/eoere-paired-cleats-frame-v1-scene.json.gz')",
        "SCENE = Path('site/eoere-retained-2x6-frame-v2-scene.json.gz')")
replace("KEY = 'eoere-paired-cleats-frame-development'",
        "KEY = 'eoere-retained-2x6-frame-development'\nPACKET = Path('docs/bolted-frame-development/paired-frame-v2')")
replace("pins = {ref(OWN)['path']: sha(OWN), 'scripts/eoere_paired_frame_basis.py': sha('scripts/eoere_paired_frame_basis.py')}",
        "pins = {ref(OWN)['path']: sha(OWN), ref(PUBLISHER_SOURCE)['path']: sha(PUBLISHER_SOURCE), 'scripts/eoere_paired_frame_basis.py': sha('scripts/eoere_paired_frame_basis.py')}")
replace("'ab07d52c99c41e84b5a75e3bb812015d7bdb6204cfa6acbb127e22f5c2c007a7'",
        "'ff3b55af904d4375c7ec9aa1fe65712da3c913f78a27b552d2c4002a35d37c0d'")
replace("clearance['occupied_part_count'] == 1097", "clearance['occupied_part_count'] == 1075")
replace("len(clearance['newly_checked_part_ids']) == 14", "len(clearance['newly_checked_part_ids']) == 4")
replace("previous['schema'] == 'bolted_frame_development_revisions/v5'",
        "previous['schema'] == 'bolted_frame_development_revisions/v6'")
replace("stage = ROOT/WORK/'publication-stage-v1'", "stage = ROOT/WORK/'publication-stage-retained-v2'")
replace("selected = selections(geometry)", """windows = read(WORK/'A574-hardware-windows-v2.json', pins)
    assert windows['geometry'] == ref(GEOMETRY) and windows['all102_tip_and_free_seating_windows_positive']
    selected = copy.deepcopy(windows['coordinated_hardware_rows'])
    assert sum('A574' in r['selected_bolt_grade'] for r in selected) == 10""")
replace("row['reason'] = 'Coordinated paired frame; six long cleat bolts use the evaluated Grade8/matching-nut requirement. Actual delivery is unobserved.'",
        "row['reason'] = ('ASTM A574 socket-head through bolt, with the specified Grade8 nut and length-specific smooth-body floor. ' if 'A574' in row['selected_bolt_grade'] else 'Retained partial-thread Grade5 through-bolt recipe. ') + 'Actual delivery is unobserved; use all catalog and installation limits in this row.'")
replace("len(holes) == 134 and len(drilling) == len(selected) == 106",
        "len(holes) == 130 and len(drilling) == len(selected) == 102")
replace("sum(r['spacer_piece_count'] for r in selected) == 36",
        "sum(r['spacer_piece_count'] for r in selected) == 34")
replace("'schema': 'eoere_paired_frame_revision/v1'", "'schema': 'eoere_retained_2x6_frame_revision/v1'")
replace("'bolt_stacks': 106, 'nuts': 106, 'washers': 212, 'spacer_pieces': 36,",
        "'bolt_stacks': 102, 'nuts': 102, 'washers': 204, 'spacer_pieces': 34,")
replace("'Hillman_axes': 66, 'receiver_occurrences': 134, 'occupied_parts': 1097",
        "'Hillman_axes': 66, 'receiver_occurrences': 130, 'occupied_parts': 1075")
replace("receipt = put('geometry.json', report)", """old_geometry = read(old['checked_geometry']['path'], pins, old['checked_geometry']['sha256'])
    old_parts = {r['id']: r for r in old_geometry['changed_finished_solids']}
    new_parts = {r['id']: r for r in geometry['changed_finished_solids']}
    delta = [r for r in new_parts.values() if r['id'] not in old_parts or old_parts[r['id']]['sha256'] != r['sha256']]
    removed = sorted(set(old_parts)-set(new_parts))
    assert len(delta) == 34 and len(removed) == 22
    assert sum(r['kind'] == 'timber' for r in delta) == 8
    assert sum(r['kind'] == 'bolt' for r in delta) == 26
    report['viewer_delta_part_ids'] = sorted(r['id'] for r in delta)
    report['viewer_removed_part_ids'] = removed
    report['retained_2x6_refinement'] = geometry['retained_2x6_refinement']
    report['front_pair_refinement'] = geometry['front_pair_refinement']
    report['socket_head_cleat_option'] = geometry['socket_head_cleat_option']
    report['socket_head_front_option'] = geometry['socket_head_front_option']
    report['hardware_windows'] = ref(WORK/'A574-hardware-windows-v2.json')
    receipt = put('geometry.json', report)""")
replace("for row in geometry['changed_finished_solids']:", "for row in delta:")
replace("'schema': 'eoere_paired_frame_patch/v1'", "'schema': 'eoere_retained_2x6_frame_patch/v1'")
replace("'parent_scene': geometry['parent_geometry']['scene'], 'parent_layout': geometry['parent_geometry']['receipt'],",
        "'parent_scene': previous['geometry']['scene'], 'parent_layout': previous['geometry']['receipt'],")
replace("'layout_report': receipt, 'part_count': 1097, 'replacements': replacements,",
        "'layout_report': receipt, 'part_count': 1075, 'replacements': replacements,")
replace("'removals': sorted(set(clearance['removed_parent_parts'])-{r['id'] for r in replacements}),",
        "'removals': removed,")
replace("'schema': 'bolted_frame_development_revisions/v6'", "'schema': 'bolted_frame_development_revisions/v7'")


if __name__ == '__main__':
    namespace = {'__file__': str(OWN), '__name__': 'retained_frame_publisher',
                 'PUBLISHER_SOURCE': SOURCE}
    exec(builtins.compile(CODE, str(SOURCE), 'exec'), namespace)
    namespace['publish']()
