"""Parent-owned, pinned, network-disabled diagnostic executable build."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,subprocess

HERE=Path(__file__).resolve().parent
CONTEXT=HERE/'context'
BASE='sha256:31336f517557f5dd5f97d85b1e6e15947fd1c10b44edc1364dbba4c1a5ab6c38'
TAG='mini-moonboard-fea:ccx-contact-point-trace-20260927-v3'

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def now():return datetime.now(timezone.utc).isoformat()
def inspect(s):return subprocess.check_output(['docker','image','inspect',s,'--format','{{.Id}}'],text=True).strip()
def write(n,d):(HERE/n).write_text(json.dumps(d,indent=2)+'\n')

def main():
    assert not (HERE/'execution.json').exists(),'Refusing to overwrite build evidence'
    assert inspect('mini-moonboard-fea:ccx-upstream-2.23-v1')==BASE
    old=subprocess.run(['docker','image','inspect',TAG],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    assert old.returncode!=0,'Image tag already exists'
    pins={p.name:sha(p) for p in sorted(CONTEXT.iterdir()) if p.is_file()}
    assert set(pins)=={'Dockerfile','Makefile.upstream','record_build.py','source.tar.bz2','diagnostic.patch','diagnostic-lock.json','base-build-manifest.json'}
    freeze={'schema':'ccx_contact_point_trace_build_freeze/v1','created_utc':now(),'base_image':BASE,'context_sha256':pins,'build_driver_sha256':sha(Path(__file__)),'scope':'Compile only; coupon-only unvalidated trace; no current-joint eligibility'}
    write('input-freeze.json',freeze)
    cmd=['docker','build','--network=none','--progress=plain','--pull=false','--build-arg','BASE_IMAGE=mini-moonboard-fea:ccx-upstream-2.23-v1','-t',TAG,str(CONTEXT)]
    d={'schema':'ccx_contact_point_trace_build_execution/v1','started_utc':now(),'command':cmd,'freeze_sha256':sha(HERE/'input-freeze.json'),'timeout_seconds':300,'joint_acceptance':False}
    with (HERE/'build.log').open('wb') as log:
        try:
            r=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,timeout=300)
            d.update(exit_code=r.returncode,timed_out=False)
        except subprocess.TimeoutExpired:d.update(exit_code=None,timed_out=True)
    d.update(ended_utc=now(),build_log_sha256=sha(HERE/'build.log'))
    write('execution.json',d)
    assert d['exit_code']==0 and not d['timed_out'],'Build failed; retain evidence'
    image=inspect(TAG)
    manifest=subprocess.check_output(['docker','run','--rm','--network','none',image,'cat','/opt/ccx-contact-point-trace/build_manifest.json'])
    (HERE/'build-manifest.json').write_bytes(manifest);m=json.loads(manifest)
    assert m['base_image_id']==BASE and m['patch_sha256']==pins['diagnostic.patch']
    assert m['build_context_sha256']==pins
    assert inspect('mini-moonboard-fea:ccx-upstream-2.23-v1')==BASE
    assert all(sha(CONTEXT/n)==v for n,v in pins.items())
    d.update(image_tag=TAG,image_id=image,build_manifest_sha256=sha(HERE/'build-manifest.json'),binary_path=m['patched_binary_path'],binary_sha256=m['patched_binary_sha256'],context_unchanged=True,historical_binaries_preserved=m['historical_binary_sha256_before_and_after'])
    write('execution.json',d)
    print(json.dumps({k:d[k] for k in ['exit_code','image_id','binary_path','binary_sha256']}))

if __name__=='__main__':main()
