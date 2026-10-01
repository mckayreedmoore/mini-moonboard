# Bottom-outer bolt placement producer review

## Review disposition

I found no material method-application defect in the frozen producer. Its
output stays at the source-join / bounded-geometry level: it sets no adopted
Table 12.5.1C pass, `Cg`, `CΔ`, resistance, criterion pass, or joint
acceptance. The review is limited to the frozen code and saved result; it
does not rerun geometry, a native solve, or the producer.

Reviewed producer `produce.py` SHA-256:
`75e7eed05e9f24c1a04b35a8faeb03e4f284259ae2af54abd45c611bb2e0684f`.
Saved result `/tmp/mini-moonboard-bottom-outer-placement-2026-10-01.json`
SHA-256: `21c2eba56b80efa174cdb5ecdb206468a6b15882732c6edd548d2027063f58c3`.
The source methods and Table 12.5.1C interpretation are recorded in
[method-review.md](method-review.md).

## What the producer establishes

The producer pins the four source axes, current feature-register and joint
packet bytes, upstream case sources, helper code, Chapter 12 PDF, and each
finished STEP. It verifies candidate/revision identity, two named receivers
per axis, stock-frame orthogonality/handedness, source-to-local axis/datum
projections, and one eligible bore-patch binding. It extracts both timber
receiver positions for each bolt, the per-member lateral plane vector, and
the separate axial tie. For the full bolt angle it adds those vectors; for
candidate cross-grain edge direction it uses the lateral plane component.
Those are the correct distinct vector roles for the reported diagnostics;
the code does not turn either into an accepted NDS load classification.

The result binds 4 axes / 8 receiver memberships, 21 states, 168
member-bolt records, and 84 two-member interface records. Each interface
record contains the intended eight source actions: two lateral bolt planes,
two outer-seat axial ties, and four contact cells, paired to the same member
set. The moment is transported to the named midpoint of the two bolt-axis
datums. The interface record explicitly says that other joint interfaces
and body loads are excluded.

Both interface pairs reproduce the pinned `33.000 mm` center spacing. The
pair geometry reports the pair-only upper bound `S/2≤16.5 mm`, confirms that
`4D=25.4 mm` dominates this bound, and explicitly leaves NDS row/group status
unadopted. All eight current memberships have stock-envelope cross-grain
edge distances above `4D`; the minimum margin is `2.5 mm`, at
`side_2` in the cleat. The saved BREP sampling reports all 48 edge rays
terminating on the corresponding stock-boundary plane at three bore-depth
stations; the minimum sampled finished edge is `27.9 mm`. The producer also
keeps `continuous_depth_extrema_proved=false`, so this is sampled boundary
evidence rather than a continuous minimum proof.

The full-interface direction diagnostic is rounding-bounded. In all 84
records the summed eight-action interface force is non-aligned with the
pair-line direction beyond the source rounding bound. This does **not**
decide NDS row applicability: the sum includes contact and axial-tie actions,
is limited to one two-member interface, and excludes body loads and the
member's other joint interface. The code separately emits
`adopted_NDS_row_or_group=false`. Do not summarize the 84 flags as proof that
`Cg` is inapplicable or that the bolts do not form a row under a complete
connection analysis.

## Boundaries that publication must preserve

- The side-pair cleat edge result is close: its smallest nominal cross-grain
  edge distance is `27.9 mm`, only `2.5 mm` above `4D`. This is a
  source-bound geometric result for the stated two-axis interface envelope;
  it is not a finished member acceptance or a blanket Table 12.5.1C pass.
- All 48 edge rays match their stock-envelope boundary at the three sampled
  depths, but no continuous-depth extremum is proved. The separate end-ray
  check is less complete: 12 `base_side_left` end rays do not terminate at
  the stock-envelope endpoint because the finished cut/nearby features occur
  earlier. Their measured shortening is about `27.65 mm` at the near end and
  `30.96 mm` at the far end. Do not turn stock-only end-distance booleans
  into finished square-cut end-distance or `CΔ` acceptance.
- The cleat side-axis grain rays at mid-depth contain internal void intervals
  before reaching the grain-span endpoint, consistent with crossing nearby
  rail bores. The producer records those intervals. Keep them visible when
  describing sampled paths; a ray is not a continuous wood ligament.
- The output's `PASS_FROZEN_SOURCE_JOIN_AND_BOUNDED_GEOMETRY_ONLY` status is
  source/geometry scope only. `criterion_pass`, adopted factors, and joint
  acceptance remain false; the end factor is `null`. The code does not
  calculate Table 12.5.1C acceptance, `Cg`, `CΔ`, the §12.3.9 axial-bearing
  requirement, the §12.5.1.2(b) equivalent shear area, local member stress,
  or strength.

No code change is requested from this review. Root's complete same-state
interface-force and station/sign summary should accompany the above scoped
geometry facts; neither report should promote source fidelity or force
direction fidelity into strength acceptance.
