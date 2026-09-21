"""Archive and recompute current compact-frame evidence without another solve."""
import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from fea.compact_thick_checks import assess, hardware_assumptions


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def base_comparisons(report, geometry):
    """Actual partial overlap and conservative end-notch shear comparisons."""
    result = {}
    psi = .006894757293168361
    for name, contact in geometry['header_overlap'].items():
        data = report['member_section_demands'][name]
        member = data['member']
        grain = member['axis']
        forces = [row['force_on_first_xyz_n'][2] for key,row in report['physical_connection_forces'].items()
                  if key.startswith('bearing_'+name+'_base_header_')]
        reactions = [max(0.,f) for f in forces]
        if not reactions or contact['area_mm2'] <= 0:
            raise ValueError('Missing actual member/header bearing: '+name)
        width, depth = member['width_mm'],member['depth_mm']
        retained = contact['full_member_face_area_mm2']/width*abs(grain[2])
        if not 0 < retained <= depth+1.e-5:
            raise ValueError('Invalid level end-cut depth')
        first_station = min(s['station_along_grain_mm'] for s in data['sections'])
        shear = max(math.hypot(s['shear_u_n'],s['shear_v_n']) for s in data['sections']
                    if abs(s['station_along_grain_mm']-first_station)<1.e-6)
        resistance = 2/3*(180*psi)*width*retained*(retained/depth)**2
        result[name] = {**contact,'compression_reaction_n':sum(reactions),
            'average_header_bearing_ratio':sum(reactions)/(contact['area_mm2']*625*psi),
            'quarter_area_corner_sensitivity_ratio':4*max(reactions)/(contact['area_mm2']*625*psi),
            'retained_end_depth_mm':retained,'removed_normal_depth_mm':depth-retained,
            'quarter_depth_margin_after_3mm_allowance_mm':depth/4-(depth-retained)-3.,
            'first_recovered_section_shear_n':shear,'conservative_notched_shear_reference_n':resistance,
            'conservative_notched_shear_ratio':shear/resistance,
            'scope':'NDS tension-side end-notch shear formula used as a conservative comparison. Bearing average and quarter-area corner sensitivity do not establish actual pressure or local splitting. No support assigned outside header.'}
    return result


def checks(report, geometry):
    if report['candidate'] != geometry['candidate']:
        raise ValueError('Native and CAD candidates differ')
    for path,sha in geometry['source_sha256'].items():
        if path.startswith('mini_moonboard/') and report['source_sha256'].get(path)!=sha:
            raise ValueError('Native and CAD model sources differ: '+path)
    diameter = next(iter(geometry['geometries_by_bolt_name'].values()))['diameter_mm']
    result = assess(report,geometry['geometries_by_bolt_name'],hardware_assumptions(),hole_diameter_mm=diameter+1.5875)
    if 'bolts' not in result:
        raise ValueError('Native numerical gates failed')
    result['base'] = base_comparisons(report,geometry)
    return result


def summary(report, result):
    bolts = result['bolts'].values()
    return {'candidate':report['candidate'],'numerically_accepted':report['numerically_accepted'],
        'peak_individual_lateral_ratio':max(b['lateral_ratio'] for b in bolts),
        'minimum_directional_edge_end_margin_mm':min(p['minimum_margin_mm'] for b in bolts for p in b['placement'].values()),
        'peak_with_additional_group_reduction':max(g['peak_with_additional_group_reduction'] for g in result['groups'].values()),
        'panel_displacement_mm':report['maximum_panel_displacement_mm'],
        'timber_displacement_mm':report['maximum_timber_displacement_mm'],
        'sampled_net_member_ratios':{n:r['sampled_net_peak']['comparison']['conservative_net_section_envelope_ratio'] for n,r in result['local']['local_members'].items()},
        'header_gross_ratio':result['local']['header_gross']['base_header']['gross_section_peak']['necessary_gross_section_ratio'],
        'maximum_notched_end_shear_ratio':max(r['conservative_notched_shear_ratio'] for r in result['base'].values()),
        'maximum_quarter_area_header_bearing_ratio':max(r['quarter_area_corner_sensitivity_ratio'] for r in result['base'].values()),
        'qualified_for_design':False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--geometry',type=Path)
    parser.add_argument('--case',nargs=2,action='append',metavar=('LABEL','DIRECTORY'))
    parser.add_argument('--output',type=Path,default=Path('fea/results/compact-thick-study'))
    args = parser.parse_args()
    out=args.output
    out.mkdir(parents=True,exist_ok=True)
    if args.case:
        if args.geometry is None:
            parser.error('--geometry required when archiving cases')
        (out/'geometry.json').write_bytes(args.geometry.read_bytes())
        manifest={'candidate':'compact-thick-development','geometry':'geometry.json','cases':{}}
        for label,directory in args.case:
            directory=Path(directory)
            report_path=directory/'report.json'
            raw=report_path.read_bytes()
            report=json.loads(raw)
            packed=out/(label+'-report.json.gz')
            packed.write_bytes(gzip.compress(raw,mtime=0))
            archive=out/(label+'-sources.zip')
            with ZipFile(archive,'w',ZIP_DEFLATED) as target:
                for path,sha in report['source_sha256'].items():
                    source=directory/'source_snapshots'/path
                    if digest(source)!=sha:
                        raise ValueError('Native source snapshot mismatch: '+path)
                    target.write(source,path)
                target.write('scripts/compact_thick_study.py','scripts/compact_thick_study.py')
            manifest['cases'][label]={'compressed_report':packed.name,'compressed_sha256':digest(packed),
                'native_report_sha256':hashlib.sha256(raw).hexdigest(),'native_directory':str(directory),
                'sources':archive.name,'sources_sha256':digest(archive)}
        manifest['geometry_sha256']=digest(out/'geometry.json')
        (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    manifest=json.loads((out/'manifest.json').read_text())
    if digest(out/manifest['geometry'])!=manifest['geometry_sha256']:
        raise ValueError('Geometry evidence changed')
    geometry=json.loads((out/manifest['geometry']).read_text())
    summaries={}
    for label,record in manifest['cases'].items():
        path=out/record['compressed_report']
        if digest(path)!=record['compressed_sha256']:
            raise ValueError('Compressed native report changed')
        raw=gzip.decompress(path.read_bytes())
        if hashlib.sha256(raw).hexdigest()!=record['native_report_sha256']:
            raise ValueError('Native report changed')
        report=json.loads(raw)
        result=checks(report,geometry)
        (out/(label+'-checks.json')).write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
        summaries[label]=summary(report,result)
    (out/'summary.json').write_text(json.dumps(summaries,indent=2,allow_nan=False)+'\n')
    print(json.dumps(summaries,indent=2))


if __name__=='__main__':
    main()
