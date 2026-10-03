# Fresh references for the 42 unchanged timber bodies

**Parent calculation complete for all 42 bodies and six cases.**
[The producer](knee-bridge-members.py) exposes `build(output)` and an equivalent
`--output` command. Importing it reads no sources and performs no arithmetic.
The parent ran saved-action arithmetic once, with no native/CAD/frame work,
coupons, software tests or review loop. Returned corner sources are unchanged.

The screen contains exactly **20 frame members and 22 unchanged blocks**, across
the six original nominal cases. `knee_outer_left_spine` and
`knee_outer_right_spine` remain Fermat's separate modified six-bore scope.
Plywood is outside this timber screen. The original 44 timber identifiers remain
the receiver inventory for existing conditional brace candidates; screening a
receiver's strength is not inferred from its presence in that inventory.

| Bound input | SHA-256 |
| --- | --- |
| `knee-bridge-members.py` | `bc0704d2c4f7cb6dc472a139b382e514ab69f0a8de02f05a19a3266de6addb0b` |
| `../member-screen-attempt02/knee-bridge-gravity01/member-results.json` | `5178d1a246aa04044429c1c2bc81709214ae9abd713313d07a949a2848de3dd0` |
| Same directory: `action-section-arrays.npz` | `3be032470253e872690637b09566076256374071adfe7d057ed4d329debef596` |
| Same directory: `geometry.json` | `c61139087fac34e8094f2336f15dd6de5c0112d26d37b9535526f47332f453af` |
| Same directory: `inputs.json` | `34219c91e8b23588f76f4e2e2b6c564b25e1b979ccd4106dd0002c9f03cc0457` |
| `rawlocal/knee-bridge-gravity/attempt01/operator-assessment.json` | `ce69ba58e3c6265d31ab0dfdec1ffac4c019b93fc1106c8f9677ed9b5b2c3f95` |
| `rawlocal/knee-bridge-frame/attempt02/response/comparison.json` | `c3a8ff024fb494032d947aedfd6f00cda8698587b8751b2cec66e4b3af243729` |
| Same response directory: `response.npz` | `62bd4116cfb577a0846f4de0d43fbeec6bb704bac7feee530ee673ded1820f90` |
| Independent `FRAME_MAP` classifier | `f867b4926ed23c9f356005c134778e138c8b1230547f0b69be7c3f9bc2a42409` |
| `../member_stability.py` | `eb70dbe72c1ed3b9518739915193083fd6a07ebd064ba17d0c07f299f6786b72` |
| `member-duration.py` | `4407e780ade7a5f4f08eb586b6aea15130a6dd81ef747f535562a812f4a10c6d` |

`FRAME_MAP` is authenticated separately through `CLASSIFIER_PINS`. It supplies
the 20-frame/24-block identifier partition only. The producer neither inserts
its hash into the saved member report nor requires that report to claim it was
consumed. Fresh material axes come from the authenticated gravity model, and
strength references come from the existing material packet. No original helper
or pin is edited. The output keeps `source_member_report_closure` unchanged and
records the classifier under `classifier_source_sha256`.

The fresh member report, its inputs and arrays must bind the same completed
gravity operators and nominal frame response. Mass remains
**225.19791414318078 kg** and dead factor **1.1110134616260479**. The geometry
packet is byte-identical to the frozen four-screw geometry. Each of the
**42 × 6 = 252** body cases checks the complete incident-row inventory,
physical points/ownership and full force/free-couple wrench against new raw
forces and D. Each nodal action is checked against fresh F; its body resultant
is checked against fresh W. Whole-body closure retains **0.1 N / 2 N·mm**;
row and signed-cut reconstruction retains **1e-7 N / 1e-5 N·mm** checks, with
**1e-6** opposite-cut and F/W component checks.

