"""APA panel section references and explicit hold/T-nut bearing demand checks.

No effective strip width or attachment sharing is inferred. Supplied section
resultants must come from a separately authenticated structural response model.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path

from fea.round_structural_screw_reference import LBF_N, wood_interaction

PRIMARY = 'https://design.medeek.com/resources/structural/D510C_2012.pdf'
PRIMARY_SHA256 = '6141e0fe02ad0db8ddec20becf2ec25c85accd21c9796e51411d19448e5762ca'
PSI_MPA = LBF_N/25.4**2
# APA D510C Table9 A-A/A-C23/32, parallel/perpendicular to strength axis.
BASE = {'parallel': {'ei':320000.,'bending':775.,'tension':5100.,'compression':4800.,'ea':5100000.},
        'perpendicular': {'ei':90500.,'bending':455.,'tension':3400.,'compression':2900.,'ea':3150000.}}


def size_factor(stressed_width_mm):
    """APA2012 §4.5.5 width perpendicular to applied stress, not mesh width."""
    if not math.isfinite(stressed_width_mm) or stressed_width_mm <= 0:
        raise ValueError('Require positive physical panel/strip width')
    inches = stressed_width_mm/25.4
    return 1. if inches >= 24 else .5 if inches <= 8 else .25+.0313*inches


def panel_reference(stressed_width_mm, axis='weaker_orthogonal'):
    """Dry Group4 family envelope, CD1, no StructuralI or impact increase."""
    if axis not in (*BASE,'weaker_orthogonal'):
        raise ValueError('Require principal panel axis or weaker orthogonal envelope')
    r = BASE['perpendicular' if axis == 'weaker_orthogonal' else axis]
    cs = size_factor(stressed_width_mm)
    return {'axis':axis,'physical_stressed_width_mm':stressed_width_mm,'size_factor':cs,
            'bending_nmm_per_mm':r['bending']*.67*cs*LBF_N*25.4/304.8,
            'tension_n_per_mm':r['tension']*.67*cs*LBF_N/304.8,
            'compression_n_per_mm':r['compression']*.61*LBF_N/304.8,
            'apparent_ei_per_width_nmm':r['ei']*.56*LBF_N*25.4**2/304.8,
            'ea_per_width_n_per_mm':r['ea']*.56*LBF_N/304.8,
            'transverse_shear_n_per_mm':350.*LBF_N/304.8,
            'membrane_shear_n_per_mm':105.*.68*LBF_N/25.4,
            'face_bearing_reference_mpa':360.*PSI_MPA}


def section_check(*, panel, width_mm, height_mm, nx_n_per_mm, ny_n_per_mm,
                  mx_nmm_per_mm, my_nmm_per_mm, qx_n_per_mm, qy_n_per_mm,
                  nxy_n_per_mm, deflection_mm, deflection_limit_mm):
    """Compare authenticated local section demands, with x horizontal/y upslope.

    This returns directional component ratios. No unverified biaxial/combined
    interaction rule is presented as APA acceptance, and no peak smoothing occurs.
    """
    values = (nx_n_per_mm,ny_n_per_mm,mx_nmm_per_mm,my_nmm_per_mm,
              qx_n_per_mm,qy_n_per_mm,nxy_n_per_mm)
    valid_deflection = ((deflection_mm is None and deflection_limit_mm is None) or
                        (deflection_mm is not None and deflection_limit_mm is not None and
                         math.isfinite(deflection_mm) and math.isfinite(deflection_limit_mm) and
                         deflection_limit_mm > 0))
    if not all(math.isfinite(v) for v in values) or not valid_deflection:
        raise ValueError('Require finite signed resultants and explicit positive deflection limit')
    x,y = panel_reference(height_mm),panel_reference(width_mm)
    def axial(value, reference):
        return abs(value)/reference['tension_n_per_mm' if value >= 0 else 'compression_n_per_mm']
    ratios = {'axial_x':axial(nx_n_per_mm,x),'axial_y':axial(ny_n_per_mm,y),
        'bending_x':abs(mx_nmm_per_mm)/x['bending_nmm_per_mm'],
        'bending_y':abs(my_nmm_per_mm)/y['bending_nmm_per_mm'],
        'transverse_shear_x':abs(qx_n_per_mm)/x['transverse_shear_n_per_mm'],
        'transverse_shear_y':abs(qy_n_per_mm)/y['transverse_shear_n_per_mm'],
        'membrane_shear':abs(nxy_n_per_mm)/x['membrane_shear_n_per_mm']}
    if deflection_mm is not None:
        ratios['deflection']=abs(deflection_mm)/deflection_limit_mm
    return {'panel':panel,'component_ratios':ratios,
            'exceeded_components':[k for k,v in ratios.items() if v > 1.],
            'all_component_limits_met':all(v <= 1. for v in ratios.values()),
            'combined_loading_accepted':False,'qualified_for_design':False,
            'limits':'Component checks only. Simultaneous membrane/bending interaction, buckling, '
                     'orthotropic coupling, stress concentration and local contact remain separate. '
                     'Membrane shear for sections deeper than610mm needs buckling/restraint assessment.'}


def hold_demand(*, downward_n, horizontal_outward_n, angle_deg, standoff_mm,
                contact_lever_arm_mm, flange_diameter_mm, panel_hole_mm,
                retention_hole_mm, retention_hole_count):
    """Single hold bolt plus unilateral front contact; no useful clamp preload.

    Force lies in the board-normal vertical plane. No independent bolt bending
    couple, hold set screw or retention fastener moment path is credited.
    The hold's finite contact arm
    is supplied, never inferred from flange diameter. T>=max(0,N+|V|e/a).
    Flange contact area is an optimistic fully engaged flat annulus minus holes.
    """
    values = (downward_n,horizontal_outward_n,angle_deg,standoff_mm,contact_lever_arm_mm,
              flange_diameter_mm,panel_hole_mm,retention_hole_mm)
    if (not all(math.isfinite(v) for v in values) or downward_n < 0 or standoff_mm < 0
            or not 0 <= angle_deg <= 90 or contact_lever_arm_mm <= 0
            or min(flange_diameter_mm,panel_hole_mm,retention_hole_mm) <= 0
            or flange_diameter_mm <= panel_hole_mm or retention_hole_count < 0):
        raise ValueError('Require physical finite force/hold dimensions')
    angle = math.radians(angle_deg)
    normal = downward_n*math.sin(angle)+horizontal_outward_n*math.cos(angle)
    tangential = abs(downward_n*math.cos(angle)-horizontal_outward_n*math.sin(angle))
    moment = tangential*standoff_mm
    minimum_tension = max(0.,normal+moment/contact_lever_arm_mm)
    disk = math.pi*flange_diameter_mm**2/4
    net = math.pi*(flange_diameter_mm**2-panel_hole_mm**2
                   -retention_hole_count*retention_hole_mm**2)/4
    if net <= 0:
        raise ValueError('No positive flange bearing area')
    pressure = 360.*PSI_MPA
    required_area = minimum_tension/pressure
    return {'downward_n':downward_n,'horizontal_outward_n':horizontal_outward_n,
            'angle_deg':angle_deg,'normal_outward_n':normal,'tangential_n':tangential,
            'standoff_mm':standoff_mm,'contact_lever_arm_mm':contact_lever_arm_mm,
            'hold_couple_nmm':moment,'minimum_bolt_tension_n':minimum_tension,
            'gross_disk_area_mm2':disk,'net_annular_bearing_area_mm2':net,
            'gross_disk_bearing_reference_n':disk*pressure,'net_bearing_reference_n':net*pressure,
            'normal_only_gross_disk_ratio':max(0.,normal)/(disk*pressure),
            'normal_only_net_bearing_ratio':max(0.,normal)/(net*pressure),
            'minimum_bearing_ratio':minimum_tension/(net*pressure),
            'required_bearing_area_mm2':required_area,
            'required_circular_outer_diameter_mm':math.sqrt(4*required_area/math.pi+panel_hole_mm**2
                                                          +retention_hole_count*retention_hole_mm**2),
            'reference_bearing_exceeded':minimum_tension > net*pressure,
            'gross_disk_reference_exceeded_without_standoff':max(0.,normal) > disk*pressure,
            'qualification':False,
            'limits':'Dry APA face bearing at0.04in deformation; no ultimate-failure claim. '
                     'Flat flange fully engaged assumed; flange bending, uneven seat, preload, '
                     'retention screw action, independent hold-bolt bending couple, hold set screws '
                     'and barrel friction not credited. Supplied front-contact '
                     'lever arm is a sensitivity input until actual hold footprint is known.'}


def attachment_check(tension_n, lateral_n, references):
    """Use individually recovered reactions, never witness/equal-share demands."""
    return wood_interaction(tension_n,lateral_n,withdrawal_n=references['withdrawal_n'],
        lateral_reference_n=references['lateral_n'],head_reference_n=references['head_n'])


def report():
    from mini_moonboard import hold_tnut_reinforcement as nuts
    from mini_moonboard import round_reinforcement_frame as model

    source_paths = [Path(__file__),Path(nuts.__file__),Path(model.__file__),
                    Path('mini_moonboard/model.py'),Path('mini_moonboard/panel_grid_v2.py'),
                    Path('docs/round-reinforcement-review/review.json')]
    hashes = {str(p.resolve().relative_to(Path.cwd())):hashlib.sha256(p.read_bytes()).hexdigest()
              for p in source_paths}
    mass = json.loads(source_paths[-1].read_text())
    for path,sha in mass['source_sha256'].items():
        if hashlib.sha256(Path(path).read_bytes()).hexdigest() != sha:
            raise ValueError('Stale current geometry: '+path)
        hashes[path]=sha
    hole = nuts.measured.V1_SELECTED_TNUT_HOLE_DIAMETER_MM
    # Require the owned current7/16in opening, never select a new hole here.
    if not math.isclose(hole,11.112,abs_tol=1e-9):
        raise ValueError('Reassess changed panel hold hole')
    rows=[]
    for family,angle in [('main',40.),('kicker',0.)]:
        for pounds in (250.,300.):
            for factor in (1.,2.):
                for horizontal in (-300.,0.,300.):
                    for standoff in (0.,50.,100.):
                        for arm in (25.,50.,100.):
                            rows.append({'family':family,'climber_lb':pounds,'load_multiplier':factor,
                                **hold_demand(downward_n=pounds*factor*LBF_N,
                                    horizontal_outward_n=horizontal,angle_deg=angle,standoff_mm=standoff,
                                    contact_lever_arm_mm=arm,flange_diameter_mm=nuts.FLANGE_DIAMETER_MM,
                                    panel_hole_mm=hole,retention_hole_mm=nuts.RETENTION_HOLE_DIAMETER_MM,
                                    retention_hole_count=3)})
    panels={name:{'horizontal_stress_reference':panel_reference(225. if name.startswith('kicker') else 1219.2),
                  'vertical_stress_reference':panel_reference(1219.2)}
            for name in ('main_lower_left','main_lower_right','main_upper_left','main_upper_right','kicker_left','kicker_right')}
    for path,sha in hashes.items():
        if hashlib.sha256(Path(path).read_bytes()).hexdigest()!=sha:
            raise ValueError('Source changed during panel check: '+path)
    return {'candidate':model.KEY,'primary_source':PRIMARY,'primary_pdf_sha256':PRIMARY_SHA256,
        'material_basis':'Owned AC23/32 PS1-09; APA2012 dry Group4 orthogonal family envelope, '
                         'CD1.0, no impact or StructuralI increase; axes remain orthogonal to cuts.',
        'source_sha256':hashes,'panel_references':panels,'hold_cases':rows,
        'case_count':len(rows),'normal_only_gross_disk_exceedance_count':sum(
            r['gross_disk_reference_exceeded_without_standoff'] for r in rows),
        'qualified_for_design':False,'global_panel_response_evaluated':False,
        'minimum_same_seam_flange_edge_ligament_mm':19.2-nuts.FLANGE_DIAMETER_MM/2,
        'minimum_same_seam_hold_hole_ligament_mm':19.2-hole/2,
        'unrecessed_barrel_front_cover_mm':model.wide.PANEL-nuts.BARREL_PROJECTION_MM,
        'limits':'Hold-level force and plywood face-bearing check is independent of panel screw sharing. '
                 'Global bending/deflection, net-hole stresses and actual individual attachment demand '
                 'require authenticated section/connection outputs; this report fabricates none. '
                 'Current Tnut seats stand behind panel; a future recess changes net thickness and cover. '
                 'Front hold contact arm, hold bolt engagement, initial preload and Tnut flange flexure '
                 'remain unspecified. Gross-disk normal-only failures do not depend on that contact arm. '
                 'All face panels and both kickers remain independent.'}


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    result=report()
    with args.output.open('x') as stream:
        json.dump(result,stream,indent=2,allow_nan=False)
        stream.write('\n')
