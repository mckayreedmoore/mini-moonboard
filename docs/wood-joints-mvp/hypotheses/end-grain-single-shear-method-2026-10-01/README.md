# Ten end-grain bolts: conditional single-shear references

October 1, 2026. This additive packet computes 210 conditional lateral
reference rows for the ten end-grain-axis bolts excluded by the earlier
[52-bolt packet](../remaining-single-shear-reference-2026-10-01/README.md).
It uses the same authenticated A1, A12 and K12 rear responses, seven states
each, for `compact-floor-flush-wood-joints-development` /
`led-clearance-2x6-runner-seated-blocks-v1`. No geometry, source demand,
selected baseline or native response changes.

## Result and boundary

The largest `Ceg`-only scenario comparison is
`center_principal_header_left_2`, K12 rear full load:
**120.091599 N / 396.632330 N = 0.302778140**, Mode IV.
The next largest is its right counterpart at A12 rear full load,
`0.290076202`. These are individual-bolt lateral arithmetic comparisons,
not fully adjusted design ratios, completed joint passes or adopted capacity.
All ten axes have 21 reference rows. Every original source-row field remains
unchanged, including the earlier method's explicit null references and ratios.
The additional `conditional_end_grain_reference` field keeps the later
method distinct. Simultaneous outer ties remain separate.

Parent replay of the independent closed-form verifier passes all **1,260
unadjusted modes and 1,260 once-adjusted modes**. Maximum relative mode
differences are `7.910789410126054e-16` before `Ceg` and
`8.047765704334135e-16` after it. All ten focused tests and Ruff pass.

The main/side interpretation and source clauses are documented in the
independent [method review](method-review.md). Each axis has exactly one
bolt-axis-parallel cleat/block, used as the conditional NDS main member;
`base_header` is the transverse side member on all ten. Five end-grain
receivers occupy each modeled seat side. Main-member selection follows the
grain relationship and retains that receiver's properties, rather than
assuming that the modeled nut-side receiver is main.

| Axes | End-grain main receiver | Modeled main bearing span |
| --- | --- | ---: |
| Four `center_post_header_{left,right}_{1,2}` | Corresponding `center_post_cleat` | 128.9 mm |
| Four `center_principal_header_{left,right}_{1,2}` | Corresponding `center_principal_cleat` | 134.7 mm |
| Two `knee_outer_right_inner_header_{1,2}` | `knee_outer_right_inner_frame_block` | 139.0 mm |

Each modeled header span is 38.1 mm. These are CAD/source bearing-interval
hypotheses, not measured stock, purchased bolt lengths or drilling instructions.
The grain maps are proposed source-bound assignments, not observed wood.

## Calculation and applicability

