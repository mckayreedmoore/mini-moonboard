# Independent source and calculation review

October 1, 2026. I found no source-join or arithmetic discrepancy within the
packet's stated scope. This review verifies the existing source responses and
geometry records; it does not establish a capacity, pressure field, joint pass,
or design acceptance.

The independent verifier is `parent_verify.py`, SHA-256
`e49fbefe980e009e40b352035988c27db5b0bab86865a4792b3d2aa5efd73486`. It
pins producer `a941dceee5c002068e9920cfe41f62270e11ff399367fdf9494c445a06d8a86d`,
the local raw report `fcf393be26c433daf760a6afcf9fd6260d88f04f43a6234def960bbba4789029`,
the prior 52-axis source report
`6551861db1112c91b87c5705bbceb3bb26f55f0d7e70029a74d828519425145e`, and
freeze `d4ba1c78eb358d25e32819201e9c59e05d425a06d9e4e5cca3dc09d7139ffd73`.
It verifies every file bound by the three-case freeze and reruns the pinned
finished-contact-graph source verifier. That verifier returned `PASS` for the
current graph's 142 pins.

The replay covered all 21 case/load states: 84 four-bolt rows, 252 contact
cells, 63 pair summaries, and 21 cleat balances. Each bolt row equals its
source-report row, and I independently reconstructed the signed native
lateral vector from both retained bilateral spring components using
`force_on_first_local_N = -endpoint_rf_N[0]`, its preserved local force basis,
and the componentwise half-last-place radii. The reconstructed action and
rounding radii agree with the response action and the prior report. All 84
separate outer-seat ties were checked against their same-state unilateral
native force; they remain separate from lateral demand. This preserves the
conditional `side_1` A1-full-load lateral ratio `1.0945088665197509` and does
not add its `197.1248 N` tie to the lateral resultant.

For the three contact pairs, each cell was rebound to its frozen compression-
only source row, native response component, receiver pair, point, unit normal,
and positive source area. The force/radius vectors, action/reaction, native
and table interval overlap, displacement-interval state, cell-average formula,
and member-specific grain context were checked. The result contains 112
resolved compressive cells, 140 resolved open cells, and no ambiguous rounded
boundary. Of 504 cell/member contexts, 182 perpendicular-grain comparisons
are applicable to resolved compression; 238 open comparisons are null and 84
parallel-rail contexts exclude the perpendicular-grain reference. These are
conditional source-cell averages and reference quotients, not contact
tractions or wood resistance. The three exact graph/atlas areas and the sums
of the corresponding four cell areas agree within `1e-6 mm²`; the direct
rail/side contacts are included in the contact register but excluded from the
cleat boundary.

I reconstructed each cleat free body without the producer's
`member_balance`: the 20 physical nodal body loads were summed from the pinned
model, and the four bolt lateral planes, four distinct ties, and eight cleat
contact actions were summed at their source points. The force-radius sum and
lever-arm moment-radius sum reproduce the all-body audit. Across the 21
states, the largest absolute residual components are `8.50716765752324e-5 N`
and `0.0035433318544158543 Nmm`; the maximum force and moment interval excesses
are both zero. Every independently recalculated state remains inside the
source `0.1 N / 2 Nmm` gates. For example, the A1-rear 0.1-load residual is
`(7.000000046e-6, -4.097629404e-6, 8.507167660e-6) N` and
`(-6.062130758e-5, 1.415338507e-4, 3.543331854e-4) Nmm`; its force and moment
rounding radii agree with the audit to about `1e-15` in the respective units.

The largest reported modeled cell averages also reproduce at A1 full load:
`0.0469222553 MPa` for rail/cleat, `0.2345212926 MPa` for side/cleat, and
`0.3118800129 MPa` for rail/side. The rail receiver is excluded from the last
pair's `Fc⊥` quotient because its proposed grain is parallel to the normal.
These numbers do not prove a peak pressure, bearing law, full host-member
boundary, or complete joint resistance. The preserved side-bolt unadjusted
reference flag and unresolved quarter-inch bolt material basis remain as the
README describes.

The full deterministic producer replay used the exact source-report path
`/tmp/mini-moonboard-remaining-single-shear-reference-2026-10-01.json` and the
project interpreter. Its separate output
`/tmp/mini-moonboard-bottom-outer-joint-2026-10-01-replay.json` is byte-identical
to the reviewed local raw output, SHA-256
`fcf393be26c433daf760a6afcf9fd6260d88f04f43a6234def960bbba4789029`. The
independent verifier returns `PASS_INDEPENDENT_SOURCE_JOIN_AND_NUMERIC_ORACLE`
for this bounded source check; Ruff passes on the verifier. To reproduce with
the repository environment:

```sh
.venv/bin/python docs/wood-joints-mvp/hypotheses/bottom-outer-joint-disposition-2026-10-01/parent_verify.py
```

The first replay attempt with system `/usr/bin/python3` stopped at import
because that interpreter has no CadQuery. The same replay completed under the
repository `.venv` (CadQuery 2.8.0); this was an interpreter-selection issue,
not a producer or numeric failure. No native solve was run for this review.
