"""One actual low-side-rail response trial; no transfer from the unbraced result."""
import argparse
import json
import math
from pathlib import Path

from fea.current_response_materials import WOOD_E
from fea.current_response_run import run
from mini_moonboard import compact_rail_frame as candidate


def bolt_properties(connection):
    washer=connection.components()[1].BoundingBox()
    diameter=connection.diameter
    hole=diameter+1.5875
    outer=max(washer.ylen,washer.zlen)
    area=math.pi*(outer**2-hole**2)/4
    steel=200000.*math.pi*diameter**2/4/connection.grip
    # Two wood seats in series; their combined compression path is the grip.
    seat=.05*WOOD_E*area/connection.grip
    return {'lateral_n_per_mm':500.**1.5*diameter/23.,
            'axial_n_per_mm':1/(1/steel+1/seat),
            'basis':f'Finite individual bolt springs, diameter {diameter:g} mm and wood grip {connection.grip:g} mm; no clamp-friction credit.',
            'washer_net_area_mm2':area}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--hold',default='A12')
    parser.add_argument('--horizontal',nargs=2,type=float,default=(0.,300.))
    parser.add_argument('--contact-seed',type=Path)
    args=parser.parse_args()
    seeded = {}
    if args.contact_seed:
        seed=json.loads(args.contact_seed.read_text())
        seeded={'contact_update_strategy':'one_per_floor_body',
                'initial_contact_names':[row['name'] for row in seed['bearings'] if row['active']]}
    by_name={c.name:bolt_properties(c) for c in candidate.connections() if c.kind=='bolt'}
    base=dict(next(iter(by_name.values())))
    base['by_name']=by_name
    monitors=[]
    for side,sign in (('left',-1),('right',1)):
        for across in (0.,.5,1.):
            x=sign*(candidate.b.HALF-across*candidate.RAIL_THICKNESS_MM)
            for along in (0.,.5,1.):
                y=candidate.previous.HEADER_BACK_Y+along*candidate.previous.HEADER_DEPTH
                monitors.append({'name':f'header_rail_{side}_{across}_{along}',
                    'first':'base_rail_tie_'+side,'second':'base_header',
                    'first_point':[x,y,candidate.RAIL_TOP_Z],
                    'second_point':[x,y,candidate.base.HEADER_BOTTOM],'normal':[0.,0.,1.]})
    result=run(args.output,module=candidate,expected_candidate=candidate.KEY,
        bolt_stiffness=base,hold=args.hold,pounds=250.,horizontal_force=tuple(args.horizontal),
        leg_floor_grid=3,patch_size=20.,clearance_monitors=monitors,**seeded)
    print({k:result[k] for k in ('candidate','numerically_accepted',
          'maximum_panel_displacement_mm','maximum_timber_displacement_mm')},flush=True)


if __name__=='__main__':
    main()
