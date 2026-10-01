# End-grain single-shear method review

**Disposition.** A conditional single-shear reference can be developed for the
ten currently excluded axes by assigning each physical end-grain cleat or
block as the NDS main member and keeping that member's own grain, bearing
length, and material inputs attached to it. The assignment need not follow the
modeled head-seat or nut-seat side. This is supported by AWC's explanatory
guidance for bolted single-shear connections, together with the conditions in
the pinned 2024 NDS. Applying the main-member end-grain provisions this way is
an explicit interpretation of the guidance, not a sentence that the 2024 NDS
states verbatim. This disposition opens a conditional calculation path; it
does not establish resistance or joint acceptance.

## Source basis

The inspected Chapter 12 PDF is
[`AWC_NDS2024_withCommentary_20250328_WebsiteChapter-12-Dowel-type-fasteners.pdf`](../hardware-material-specification-2026-09-30/materials-source/AWC_NDS2024_withCommentary_20250328_WebsiteChapter-12-Dowel-type-fasteners.pdf),
SHA-256 `5fc837523ff10acc097a162718700a9b4ba64e627d2b0023439146d42fe4ee2a`.
The pin identifies the local bytes reviewed; it is not a separate claim about
publisher provenance.

- Section 12.3.1, printed page 91, defines reference lateral value `Z` as the
  minimum of the applicable yield-mode equations and requires contacting
  member faces, load perpendicular to the dowel axis, and compliant geometry.
  Table 12.3.1A uses main/side bearing lengths and properties. Figure 12B,
  printed page 92, depicts one common orientation, with the side member at the
  bolt head and the main member at the nut. Neither the accompanying text nor
  the figure states that this head/nut orientation defines the main member.
- Section 12.1.2, printed page 81, defines edge distance, end distance,
  spacing, and rows; it does not define the single-shear main member by
  head-seat or nut-seat position.
- Section 12.3.3.4, printed page 92, requires `Fe⊥` for the main member when
  a dowel with `D ≥ 1/4 in` is inserted into that member's end grain with its
  axis parallel to the wood fibers.
- Section 12.5.2.2, printed page 100, requires multiplying the reference
  lateral value `Z` by `Ceg = 0.67` when a dowel is inserted in the main
  member's end grain with its axis parallel to the fibers. The clause applies
  the factor to `Z`; it is not a factor to apply only to one yield mode or to
  omit because the end-grain member is on a particular bolt-seat side.
- AWC's [single-shear main-member FAQ](https://awc.org/faq/which-member-is-the-main-member-in-a-single-shear-connection-2/)
  (also listed in AWC's [FAQ collection](https://awc.org/about/frequently-asked-questions/),
  September 30, 2021; based on the DES330 presentation) says that for bolted
  connections the distinction is less clear and that it does not matter which
  member is called main if the correct main and side properties are used.
  This is explanatory AWC guidance, not 2024 NDS normative text. Extending
  that role guidance to the end-grain-specific `Fe⊥` and `Ceg` clauses is the
  interpretation identified above.

The 45,000 psi bolt entries do not establish `Fyb` for the modeled quarter-inch
shaft. In Table 12A, printed page 101, the listed bolt diameters start at
`1/2 in`; its 45,000 psi footnote applies to those full-body bolt table cases.
The separate 2024 NDS Appendix I is explicitly non-mandatory. Its Table I1,
printed page 186, lists 45,000 psi for bolts only for `D ≥ 3/8 in`. The pinned
appendix copy is
[`appendix-2024-awc-20260911.pdf`](../upper-block-strength-2026-10-01/source-cache/appendix-2024-awc-20260911.pdf),
SHA-256 `1fa2bcf52803b1bbed8ea30cf13551dd5f76c90bf110ac475b401f81d116ec31`.
Neither table supplies a quarter-inch `Fyb` basis, and this note adopts none.

The end-grain provisions are conditional on a dowel-type fastener and
the stated axis/grain relationship. The stored CAD shaft diameter is 6.35 mm;
that geometry alone does not establish a candidate fastener's NDS diameter,
thread/root occupancy, or compliance with the `D ≥ 1/4 in` condition in
§12.3.3.4.

## Ten-axis role and orientation census

The source register is
`/tmp/mini-moonboard-remaining-single-shear-reference-2026-10-01.json`,
SHA-256 `6551861db1112c91b87c5705bbceb3bb26f55f0d7e70029a74d828519425145e`.
The read-only role census reauthenticated the frozen source and geometry
inputs and reported ten axes, three cases, seven increments per case, and 210
signed lateral/tie state rows. It assigned no NDS roles and computed no
reference values or ratios.

