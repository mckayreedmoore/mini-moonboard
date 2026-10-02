# Twenty screws per main panel with matched grain

Completed October 2, 2026. The owner's proposed two extra screws per edge
adds eight to each main panel: **20 per main, 80 main plus 18 kicker = 98**.
The comparison retains the four authorized upper moves and the full 250 lb
dynamic load scenario. The proposal is an analysis option; the physical
66-screw inventory and authority remain current. No added screw is installed
or qualified, and complete joints/physical release remain **HOLD**.

## Decision

The matched strong-X 20-count packet completes all twelve frame states.
Upper-panel demands fall, but the largest axial force moves to an added
lower-left screw. Thus adding screws does not close the current model's
head-reference comparison. This is a sharing result under declared elastic
and contact laws, not a physical failure claim or a hardware recommendation.

The [grain comparison](panel-orientation-comparison.md) explains strong X
versus strong T. Every option below keeps the same applied loads, source
screw laws, timber, contacts and frame-bolt clearances. These are separate
nominal-clearance panel envelopes, not one simultaneous state.

| Panel | 12/main, strong X: peak T, N | 20/main, strong T: peak T, N | 20/main, strong X: peak T, N |
| --- | ---: | ---: | ---: |
| Upper left | 1280.799 | 1245.028 | 1030.400 |
| Upper right | 1174.975 | 1550.561 | 1122.014 |
| Lower left | 1213.615 | 2171.245 | 2180.721 |
| Lower right | 120.691 | 75.804 | 77.823 |
| Kicker left | 290.636 | 286.500 | 289.912 |
| Kicker right | 264.883 | 262.171 | 265.315 |

The strong-X 20-count peak is A1-rear,
`hyp20_main_lower_left_edge_gap_1` into `base_rail_bottom_left`:
**T=2180.721 N, simultaneous V=75.893 N, opening=0.810774 mm**.
Zero clearance gives T=2146.715 N on that same added axis.
The largest nominal lateral screw force is a different state: 928.145 N
at upper-right `rim_4`, K12-rear.

The favorable retailer-nominal head references in the
[head-basis worksheet](head-reference-basis.md) remain 930.222–984.128 N
under its explicit duration/plywood hypotheses. Even the upper-panel peaks
remain above them. The lower-left peak is 2.216 times the larger reference.
Neither a measured Hillman resistance nor physical breaking load is inferred
from these ASD comparisons. Lateral and combined resistance require their
own applicable basis; lower axial demand alone does not qualify an attachment.

