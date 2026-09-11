"""Sequential bounded sensitivity cases for the horizontal-frame diagnostic."""
import argparse
import hashlib
import json
from pathlib import Path

from fea import horizontal_panel_frame as frame

CASES = (
    ('c10-k1000', {}),
    ('c10-k100', {'stiffness':100.}),
    ('c10-k10000', {'stiffness':10000.}),
    ('c10-300lb', {'pounds':300.}),
    ('f10-k1000', {'hold':'F10'}),
    ('c6-k1000', {'hold':'C6'}),
    ('c7-k1000', {'hold':'C7'}),
    ('frame-only-c10', {'mode':'frame_only'}),
    ('panel-credit-c10', {'mode':'panel_credit'}),
    ('c10-refined', {'frame_size':75.,'panel_size':50.}),
)
DEFAULTS = {'mode':'coupled','hold':'C10','pounds':250.,'load_kind':'full',
            'stiffness':1000.,'frame_size':100.,'panel_size':80.}


def common_loads(first, second):
    """Check actual discrete loads and locations, without assuming equal meshes."""
    def signature(record):
        nodes={int(n):xyz for n,xyz in record['nodes'].items()}
        return sorted((tuple(nodes[int(n)]),tuple(force)) for n,force in record['loads'].items())
    return signature(first)==signature(second)


def summary(root):
    rows=[];reports={};inputs={}
    for name,_ in CASES:
        path=root/name/'report.json'
        if not path.exists():continue
        report=json.loads(path.read_text());reports[name]=report
        inputs[name]=json.loads((path.parent/report['final_cycle_directory']/'input.json').read_text())
        rows.append({'case':name,'checks_passed':report['contact_diagnostic_checks_passed'],
            'panel_displacement_mm':report['maximum_panel_displacement_mm'],
            'timber_displacement_mm':report['maximum_timber_displacement_mm'],
            'load_work_nmm':report['load_work_nmm'],'cycles':len(report['contact_cycles']),
            'maximum_connector_force_n':max(r['force_magnitude_n'] for r in report['connector_forces'].values()),
            'report_sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    result={'cases':rows,'qualified_for_design':False,'full_board_envelope_established':False}
    if all(name in reports for name in ('frame-only-c10','panel-credit-c10')):
        a,b=reports['frame-only-c10'],reports['panel-credit-c10']
        same=common_loads(inputs['frame-only-c10'],inputs['panel-credit-c10'])
        accepted=same and a['contact_diagnostic_checks_passed'] and b['contact_diagnostic_checks_passed']
        result['common_load_panel_credit']={'identical_discrete_loads':same,'diagnostic_comparison_checks_passed':accepted,
            'work_ratio':b['load_work_nmm']/a['load_work_nmm'] if accepted else None,
            'timber_displacement_ratio':b['maximum_timber_displacement_mm']/a['maximum_timber_displacement_mm'] if accepted else None,
            'limits':'Passive stiffness surrogate under identical framing loads; not physical hold-force sharing or strength qualification.'}
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=False)
    source=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    for name,override in CASES:
        print(name,flush=True)
        frame.run_current(args.output/name,**(DEFAULTS|override))
        result=summary(args.output)
        result['batch_source_sha256']=source
        (args.output/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    if source!=hashlib.sha256(Path(__file__).read_bytes()).hexdigest():
        raise ValueError('Batch source changed during execution')


if __name__=='__main__':main()