| Modeled axis family | Axes | End-grain receiver | Modeled seat-side split for that receiver | Modeled shaft-bearing interval |
| --- | ---: | --- | --- | --- |
| `center_post_header_{left,right}_{1,2}` | 4 | `center_post_cleat_{left,right}`; `base_header` is transverse to the bolt axis | Nut-seat side, all 4 | Cleat 128.9 mm; header 38.1 mm |
| `center_principal_header_{left,right}_{1,2}` | 4 | `center_principal_cleat_{left,right}`; `base_header` is transverse | Head-seat side, all 4 | Cleat 134.7 mm; header 38.1 mm |
| `knee_outer_right_inner_header_1/2` | 2 | `knee_outer_right_inner_frame_block`; `base_header` is transverse | Axis 1 nut-seat side; axis 2 head-seat side | Block 139.0 mm; header 38.1 mm |

Thus five end-grain receivers are on each modeled seat side. The census records
modeled seat order only; it does not establish the physical head/nut orientation
of delivered hardware. Across all 210 saved plane states, the end-grain
receiver's force is perpendicular to its proposed grain axis: the largest
absolute normalized force/grain dot product is `6.5217e-16`, and the largest
departure from 90 degrees is `4.2633e-14°`. This confirms the conditional
plane-vector relationship in these records; the source grain map is proposed,
not observed. For the conditional `D ≥ 1/4 in` equation set, this makes the
maximum load-to-grain angle `θ = 90°`, so Table 12.3.1B gives `Kθ = 1.25` for
these lateral-plane rows. It says nothing about the separately reported
same-state tension-only outer tie, which is not part of the lateral
single-shear calculation.

## Conditional calculation boundary

For a later reference calculation, keep each end-grain cleat/block as the main
member across all ten axes, independent of its modeled seat side. Use that
member's own bearing length and grain/material basis; apply `Fe⊥` to its main
member bearing term only when the specified candidate fastener satisfies
§12.3.3.4. Keep the base header's candidate member properties and
load-to-grain angle as the side member inputs. Evaluate the six applicable
single-shear yield modes for the same-state lateral force, then apply
`Ceg = 0.67` once to the resulting `Z` under the stated main-role
interpretation. Do not transfer `Fe⊥` to the side member, count a tension tie
as lateral force, sum axis references, or omit `Ceg` on the five head-seat
axes.

The available record supports only this conditional method step. An
engineering reference needs source-supported candidate inputs for fastener
type and diameter, thread/root and shank bearing occupancy, member material,
grade and grain, contact and bearing geometry, NDS spacing/edge/end-distance
checks, and applicable adjustment factors. The complete joint also needs its
simultaneous axial, washer/seat, bolt-bending and other failure modes
addressed. These are analytical input and method questions; this note adds no
blanket purchase, receiving, or physical-inspection prerequisite. Delivered
hardware and wood remain unobserved, and Actual/Disposition fields remain
blank until observed. The intervals above are source/CAD shaft intersections,
not measured embedment lengths or drilling instructions.

A separate [`produce.py`](produce.py) now implements a conditional
end-grain `Ceg` reference path. This source review does not independently
validate that producer's arithmetic or quarter-inch `Fyb` basis, and adopts no
numerical reference, ratio, capacity, pass/failure, geometry change, or
native-solve result.

The independent review and historical replay above apply to the original
role-census snapshot, SHA-256
`98d1a619912fc42c5da4c264cc52227f06e4a8752d6bb7603d1ee9fc27b59bde`, invoked
with `--register`. That run returned
`PASS_SOURCE_CENSUS_ONLY_NDS_MAIN_ROLE_UNESTABLISHED`; its JSON output SHA-256
was `a32fae176b3f8d4a8b70bb7d4ae0ad9dc8ee5cdea336e5923e57e397ee1ced12`.

The script later received an additive `build_census` API; its current SHA-256
is `a8bd7797b1f46c11f0a9603c5a2fa87742bf9d39e99e0db33942546216ec664c`.
The source author reports that the later API replay retained the exact same
ten axes and 210 state rows. I did not independently review or replay those
later bytes; this review's independent replay finding applies to the original
snapshot only. The source author's current invocation is:

```sh
.venv/bin/python docs/wood-joints-mvp/hypotheses/end-grain-single-shear-method-2026-10-01/role_census.py \
  --source-report /tmp/mini-moonboard-remaining-single-shear-reference-2026-10-01.json
```
