"""Independent exact row comparison to fresh audited forces, including floor sums."""
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path

HERE=Path(__file__).resolve().parent
BASE=HERE.parent

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    response_path=BASE/'current-k12-rear-spr489-direct-native-attempt01/response.json'
    export_path=BASE/'current-corner-k12-rear-case-bound-export-attempt01/corner-demand-report.json'
    response=json.loads(response_path.read_text());report=json.loads(export_path.read_text())
    checks=[]
    for out,source in zip(report['increments'],response['increments'],strict=True):
        assert out['load_factor']==source['load_factor'] and out['time']==source['time']
        native=source['physical_connection_forces']
        floors=defaultdict(list)
        for row in source['exact_floor_tangent_reactions']+source['inactive_floor_tangent_zero_actions']:
            floors[row['source_connection_name']].append(row)
        direct_count=floor_count=0
        for row in out['all_corner_interfaces']:
            name=row['source_connection_name']
            if name in native:
                r=native[name]
                for field in ['first','second','force_on_first_xyz_n','force_on_second_xyz_n','force_rounding_radius_xyz_n']:
                    assert row[field]==r[field],(name,field)
                assert row['first_point_global_xyz_mm']==r.get('first_point',r['point'])
                assert row['second_point_global_xyz_mm']==r.get('second_point',r['point'])
                direct_count+=1
            else:
                channels=floors[name];assert len(channels)==2,name
                for field in ['force_on_first_xyz_n','force_on_second_xyz_n','force_rounding_radius_xyz_n']:
                    expected=[math.fsum(r[field][j] for r in channels) for j in range(3)]
                    assert row[field]==expected,(name,field)
                assert all(row['first']==r['first'] and row['second']==r['second'] and row['first_point_global_xyz_mm']==r['point'] for r in channels)
                floor_count+=1
        assert direct_count==334 and floor_count==4
        checks.append({'load_factor':source['load_factor'],'exact_native_owner_point_force_radius_rows':direct_count,'independently_summed_floor_vectors_and_radii':floor_count})
    assert len(checks)==7
    value={'status':'PASS_PARENT_EXACT_K12_CORNER_EXPORT_ROW_COMPARISON',
           'source_response_sha256':sha(response_path),'source_export_sha256':sha(export_path),
           'source_script_sha256':sha(Path(__file__)),'increments':checks,
           'total_interface_rows_checked':2366,'mechanical_acceptance':False}
    (HERE/'corner-export-verification.json').write_text(json.dumps(value,indent=2)+'\n')
    print(value['status'])

if __name__=='__main__':main()
