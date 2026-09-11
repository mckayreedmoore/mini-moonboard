"""Read-only panel screw inventory; proposed deletions are untested hypotheses."""
import argparse
import csv
import hashlib
import itertools
import json
from collections import defaultdict
from pathlib import Path

import numpy as np

CSV=Path('exports/horizontal-service-development/connections.csv')
RESERVES=Path('exports/horizontal-service-development/future-insert-reserves.csv')
BATCH=Path('fea/generated/horizontal-frame-batch-v2')
PLY=18.25625


def vector(row, keys):return np.array([float(row[k]) for k in keys])


def reduced_group(rows, maximum_gap=300.):
    """Keep original axes; retain minimum existing infill per original interval."""
    ordered=sorted(rows,key=lambda r:r['grain_station_mm'])
    original=[r for r in ordered if r['provenance']=='original']
    keep={r['connection'] for r in original}
    for first,last in itertools.pairwise(original):
        current=first
        while last['grain_station_mm']-current['grain_station_mm']>maximum_gap+1.e-7:
            options=[r for r in ordered if current['grain_station_mm']<r['grain_station_mm']<=current['grain_station_mm']+maximum_gap+1.e-7]
            if not options:raise ValueError('Existing stations cannot meet candidate spacing')
            current=options[-1];keep.add(current['connection'])
    return keep


COUPLED_CASES={'c10-k1000','c10-k100','c10-k10000','c10-300lb','f10-k1000','c6-k1000','c7-k1000','c10-refined'}


def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):h.update(block)
    return h.hexdigest()


def load_force_reports(directory):
    directory=Path(directory);summary=json.loads((directory/'summary.json').read_text())
    rows=summary['cases'];expected=COUPLED_CASES|{'frame-only-c10','panel-credit-c10'}
    if len(rows)!=10 or {r['case'] for r in rows}!=expected:raise ValueError('Incomplete force case inventory')
    reports={};sources=None;paths=[directory/'summary.json']
    for row in rows:
        if row['case'] not in COUPLED_CASES:continue
        root=directory/row['case'];path=root/'report.json'
        if digest(path)!=row['report_sha256']:raise ValueError('Force report hash mismatch')
        report=json.loads(path.read_text());paths.append(path)
        if not report['contact_diagnostic_checks_passed']:raise ValueError('Rejected force case')
        if sources is not None and report['source_sha256']!=sources:raise ValueError('Force source closures differ')
        sources=report['source_sha256']
        required={'docs/led-wiring-reference.json','docs/ml24z-reference.json','docs/panel-insert-reference.json','docs/ml23z-reference.json'}
        if not required<=set(sources):raise ValueError('Force runtime reference closure incomplete')
        for name,sha in sources.items():
            if digest(root/'source_snapshots'/name)!=sha:raise ValueError('Force source snapshot hash mismatch')
        cycle=report['final_cycle_directory'];job=root/cycle
        cycle_sha=digest(job/'report.json')
        history=[r for r in report['contact_cycles'] if r['directory']==cycle]
        if len(history)!=1 or history[0]['report_sha256']!=cycle_sha or report['artifact_sha256'].get(cycle+'/report.json')!=cycle_sha:
            raise ValueError('Force final cycle hash mismatch')
        native=json.loads((job/'report.json').read_text())
        if native['connector_forces']!=report['connector_forces']:raise ValueError('Force final cycle values differ')
        for name in ('input.json','frame.inp','frame.dat','frame.log'):
            sha=digest(job/name)
            if native['artifact_sha256'].get(name)!=sha or report['artifact_sha256'].get(cycle+'/'+name)!=sha:
                raise ValueError('Force native artifact hash mismatch')
        reports[row['case']]=report
    return reports,paths


