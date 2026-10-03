# Saved panel/backing contact-gap recovery

Completed October 2, 2026, in the parent's corrected attempt02. **The saved
displacements reproduce all original contact coordinates and contain positive
closure at additional half-spacing points.** This demonstrates an unsampled
response of the frozen contact solution, not a revised screw force or physical
panel failure. The first stopped attempt remains preserved.

This bounded check recovers displacement for `main_lower_left` and
`base_rail_bottom_left` in the saved A1-rear nominal-clearance states of the
12- and 20-screw strong-X frame packets. It checks whether the existing
patch59 contact samples omit positive closure between their centroids.
It does not allocate new forces or change a contact, screw or material law.

## Frozen inputs

All paths below are relative to this folder except the native directory.
The producer verifies both assessment receipts, their generated operators,
row identities, models and inherited source pins before recovery.

| Packet | Comparison SHA256 | Response SHA256 |
| --- | --- | --- |
| `panel-width-frame-250-attempt05-conic` | `5a49b2076e0e32e5fbae90b1da41be6b77973da9057aee860acebaee9cef05f0` | `ff54c8f662bce93e03b46e47b088408c82471c5956b824e3320afb32b79919ef` |
| `count20-width-grain-frame-attempt01` | `0a8bcf1ac6679d970d72e11e652d31e3406607699230bcf9915bb009e34e9b88` | `8271a9e6c3ff15440703f78b704e6f601a545b538611c09009afdeb77393eb7c` |

Native matrices and labels come from
`../../mvp-acceleration-2026-09-28/current-frame-pure-solid-matrix-export-native-attempt01/`.
The pinned deck supplies the existing panel-layer engineering constants.
The unchanged physical source carrier supplies element ownership and
contact-cell identities. The source contact geometry supplies patch59's
plane and circular exclusions. No scene or mesh is regenerated.

## Recovery and interpretation

For each body, recover elastic displacement under the prescribed saved
nodal load `Fwork - B.T @ f`, then add its saved representative rigid pose.
The producer retains the existing rigid basis, C3D20 stiffness kernel,
bordered KKT factor and elastic-quotient residual checks. It checks the raw
body wrench before projecting the elastic right-hand side. Main-panel K
is explicitly reassembled with the saved strong-X material swap; its
strong-T reconstruction must first match the native K within 1e-6 relative
maximum-entry difference. Bottom-rail K remains the saved native timber K.

Patch59 has 22 original centroids: eleven longitudinal stations in each
of two transverse bands. Additional points are the longitudinal midpoints,
transverse midpoints and four-centroid averages. There are 63 proposed
points before excluding points inside source circular holes. C3D20 shape
interpolation recovers each body's displacement at each retained point.

Positive closure is penetration in the source contact-normal convention;
negative closure is opening. Before interpreting new points, all 22
original values must reproduce `q = D @ a + e - H @ f` within 1e-6 mm.
Existing penalty compression is included in this closure. Positive closure
at a new point identifies an unsampled response of this frozen solution;
it does not supply a corrected pressure, force allocation or failure load.

The calculation uses **representative saved rigid coordinates only**.
Bounded seating and nonunique poses remain explicit limits. These samples
are not a gap envelope over those poses or a bound on the continuous
maximum between points. Material fit, screw stiffness, contact penalties,
filled-bore mesh and circular contact-face abstractions remain unchanged.
No hardware deficiency, physical indentation capacity or panel acceptance
can be inferred solely from the recovered gaps.

## Parent execution handoff

Producer [contact-gap-recovery.py](contact-gap-recovery.py), SHA256
`37d8b7a1f6789fe993f0036ba7e390c5f1a55262b5736c9bfc4e484dc04ea93b`.
API: `build(Path(fresh_output_child))`. The CLI also acquires the existing
shared mechanics lock and requires an idle run ledger. Parent owns execution.

```sh
.venv/bin/python docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/contact-gap-recovery.py --output docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/contact-gap-recovery/attempt02
```

