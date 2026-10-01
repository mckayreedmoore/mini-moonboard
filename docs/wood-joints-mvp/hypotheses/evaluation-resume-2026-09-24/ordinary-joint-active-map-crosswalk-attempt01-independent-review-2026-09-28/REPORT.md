# Independent review: ordinary-joint active-map crosswalk attempt01

Review date: 2026-09-28. This is a bounded, read-only source and claim audit
of the sibling `ordinary-joint-active-map-crosswalk-attempt01-2026-09-28`
packet. No subject files, geometry, queue, ledger, plan, criteria, or solver
state were changed. No solver or geometry kernel was run.

## Outcome

**Pass, with one non-blocking reproducibility note.** I found no material
source-binding, transform, arithmetic, fixture-scope, or failure-status error.
The packet's boundaries are sound: it establishes A09 input composition and
coordinate mappings only; it does not claim an accepted A09 response, joint
mechanics, capacity, criterion closure, or release.

The packet-local checksum lists pass (3/3). All 35 source pins match both the
current files and the `crosswalk.json` `source_sha256` object. The four rows
join the ordered `per_nut` input maps to the current-map axis inventory by
`axis_index`, then to the physical axis IDs, shaft bodies, nut carriers, and
dependent equation rows. The frozen case lock binds the exact A09 deck; its
bundle lock binds the base input freeze; all 14 base-freeze artifact hashes
match. All seven direct deck includes are hash-bound, with three carried
transitively by the pinned base freeze.

The recorded basis is right-handed and orthonormal. Independent arithmetic
reproduces local N `+1 mm` as global `(0, 0.7660444431, 0.6427876097) mm`,
the rail/principal controls as `+0.5/-0.5 mm` local N, and their difference as
the specified `+1 mm` local N. The four global shaft directions project to the
listed local directions. The A00 fixture's global-Y coefficient `1.2` maps to
local `(0, 0.7713451316, 0.9192533317)` per second.

The crosswalk correctly limits the passing known-answer fixture to A00 and
its optional A00 carrier under its small rotational body-force history. The
three cases each record ten accepted states. The A09 static case records exit
137 after its declared timeout, no accepted increment, empty `.dat`/`.sta`,
and an 80-byte `.frd`. The record distinguishes a failed numerical path from
physical joint failure and says the 0.575 mm nominal gap was not reached. The
proposed approximately 1.3 mm transient remains an unselected geometry target,
not a frozen history or service demand. T02/T03 mechanics and acceptance
gates remain open.

## Finding

The subject packet records `offline_replay.status=PASS...` and enumerates its
assertions, but contains no replay script or captured replay command/output.
The data are independently reproducible from the pinned inputs, as this
review demonstrates, so this is not a content blocker. For future audit
packets, include or hash-pin the replay script and record the exact command
and exit status. This makes the offline pass directly rerunnable instead of
attested only by the JSON status.

There is also a pre-run A00 `fixture-design.md` that still says the fixture
was not frozen or run. The crosswalk cites the later terminal `RESULTS.md`
and verifier records, so its qualification claim is correct. The older design
note should be understood as a pre-run artifact; label it that way in future
contextual references to avoid confusion.

## Exact reproduction commands

Run the packet checksum from its directory:

```sh
cd /home/mckay-linux/repos/mini-moonboard/docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/ordinary-joint-active-map-crosswalk-attempt01-2026-09-28
sha256sum -c SHA256SUMS
```

Run the 35 source-pin checks from the repository root:

```sh
cd /home/mckay-linux/repos/mini-moonboard
sha256sum -c docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/ordinary-joint-active-map-crosswalk-attempt01-2026-09-28/SOURCE-SHA256SUMS
```

Recheck the source-pin object, all 14 base artifacts, and the freeze-lock
digest chain:

