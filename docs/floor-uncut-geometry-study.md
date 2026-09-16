# Full-thickness rear-leg and outboard-runner geometry study

Date: September 14, 2026. Candidate: `compact-floor-uncut-development`.

## Decision and scope

This separately modeled candidate removes the lower rear-leg taper by moving each
runner outside the full 4×6 leg. Single 6×6 outer posts connect those runners to
the existing kicker attachment region. It is not a selected viewer default or a
construction release. The preceding flush candidate and its evidence remain
unchanged. Fresh response, contact, member, connection, and fabrication checks
must address this assembly; previous numerical passes do not transfer.

The model is [compact_floor_uncut_frame.py](../mini_moonboard/compact_floor_uncut_frame.py).
Its geometry tests are [test_compact_floor_uncut_frame.py](../tests/test_compact_floor_uncut_frame.py).
The parent assessment work owns subsequent rim support, bracket resistance,
contact, material, and six-case decisions.

## Geometry changes

Coordinates below describe the left side; the right side mirrors X.

| Item | Preceding flush geometry | Uncut candidate |
| --- | --- | --- |
| Rear leg | 4×6 raw stock with 38.1 mm lower inner-face recess and 1:12 runout | Same raw 4×6 profile, X −1308.1 to −1219.2 mm; no lower recess or taper |
| Runner | X −1257.3 to −1219.2 mm | X −1346.2 to −1308.1 mm, an 88.9 mm outward translation |
| Outer front post | X −1219.2 to −1181.1 mm | Single 6×6, X −1308.1 to −1168.4 mm |
| Post Y/Z | Y −175.7 to −36 mm; Z 0 to 238.9 mm | Unchanged; no floor gap |
| Header | X −1219.2 to +1219.2 mm | X −1308.1 to +1308.1 mm; total 2616.2 mm |
| Header Y/Z | Y −175.7 to −36 mm; Z 238.9 to 277 mm | Unchanged in this first candidate |
| Header/post ML24Z station | Left X −1181.1 mm | Left X −1168.4 mm; 12.7 mm inward shift |

The runner retains its front post-plane and rear inclined-leg-plane end profiles.
It touches the full leg's outside face and the new post's outside face without
solid overlap. The leg retains the preceding upper flush trim and two upper
½-inch bolt axes. This change removes the *lower* taper; it does not independently
resolve upper joint or rim-end questions. The 277 mm kicker datum, whole kickers,
66 panel/kicker screws, and existing panel attachment axes remain.

The wider post contains the original outer kicker screw X = −1200.15 mm, with
31.75 mm to its inward X face. Each of those screws has 32.5438 mm modeled
receiver engagement. Each relocated header/post angle upright SDS screw has
35.5448 mm modeled engagement. These are geometric intersections, not withdrawal
or lateral capacity determinations.

## Bolt stack consequences

All twelve bolt tips face outward. The four upper stacks are retained. Front
runner connections pass through the post first; rear runner connections now pass
through the full leg first, then the runner. The interface lies at X = ±1308.1 mm.

| Location | Quantity / diameter | Wood grip | Provisional length | Assumed minimum thread length |
| --- | --- | ---: | ---: | ---: |
| Front post/runner | Four / ⅜ inch | 177.8 mm | 203.2 mm / 8 inches | 31.75 mm |
| Rear leg/runner | Four / ⅜ inch | 127 mm | 152.4 mm / 6 inches | 25.4 mm |

These are provisional CAD stack dimensions, not newly verified catalog selections.
The inherited nominal washers and nuts permit nominal thread seating and tip
projection. They do not guarantee delivered smooth-shank coverage or actual nut
seating.

The front stack is especially restrictive. Under the existing maximum-washer
and quarter-nut-side-bearing assumption, required full body extends to
`177.8 + 2.6416 − 38.1/4 = 170.9166 mm`. An 8-inch bolt minus the provisional
minimum thread length leaves 171.45 mm: only **0.5334 mm** before bolt-length
variation and thread runout. Minimum thread length does not guarantee this
full-body length. Do not accept the nominal-diameter bearing route without an
explicit delivered-hardware bound or a different justified resistance route.
No spacer washer stack has been added or assessed.

The [combined front-bolt envelope](floor-uncut-front-bolt-envelope.md) now checks
the revised 40.5 mm pitch against spacing, timber boundaries, maximum washer
diameter and the existing error assumptions. Its tightest wood margin is only
0.143588 mm. Applying the catalog's −0.18-inch length tolerance makes the
front full-body budget negative by 4.0386 mm before runout; nominal length alone
does not establish a usable catalog-wide stack.

## Single rotated 4×6 post investigation

A possible smaller-stock substitution rotates a 4×6 post to 139.7 mm across X
and 88.9 mm along Y, retaining the kicker-facing plane Y = −36 mm. Its back face
would move to Y = −124.9 mm.

This direct substitution is rejected for the existing layout and force witness:

- The lower front bolt at Y = −105.5278589 mm has only 19.3721411 mm to the
  negative-Y edge, or 16.3721411 mm after the existing 3 mm boundary allowance.
  The saved flush A12-left force loads that edge. Its conservative 4D screen
  misses by **21.7278589 mm**. Those old forces are a screening witness, not a
  solved response for the changed assembly.
