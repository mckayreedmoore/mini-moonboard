"""Record actual flush geometry and load-independent end-cut comparisons."""
import json
from pathlib import Path

from mini_moonboard import compact_floor_flush_frame as model
from scripts.clear_space_study import geometry as existing_geometry


def geometry():
    result = existing_geometry(model)
    result['floor_taper_geometry'] = model.floor_recess_geometry()
    for name, record in result['floor_taper_geometry'].items():
        result['members'][name]['floor_taper_geometry'] = record
    result['runner_end_geometry'] = model.runner_end_geometry()
    return result


def end_cut_screen(geometry):
    result = {}
    for name in ('base_side_left', 'base_side_right'):
        member = geometry['members'][name]
        contact = geometry['header_overlap'][name]
        retained = contact['full_member_face_area_mm2']/member['width_mm']*abs(member['grain'][2])
        removed = member['depth_mm']-retained
        margin = member['depth_mm']/4-removed-3.
        result[name] = {'retained_depth_mm': retained, 'removed_depth_mm': removed,
            'quarter_depth_margin_after_3mm_allowance_mm': margin, 'passes_existing_screen': margin >= 0}
    return {'candidate': model.KEY, 'receiver_fit_pass': geometry['receiver_fit_pass'],
        'rim_end_cut_screen': result, 'qualified_for_design': False,
        'scope': 'Geometry-only comparison against existing quarter-depth end-cut screen with 3 mm allowance. No fresh native response or unconditional failure prediction.'}


if __name__ == '__main__':
    data = geometry()
    Path('docs/floor-flush-geometry.json').write_text(json.dumps(data, indent=2, allow_nan=False)+'\n')
    review = end_cut_screen(data)
    Path('docs/floor-flush-fit-review.json').write_text(json.dumps(review, indent=2, allow_nan=False)+'\n')
    print(json.dumps(review, indent=2))
