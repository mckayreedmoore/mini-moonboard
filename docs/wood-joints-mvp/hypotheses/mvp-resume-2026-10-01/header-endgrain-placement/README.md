# Current header end-grain bolt placement

The applicable translational placement checks clear for the current twelve
axes and 72 signed states. There are **70 zero in-plane states and two pure-X
states**, using the existing direction threshold of 1e-10 N. No adopted
placement failure or required axis move is established. Local splitting,
eccentric load transfer and torque resistance remain unestablished. This is
a bounded calculation on saved forces, not complete joint acceptance.

The engineering question is whether the current receiver geometry meets the
applicable NDS placement requirements under these particular saved actions.
The older BG045 Y-edge rule and five oblique states do not answer this question.
The parent's geometry, source documents, authority and HOLD flags are unchanged.

## Current sources and scope

The exact existing result directory is
[`../header-joint-attempt02/final/`](../header-joint-attempt02/final/checks.json),
not `header-joint-checks-attempt02/final`. This worksheet reads the current
section of [header-joint-checks.md](../header-joint-checks.md), pins
[header_joint_checks.py](../header_joint_checks.py), and reuses its frozen
placement, signed states and complete interface actions. It reconstructs all
72 lateral forces and axial ties from the saved response and row identities.
It imports only the existing small `frame_state_contract` helper; no frame
solve, CAD, native mechanics, software tests or agent review is run.

| Input | SHA-256 |
| --- | --- |
| `../two-receiver-frame-attempt03/comparison.json` | `0ff0dfc00c112a906910641141fd242f4a58295aa3324ca569132a3fa2d388a5` |
| `../two-receiver-frame-attempt03/response.npz` | `774c3bbddf8061f6b9d1cfdd5f22efbeb1025bd57431a249912ae8e60a731f52` |
| `../header-joint-attempt02/final/checks.json` | `8daded05317ef0babb3be8e60adccd5a688bb386be19e8ce2cea32718ab560f9` |
| `../header-joint-attempt02/final/source-pins.json` | `72aa536e1e7a75944ff5339324c86c728c40d4e53ce521f58f50f5d04d7e8090` |

[source-pins.json](results/final02/source-pins.json) enumerates every consumed
input, including model inputs, frame model/rows, finished feature bounds,
seven receiver STEP hashes, current header evidence and official references.
All are checked before and after arithmetic. STEP files are hashed, not opened
as CAD. The signed source is the six nominal-gap `case_id + '_gap_raw_force_n'`
arrays. Fixed-force seating freedom does not establish a unique pose or strict
tangent stability; the existing scope contract is preserved.

The blocks retain **+Z grain**, the header **+X grain**, and the target shafts
**±Z axes**. The source header is X = −1219.2…1216.025,
Y = −175.7…−36, Z = 238.9…277 mm. Source shaft midpoint Z may be outside
the header: distances use the intersecting axis line, not an invented header
point at that midpoint. Receiver bounds and grain identities are in
[worksheet.json](results/final02/worksheet.json); full source points, shaft
directions and bearing lengths are in [axes.csv](results/final02/axes.csv).

## Placement worksheet

All distances below are millimetres, from the axis to the external source
boundary, ordered **minus / plus**. They are not bore-edge ligaments, bit
instructions, inspected dimensions or ray travel distances.

| Exact axis | Block X edges | Block Y edges | Header X ends | Header Y edges |
| --- | ---: | ---: | ---: | ---: |
| `center_post_header_left_1` | 43.95 / 44.95 | 26.95 / 61.95 | 993.49 / 1441.735 | 26.95 / 112.75 |
| `center_post_header_left_2` | 43.95 / 44.95 | 61.95 / 26.95 | 993.49 / 1441.735 | 61.95 / 77.75 |
| `center_post_header_right_1` | 44.95 / 43.95 | 26.95 / 61.95 | 1443.55 / 991.675 | 26.95 / 112.75 |
| `center_post_header_right_2` | 44.95 / 43.95 | 61.95 / 26.95 | 1443.55 / 991.675 | 61.95 / 77.75 |
| `center_principal_header_left_1` | 56.95 / 26.95 | 35.7 / 104 | 1103.2 / 1332.025 | 35.7 / 104 |
| `center_principal_header_left_2` | 56.95 / 26.95 | 100.7 / 39 | 1103.2 / 1332.025 | 100.7 / 39 |
| `center_principal_header_right_1` | 26.95 / 56.95 | 35.7 / 104 | 1335.2 / 1100.025 | 35.7 / 104 |
| `center_principal_header_right_2` | 26.95 / 56.95 | 100.7 / 39 | 1335.2 / 1100.025 | 100.7 / 39 |
| `knee_outer_left_inner_header_1` | 44.45 / 44.45 | 113.35 / 20 | 133.35 / 2301.875 | 113.35 / 26.35 |
| `knee_outer_left_inner_header_2` | 44.45 / 44.45 | 20 / 113.35 | 133.35 / 2301.875 | 20 / 119.7 |
| `knee_outer_right_inner_header_1` | 44.45 / 44.45 | 113.35 / 20 | 2301.875 / 133.35 | 113.35 / 26.35 |
| `knee_outer_right_inner_header_2` | 44.45 / 44.45 | 20 / 113.35 | 2301.875 / 133.35 | 20 / 119.7 |

