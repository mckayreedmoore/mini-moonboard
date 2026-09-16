"""Record the separate uncut geometry with explicit post material and provenance."""
import argparse
import hashlib
import json
from pathlib import Path

from fea.current_response_materials import df_l_no2_post_timber
from fea.current_response_run import repository_source_closure
from mini_moonboard import compact_floor_uncut_frame as model
from scripts.clear_space_study import geometry as existing_geometry


def geometry():
    result = existing_geometry(model)
    post = df_l_no2_post_timber()
    names = ('base_post_outer_left', 'base_post_outer_right')
    records = [result['members'], *(row['members'] for row in result['geometries_by_bolt_name'].values())]
    for members in records:
        for name in names:
            if name in members:
                members[name].update(reference_override=dict(post['reference_override']),
                                     elastic_modulus_psi=1_300_000., material_basis=post['basis'])
    result['runner_end_geometry'] = model.runner_end_geometry()
    result['bolt_axes'] = {connection.name: {
        'start_xyz_mm': list(connection.start.toTuple()),
        'direction_xyz': list(connection.direction.toTuple()),
        'members': list(connection.members)}
        for connection in model.connections() if connection.kind == 'bolt'}
    paths = set(repository_source_closure([Path(model.__file__), Path('fea/current_response_materials.py')]))
    paths.update(Path(path) for path in (__file__, 'scripts/clear_space_study.py',
                                        'scripts/compact_thick_geometry.py', 'scripts/compact_rail_study.py'))
    paths.update(Path('mini_moonboard').glob('*.py'))
    paths.add(Path('fea/results/compact-splice-study/a12-rear/geometry.json'))
    result['source_sha256'].update({str(path.resolve().relative_to(Path.cwd())):
                                   hashlib.sha256(path.read_bytes()).hexdigest() for path in paths})
    result['qualified_for_design'] = False
    result['scope'] += (' Separate unselected full-stock investigation. Post material is explicit; '
                        'nominal receiver fit does not qualify hardware, placement tolerances or resistance.')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = geometry()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
    print(json.dumps({'candidate': result['candidate'], 'receiver_fit_pass': result['receiver_fit_pass'],
                      'qualified_for_design': False}))