The [existing strong-T count study](../panel-attachment/README.md#owner-requested-12-versus-20-screw-and-model-check)
retains its own force packet. Its 2171 N lower-panel result is not caused by
doubling the applied load. The new strong-X comparison preserves that same
phenomenon. A saved-force contact/wrench extraction is the next bounded check:
identify the opposing compression reactions and local lever arms before
interpreting the concentrated screw demand as a hardware deficiency. The
completed [signed contact account](panel-contact-sharing.md) now shows an
identical external wrench, a larger self-equilibrating reaction couple and
approximately 95 mm contact sampling at the bottom rail. Nearby cells are
open while a farther cell bears. It supplies no alternate force allocation
or conclusion that the actual hardware fails.

## One coherent operator per comparison

[panel_count_orientation.py](panel_count_orientation.py) reuses the frozen
four-panel C3D20 reassembly through two checked, hash-pinned substitutions:
the source directory and source model identity. It uses the **entire**
98-screw B matrix when replacing all four panels' H/e contributions,
including old-to-new cross terms. It does not attach old-grain added-row
compliance to the 66-count strong-X matrix.

All four reassembled old K matrices match their authenticated native sources
within 1.075e−11 relative maximum difference. D, W and F retain the count
source arrays; source B/rows/connection inputs are copied unchanged. Timber
and kicker contributions remain frozen. The updated compliance reciprocity
error is 9.150e−11; minimum symmetric eigenvalue is −1.169e−17 mm/N, within
the existing gates. All 121 input pins and seven output pins match.

There are **96 added scalar rows**: two lateral and one axial row per added
screw. The inherited placement screen is AABB only, not finished B-rep
backing, hole conflict, tool fit or installation evidence. Added hardware mass
is omitted; all comparisons keep the same 224.949955 kg modeled frame and
25 kg proportional accessory allowance. Neither quantity nor geometry is
adopted by the shop packet.

[count_conic_frame.py](count_conic_frame.py) changes only the frozen frame
inventory guard and pads two historical saved-force seed/comparison reads
with zeros for the added rows. It reuses the published
[initialization wrapper](conic_frame.py). This run needs no convex fallback:
all states return from the original equations and existing bounded-seating
path. All **157 frame source pins** match.

Maximum final force/moment residuals are 1.464e−11 N / 8.64e−9 N·mm;
finite-law error is 9.11e−7 N; circular law error is 3.31e−9 N. Positive-spring
motion stays below 0.810775 mm against the unchanged 10 mm domain. Zero-gap
rank is 300; nominal rank is 296/297 with bounded fixed-force seating.
Strict stability, unique force/pose and dynamic motion qualification remain
unestablished. No new native solve, geometry run or software tests occur.

## Saved-force consumer and receipts

[count_head_check.py](count_head_check.py) reuses the frozen 66-count consumer
with checked inventory substitutions and the two known operator statuses.
It preserves source/output hashes, signed force bases, same-datum motion,
every screw-law reconstruction and all panel census checks. It consumes
**3144 screw states**: 792 at twelve per main, and 1176 for each twenty-count
orientation. All 23 direct source pins match. Maximum screw-law error among
the three packets is 2.81e−8 N. No force allocation or frame solve runs in
this consumer.

The prepared projection attempt01 remains preserved. Attempt02 adds only an
inline lint exemption for executing the hash-pinned adapted source, then
recalculates with the maintained producer identity. No mechanics operation
changes between those two projections. Targeted Ruff checks pass; no review
loop is used.

Raw artifacts remain local and ignored:

| Artifact | SHA-256 |
| --- | --- |
| `panel_count_orientation.py` | `b1e16c26148f3d277b8f5bf8253d58307c7c5fd30bec3fb2b5ce0c63cf4ab6b0` |
| `count_conic_frame.py` | `acd9d6bb81c8e156a098e3aa9395854cbb576709feeabde7397293cc64492298` |
| `count_head_check.py` | `240d403c7cf4793d7c1c6d79a6c40c6e95e1c709011d47e1d918275d6b79fb91` |
| `count20-width-grain-operators-attempt02/operator-assessment.json` | `d94732bb20ede8da48a7799c014b2c9d66e16062b7c4f485ec008e494c5488a1` |
| `count20-width-grain-operators-attempt02/operators.npz` | `cc64d9d94abd2e34393183764b3f445b4085e298d5da2549c33645a27ee696ff` |
| `count20-width-grain-frame-attempt01/comparison.json` | `0a8bcf1ac6679d970d72e11e652d31e3406607699230bcf9915bb009e34e9b88` |
| `count20-width-grain-frame-attempt01/response.npz` | `8271a9e6c3ff15440703f78b704e6f601a545b538611c09009afdeb77393eb7c` |
| `rawlocal/count-head-check/attempt01/comparison.json` | `edea3f11de9c2ee75e5f6afcb05b511a3b20bcd4aa23e448ffac33bdd27d8c71` |
| `rawlocal/count-head-check/attempt01/receipt.json` | `0295c93e0924813dc0b570be5a232d6fea5ceae94267d260aa753139d6e72d62` |

Use a fresh output directory with the pinned NumPy 2.2.6 / SciPy 1.15.3 /
OSQP 1.0.4 / Clarabel 0.11.1 environment and the parent's serialized slot:

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 uv run --no-project \
  --with numpy==2.2.6 --with scipy==1.15.3 --with osqp==1.0.4 \
  --with clarabel==0.11.1 python \
  docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/count_conic_frame.py \
  --operators docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/count20-width-grain-operators-attempt02 \
  --output <new-output-directory>
```

The [current joint register](joint-register.md) remains bound to its strong-T
66-count packet. These new panel and bolt forces transfer no prior component
ratio or joint acceptance. The next finite sharing result must retain this
distinction.