D = 6.35 mm; 1.5D = 9.525, 3D = 19.05, 4D = 25.4,
5D = 31.75 and 7D = 44.45 mm. Minimum main/side bearing length is
38.1 mm, so ℓ/D = 6. Floating arithmetic is compared within 1e-6 mm;
the nominal source dimensions define this branch.

| Obligation | Applicability and result |
| --- | --- |
| Table 12.5.1A: header ends | Active parallel softwood action: toward-end 7D, away-end 4D. Both ends of every target axis also clear the conservative 7D geometry envelope; closest is 133.35 mm. |
| Table A: block ends | Shaft runs through the grain direction. A transverse-fastener center/end construction is not supplied by its shaft midpoint. No numerical Z end-distance pass is invented. Local end-grain splitting remains separate. |
| Table 12.5.1C: active block edges | Pure ±X perpendicular-to-grain action identifies the X loaded/opposite edges directly: 26.95 ≥ 25.4 and 56.95 ≥ 9.525 mm. Adjacent Y faces are unselected by these actions. |
| Table C: active header edges | Parallel-to-grain action; ℓ/D = 6 uses 1.5D, not the >6 half-row-spacing branch. Both active-axis Y edges, 100.7 / 39 mm, clear 9.525 mm. |
| Tables A–D: zero-action states | No lateral direction or loaded-face assignment. Retain all dimensions and geometric comparators; retain axial ties, contact forces and moments. A 1.5D comparison on every measured edge is only a geometry envelope. |
| Table 12.5.1B: load-aligned rows | Current target pairs lie along Y; current lateral action lies along X. They are not load-aligned rows. All 66 header-axis pair distances are enumerated; smallest is 35 mm. Perpendicular full-value row spacing depends on attached members, not a universal 4D. |
| Table 12.5.1D: transverse target pairs | Active X layout: header parallel branch requires 1.5D; block perpendicular branch at ℓ/D = 6 requires 5D. Pair pitches are 35 mm at posts, 65 mm at principals and 93.35 mm at knees; all clear 31.75 mm. In the other states this is a dimensional envelope. |
| §12.5.1.3: cross-grain spread | Header target-axis Y span is 93.35 mm ≤ 127 mm. Each block's target-pair span is no larger. This covers the twelve target axes, not an invented common layout for orthogonal fasteners. |
| §§12.6.1–.3, 11.3.6 | Symmetric staggering where possible, gravity-axis/center-of-resistance behavior and local stresses remain explicit joint obligations. No uniform sharing or new Cg is adopted; prior Cg values remain sensitivities. |
| Tables E/F/G | Withdrawal-only lag screws, glulam and CLT branches do not describe these sawn-lumber through bolts. |

The two signed active states are:

| Case / axis | Block Fx, N | Header Fx, N | Block loaded edge | Header toward-end / away-end distance, mm |
| --- | ---: | ---: | --- | ---: |
| `a12-left / center_principal_header_left_2` | +23.376702544 | −23.376702544 | +X, 26.95 mm | −X 1103.2 / +X 1332.025 |
| `k12-right / center_principal_header_right_2` | −26.692597158 | +26.692597158 | −X, 26.95 mm | +X 1100.025 / −X 1335.2 |

[receiver-states.csv](results/final02/receiver-states.csv) records all **144
receiver states**, with raw signed forces, axial ties, row identities, null
directions and explicit applicability. The knee 20 mm Y offsets do not
establish a loaded-edge failure in these states. No first-ray diagnostic is
converted into a normative rule, and neither Ceg nor CΔ waives an edge minimum.

[spacing.csv](results/final02/spacing.csv) includes all 66 target-axis pairs.
Pairs from different interfaces are identified: a small Y projection alone
does not define an adjacent row or authorize combining their capacities.
The receiver inventory also retains twelve other structural bolts in the
six blocks and ten Hillman axes in the header. The 24 target/orthogonal-bolt
comparisons in [neighbor-bores.csv](results/final02/neighbor-bores.csv) have
minimum nominal source bore ligament **7.452644216 mm**. That is geometry,
not splitting capacity or an invented cross-axis Tables B/D minimum.
The ten Hillman duties remain with the parent's panel correction.

## Exact remaining requirement