The fresh ignored child preserves `inputs.json`, the byte-exact producer
snapshot, nodal `displacement.npz` and `result.json`. Successful output
records the original-q reproduction error, every retained sample, maximum
original and half-spacing closures, source-hole exclusions and KKT/raw
wrench residuals. Source hashes are rechecked before final output. A stop
is retained rather than bypassing the original-q or source-identity checks.

Parent reported attempt01 recovered both bodies in both states, then stopped
with `KeyError: 'source_patch_index'`: the complete contact-ownership list
also contains records without that source-face field. Attempt01's inputs
and producer snapshot remain preserved. The sole correction filters entries
with `r.get("source_patch_index") == 59`; unindexed entries are outside this
source-patch scope. The expected 22-cell check remains in force. Attempt01
produced no final displacement or contact-sample result.

## Completed recovery

The parent completed `rawlocal/contact-gap-recovery/attempt02/` with 138
source pins matching and the displacement hash verified. Both bodies were
recovered for both states. Strong-T panel K reconstruction differed from
the frozen native K by only 4.21209e-12 relative maximum-entry difference;
the recovery then used strong-X K. Maximum elastic KKT upper-force relative
residual was 1.76831e-12. Raw body-wrench residuals were at numerical noise
levels before elastic projection. No sample fell inside a source hole.

| A1-rear nominal state | Twelve screws | Twenty screws |
| --- | ---: | ---: |
| Original-q maximum reproduction error, mm | 1.41842e-10 | 1.37420e-10 |
| Retained samples: original + additional | 22 + 41 | 22 + 41 |
| Largest original-cell closure, mm | 0.00265649 | 0.00825367 |
| Largest additional-point closure, mm | 0.04459313 | 0.01085113 |
| Additional points with closure above 1e-6 mm | 3 | 2 |

All additional positive witnesses are longitudinal half-spacing points.
The largest twelve-screw witness is
`[-751.469048,49.447754,385.384132]` mm. The largest twenty-screw witness
is `[-657.004545,49.475624,385.417346]` mm. In the existing board-slope
coordinate T these are approximately 327.005777 and 327.049134 mm, roughly
9.568 and 9.525 mm below the bottom-rail screw row.

Their X distances from A1 at -1019.2 mm are **267.731 and 362.195 mm**.
Their X distances from the added peak screw at -1017.6125 mm are
**266.143 and 360.608 mm**. The twelve-screw witness is 83.606 mm in X
from that state's original peak screw at -835.075 mm. Thus the largest
unsampled closures are not located beside the added 2181 N screw or A1.

The longitudinal midpoints nearest the added screw lie at X=-1035.640909 mm,
18.028 mm from it and 16.441 mm from A1. Both transverse-band midpoints
remain open: **2.233/2.769 mm** in the twelve-screw state and
**0.651/0.730 mm** in the twenty-screw state. The twenty-screw original
maximum closure is still `contact_59_20`, at X=-1082.970455 mm, rather than
the new largest half-spacing witness. These locations prevent attributing
the concentrated screw demand solely to the largest missed closure.

The finite result identifies contact discretization sensitivity worth
examining with an area-preserving patch59 refinement. It does not establish
the direction or magnitude of any resulting screw-force change. Existing
penalty compression and the sampled rather than continuous contact law
remain explicit; no numerical closure is treated as a physical bearing
capacity. The representative-pose and bounded-seating limits above remain.

| Completed output | SHA256 |
| --- | --- |
| `attempt02/inputs.json` | `a6b3bc90f716ae20dd88235dec6d0c09527337981f782400c2376d182b5766e9` |
| `attempt02/producer.py.snapshot` | `37d8b7a1f6789fe993f0036ba7e390c5f1a55262b5736c9bfc4e484dc04ea93b` |
| `attempt02/displacement.npz` | `a121c2fcb47c638a7c5e02d6dc5083e41d56ac5249875d9572b8b7f0ea9433ae` |
| `attempt02/result.json` | `99a5b1e9a3cd534260728e5b5fd607e5c8d1bbaa9f0b8ee4916100dc5b0a3345` |

Parent executed recovery; the worker reconciled the completed saved results.
No native/frame/CAD run, software tests, staging or commit was performed by
this worker. No source geometry, force allocation or acceptance was changed.