```sh
python3 - <<'PY'
import hashlib, json
from pathlib import Path
root = Path.cwd()
packet = root / "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/ordinary-joint-active-map-crosswalk-attempt01-2026-09-28"
a09 = root / "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/ordinary-port-motion-attempt09-common-map"
pins = {}
for line in (packet / "SOURCE-SHA256SUMS").read_text().splitlines():
    digest, name = line.split("  ", 1)
    pins[name] = digest
crosswalk = json.loads((packet / "crosswalk.json").read_text())
assert len(pins) == 35 and pins == crosswalk["source_sha256"]
for name, expected in pins.items():
    assert hashlib.sha256((root / name).read_bytes()).hexdigest() == expected, name
freeze = json.loads((a09 / "input-freeze.json").read_text())
assert len(freeze["artifacts_sha256"]) == 14
for name, expected in freeze["artifacts_sha256"].items():
    assert hashlib.sha256((a09 / name).read_bytes()).hexdigest() == expected, name
case_lock = json.loads((a09 / "port-motion-n_plus-lock.json").read_text())
bundle = json.loads((a09 / "bundle-lock.json").read_text())
deck_hash = hashlib.sha256((a09 / "port_motion_n_plus.inp").read_bytes()).hexdigest()
assert deck_hash == crosswalk["scope"]["case_sha256"] == crosswalk["freeze_binding"]["case_deck_sha256_from_lock"]
assert hashlib.sha256((a09 / "bundle-lock.json").read_bytes()).hexdigest() == case_lock["external_port_bundle_lock_sha256"]
assert hashlib.sha256((a09 / "input-freeze.json").read_bytes()).hexdigest() == bundle["input_freeze_sha256"]
print("35 source pins and source_sha256 map: PASS")
print("14 base artifacts and deck -> case lock -> bundle -> base freeze: PASS")
PY
```

Recompute the translations, four axis projections, and A00 fixture drive
coefficient from the packet values:

```sh
python3 - <<'PY'
import json
from pathlib import Path
root = Path.cwd()
base = root / "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24"
crosswalk = json.loads((base / "ordinary-joint-active-map-crosswalk-attempt01-2026-09-28/crosswalk.json").read_text())
a09 = base / "ordinary-port-motion-attempt09-common-map"
ct = crosswalk["coordinate_transform"]
B, Bt = ct["B_global_from_local_rows"], ct["B_transpose_local_from_global_rows"]
def mul(A, v):
    return [sum(row[i] * v[i] for i in range(3)) for row in A]
assert all(abs(B[i][j] - Bt[j][i]) < 1e-15 for i in range(3) for j in range(3))
n_global = mul(B, [0, 0, 1])
assert max(abs(a-b) for a,b in zip(n_global, [0, .7660444431187603, .6427876096867989])) < 1e-12
for axis in crosswalk["deck_binding"]["active_maps"]:
    projected = mul(Bt, axis["shaft_axis_direction_head_to_nut_global_xyz"])
    assert max(abs(a-b) for a,b in zip(projected, axis["shaft_axis_direction_head_to_nut_local_X_T_N"])) < 1e-12
ports = json.loads((a09 / "port-motion_n_plus.json").read_text())["ports"]
rail = ports["rail"]["controlled_q_port_local_mm"]
principal = ports["principal"]["controlled_q_port_local_mm"]
assert rail[:3] == [0.0, 0.0, 0.5] and principal[:3] == [0.0, 0.0, -0.5]
assert [rail[i]-principal[i] for i in range(6)] == [0, 0, 1, 0, 0, 0]
alpha_local = [1.2*x for x in mul(Bt, [0, 1, 0])]
assert max(abs(a-b) for a,b in zip(alpha_local, [0, .7713451316241587, .9192533317425123])) < 1e-12
print("n_plus transform:", n_global)
print("rail minus principal local port:", [rail[i]-principal[i] for i in range(6)])
print("A00 global-Y coefficient in X/T/N:", alpha_local)
print("four shaft-axis projections: PASS")
PY
```

## Limits

This review verifies hashes, source relations, listed arithmetic, fixture
scope, and status wording. It does not qualify a solver method, infer accepted
runtime activation, reproduce native response, establish force transfer,
evaluate mechanical criteria, or close T02/T03. The numerical calculations
are not material or capacity checks.