An applicable local load distribution and resistance is still needed for
the bored blocks/header under **each simultaneous lateral, axial and contact
wrench and couple**. It must cover header tension perpendicular to X grain
from Y/Z actions, transverse end-grain block splitting, crossing-bore
ligaments and the disconnected header strips. The actual eccentric load path
must also resolve Table C note 2 / §3.8.2 concentrated-load applicability;
if applicable, mechanical or equivalent reinforcement must resist the
perpendicular tension. NDS §§11.1.2–.3 and 12.6.3 govern this local requirement.
An Ft⊥ allowable cannot be inferred from Fc⊥ or Fv. Appendix E's parallel-grain
scope does not establish perpendicular splitting resistance.

[joint-demands.json](results/final02/joint-demands.json) retains all 36 complete
interface states, their role wrenches, pair couples and simultaneous section
peak states. Force/moment sums are independently reconstructed from the
existing saved point actions, including free moments. Zero net lateral force
does not remove the outer-tie/contact couple. The active lateral pair moments
are −759.742833 and +867.509408 N·mm about their pair centres; no moment
capacity is assigned by a spacing pass.

The current largest connection-zone |VY| is **185.724277191 N**, at
`k12-rear / center_post_cleat_right`, station 1419.2 mm after the cut.
Its simultaneous `(N,VY,VZ,T,MY,MZ)` is
`(0.704303, −185.724277, 55.473437, 760.419070, −28210.149883, −55745.788384)`
in N and N·mm. Separately, the saved header torque envelope is
**−32968.545338 N·mm**, at `a1-rear`, station 22.225 mm after the cut.
Those separate states are not combined. Existing F90 characteristic
comparisons, connected-section proxies and washer bearing results do not
supply the missing resistance or hole-ligament load division.

The bounded next action is a local splitting/load-transfer calculation for
the current `k12-rear / center_post_cleat_right` demand, followed by coverage
of the other saved demands within the chosen method's applicability. Parent
owns integration and any heavy geometry/native work. This worksheet adds no
blanket external sign-off prerequisite or physical-work authorization.

## Official sources and reproduction

The existing cached official [AWC NDS 2024 Chapter 12](https://awc.org/wp-content/uploads/2026/09/AWC_NDS2024_withCommentary_20260911_Website_Chapter-12-Dowel-Type-Fasteners.pdf)
was read at printed pp.81, 97–100: §§12.1.2–.3, 12.5.1–.2, 12.6 and Tables A–D.
[Chapter 11](https://awc.org/wp-content/uploads/2026/09/AWC_NDS2024_withCommentary_20260911_Website_Chapter-11-Mechanical-Connections.pdf)
was read at pp.70–71, 74; [Appendix E](https://awc.org/wp-content/uploads/2026/09/AWC_NDS2024_withCommentary_20260911_Website-Appendix.pdf)
at p.174. Public PDFs contain specification text despite their filenames.
All three official URLs were retrieved with `curl -fsSL --max-time 30 URL |
sha256sum`; bytes matched the reused cache exactly. No new manual copies
were retained.

| Reference | SHA-256 |
| --- | --- |
| Chapter 12 | `53f6ec05dfd1ceabeccd4d6e88c342111678d3da4631ee7b482b706f77c1780f` |
| Chapter 11 | `45a3d78de1a4fba573589be0fc776e37bd581e4cedec24e38d63856161092d33` |
| Appendix | `1fa2bcf52803b1bbed8ea30cf13551dd5f76c90bf110ac475b401f81d116ec31` |

Run from the repository root, choosing a new output name:

```sh
uv run python docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/header-endgrain-placement/study.py \
  --output results/replay
uv run ruff check docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/header-endgrain-placement/study.py
uv run ruff format --check --line-length 100 \
  docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/header-endgrain-placement/study.py
```

Execution used Python 3.12.3, NumPy 2.5.2 and Ruff 0.16.6 from the existing
shared project environment. PDF reading used cached pypdf 6.19.0 and
cryptography 50.0.2 through
`uv run --no-project --with 'pypdf[crypto]'`; PDF extraction is not needed
to replay the calculation. The producer refuses changed pinned inputs or
an existing output directory. Ruff checks pass. No software tests were run.

| Active artifact | SHA-256 |
| --- | --- |
| [study.py](study.py) | `cabe01fb8e164673c9706c01374ff172c1144560d8b2d3b26242e6b013af6932` |
| [worksheet.json](results/final02/worksheet.json) | `482048c4e28b3c7d5916dad44fd7835d2770337d41d351db47320a72e966af40` |
| [source-pins.json](results/final02/source-pins.json) | `37f1fdfcd994f8cd169c646f7d3dcb3fead3238c7e48941ac020d52e72887871` |

Only this README and the producer are maintained files. The seven generated
receipts, approximately 316 KB total, inherit the existing hypotheses ignore
rules. `results/final02` is active; the initial `results/final` is a superseded
local execution receipt. No upstream evidence is archived or pruned, and no
routine status file, shared staging, commit or push is created.
