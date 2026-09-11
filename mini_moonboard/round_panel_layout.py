"""Mirrored 12-per-face screw layout hypothesis for the round-passage candidate.

Rows and columns are explicit shared datums. No screw is individually shifted
around a clash: failed fit requires revising the shared pattern and rechecking.
Count, resistance and stiffness are not qualified by this layout.
"""
from math import hypot

HALF=1219.2
OUTER_X=1200.15
CENTER_X=70.
INNER_X=(CENTER_X+(OUTER_X-CENTER_X)/3,CENTER_X+2*(OUTER_X-CENTER_X)/3)
# The upper center principal ends 38.1 mm below the panel edge. An 85 mm
# top inset leaves 46.9 mm to that stock end (44.45 mm reversible minimum).
BOTTOM_INSET=59.05
TOP_INSET=85.
FACE_ROWS=tuple(BOTTOM_INSET+i*(HALF-TOP_INSET-BOTTOM_INSET)/3 for i in range(4))
RAIL_S={'lower_edge':59.05,'lower_service':1050.15,
        'upper_service':1238.25,'upper_edge':2419.35}
KICKER_ROWS=(50.8,127.)


def datums():
    rows=[]
    for side,sign in (('left',-1.),('right',1.)):
        for band,offset in (('lower',0.),('upper',HALF)):
            panel=f'main_{band}_{side}'
            for role,x,receiver in (('rim',OUTER_X,f'base_side_{side}'),
                                    ('center',CENTER_X,f'base_principal_center_{side}')):
                for index,s in enumerate(FACE_ROWS,1):
                    rows.append({'name':f'round_panel_{band}_{side}_{role}_{index}','panel':panel,
                                 'receiver':receiver,'x':sign*x,'s':offset+s,'role':role})
            for role in ('edge','service'):
                receiver=(f'base_rail_bottom_{side}' if band=='lower' else 'base_rail_top') if role=='edge' else f'base_rail_service_{band}_{side}'
                for index,x in enumerate(INNER_X,1):
                    rows.append({'name':f'round_panel_{band}_{side}_{role}_{index}','panel':panel,
                                 'receiver':receiver,'x':sign*x,'s':RAIL_S[band+'_'+role],'role':role})
        for role,x,receiver in (('rim',OUTER_X,f'base_post_outer_{side}'),
                                ('center',CENTER_X,f'base_post_center_{side}')):
            for index,z in enumerate(KICKER_ROWS,1):
                rows.append({'name':f'round_kicker_{side}_{role}_{index}','panel':f'kicker_{side}',
                             'receiver':receiver,'x':sign*x,'s':z,'role':role})
    return tuple(rows)


def panel_connections():
    import cadquery as cq

    from . import horizontal_service_frame as model
    result=[]
    for row in datums():
        main=row['panel'].startswith('main_')
        start=model.b.point(row['x'],row['s'],-model.wide.PANEL) if main else cq.Vector(row['x'],model.base.HEADER_FRONT_Y+model.wide.PANEL,row['s'])
        direction=model.b.normal() if main else cq.Vector(0,-1,0)
        result.append(model.timber.PanelScrew(row['name'],start,direction,50.8,4.1402,
            (row['panel'],row['receiver']),product_status=model.timber.PanelScrew.product_status+'; mirrored12-per-face comparison hypothesis; not qualified'))
    return tuple(result)


def planar_checks():
    from . import panel_grid_v2 as grid
    rows=datums();main=[r for r in rows if r['panel'].startswith('main_')]
    service=[(name,x-HALF,s) for mapping in (grid.main_tnut_datums(),grid.main_led_datums()) for name,(x,s) in mapping.items()]
    distances=[(hypot(row['x']-x,row['s']-s),row['name'],name) for row in main for name,x,s in service]
    nearest=min(distances)
    main_edge=min(min(abs(r['x']),HALF-abs(r['x']),r['s']%HALF,HALF-r['s']%HALF) for r in main)
    return {'count':len(rows),'main_count':len(main),'minimum_service_axis_distance_mm':nearest[0],
            'service_clearance_witness':list(nearest[1:]),'required_service_axis_distance_mm':28.,
            'minimum_panel_edge_distance_mm':main_edge,
            'future_insert_outer_radius_mm':6.0706,'minimum_face_reserve_to_edge_mm':main_edge-6.0706,
            'service_axis_check_passed':nearest[0]>=28.,'qualified_for_design':False,
            'limits':'Planar geometry only; retained hardware, actual wood, round passages and strength require separate checks.'}
