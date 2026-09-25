import datetime
import hashlib
import json
import time
import traceback
from pathlib import Path

import importlib
import scripts.wood_joint_current_midpoint_clearance as midpoint_module
importlib.reload(midpoint_module)

from scripts.wood_joint_current_midpoint_clearance import (
    build_current_midpoint_clearance_report,
)

repo = Path('/home/mckay-linux/repos/mini-moonboard')
base = repo / 'docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24'
producer = repo / 'scripts/wood_joint_current_midpoint_clearance.py'
snapshot_path = base / 'geometry-snapshot.json'
assert hashlib.sha256(producer.read_bytes()).hexdigest() == '6915e1213cf425b1f459594c55c403679f3fab18915cb6d976aa2cae0adae806'
assert hashlib.sha256(snapshot_path.read_bytes()).hexdigest() == '0b92357af648604ee8ce42d2f8906e0a4e5498e9e4b835a07938b81dc151d187'
out = base / 'current-midpoint-clearance-attempt03'
out.mkdir(exist_ok=False)
(out / 'parent-wrapper.py').write_bytes(Path('/tmp/run-wj-current-midpoint-20260925-attempt03.py').read_bytes())
record = {
    'started_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'status': 'running',
    'scope': 'Read-only current CAD midpoint clearance; no rebuild or geometry edits',
    'producer_sha256': hashlib.sha256(producer.read_bytes()).hexdigest(),
    'snapshot_sha256': hashlib.sha256(snapshot_path.read_bytes()).hexdigest(),
}
(out / 'execution.json').write_text(json.dumps(record, indent=2) + '\n')
started = time.monotonic()

def midpoint_progress(message):
    with (out / 'progress.log').open('a') as handle:
        handle.write(str(message) + '\n')
    print(message, flush=True)

try:
    report = build_current_midpoint_clearance_report(
        g24_outer_2x6, json.loads(snapshot_path.read_text()), progress=midpoint_progress,
        output_directory=str(out.relative_to(repo))
    )
    (out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    record['status'] = 'completed'
    record['report_sha256'] = hashlib.sha256((out / 'report.json').read_bytes()).hexdigest()
except Exception:
    record['status'] = 'failed'
    record['error'] = traceback.format_exc()
    print(record['error'], flush=True)
finally:
    record['elapsed_seconds'] = time.monotonic() - started
    (out / 'execution.json').write_text(json.dumps(record, indent=2) + '\n')
    print('WJ_CURRENT_MIDPOINT_OUTCOME', json.dumps(record), flush=True)