def build():
    source_paths=[CSV,RESERVES,Path(__file__)]
    rows=[r for r in csv.DictReader(CSV.open()) if r['members'].startswith(('main_','kicker_'))]
    reserves={r['connection']:r for r in csv.DictReader(RESERVES.open())}
    reports,authenticated_paths=load_force_reports(BATCH)
    source_paths.extend(authenticated_paths)
    reference=reports['c10-k1000'];input_path=BATCH/'c10-k1000'/reference['final_cycle_directory']/'input.json'
    source_paths.append(input_path);record=json.loads(input_path.read_text())
    expected=reference['artifact_sha256'][reference['final_cycle_directory']+'/input.json']
    if hashlib.sha256(input_path.read_bytes()).hexdigest()!=expected:raise ValueError('Reference input hash mismatch')
    members={r['name']:r for r in record['members']}
    normal=vector(rows[0],('dx','dy','dz'));along=np.array([0.,normal[2],-normal[1]])
    hold_s=1219.2+100.+200.*(int(record['hold'][1:])-7)
    offset=np.dot(record['target_xyz_mm'],along)-hold_s
    expected_names={r['connection'] for r in rows}
    if len(expected_names)!=87 or len(rows)!=87:raise ValueError('Expected 87 unique panel screw names')
    axes=[tuple(round(float(r[k]),7) for k in ('x_mm','y_mm','z_mm','dx','dy','dz')) for r in rows]
    if len(set(axes))!=len(axes):raise ValueError('Duplicate panel screw axes across groups')
    for report in reports.values():
        actual={n for n in report['connector_forces'] if n.startswith(('timber_panel_','timber_kicker_','infill_','horizontal_panel_'))}
        if actual!=expected_names:raise ValueError('Panel force inventory differs from CSV')
    result=[];groups=defaultdict(list)
    for row in rows:
        name=row['connection'];panel,receiver=row['members'].split(' + ')
        start=vector(row,('x_mm','y_mm','z_mm'));direction=vector(row,('dx','dy','dz'));entry=start+direction*PLY
        member=members[receiver];axis=np.array(member['axis']);u=np.array(member['section_u']);v=np.array(member['section_v'])
        grain=float(entry@axis);low=float(np.array(member['start'])@axis);high=float(np.array(member['end'])@axis)
        first=grain-low
        if receiver.startswith(('base_side_','base_principal_')):
            first=(entry[2]-member['start'][2])/axis[2]
        cross=np.cross(axis,direction);cross/=np.linalg.norm(cross)
        centre=np.array(member['section_centroid_xyz_mm'])-v*member['section_centroid_shift_v_mm']
        half=(member['gross_width_mm']*abs(cross@u)+member['gross_depth_mm']*abs(cross@v))/2
        edge=float(half-abs((entry-centre)@cross))
        station=float(start@along-offset) if panel.startswith('main_') else float(start[2])
        panel_lo=1219.2 if 'upper' in panel else 0.;panel_hi=panel_lo+1219.2 if panel.startswith('main_') else 225.
        xlo=-1219.2 if panel.endswith('left') else 0.;xhi=xlo+1219.2
        provenance='infill' if name.startswith('infill_') else 'original'
        purpose=('Supplemental inherited 150 mm principal interval rule' if provenance=='infill' else
                 'Original center panel-edge retention' if 'principal_' in receiver else
                 'Outer panel-edge retention' if receiver.startswith('base_side_') else
                 'Horizontal service/seam rail attachment' if 'service_' in receiver else
                 'Panel top/bottom edge attachment' if 'rail_' in receiver else 'Kicker perimeter retention')
        demands=[]
        for case,report in reports.items():
            if not report['contact_diagnostic_checks_passed']:raise ValueError('Rejected source force case')
            witness=report['connector_forces'][name]
            if np.linalg.norm(np.array(witness['first_point_xyz_mm'])-(start+direction*PLY/2))>1.e-6:
                raise ValueError('Force witness differs from exported screw axis')
            force=np.array(witness['force_on_first_xyz_n'])
            signed=float(force@direction)
            demands.append((case,max(0.,-signed),float(np.linalg.norm(force-signed*direction))))
        withdrawal=max(demands,key=lambda x:x[1]);lateral=max(demands,key=lambda x:x[2])
        r={'connection':name,'panel':panel,'receiver':receiver,'provenance':provenance,'purpose':purpose,
           'direction_xyz':direction.tolist(),'x_mm':float(start[0]),'panel_s_or_z_mm':station,'grain_station_mm':grain,
           'receiver_low_end_distance_mm':float(first),'receiver_high_end_distance_mm':high-grain,
           'receiver_face_edge_distance_mm':edge,'nearest_panel_edge_mm':min(start[0]-xlo,xhi-start[0],station-panel_lo,panel_hi-station),
           'gross_penetration_mm':float(row['length_mm'])-PLY,'nominal_embedded_thread_mm':31.496,
           'future_insert_reserve_passed_historical':reserves[name]['passes_nominal_reserve']=='True',
           'maximum_withdrawal_n':withdrawal[1],'withdrawal_case':withdrawal[0],
           'maximum_lateral_n':lateral[2],'lateral_case':lateral[0],
           'proven_removable':False,'candidate_300_action':'keep','candidate_remove_all_infill_action':'drop' if provenance=='infill' else 'keep'}
        result.append(r);groups[panel,receiver].append(r)
    summaries=[]
    for (panel,receiver),items in sorted(groups.items()):
        ordered=sorted(items,key=lambda r:r['grain_station_mm'])
        for index,r in enumerate(ordered):
            distances=[abs(r['grain_station_mm']-q['grain_station_mm']) for q in ordered if q is not r]
            r['nearest_same_panel_receiver_spacing_mm']=min(distances) if distances else None
            if min(distances,default=1.)<1.e-6:raise ValueError('Duplicate panel/receiver station')
        keep=reduced_group(ordered) if 'principal_' in receiver else {r['connection'] for r in items}
        for r in items:r['candidate_300_action']='keep' if r['connection'] in keep else 'drop'
        gaps=[b['grain_station_mm']-a['grain_station_mm'] for a,b in itertools.pairwise(ordered)]
        summaries.append({'panel':panel,'receiver':receiver,'count':len(items),
                          'infill_count':sum(r['provenance']=='infill' for r in items),
                          'minimum_spacing_mm':min(gaps,default=None),'maximum_spacing_mm':max(gaps,default=None),
                          'candidate_300_count':len(keep)})
    for r in result:
        r['nearest_all_panel_same_receiver_spacing_mm']=min(abs(r['grain_station_mm']-q['grain_station_mm'])
            for q in result if q is not r and q['receiver']==r['receiver'])
    return {'screws':result,'groups':summaries,'count':len(result),'qualified_for_design':False,
            'proven_removable_count':0,'candidate_300_count':sum(r['candidate_300_action']=='keep' for r in result),
            'candidate_remove_all_infill_count':sum(r['provenance']=='original' for r in result),
            'limits':'CSV inventory and historical grooved-frame force evidence; no removal solve, current round-bore fit or strength qualification. Both candidate spacings are hypotheses, not manufacturer prescriptions. Face-edge/end figures describe gross stock and true lower bevel plane; service cuts need separate solid checks.',
            'source_sha256':{str(p.resolve().relative_to(Path.cwd())):hashlib.sha256(p.read_bytes()).hexdigest() for p in source_paths}}


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=False);report=build()
    (args.output/'inventory.json').write_text(json.dumps(report,indent=2)+'\n')
    with (args.output/'panel-screws.csv').open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(report['screws'][0]),lineterminator='\n');writer.writeheader();writer.writerows(report['screws'])
    print({k:report[k] for k in ('count','candidate_300_count','candidate_remove_all_infill_count','proven_removable_count')})


if __name__=='__main__':main()
