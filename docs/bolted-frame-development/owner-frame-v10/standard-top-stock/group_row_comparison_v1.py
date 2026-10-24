"""Conditional row benchmarks; never a MoonBoard connection acceptance."""
import argparse
import hashlib
import json
import math
from pathlib import Path

N_PER_LBF = 4.4482216152605
MM_PER_IN = 25.4
SOURCES = [
    'https://dot.ca.gov/-/media/dot-media/programs/engineering/documents/structureconstruction/fw-appendixd-ex12-a11y.pdf',
    'https://web-media.awc.org/wp-content/uploads/2025/03/31134949/2024-NDS-Errata-and-Addenda-03.28.25.pdf',
]

def cg(n, spacing_in, diameter_in, EA_main_lbf, EA_side_lbf, metal=False):
    assert isinstance(n, int) and n >= 1
    assert min(spacing_in, diameter_in, EA_main_lbf, EA_side_lbf) > 0
    gamma = (270000 if metal else 180000) * diameter_in**1.5
    ratio = min(EA_main_lbf / EA_side_lbf, EA_side_lbf / EA_main_lbf)
    u = 1 + gamma * spacing_in / 2 * (1 / EA_main_lbf + 1 / EA_side_lbf)
    # Stable reciprocal equivalent of u-sqrt(u*u-1).
    m = 1 / (u + math.sqrt(u*u - 1))
    factor = (m * (1-m**(2*n)) / (n*((1+ratio*m**n)*(1+m)-1+m**(2*n)))) * ((1+ratio)/(1-m))
    return {'Cg': factor, 'gamma_lbf_per_in': gamma, 'REA': ratio, 'u': u, 'm': m}

def cg_si(n, spacing_mm, diameter_mm, EA_main_N, EA_side_N, metal=False):
    return cg(n, spacing_mm/MM_PER_IN, diameter_mm/MM_PER_IN,
              EA_main_N/N_PER_LBF, EA_side_N/N_PER_LBF, metal)

def tests():
    ex = cg(3, 2.5, .625, 1600000*144, 1600000*10.88)
    assert abs(ex['Cg']-.9806318451462117) < 1e-12
    assert round(ex['Cg'], 2) == .98
    si = cg_si(3, 63.5, 15.875, 1600000*144*N_PER_LBF,
               1600000*10.88*N_PER_LBF)
    assert abs(ex['Cg']-si['Cg']) < 1e-13
    assert abs(cg(1,2,.5,1e7,2e7)['Cg']-1) < 1e-12
    assert abs(cg(2,2,.5,1e7,2e7)['Cg']-cg(2,2,.5,2e7,1e7)['Cg']) < 1e-13
    assert cg(2,2,.5,1e7,2e7)['Cg'] > .5
    try:
        cg(2,0,.5,1e7,2e7)
        raise AssertionError('zero spacing accepted')
    except AssertionError as err:
        assert str(err) != 'zero spacing accepted'
    return {'tests_passed':6, 'Caltrans_example':ex,
            'scope':'equation benchmark, SI conversion, n=1, EA symmetry, diagnostic comparison, invalid spacing'}

