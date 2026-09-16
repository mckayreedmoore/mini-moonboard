# Compact spliced flush-top study

2026-09-14. Candidate: `compact-spliced-flush-top-development`.

All six fresh assembled load cases meet all 21 listed conditional splice
criteria. This closes the numerical comparison for the flush-top revision under
the recorded loads, material properties, catalog hardware assumptions and
no-slip support assumption. It does not close the retained ML24Z/SDS separation
and independent flange-couple connection gate. It remains engineer-unreviewed
DIY evidence, not an unconditional climber rating or a construction approval.

## Revision assessed

This candidate retains the selected compact spliced-knee arrangement: solid
4x6 legs and side rims, compact 2x6 base, four independent unnotched 2x6 knee
pieces, 20 complete outward-facing bolt stacks, the lower kicker screw row and
the 7 mm rear rim reserve. It removes the former 18 mm rear-leg-top projection.
The two half-inch upper bolts on each side move to a new 56 mm-pitch pair so the
leg top can finish flush with the side rim.

These are fresh-stock members and fresh native responses. No result is
transferred from the original `compact-spliced-knee-development` cases or its
later unloaded-tail trim approximation. The tapered floor-runner candidate is
also separate and supplies no strength acceptance here.

## Six fresh cases

Each case applies 2224.111 N downward, corresponding to twice the static weight
of the 250 lb target, plus the listed 300 N horizontal component. Load remains
100 mm in front of the face. Self-weight and the recorded 25 kg equipment
allowance remain active. Normal floor contact may open; tangential support is a
conditional no-slip assumption, with no friction coefficient or installed
anchor qualification.

Ratios at or below 1.0 meet their listed comparison. Displacements are response
outputs, not utilization ratios.

| Case | Horizontal action | Actual-angle bolt | Local parallel | Supplemental splitting | Sampled net member | Header stability | Timber displacement | Panel displacement |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| A12 left | 300 N left | 0.67036 | 0.28398 | 0.34050 | 0.41810 | 0.15745 | 6.394 mm | 14.955 mm |
| A12 rear | 300 N rearward | 0.71241 | 0.30243 | 0.36496 | 0.45478 | 0.31200 | 6.932 mm | 17.001 mm |
| A12 forward | 300 N forward | 0.59482 | 0.25196 | 0.30196 | 0.38743 | 0.12841 | 4.617 mm | 13.682 mm |
| K12 right | 300 N right | 0.66142 | 0.28001 | 0.33604 | 0.41042 | 0.16263 | 6.631 mm | 14.220 mm |
| K12 rear | 300 N rearward | 0.70371 | 0.29835 | 0.36055 | 0.44797 | 0.31367 | 7.220 mm | 16.495 mm |
| A1 rear | 300 N rearward | 0.09356 | 0.05588 | 0.04817 | 0.11612 | 0.21070 | 1.942 mm | 8.475 mm |

Each archived response passes native global and member equilibrium, multipoint
constraint, normal-contact convergence and closed-bearing gates before its
resistance checks are interpreted. Every bolt-center section has a recovery
sample. Every modeled opening is represented, all sampled member stability
checks pass, and compression-only knee overlap contact carries no tension,
friction or assumed composite action.

## Governing adopted comparisons

The A12 rearward case governs actual-angle bolt lateral resistance at 0.71241,
the local parallel check at 0.30243, supplemental EC5 splitting at 0.36496 and
the sampled net-member envelope at 0.45478. K12 rearward governs gross header
full-length stability at 0.31367. Other six-case governing values are:

| Comparison | Governing value |
| --- | ---: |
| Additional conservative group-reduction sensitivity | 0.71241 |
| Direct combined steel | 0.14353 |
| Washer wood bearing | 0.07179 |
| Washer bending | 0.16866 |
| Knee overlap wood bearing | 0.00084 |
| Average header bearing | 0.03159 |
| Quarter-area header-bearing sensitivity | 0.06308 |
| Retained base end-cut shear | 0.000016 |
| Minimum directional edge/end reserve | 0.361 mm |
| Minimum component group-spacing reserve | 1.900 mm |

The 0.361 mm edge/end value is the remaining modeled reserve after the adopted
allowances. It is not additional shop tolerance. Hardware dimensions, lumber
grade and condition, drilling control, full washer seating and assembly checks
remain requirements of a matching construction package.

## Full-root sensitivity is not adopted

The adopted bolt comparison requires the documented nominal-diameter full-body
bearing condition. A separate sensitivity assumes root diameter over the whole
bearing length. It does not pass in every case:

| Case | Actual-Ktheta full-root ratio | Fixed-maximum-Ktheta full-root ratio |
| --- | ---: | ---: |
| A12 left | 0.97053 | 1.01612 |
| A12 rear | **1.03168** | **1.08060** |
| A12 forward | 0.86116 | 0.90159 |
| K12 right | 0.95750 | 1.00235 |
| K12 rear | **1.01891** | **1.06695** |
| A1 rear | 0.13139 | 0.14229 |

These values are deliberately excluded from the adopted pass. They show why a
fully threaded bolt cannot be substituted without a new decision. Delivered
bolts must satisfy the construction package's full-body-to-thread-transition
limits; otherwise the nominal-diameter acceptance does not apply.

## Evidence identity and reproduction

[Aggregate evidence](compact-spliced-flush-top-evidence.json) binds the exact
six archive manifests, native reports, geometry, first-stage checks and splice
checks by SHA-256. All six cases share geometry SHA-256
`be18d0a1149757ac91212b3d4bc701cb646c680a9015a06d9068d00b7040a14e`.
The aggregate also verifies each archived source hash and matches every saved
hold and horizontal load to the canonical case definitions.

Rebuild the deterministic aggregate without CAD generation or another solve:

```sh
uv run --no-sync python -m scripts.compact_spliced_flush_top_evidence
```

Accepted archives are `a12-left-07`, `a12-rear-03`, `a12-forward-03`,
`k12-right-03`, `k12-rear-03` and `a1-rear-03` under
`fea/results/compact-spliced-flush-top/`. Earlier partial and failed diagnostic
archives remain historical and are not included in this six-case decision.

## Open connection gate and limits

The 21 listed criteria cover bolt/splice, member, contact and geometry checks;
they do not establish the retained commercial-angle connections' unlisted
separation capacity or independent flange-couple applicability. That connection
gate remains open and blocks fabrication release.

This study evaluates the current legs, relocated upper joints, spliced knees
and retained base under the finite specified cases. It does not requalify the
accepted panel/T-nut construction, measure floor friction, prove an anchor,
inspect delivered lumber or hardware, cover every possible climbing action, or
replace professional engineering review. `qualified_for_design` therefore
remains false in the machine-readable evidence even though all listed
conditional criteria pass.
