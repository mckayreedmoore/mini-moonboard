# Knee bridge static replay

**Parent calculation complete: all twelve body/case static constructions satisfy their declared references.**
[`knee-bridge-joint-replay.py`](knee-bridge-joint-replay.py) exposes `build(output)`.
The parent ran saved-action and section arithmetic once, with no software tests,
coupons, review loop, frame/native solve or CAD rebuild. Use a fresh immediate
child of `rawlocal/knee-bridge-joint-replay/`.

Executed producer SHA256:
`5f0fae2433ee062144095a06853f61bfa5b4d9ba4ef9560588ce6d3e84dade85`.

From the repository root:

```sh
.venv/bin/python -B docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/knee-bridge-joint-replay.py --output docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/knee-bridge-joint-replay/attempt01
```

## Frozen inputs and arithmetic

- Fresh member extraction `member-screen-attempt02/knee-bridge-gravity01/`:
  `member-results.json` SHA256
  `5178d1a246aa04044429c1c2bc81709214ae9abd713313d07a949a2848de3dd0`;
  `action-section-arrays.npz`
  `3be032470253e872690637b09566076256374071adfe7d057ed4d329debef596`.
  Its 134 source pins, input/output bindings, six nominal force keys, row
  ownership, points and full force/free-couple actions are authenticated.
- Gravity assessment `ce69ba58e3c6265d31ab0dfdec1ffac4c019b93fc1106c8f9677ed9b5b2c3f95`;
  fresh comparison `c3a8ff024fb494032d947aedfd6f00cda8698587b8751b2cec66e4b3af243729`;
  fresh response `62bd4116cfb577a0846f4de0d43fbeec6bb704bac7feee530ee673ded1820f90`.
  Recorded mass is 225.19791414318078 kg; deadfactor is 1.1110134616260479.
- The frozen remaining-block source is replayed first for both spines, all six
  cases and every original grain/v cut and signed limit. Full mechanical
  actions are reconstructed with the original `-D` extraction, row ownership,
  physical node-mean datum and recorded application point. Free couples remain
  explicit; no division by historical force is used.
- Fresh arrays supply mechanical actions directly. Only mapped gravity is
  replaced: existing `longitudinal-bore-geometry.volume_first` integrates the
  proposal's six-bore timber at the new deadfactor; original allocated hardware
  forces and free couples scale by new/old deadfactor; 20 positive new hardware
  components act at the assessment's geometric centers. The four negative
  cylinder-removal point masses are excluded because the wood integral already
  removes those volumes. Whole gravity must recover fresh mapped loads and W
  within 1e-6 N/Nmm; whole-body closure retains 0.1 N/2 Nmm gates about the
  physical node mean.
- The fresh member geometry remains an original four-bore descriptor. Both
  spines are explicitly overridden with the frozen reinforcement geometry and
  integration STEP hashes: left
  `534ec2db81bbedfddba6cdf92c8703112231e970eff9b10e6a11fd11ce134645`,
  right `847e644efdb36156a74dee1641e52a18cf17d301f03f59d2fa0bb68cd7d2b273`.
  Canonical bridge IDs join by body/local center, global center, direction and
  both seats; fitter aliases remain in exports.
- Normal-v and grain cuts retain original events and add bore centers,
  tangencies, hardware centers and interval midpoints, with before/after limits.
  Hardware centers outside the timber have explicit event records; wood
  pressure is evaluated only inside the timber. One two-variable LP per
  body/case determines constant bolt tensions; only its prescribed 1.25 margin
  pressure construction is evaluated. The original Fc-perpendicular and axial
  steel references, both shears, torque and finite regional grain-sharing
  hypotheses remain explicit. Actual six-bore net grain sections use the
  existing section/nominal helpers. This is a finite census, not a continuous
  maximum proof.
  Inward forces at the canonical wood seats must recover the constructed wood
  allocation; each equal axial pair has zero whole-body and grain-cut wrench.

## Outputs and limits

The child contains `checks.json`, `receipt.json`, source hashes before/after,
producer snapshot, original replay proof, physical gravity accounting, fresh
mechanical actions, compressed normal/grain cuts, hardware event records and
24 internal allocations/48 ends. Records retain constant T, finite pressure,
stack reference comparisons and grain indices. Failed source/replay/closure
gates or named reference screens produce `stop.json`; the command exits 2.
Partial results never report completion. Sources are immutable inputs.

Loads remain 250 lb × 2, 300 N horizontal and the preserved 100 mm lever, with
the proportional 25 kg equipment convention. The consumed frame retains its
declared FILLED-BORE gross elastic approximation; this replay supplies no actual
new-hole stiffness qualification. Static allocation, local elastic
compatibility, hardware qualification, proposal adoption and physical release
remain separate. No historical force, elementary member screen or global
compatibility acceptance is transferred. Parent owns the other 42 timber
members and all executions.

## Completed parent result

`rawlocal/knee-bridge-joint-replay/attempt01/` completes **2,352 normal cuts,
5,124 grain cuts, 24 internal allocations / 48 ends and 480 hardware event
records**. The parent authenticated **159 source pins and twelve receipt
artifacts**. Fresh point-action errors are below 4e-12 N/Nmm, physical gravity
versus frame W below 5e-12 N/Nmm, and whole-body residuals below 3e-9 N/Nmm.
All original replay vectors recover before the changed-geometry calculation.

| Comparison | Fresh peak | Declared reference index |
| --- | ---: | ---: |
| Constant internal bolt tension | 1038.983907 N | 0.079838 bolt / 0.061209 nut |
| Mean washer-to-wood pressure | 2.295966 MPa | 0.532803 |
| Constructed normal wood pressure | 2.652628 MPa | 0.615570 |
| Grain tension / compression / bending | Separate signed states | 0.134417 / 0.077064 / 0.090194 |
| Regional grain shear/torsion | Same-state signed wrench | 0.416327 |

The peak tie is left/A12-forward, `proposed_v_bridge_2`; it already includes
the single 1.25 construction margin. All 24 fresh ties are below the preserved
**1060.656605 N concentric M=0 washer envelope**. Its fixed linear-elastic plate,
zero-gap/no-preload contact model permits positive scaling with maximum factor
**0.979566715**; the saved stress index **0.697914** remains a conservative
bound. No new washer solve or actual hardware qualification follows.

| Artifact under the completed child | SHA-256 |
| --- | --- |
| `checks.json` | `71980f983dd3466d02eb6c5f838186de4b77dc2ebe04653f66cf3f3598fbe891` |
| `receipt.json` | `10503afef20c8fc69c0f5b4877f8deb2794646c258b05ca63616611443c6c22b` |

These are finite static witnesses on modified timber, including its physical
weight and added hardware. They do not establish elastic compatibility, actual
changed-hole stiffness, delivered hardware resistance or complete-joint release.
All historical source files and results remain preserved.
