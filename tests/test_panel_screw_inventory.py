"""A reduction hypothesis preserves originals and tests a defined joint pattern."""
import pytest

from fea.panel_screw_inventory import reduced_group


def test_reduction_retains_originals_and_only_selects_existing_infill():
    rows=[{'connection':str(i),'grain_station_mm':float(i),'provenance':'original' if i in (0,400,800) else 'infill'}
          for i in range(0,801,100)]
    keep=reduced_group(rows,300.)
    assert keep=={'0','300','400','700','800'}
    assert {'0','400','800'}<=keep
    with pytest.raises(ValueError,match='cannot meet'):
        reduced_group([rows[0],rows[-1]],300.)


def force_fixture(root):
    import json

    from fea.panel_screw_inventory import COUPLED_CASES, digest
    summary=[]
    for case in sorted(COUPLED_CASES):
        directory=root/case;job=directory/'cycle-00';job.mkdir(parents=True)
        sources={}
        for name in ('led-wiring-reference.json','ml24z-reference.json','panel-insert-reference.json','ml23z-reference.json'):
            path=directory/'source_snapshots/docs'/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text('{}')
            sources['docs/'+name]=digest(path)
        artifacts={}
        for name in ('input.json','frame.inp','frame.dat','frame.log'):
            path=job/name;path.write_text('original');artifacts[name]=digest(path)
        native={'artifact_sha256':artifacts,'connector_forces':{}}
        (job/'report.json').write_text(json.dumps(native));sha=digest(job/'report.json')
        report={'contact_diagnostic_checks_passed':True,'source_sha256':sources,'final_cycle_directory':'cycle-00',
                'contact_cycles':[{'directory':'cycle-00','report_sha256':sha}],
                'artifact_sha256':{'cycle-00/'+n:v for n,v in artifacts.items()}|{'cycle-00/report.json':sha},'connector_forces':{}}
        (directory/'report.json').write_text(json.dumps(report))
        summary.append({'case':case,'report_sha256':digest(directory/'report.json')})
    summary.extend({'case':name} for name in ('frame-only-c10','panel-credit-c10'))
    (root/'summary.json').write_text(json.dumps({'cases':summary}))


def test_force_authentication_rejects_native_and_source_mutations(tmp_path):
    from fea.panel_screw_inventory import load_force_reports
    force_fixture(tmp_path)
    reports,_=load_force_reports(tmp_path)
    assert len(reports)==8
    path=tmp_path/'c10-k1000/cycle-00/frame.dat';path.write_text('mutated')
    with pytest.raises(ValueError,match='native artifact hash'):
        load_force_reports(tmp_path)
    path.write_text('original')
    (tmp_path/'c10-k1000/source_snapshots/docs/led-wiring-reference.json').write_text('changed')
    with pytest.raises(ValueError,match='source snapshot hash'):
        load_force_reports(tmp_path)


def test_force_authentication_rejects_report_mutation_and_missing_cases(tmp_path):
    import json

    from fea.panel_screw_inventory import load_force_reports
    force_fixture(tmp_path)
    path=tmp_path/'c10-k1000/report.json';path.write_text(path.read_text()+' ')
    with pytest.raises(ValueError,match='report hash'):
        load_force_reports(tmp_path)
    path=tmp_path/'summary.json';data=json.loads(path.read_text());data['cases'].pop();path.write_text(json.dumps(data))
    with pytest.raises(ValueError,match='case inventory'):
        load_force_reports(tmp_path)
