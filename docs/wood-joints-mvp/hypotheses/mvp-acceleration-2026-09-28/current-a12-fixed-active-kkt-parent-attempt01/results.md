# Parent result: direct refinement stops at force comparison

The frozen one-shot run completed in 4.192 seconds. Parent separately
verified every frozen source hash and the assessment/output pins afterward.
No native solve, floor-mask change, geometry change or force adoption occurred.

The 2,649-order KKT system has numerical rank 2,649 at the unchanged 1e-12
relative cutoff; smallest/largest singular-value ratio is 1.08523e-7.
Relative KKT residual is 1.71536e-17. The fixed nonfloor active-set and
strict boundary checks pass. No alternate set or threshold was searched.

| Original gate | Result |
| --- | --- |
| All ten physical/source-law/floor gates | Pass |
| Body force balance | Maximum 4.093e-12 N |
| Body moment balance | Maximum 2.387e-9 N mm |
| Source spring laws using raw H | Maximum residual 0.000108219 N |
| Projected-q DAT intervals | All pass; maximum ratio 0.862139 |
| 300 rigid-coordinate DAT intervals | All pass; maximum ratio 0.379230 |
| Force DAT intervals | **25 fail**; maximum difference 0.000484644 N, maximum ratio 128.607 at global row 1586 |

Final status is `STOP_PHYSICAL_OR_SOURCE_COMPARISON_GATE`.
The known-answer reproduction requirement is not satisfied. The worst
relative force mismatch is at a nonzero service-clip outer-seat axial tie,
not a floor normal: row 1586, native center 0.0036338206319 N and native
radius 7.0441603e-10 N. The corresponding direct free-force minimum is
0.0036339112283 N. This very small difference still exceeds the original
force interval; no radius is widened and no candidate forces are adopted.
The assessment retains only aggregate failures and the worst row, not the
full refined force vector. It does not establish all 25 row identities.
Failure identities must not be inferred from the earlier OSQP candidate;
the subsequent bound-radius proof below does establish their nonzero-source
classification without another solve.

Compared with the previous OSQP result, direct refinement removes the
unilateral-sign and all 30 q-interval failures, while reducing force failures
from 69 to 25. This demonstrates a numerical improvement under the same
episode; it does not validate a staged history, recover a fourth case or
close joint resistance. The next diagnosis is the remaining force-source/
interval dependency, rather than another solver-settings campaign.

The subsequent read-only diagnosis rules out the fixed-zero bucket: all
734 estimated bound rows have native centers zero and radii at least
5e-7 N, exceeding the largest direct bound residual 3.126e-12 N. The 225
omitted rows are exactly zero with native centers zero. Thus the 25 force
misses are among nonzero-source rows; their full identities remain unsaved.

Row 1586 has stiffness 3975.8157915 N/mm. The native force record uses
endpoint RF; its geometric SPRINGA `dd-dd0` table-force calculation agrees
with RF to 3.79e-10 N. In contrast, the reduced source comparison uses
`B@U`, with q center 1.30019e-6 mm and radius 3.81344e-6 mm; that displacement
radius corresponds to about 0.01516 N under the row stiffness. Passing this
q interval does not establish agreement with the much narrower RF interval.
The representation/precision dependency is concrete, but its sole cause is
not proved. The initial emitted spring span differs from nominal by
3.77014e-11 mm, giving a stiffness-scaled magnitude 1.499e-7 N; this is a
candidate numerical effect, not an established correction or error bound.

The native final increment logs report largest residual force as
0.000000 N and displacement correction 7.541133e-13. The convergence file
records force residual percent 0.0000 and correction-displacement percent
1.070e-10. These printed values do not prove exact zero, but do not support
blaming default FIELD convergence settings for the discrepancy. Parent
checked the pinned 2.23 manual's FIELD definitions (PDF page 445, SHA256
`a0bf3fc03f374912ff2bf28da3f7dfb6a61428dd7f41b281a2e7e1fdb318f330`);
no controls change or native retry is justified from this evidence alone.
The next bounded source check examines ghost-coordinate/elongation arithmetic
and translation invariance before proposing any native method coupon.

That [source-only arithmetic check](../current-springa-ghost-coordinate-translation-diagnostic-attempt01/README.md)
is now complete and independently replayed. The actual carrier coordinates
reach about 1192 mm, not an extreme artificial origin. Preserving their
parsed relative vector, common translation changes the printed-state
SPRINGA table force by only 3.39e-10 N, within the native RF radius and about
267 times smaller than the row-1586 miss. The actual emitted span is
99.9999999999623 mm and is the subtracted `dd0` datum; its nominal-span
difference cancels and is not a force correction. A translation-only native
coupon is not justified as the next reproduction remedy. No carrier moves
or native runs followed. Other force-source/operator precision effects
remain unresolved; this one-row check does not explain the other 24 misses.
