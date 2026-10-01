# Upper-block conditional strength evaluation

The two top outer blocks remain the priority. Their largest sampled bolt
actions exceed the existing unadjusted, nominal-diameter lateral references
by 16.3% left and 36.7% right. Those references use an unadopted 106 ksi bolt
bending-yield estimate. This packet resolves the arithmetic, source,
sampled-section and nominal washer-support questions below; it does not
establish an adopted joint failure or pass.

The owner directed this parallel work and a bounded goal on October 1,
2026 (UTC). Four Luna maximum-reasoning workers implemented the calculations,
method review, exact section inventory and washer-seat evaluation. Root
investigated sources and hardware fit, integrates the packet, and owns final
validation. The reviewed revision remains
`led-clearance-2x6-runner-seated-blocks-v1`. No geometry was changed and no
native solver was run. The mechanics coordinator retains gravity, the
six-case response and primary lower-corner work.

## Coverage and results

The packet combines the authenticated uppermost and service-upper action
records: eight blocks, 32 physical bolts, A12-rear/A1-rear/K12-rear, seven
increments per case. The 672 bolt-state rows retain simultaneous signed
lateral and axial actions. They are not a six-case envelope. The twelve
starting leg/runner stacks and 66 Hillman panel/kicker screws remain separate.

| Block | Bolts | Largest unadjusted nominal-D demand/reference | Governing sampled case |
| --- | ---: | ---: | --- |
| Top outer left | 4 | 1.1631 | A12-rear |
| Top outer right | 4 | 1.3667 | K12-rear |
| Top center left | 4 | 0.1658 | A12-rear |
| Top center right | 4 | 0.1723 | K12-rear |
| Left service outer | 4 | 0.0353 | A1-rear |
| Right service outer, WJ06 | 4 | 0.0404 | A1-rear |
| Left service inner | 4 | 0.0422 | A1-rear |
| Right service inner, G7 | 4 | 0.0345 | A1-rear |

Every row is a conditional component comparison. A ratio below one does not
qualify its block, host, bolt or complete joint. The
[lateral calculation](lateral.md) replays all six yield modes for every row.
For the two controlling outer states it also supplies required aggregate
resistance multipliers and conditional material/duration sensitivities. It
does not silently select a duration factor or infer a quarter-inch bolt
property from larger-diameter tables.

| Question | Result established here | Remaining boundary |
| --- | --- | --- |
| Nominal-D thread criterion | Both declared partial-thread scenarios satisfy the per-member quarter-thread limit; conditional 6/8 in class LB minima also clear the 32-axis requirements | Actual item profile, functional nut travel and qualified material remain separate |
| Lateral arithmetic | 672 same-state rows and 4,032 nominal-D mode values reproduce the frozen inputs | Qualified Fyb, contact idealization, applicable adjustment/group treatment and complete interaction |
| Directional geometry | 64 member-direction summaries, 16 two-bolt receiver pairs and 15 pinned STEP sources | Outer-box end/edge comparators exclude local cuts; oblique detailing needs an applicable method |
| Finished block sections | Forty exact sampled cuts include the saved bores; areas are 7,903.21, 7,236.46 or 6,569.71 mm² with one, two or three face regions | Section force/moment and regional load transfer; unsampled critical cuts and host sections |
| Nominal washer support | All 64 seats support all three annulus scenarios: 192 geometric checks | Eccentricity, tolerances, physical contact, head/nut footprint, washer bending and coupled transfer |
| Conditional wood-seat pressure | 1,344 signed seat states; peak ideal Fc-perp ratio 0.5816 for minimum catalog area | Uniform annulus pressure is a reference assumption, not a local contact field or joint resistance |
| Local-stress source | Authenticated 2024 Appendix E equations match the existing helpers | Their parallel-grain method does not close general oblique loading or splitting |

Detailed results and limits are in [geometry.md](geometry.md),
[seats.md](seats.md), [methods.md](methods.md),
[local-stresses.md](local-stresses.md) and [hardware.md](hardware.md).
Hardware travel and thread engagement remain distinct from sufficient bolt
length. The source audit also identifies Chapter 12's inconsistent washer
table cross-reference and the missing quarter-inch standard crosswalk; it
does not waive the washer requirement.

## Coordinator handoff

Resolve the two outer `side_2` states first using their bound material,
contact and adjustment assumptions. Retain the paired receiver forces and
same-state axial actions; do not combine independent maxima or divide a pair
equally. A hypothetical passing multiplier is not evidence for adopting it.

Use the actual block cuts to bind section and local failure-path actions.
Treat the two or three face regions as geometry on a cut, not independent
whole bodies or a uniform stress distribution. Preserve the shorter G7 and
top-center end conditions. Check applicable splitting and nonparallel
actions separately from the authenticated Appendix E arithmetic.

Apply the functional bolt/nut fit work to the upper 6 in and 8 in cohorts.
Nominal washer support can now be reused as frozen geometry evidence; washer
bending, prying and bolt moment still require their own supported model.
Reconcile the upper actions when the coordinator qualifies the remaining
three cases and consistent gravity/climber loading history. These are
specific follow-on dependencies, not requests to redesign the frame or
repeat the unchanged original bolt and panel studies.

The bounded goal ends with a locally replayable, independently reviewed packet and
this handoff. Complete upper joints, the whole frame and all 47 formal MVP
criteria remain outside that completion claim. No wood, holes, hardware or
floor is represented as inspected; no drilling, fabrication or climbing is
released.

## Replay and review

Use the existing repository environment from the root:

```sh
uv run --no-sync python docs/wood-joints-mvp/hypotheses/upper-block-strength-2026-10-01/lateral.py --verify
uv run --no-sync python docs/wood-joints-mvp/hypotheses/upper-block-strength-2026-10-01/geometry.py --verify
uv run --no-sync python docs/wood-joints-mvp/hypotheses/upper-block-strength-2026-10-01/seats.py --verify
uv run --no-sync pytest -q docs/wood-joints-mvp/hypotheses/upper-block-strength-2026-10-01/test_lateral.py docs/wood-joints-mvp/hypotheses/upper-block-strength-2026-10-01/test_geometry.py docs/wood-joints-mvp/hypotheses/upper-block-strength-2026-10-01/test_seats.py
```

The producers pin their consumed source data, implementations and finished
solids. Changed or missing inputs stop replay. Verification success means
the packet reproduces, not that a strength criterion passes. Source, tests
and summaries are published on master; raw JSON, STEP and downloaded PDFs
remain local under repository policy. A source-only checkout cannot replay
without that evidence.

Independent review and final parent checks are recorded in
[review.md](review.md). Publication is restricted to this packet's owned
files, outside quiet hours, while preserving other agents' work.