- Requiring 4D on both Y edges leaves only 6.7 mm of available bolt-center Y
  separation. Requiring 7D plus 3 mm above the post foot gives Z ≥ 69.675 mm;
  requiring 4D plus 3 mm below the 139.7 mm runner top gives Z ≤ 98.6 mm.
  Therefore the largest pair separation in that common envelope is
  `sqrt(6.7² + 28.925²) = 29.691 mm`, below the adopted 38.1 mm spacing screen.
- The existing angle's outer upright screw at Y = −143.95 mm misses the narrower
  post. Centering the bracket 25.4 mm farther forward would put its outer upright
  screw axes only 6.35 mm from the post Y edges; this needs its own installation
  and connection justification.

This rejects the direct substitution and all-direction placement envelope, not
every possible rotated-post design. A revised force-directed arrangement would
require new geometry, bracket details, forces, and applicability checks.

## Required 6×6 material basis

A nominal 6×6 is a timber. Use the **US Douglas Fir–Larch / Douglas Fir / Western
Larch, No. 2, Posts and Timbers** row of **2024 NDS Supplement Table 4D**, printed
page 47 (PLIB or WWPA grading rules), rather than dimension-lumber Table 4A.

| Reference property | psi |
| --- | ---: |
| Bending, Fb | 750 |
| Tension parallel, Ft | 475 |
| Shear parallel, Fv | 170 |
| Compression perpendicular, Fc⊥ | 625 |
| Compression parallel, Fc | 700 |
| Mean modulus, E | 1,300,000 |
| Stability modulus, Emin | 470,000 |

Tabulated specific gravity is 0.50. Table 4D uses CF = 1 for depth ≤ 12 inches;
do not transfer dimension-lumber size increases. These are reference values,
subject to applicable adjustments and stability checks. The North species row
has different Fb and specific gravity. Require matching grade/species identity
and the stated dry, unincised service basis. Source: [AWC 2024 Supplement](https://awc.org/resources/2024-nds-supplement/).

The values above were transcribed from the previously downloaded primary chapter
PDF `/tmp/reinforced-NDS2024-supp.pdf`, SHA-256
`1f65975633f111c308944c470b6cc10e9207b6c45e8a0804b8bdec3378bbc71b`, with its extracted
text. The [chapter URL recorded elsewhere in this repository](https://awc.org/wp-content/uploads/2026/08/AWC_NDS2024-Supplement_20240719_Chapter-4-Reference-Design-Values_Website-1.pdf)
was inaccessible during this follow-up; a fresh download was not represented.

Implementation must assign these values specifically to the two outer posts.
The response model must use their changed stiffness, and resistance calculations
must use their timber references. E for response and Emin for stability are
different inputs. Any additional orthotropic constants, density, or connection
bearing relations need their own explicit basis; Table 4D does not supply a
complete three-dimensional constitutive model. Existing lumber values remain
applicable only to their own unchanged, correctly classified members.

The implementation now provides `df_l_no2_post_timber()` in
`fea/current_response_materials.py`. Its response constants scale the existing
explicit FPL ratios to the timber E; its separate resistance dictionary uses
the Table 4D values above. A caller assigns response constants through
`materials['timber_by_name'][member_name]` and resistance values through the
member's `reference_override`. Gross section reports, current response member
comparisons, sampled cut-box checks, and local parallel row/group/net-tension
checks carry that override. An explicit `elastic_modulus_psi` on a geometry
member also enters the existing group-factor sensitivity through the minimum
pair modulus and minimum area, an equal-EA sensitivity rather than an actual
unequal-member joint model. Unspecified members retain their historical
defaults; unknown response member names and incomplete resistance dictionaries
are rejected. The native adapter must opt in for both outer posts.

The uncut adapter also corrects the front bolt's assumed axial seat compliance:
139.7 mm of post uses its timber E and 38.1 mm of runner retains its own E.
The two wood paths and steel bolt compliance act in series under the existing
0.05E seat analogy. Using the old E throughout the grip would overstate the
post's contribution to stiffness. A 100 mm² seat witness changes from
309.029 to 261.752 N/mm; other joints and lateral spring assumptions are
unchanged. This is an explicit response assumption, not measured joint stiffness.
The two focused adapter tests pass, including unchanged-joint and mismatched-grip
checks. No uncut native result is implied.

## Verification completed

`python -m pytest -q tests/test_compact_floor_uncut_frame.py`: **5 passed** after
the full-bevel rim and 40.5 mm front-pitch revisions.

Tests establish mirrored full-stock contacts with zero solid overlap; floor
contact; retained raw leg volume and kicker axes; twelve outward bolt stacks;
actual runner bore-bearing lengths matching stated grips; nominal thread-seat
and projection geometry; and relocated angle stations on the new post faces.
A separate lightweight CAD cylinder intersection check produced the receiver
engagement lengths above. No fresh native structural solve or construction
export was performed by this geometry study.

Material implementation checks: **28 tests passed** across the focused new
post-material tests and existing material, timber resistance, and thick-leg
checks. Tests distinguish the post's deck assignment and lower references from
an unchanged member, carry references through sampled net sections, and reject
missing/nonfinite reference values. These are software checks, not native solves.

A follow-up focused check of the remaining local-group and current gross-member
paths passed **24 tests** (six deselected by repository test configuration).
Known-demand witnesses pass with the former dimension-lumber references but fail
with the lower post references; an adjacent member's local result remains
unchanged. No historical response output was regenerated by these checks.
