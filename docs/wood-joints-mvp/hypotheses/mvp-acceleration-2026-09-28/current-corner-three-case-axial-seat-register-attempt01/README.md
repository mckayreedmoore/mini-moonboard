# Three-case left-corner axial tie and washer-seat demand register

This packet consolidates the signed outer-seat axial-tie actions for all six
BG001/BG003/BG045 bolts in the accepted A12-rear, A1-rear and K12-rear
conditional response exports. It retains seven source increments per case,
the two physical washer seats per tie, each seat's member/role/global point and
force vector, the source hash, and the source CAD-annulus average-pressure
conversion. It contains 21 case-increment states, 126 tie-state records and
252 seat-state records. It does not qualify a joint, product, material or
installation and is not a six-case envelope.

The per-axis maxima below are the largest positive signed tie action observed
in these three case sources only. The pressure is `T / 222.726212 mm²` for the
modeled full CAD washer annulus; it is a conditional uniform average, not a
local contact-pressure solution or verified wood support area.

| Group / axis | Maximum signed tension (N) | Source case | Full-CAD-annulus average (MPa) |
| --- | ---: | --- | ---: |
| BG001 `post_1` | 64.96606 | A12-rear | 0.29168574 |
| BG001 `post_2` | 47.00119 | A1-rear | 0.21102676 |
| BG003 `side_1` | 99.23822 | K12-rear | 0.44556148 |
| BG003 `side_2` | 73.62760 | K12-rear | 0.33057447 |
| BG045 `inner_header_1` | 119.34300 | A12-rear | 0.53582827 |
| BG045 `inner_header_2` | 98.44241 | A1-rear | 0.44198844 |

Across the 126 signed tie-state scalars, all 126 are positive tension; none is
compression or zero within the stated `1e-9 N` sign tolerance. The highest
three-case value is `119.343 N` on BG045 `inner_header_1` in A12-rear at load
factor 1.0. The complete case/increment rows and unrounded source seat values
are in [`axial-seat-register.json`](axial-seat-register.json), SHA-256
`7e1c393f0670b4f7428946a856dde757315307d0e92ecfa77e72d70f40bdde90`.

The scalar is taken from each export's `physical_bolt_outer_seat_tension`
interface row. Its source value and the two source receiver-force vectors are
preserved. Both outer seats carry that same signed scalar, and their exported
force vectors are equal and opposite. Seat member, head/nut role, point and
force remain case-bound. BG003's continuous three-member stacks have one axial tie and two outer
washer seats per physical bolt; the middle `base_side_left` member has no
separate axial washer seat. Signed force does not replace the separate lateral
planes; this packet neither combines nor qualifies axial/lateral action.

The attempt04 response register authenticates the three usable cases and
distinguishes accepted K12-rear direct-master response from the rejected
K12-rear attempt03 proposal. The K12 source here is
[`current-corner-k12-rear-case-bound-export-attempt01/corner-demand-report.json`](../current-corner-k12-rear-case-bound-export-attempt01/corner-demand-report.json),
SHA-256 `a78ca15d9d888dbddf6963be34a2f5e57159b0df77ef6b754cf631dbba8c10d0`.
The A12-rear and A1-rear source reports are pinned with their model/response
and parent-audit evidence in [`source-pins.json`](source-pins.json). Replay
checks every listed file hash, the attempt04 case statuses, seven increments
and response gates, six tie identities and twelve seat identities per state,
paired action closure, CAD-area/seat geometry identity, and signed `T/A`
arithmetic. It also confirms the full-load A12/A1 tie values against their
existing component screens and leaves their parent audits marked
`joint_accepted=false`. K12 axial-seat coverage is added here; no K12
resistance comparison is introduced.

The existing conditional comparison basis is reused without extending its
resistance arithmetic. The washer geometry screen gives the modeled annular
area and seat identities. Existing A12/A1 axial screens retain the conditional
DF-L No. 2 `Fc⊥` references only for their applicable base-post/base-header,
transverse, full-support cases and the candidate 1/4-20 Grade 5 first-yield
component scenario. Those are conditional component references, not design
resistances. Candidate-block elastic properties do not assign a strength
grade; BG045 block seats load parallel to the proposed grain, so the `Fc⊥`
comparison is inapplicable there. The exported per-seat conditional reference
values/statuses are retained, but this three-case register computes no new
`Fc⊥` ratio or bolt resistance. It does not infer actual delivered shank,
washer, nut or wood properties.

The exact remaining inputs for a physical resistance decision are: selected
and delivered bolt/nut/washer identities and lot properties; actual shank,
thread location/class and nut engagement; applicable bolt fracture/yield,
thread stripping and nut/pull-through resistances; a reviewed combined
axial/lateral/bending method using the actual controlling sections; delivered
washer dimensions and head/nut footprints; washer steel bending/spreading
resistance; finished wood seat support geometry/condition; and verified wood
strengths. Candidate-block bearing strength remains unassigned. BG003
continuous-bolt/three-member receiver compatibility and BG045 block end
bearing also remain unresolved. These omissions are missing checks, not
inferred physical failures.

Rebuild and verify using Python 3 standard library only:

```sh
python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-corner-three-case-axial-seat-register-attempt01/produce.py --write
python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-corner-three-case-axial-seat-register-attempt01/produce.py --verify
```

This is a bounded axial/washer-demand coverage result for the complete-corner
resistance register. It does not establish a physical tie or seat, actual
pressure, hardware/material capacity, complete-joint acceptance, or climbing
release.