The inspected [NDS-2024 Chapter 12 publication](https://awc.org/wp-content/uploads/2026/08/AWC_NDS2024_withCommentary_20250328_WebsiteChapter-12-%E2%80%93-Dowel-type-fasteners.pdf)
is pinned to SHA-256
`5fc837523ff10acc097a162718700a9b4ba64e627d2b0023439146d42fe4ee2a`.
Section 12.3.3.4, printed page 92, supplies the end-grain main-member
perpendicular-bearing rule for `D ≥ 1/4 in`. Section 12.5.2.2, printed
page 100, applies `Ceg = 0.67` to connection reference lateral value `Z`.
AWC's [main-member FAQ collection](https://awc.org/about/frequently-asked-questions/)
allows either bolted single-shear member to be called main when the correct
properties follow the roles. Extending that explanatory guidance to the
main-member-only end-grain clauses is an explicit engineering interpretation;
the pinned NDS does not state that interpretation verbatim.

The conditional main bearing input is `Fe⊥ = 4,450 psi`. The side header
uses its actual signed lateral resultant's acute grain angle and the pinned
SG 0.50 bearing interpolation, with rounded 5,600/4,450-psi endpoints.
Every saved lateral force is perpendicular to the bolt axis and to the
end-grain main's grain. Consequently the largest member load angle is
90 degrees, giving `Kθ = 1.25`. The pinned quadratic single-shear helper
computes all six unadjusted reference modes. `Ceg` multiplies each mode
and the governing `Z` **once**; it does not change `Fe`, add an axial tie,
or provide another adjustment factor.

The scenario retains a smooth full-body 0.25-inch bearing diameter, zero
interface gap and **unadopted `Fyb = 45,000 psi`**. Table 12A's full-body
45,000-psi footnote concerns tabulated diameters starting at 1/2 inch; it
does not qualify quarter-inch bending yield. The Table I1 / TR-12 example's
`D ≥ 3/8 in` basis also does not qualify it. Grade 5 proof, axial yield and
tensile values remain distinct from dowel bending yield. No actual bolt
conformity or thread-in-bearing qualification follows from the modeled shaft.

These calculations establish neither contacting faces nor compliant
spacing/end/edge distances. Source-supported fastener/material/geometry
inputs, applicable service/group/geometry adjustments, splitting, tear-out,
axial/lateral/bending interaction, wood/washer/contact resistance and complete
joint transfer still require supported dispositions. Two continuous right-side
bolts remain outside this two-member method. Three missing frame cases and
all applicable criteria in the integrated 47-question package remain open.
No new receiving or inspection prerequisite is added to conditional analysis;
observed checklist fields stay blank and no physical operation is released.

## Reproduction

The unchanged upstream producer is pinned to
`5f2a7fdca2ef0c56c661fa10e4122189f8a7a1ae0725062cb8c56d95dd911edf`;
its local full report to
`6551861db1112c91b87c5705bbceb3bb26f55f0d7e70029a74d828519425145e`.
The role-census API is pinned to
`a8bd7797b1f46c11f0a9603c5a2fa87742bf9d39e99e0db33942546216ec664c`.
It reauthenticates the geometry, method/grain maps, three-case freeze and
source files before returning ten geometry records and 210 unchanged rows.
The new producer additionally binds the NDS PDF and records its own digest.
Raw source/native/STEP/result data remain local; publication includes code,
tests, reviews and summaries.

New producer SHA-256:
`8e10846bf008430b7e5e30c484c20624bbaa71a6addc74a63bd17b1445c229b8`.
Parent's local result SHA-256:
`29854f8b333fd952fab92788517fad1af64a9a807be5b0c134fc1bc47756779f`.
Independent verifier SHA-256:
`71ecdc282c4c4ed552ef53c3b95271dcb6dfa191733acbe7566e0eb233a2392c`.
The separate local census file used by that verifier is pinned to
`5ec2ef3f76dbc7eab0a7a83ae7a5007ff7caec77da56418641208e29846bb16c`;
its path-sensitive source pin uses the identical upstream bytes at the
second `/tmp` name shown below.

```sh
.venv/bin/python docs/wood-joints-mvp/hypotheses/end-grain-single-shear-method-2026-10-01/produce.py --source-report /tmp/mini-moonboard-remaining-single-shear-reference-2026-10-01.json > /tmp/mini-moonboard-end-grain-reference-2026-10-01.json
.venv/bin/python docs/wood-joints-mvp/hypotheses/end-grain-single-shear-method-2026-10-01/role_census.py --source-report /tmp/remaining-single-shear-reference-2026-10-01.json > /tmp/end-grain-role-census-2026-10-01.json
.venv/bin/python docs/wood-joints-mvp/hypotheses/end-grain-single-shear-method-2026-10-01/parent_verify.py --report /tmp/mini-moonboard-end-grain-reference-2026-10-01.json
.venv/bin/python -m unittest discover -s docs/wood-joints-mvp/hypotheses/end-grain-single-shear-method-2026-10-01 -p 'test_*.py' -v
.venv/bin/ruff check docs/wood-joints-mvp/hypotheses/end-grain-single-shear-method-2026-10-01
```

Focused tests reject ambiguous/oblique grain, non-lateral forces, zero
direction, changed interval lengths and malformed source rows; they check
that endpoint reversal preserves the physical main member, that source rows
remain unchanged, and that the end-grain factor applies once while axial
ties stay separate. Independent arithmetic validation is recorded in
[the calculation review](independent-calculation-review.md).
