# Upper bolts' conditional eccentric washer-seat geometry

Checked October 1, 2026. Parent implemented and ran
[check_support.py](check_support.py), SHA-256
`b9dd40be82d309da0ab1c61f4a277cc71e5bbbbc11ffc444bbfedee3e8a9fe57`.
All **32 upper candidate bolts / 64 outer seats on 15 finished members**
meet the declared swept-geometry gates. This extends the
[upper owner's nominal-seat packet](../upper-block-strength-2026-10-01/README.md)
without changing its evidence, reviewed model or numerical resistance inputs.
It is a conditional geometry screen, not a resistance or joint pass.

## Source binding and method

The implementation imports the authenticated
[remaining-seat helper](../remaining-candidate-washer-seats-2026-10-01/check_support.py)
(`a3cedb8e6fddf9d4080afd82cf12cf3e5a39658868baa478ad1f14eee7d07967`)
and its frozen primary and eccentric methods. Its source partition checks
all 92 candidate axes: six primary, 32 upper and 54 remaining, with no
overlap or omissions. The two existing sixteen-axis upper source hashes,
candidate/revision, model/hardware/bundle pins and every used finished STEP
binding are checked before their geometry is used. One valid solid, source
face count and source volume must agree for each of the 15 imported members.
Seats come from the first and last actual receiver intervals; no middle
washer is invented for a continuous bolt.

Each upper seat has a modeled bore radius of 3.75 mm and a conditional
nominal smooth body diameter of 6.35 mm. Plain Type A Wide catalog bounds are
OD 18.4658–19.0246 mm and ID 7.7978–8.3058 mm; the existing CAD ring is also
included. The combined geometric offset is bolt/bore radial play plus
washer/body radial play. Its largest value is 1.5529 mm. The enclosing outer
radius is 11.0652 mm.

At each source seat, the Boolean test compares the finished solid with the
entire annular swept region from bore radius to enclosing outer radius,
at 0.01, 0.05 and 0.1 mm inward depths. That region encloses the part of every
declared translated washer footprint outside its own receiver bore in every
direction. Its containment supports the hole-only area formula; it does
**not** mean the eccentric washer has no unsupported area over the bore.
An outward disk at the same enclosing radius checks obstruction only over
the same three near-face depths. Actual washer thickness, tilt, flatness,
seat-position tolerance and other hardware envelopes are not bounded here.

## Recorded result

| Check | Observed result |
| --- | --- |
| Seat coverage | 64 unique `(axis, role)` pairs; no geometry exceptions |
| Source seat-plane offset | Maximum `1.0034e-9 mm` |
| Swept inward support fraction | Minimum `0.9999999933494677`; required at least `1 − 1e-7` |
| Outward near-face overlap fraction | Zero at all three depths |
| Direct STEP/area-oracle comparisons | 768 comparisons: four directions × three depths × 64 seats |
| Maximum direct area discrepancy | `3.2869e-6 mm²`, below `2e-5 mm²` |
| CAD ring area at combined-offset endpoint | `214.8026699 mm²` |
| Smallest plain catalog-ring area at combined-offset endpoint | `206.0131521 mm²` (minimum OD / maximum ID) |

The four direction samples independently check the circular-hole area
calculation against the production STEP Boolean. They are not the continuum
proof; that comes from the swept-region containment. Formula results are
marked inapplicable if containment fails. A failed support or clearance gate
is reported as a geometry exception with nonzero exit status. Area-oracle
mismatches are also recorded against their exact seat and samples and produce
nonzero exit status; source discrepancies stop the check before using them.

Run from the repository root:

```sh
.venv/bin/python docs/wood-joints-mvp/hypotheses/upper-washer-eccentric-support-2026-10-01/check_support.py --check > /tmp/mini-moonboard-upper-eccentric.json
```

Parent's raw local report is
`/tmp/mini-moonboard-upper-eccentric-parent-2026-10-01.json`, SHA-256
`62385f3e947f94fd5682f2b15a76d401bcceb5b6cff6a8fd18e7a4946dae1e0e`.
Publication contains code and summaries only. The code passed Ruff; the
known bored-seat fixture agrees within `4.84e-13 mm²` and rejects a corrupted
area, an empty sample list and a nonfinite error. Run it with `--oracle-fixture`.
The independent review is recorded separately. No native or heavy mechanics
calculation was run.

## Integrated boundary

Together with the primary and remaining-seat packets, every one of the
**184 candidate outer seats** now has a declared conditional eccentric
geometry screen. Of those, 183 meet their declared geometry gates;
`center_principal_right_2`'s nut seat remains the separately diagnosed
[partial-support exception](../remaining-candidate-washer-seats-2026-10-01/cut-diagnosis-review.md).
The twelve retained frame-bolt arrangements are outside this 92-axis set.

The 6.35 mm scenario is not a sourced minimum delivered shank; bore and seat
tolerances, bolt/washer tilt and physical seating remain open. Hole-only area
does not establish wood pressure, load-footprint support, washer-metal stress,
bolt/nut resistance, coupled prying or six-case joint acceptance. No actual
hardware, wood, holes or floor were inspected. No physical work, candidate
selection or climbing release follows from this result.
