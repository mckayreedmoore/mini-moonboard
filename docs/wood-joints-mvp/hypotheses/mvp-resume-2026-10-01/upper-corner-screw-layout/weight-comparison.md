# 140 lb proportional-live comparison: partial result

The owner retained **250 lb including dynamic moves** as the intended upper
limit and reported an actual weight of **140 lb**. This comparison keeps the
66-screw strong-X packet and scales vertical/horizontal live action together
by 140/250 = 0.56 at the same assumed acceleration. Downward live force is
1245.502 N; horizontal force is 168 N. Frame gravity, the 25 kg accessory
allowance, geometry, materials and all contact/screw laws remain unchanged.
It is not the separate fixed-300 N comparison or a replacement design limit.

## Returned result and numerical stop

Two zero-clearance states return with rank 300 and the original equilibrium,
finite-law, floor and domain gates satisfied. Both axial peaks occur at
upper-left `round_panel_upper_left_edge_2` into `base_rail_top`.

| Returned case | Peak screw axial force, N | Representative opening, mm |
| --- | ---: | ---: |
| A12 rear, zero clearance | 777.501 | 0.289068 |
| A12 forward, zero clearance | 656.745 | 0.244172 |

Those two peaks are below the favorable retailer-nominal 930.222–984.128 N
head scenarios in the [reference worksheet](head-reference-basis.md), with
its explicit plywood/net-thickness/1.6-duration hypotheses. They remain above
some unadjusted generic references. Neither comparison establishes measured
Hillman resistance, all-case bounds or a climber rating.

A12-left zero clearance stops on **normal active-set cycle**. A fixed-floor
convex initializer reports `Solved`, but the original floor/contact equations
still cycle afterward. The convex guess is not an accepted state. No nominal
clearance state or complete six-case 140 lb envelope returns. This is a
numerical calculation stop, not evidence that the lighter climber causes a
physical failure. Scaling a 250 lb peak cannot fill the missing states.

The completed [250 lb grain comparison](panel-orientation-comparison.md)
remains available. Its nominal head peak of 1280.799 N still exceeds the
declared favorable head references. The [contact sharing account](panel-contact-sharing.md)
identifies specific sampled-contact and unmeasured force-slip assumptions
that need scrutiny when interpreting local concentrations. Physical release
and full-joint HOLD remain unchanged.

## Frozen calculation

[weight_conic_frame.py](weight_conic_frame.py) passes live-load scale arguments
to the preserved producer and uses the existing numerical initialization.
No mechanical equation or acceptance tolerance changes. All 143 directly
bound source pins match. Returned states have maximum force/moment residuals
3.411e−12 N / 4.981e−9 N·mm and finite-law error 3.766e−7 N.

Attempt01 remains preserved. Attempt02 adds explicit weight/horizontal
metadata to the STOP receipt; both returned force arrays are unchanged. The
unaccepted terminal iterate stays separately labeled. Raw files remain local
and ignored, and no software tests, geometry/native run or review loop occur.

| Artifact | SHA-256 |
| --- | --- |
| `weight_conic_frame.py` | `3aa6a9ee6e1bdfe6dc0809b944e4f7c399c938e562f1e4e55e61a2bb844f68ba` |
| `panel-width-frame-140-attempt02-conic/stop.json` | `4e96e8748d938a8da8f0d80d9347f62001ffe8603e91849b6b4f0fc5f4a74230` |
| `panel-width-frame-140-attempt02-conic/partial-response.npz` | `ffaae05da791b56047624d35a86fbe650fc03f083ee79827332e8f7449c5e430` |
| `panel-width-frame-140-attempt02-conic/conic-seeding.json` | `86c69091f0690b5917d45ab2f867e05ffc6a84477e5f1a35a4aa74e3a46b8cf3` |

For a fresh serialized attempt, use the pinned NumPy 2.2.6 / SciPy 1.15.3 /
OSQP 1.0.4 / Clarabel 0.11.1 environment:

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 uv run --no-project \
  --with numpy==2.2.6 --with scipy==1.15.3 --with osqp==1.0.4 \
  --with clarabel==0.11.1 python \
  docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/weight_conic_frame.py \
  --operators docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/panel-width-operators-attempt01 \
  --output <new-output-directory> --weight-lb 140
```
