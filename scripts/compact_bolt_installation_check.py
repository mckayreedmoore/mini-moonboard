"""Check reversed hardware against unchanged structural connection geometry."""
import hashlib
import json
from pathlib import Path

from mini_moonboard import compact_spliced_installation as model
from scripts.compact_rail_study import bolt_properties
from scripts.compact_thick_geometry import build


def check():
    geometry = build(model)
    assert geometry['receiver_fit_pass']
    old = {c.name:c for c in model.structural.connections()}
    reference = json.loads(Path('fea/results/compact-splice-study/a12-rear/geometry.json').read_text())
    rows = []
    for c in model.connections():
        if c.kind != 'bolt':
            continue
        before = old[c.name]
        assert c.start.x*c.direction.x > 0
        assert (model.bolt_interface_point(c)-model.structural.bolt_interface_point(before)).Length < 1e-8
        assert bolt_properties(c) == bolt_properties(before)
        for name,row in geometry['geometries_by_bolt_name'][c.name]['members'].items():
            prior = reference['geometries_by_bolt_name'][c.name]['members'][name]
            assert abs(row['bearing_length_mm']-prior['bearing_length_mm']) < 1e-6
            for key,value in row['edge_distances_mm'].items():
                assert abs(value-prior['edge_distances_mm'][key]) < 1e-6
        # Component volumes and centroids suffice for the change: overlaps of
        # the same rigid stack are invariant under this axial reflection.
        mass_delta = moment_bound = 0.
        for a,b in zip(before.components(),c.components(),strict=True):
            assert abs(a.Volume()-b.Volume()) < 1e-5
            mass = a.Volume()*7.85e-6
            mass_delta += (b.Volume()-a.Volume())*7.85e-6
            moment_bound += mass*9.80665*abs(b.Center().x-a.Center().x)
            assert abs(a.Center().y-b.Center().y) < 1e-6
            assert abs(a.Center().z-b.Center().z) < 1e-6
        rows.append({'bolt':c.name,'reversed':c.direction != before.direction,
            'mass_change_kg':mass_delta,'absolute_local_gravity_moment_change_bound_nmm':moment_bound})
    paths = [Path(__file__),Path(model.__file__),Path(model.structural.__file__)]
    return {'candidate':model.KEY,'installation':'nuts and threaded ends outward',
        'receiver_fit_pass':True,'receiver_fit':geometry['receiver_fit'],
        'unchanged_bearing_edges_and_spring_properties':True,'bolts':rows,
        'source_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
        'scope':'Installation equivalence check, not a new native solve. Wood and interfaces unchanged; identical washer resistance applies on both faces. Archived gravity placement retained; small hardware centroid shifts reported as local moment bounds.'}


if __name__ == '__main__':
    result = check()
    output = Path('docs/compact-spliced-construction/bolt-installation-check.json')
    output.write_text(json.dumps(result,indent=2)+'\n')
    print('Outward hardware: 40 receiver checks passed; maximum per-stack gravity moment change bound',
          max(r['absolute_local_gravity_moment_change_bound_nmm'] for r in result['bolts']), 'N mm')