The producer reuses `references`, `brace_candidates`, `stability_kernel`,
`normal_check`, `shear_check`, `saved_actions`, `wrench`, `basis` and
`cut_vectors`. It calls no historical `run`, `main`, `build`, coupon or test
entry point. Both end-only and existing weak timber restraint kernels keep
their original span and receiver assumptions. No effective-length search,
tuning or additional restraint variant is introduced.

Every saved before/after cut retains its signed `[N, Vu, Vv, T, Mu, Mv]` vector
and original section status. Intact rectangles also retain their centroid offset
and shifted signed vector. Normal results preserve the full domain, Euler,
null-interaction and exceedance flags. Unsupported local sections keep null
references in both duration scenarios. Aligned orthotropy, the nonaligned
equal-shear-modulus approximation and the existing fixed-action R/T diagnostic
remain explicit. Numeric peaks are not filtered to hide an unqualified domain;
nulls and exceptions have separate counts.

`cd1` and `cd1_25` use the same fresh actions. C_D=1.25 scales only
Fb/Ft/Fc/Fv; Emin, Fc perpendicular, Euler references, geometry and elastic
orientation stay unchanged. Shear uses the original C_D=1 pure helper and the
existing fixed-action ratio division by 1.25, because that helper binds its
coefficient-5 diagnostic to the base Fv. The declared **at most seven cumulative
full-peak days** hypothesis remains conditional and unobserved. The separate
permanent-load C_D=0.9 comparison remains pending. No duration adoption or
complete member/joint acceptance is claimed.

From the repository root, the parent runs one serialized calculation into a
fresh immediate child:

```sh
member_packet=docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 \
  .venv/bin/python "$member_packet/knee-bridge-members.py" \
  --output "$member_packet/rawlocal/knee-bridge-members/attempt01"
```

The returned result and `checks.json` expose `members[]` with both references,
both stability kernels, orthotropy, brace candidates, peaks and exception counts.
`same-cut-states.jsonl` stores every cut with `scenarios.cd1` and
`scenarios.cd1_25`, each containing full `normal` and `shear` records or explicit
nulls. `body-balances.json` stores the 252 body-case receipts. The ignored child
also contains a producer snapshot and `receipt.json` with source/classifier
pins and output hashes, checked before and after the calculation and writes.
An invalid source/action/geometry join raises `STOP`; conditional exceedances
are retained as results.

`top_rail_point_action_diagnostic` retains the fresh `base_rail_top` peaks and
exceptions for both scenarios. Actual pressure placement is separately refreshed in
[knee-bridge-top-rail.md](knee-bridge-top-rail.md). Physical and fabrication release flags remain
false. This producer and its frozen input packets stay active for that parent
run and consumption; no history or raw run was archived or pruned.

## Completed finite result

`rawlocal/knee-bridge-members/attempt01/` completes **252 whole-body balances
and 53,784 signed traces**, with **33,912 bore-free references** and 19,872
unsupported local-section traces kept null. The parent authenticated **150
source pins, one independent classifier and five receipt artifacts**.

At C_D=1.25, existing-timber-restraint normal, face-shear and sufficient
component-bound peaks are **0.518822 / 0.817219 / 0.951344**. End-only domain
exceptions remain recorded; the timber-restraint assumption is not a brace
stiffness proof. The coefficient-5 alternative is a non-adopted diagnostic,
with peak 1.054429. Original C_D=1 face/component excesses remain visible.
The separate physical top-rail comparison handles its opening sections.

| Artifact under the completed child | SHA-256 |
| --- | --- |
| `checks.json` | `0d623eb62605ddac9aa5111e2469a1c63f4857e356fe607741fc425d5ea59e65` |
| `receipt.json` | `fa4d5f5568d53c0e4e62a74d31a814738b39a78951a4c27ae6e4c141ef5be794` |

The original pre-calculation classifier-binding STOP remains preserved in
`../member-stability-attempt01/knee-bridge-gravity01/`. This producer resolves
that provenance error without editing the old member helper or inventing
consumed inputs. Modified spines and plywood remain outside this screen.