def bound(path):
    return {'path':str(path), 'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--repo', required=True, type=Path)
    ap.add_argument('--out', required=True, type=Path)
    a=ap.parse_args()
    root=a.repo
    gp=root/'fea/generated/v10-standard-top-stock-v1/4x6/geometry-v2/geometry.json'
    bp=root/'fea/generated/v10-standard-top-stock-v1/mechanics-proposal/4x6/analysis-v4/response-bank.json'
    rp=bp.parent/'reference-review.json'
    assert bound(bp)['sha256']=='9a885d4dbfe5ef54fbb0d598e3c30d7d0d7233af67d75b39695b6ccdea066736'
    assert bound(rp)['sha256']=='88018056e852726221561ef1823cb603ba8afec2224c21ee84dd001b2e245abf'
    geom=json.loads(gp.read_text())
    profiles=geom['profiles']
    axes={x['id']:x for x in geom['axes']}
    def area(member):
        return math.prod(profiles[member]['blank_mm'][1:])
    Ewood=11031.612
    def point(axis):
        return axes[axis]['point_xyz_mm']
    rear_spacing=math.dist(point('lumber_leg_bolt_left_1'),point('lumber_leg_bolt_left_2'))
    assert abs(rear_spacing-67.3227228110)<1e-6
    header_ids=['eoere_bolt_081','eoere_bolt_082','v10_header_bolt_001','v10_header_bolt_002']
    header_distances=[math.dist(point(x),point(y)) for i,x in enumerate(header_ids) for y in header_ids[i+1:]]
    for required in (41.275,50.8):
        assert any(abs(d-required)<1e-6 for d in header_distances)
    scenarios=[]
    def add(name,spacing,D,mainEA,sideEA,metal,physical,limitations,legacy):
        result=cg_si(2,spacing,D,mainEA,sideEA,metal)
        scenarios.append(dict(name=name,n_per_assumed_row=2,spacing_mm=spacing,D_mm=D,
            EA_main_N=mainEA,EA_side_N=sideEA,metal=metal,**result,
            legacy_receiver_signature_factor=legacy,
            comparison_scope='Conditional elastic axial-row surrogate ONLY; not applicable complete candidate factor',
            physical_inputs=physical,applicability_failures=limitations,
            actual_connection_Cg=None,complete_connection_status='UNRESOLVED'))
    add('rear wood-to-wood gross-EA aligned-row surrogate',rear_spacing,12.7,
        Ewood*area('base_side_left'),Ewood*area('lumber_leg_left'),False,
        'Two actual centers, modeled gross member areas and E; nominal diameter. Hypothetical force aligned with centerline and axial member load paths.',
        ['Actual centerline is oblique to both member grains',
         'Actual individual forces not uniform or aligned with row',
         'Saved local force couples cannot be replaced by scalar axial-row demand',
         'Effective axial transfer areas and calibrated slip are not established'],.5)
    # Header rectangle: two possible principal-direction row definitions.
    # Steel gross strip is modeled thickness times full flange width, NOT an established effective EA.
    steelEA=200000*6.35*88.9
    for spacing in (41.275,50.8):
        for strips in (1,2):
            add(f'header {spacing}mm two-fastener row, {strips} gross steel strip(s)',spacing,9.525,
                Ewood*area('base_header'),strips*steelEA,True,
                'Wood gross EA; E steel200000MPa times modeled6.35x88.9mm strip. Two strips assumes simultaneous equal-action participation, not verified.',
                ['Formed fitting effective EA/heel bending not equal to full gross axial strip by proof',
                 'Actual force directions vary across bolts and cases; principal rows are comparators',
                 'Two steel interfaces are coupled and not established symmetric double shear',
                 'Local couples, splitting and steel transfer remain'],.25)
    result={'schema':'conditional-group-row-comparison-v1','revision':geom.get('revision'),
        'selected_revision':'v10-standard-top-4x6-stock-proposal-v2',
        'sources':[bound(gp),bound(bp),bound(rp)],'primary_references':SOURCES,
        'row_geometry_checks':{'rear_center_spacing_mm':rear_spacing,'header_pair_distances_mm':header_distances,
            'status':'center spacings verified; load alignment NOT established'},
        'equations':{'gamma':'180000*D_in**1.5 wood/wood;270000*D_in**1.5 wood/metal; lbf/in',
        'REA':'min(EAm/EAs,EAs/EAm)',
        'u':'1+gamma*s/2*(1/EAm+1/EAs)',
        'm':'u-sqrt(u*u-1)',
        'Cg':'m*(1-m**(2*n))/(n*((1+REA*m**n)*(1+m)-1+m**(2*n)))*(1+REA)/(1-m)'},
        'units':{'EA':'N in inputs, converted to lbf','spacing':'mm in inputs, converted to in'},
        'model_Ewood_MPa':Ewood,'tests':tests(),'conditional_scenarios':scenarios,
        'upper_cleat':{'axes':['eoere_bolt_067','eoere_bolt_071','eoere_bolt_070','eoere_bolt_074'],
            'status':'UNRESOLVED; no two-member Cg mapping calculated',
            'reason':'Serial plywood/sidewood/steel; differently oriented members, shared continuous laminated cleat and other bolt paths. Effective areas, bond/slip, shear-plane load partition and external moments require coupled treatment.'},
        'model_coverage':{'present':['gross beam axial EA','distributed shaft foundations','unequal individual forces','saved local moments','hole gaps'],
            'not_demonstrated':['NDS-equivalent calibrated load-slip','resolved local row ligament deformation','physical fitting effective EA','full brittle wood capacities','full simultaneous wrench capacity'],
            'double_counting':'Neither fully established nor excluded; compare same-boundary-condition row benchmark before adopting a treatment.'},
        'legacy_diagnostics':{'case_rows':15,'components':8,'preserved':True,'not_established_physical_failures':True},
        'actual_Cg_adopted':None,'acceptance_changed':False,'release_changed':False,
        'minimum_next_evidence':['Physical row and effective member load-path definition',
        'Applicable calibrated/standard slip and clearance basis',
        'Matched benchmark of existing FE axial-row redistribution vs NDS equation',
        'Full actual force-plus-moment mapping, splitting/tear-out/net/fitting checks']}
    a.out.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'out':str(a.out),'tests':result['tests'],
        'conditional_factors':[(x['name'],x['Cg'])for x in scenarios],
        'actual_factor_adopted':None},indent=2))

if __name__=='__main__': main()
