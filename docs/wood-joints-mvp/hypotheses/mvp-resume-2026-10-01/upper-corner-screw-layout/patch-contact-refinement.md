# Patch59 contact refinement: frozen operator preparation

Completed October 2, 2026. **Doubling patch59's X sampling changes the
same-state peak screw tension by only -0.271% with twelve screws and
-1.245% with twenty.** Both parent A1 comparisons and the subsequent gap
recovery are complete. No physical capacity or candidate acceptance is
claimed here; one finer contact grid does not establish convergence.

The [saved gap recovery](contact-gap-recovery.md) found positive closure
between original bottom-rail contact centroids. This producer replaces only
patch59's 22 contact rows with 44 area-centroid rows to examine that sampling
choice. It preserves the existing physical face, penalty modulus, material
fit, screw and bolt laws, load cases and member geometry.

## Exact bounded change

Patch59 joins `base_rail_bottom_left` to `main_lower_left`. Its saved plane
has X bounds -1130.3 to -89.05 mm and transverse bounds approximately
±19.05 mm about its area centroid. The saved rectangle contains two circular
holes of radius 3.5 mm centered on the transverse midline. The producer uses
analytic half-disk strip area and first-moment integrals to clip each cell.
It performs no CAD operation or scene reconstruction.

The old grid has eleven X bins and two transverse bins; the refined grid
has twenty-two X bins and the same two transverse bins. Regular X bin width
changes from approximately 94.659 to 47.330 mm. Circular clipping still
shifts the affected cell centroids. The new rows replace the old rows;
they do not add duplicate area or an extra backing member.

Each new spring retains compression-only `k * max(q,0)` with
`k = 100 N/mm³ * clipped cell area`. Direction, member ordering, finite
table domain and source plane remain unchanged. New row IDs are
`contact_59_refined_X2_{ix:02}_{it}`, appended after the retained rows.
Every retained row keeps its source row ID and law; its numerical row index
is remapped to the new contiguous matrix ordering.

| Operator packet | Original scalar rows | Removed | Appended | Refined scalar rows |
| --- | ---: | ---: | ---: | ---: |
| Twelve screws per main panel, strong X | 1888 | 22 | 44 | 1910 |
| Twenty screws per main panel, strong X | 1984 | 22 | 44 | 2006 |

This is a contact discretization comparison. The twelve-screw packet still
has 66 panel/kicker screws; the hypothetical twenty-screw packet still has
98. No purchased inventory or modeled hardware arrangement changes here.

## Completed geometry accounting

The authorized lightweight geometry-only invocation completed in
`rawlocal/patch-contact-refinement/geometry-attempt01/`. It first reproduces
the original eleven-by-two analytic cells against all 22 saved clipped-cell
areas and centroids, then checks the refined grid against the same source
area and area centroid.

| Quantity | Completed value |
| --- | ---: |
| Maximum original-cell centroid coordinate difference | 5.68434e-13 mm |
| Maximum original-cell area difference | 2.56932e-11 mm² |
| Refined total contact area | 39594.65597998453 mm² |
| Refined area minus saved source area | -7.27596e-12 mm² |
| Maximum refined area-centroid coordinate difference | 2.27374e-13 mm |

The refined area centroid is
`[-609.6256243188644,55.59817556074772,392.71391901637145]` mm.
These quantities authenticate clipping and first-moment preservation;
they do not demonstrate mechanics convergence or physical contact pressure.

| Geometry-only output | SHA256 |
| --- | --- |
| `geometry-attempt01/geometry.json` | `3aef4e5d460b9733037e1832f2a26211ce85ba706ba078b302f70a3906421b4d` |
| `geometry-attempt01/inputs.json` | `a41e9365f2d4bfce5cdadc7eafa3677b6c348e2560f0b9235bfbb2f0ddddaa30` |
| `geometry-attempt01/producer.py.snapshot` | `0c4e711c1cd64b25c4f53e63b33d6c84454f88eb320125ac07c517bf50e74b51` |

## Operator method and frozen sources

The source operator assessment hashes are:

| Source directory | Assessment SHA256 |
| --- | --- |
| `panel-width-operators-attempt01` | `47e3405e15e3d97f8666ffdead694f1a83fe6f3f76608fc81882112075e98fe0` |
| `count20-width-grain-operators-attempt02` | `d94732bb20ede8da48a7799c014b2c9d66e16062b7c4f485ec008e494c5488a1` |

The producer inherits and verifies both source assessments' complete source
and output pin sets. Coordinates, body ordering and nodal/rigid load arrays
must agree between the two count packets. Existing saved K and DOF labels,
C3D20 point interpolation, rigid projection and bordered elastic-quotient
helpers are reused. The pinned
[recovery producer](contact-gap-recovery.py), SHA256
`37d8b7a1f6789fe993f0036ba7e390c5f1a55262b5736c9bfc4e484dc04ea93b`,
supplies the explicit strong-X main-panel K reassembly. Bottom-rail K remains
the original native timber K.

Only these two bodies need new projections. Each receives 44 new scalar
right-hand sides. Their two KKT factors and solutions are shared between
the twelve- and twenty-screw packet preparation. The producer retains each
packet's H/D/e block on all surviving rows exactly and adds new-versus-old
cross terms and new-versus-new terms. It checks the source rigid map and
updated reciprocity. F and W remain exact; no new load allocation or force
response is computed. No full frame or CAD rebuild is needed.

## Parent handoff and output contract

Producer [patch-contact-refinement.py](patch-contact-refinement.py), SHA256
`0c4e711c1cd64b25c4f53e63b33d6c84454f88eb320125ac07c517bf50e74b51`.
API: `build(Path(fresh_output_child))`. Parent owns serialized operator
execution and its separate A1-only response adapter.

```sh
.venv/bin/python docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/patch-contact-refinement.py --output docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/patch-contact-refinement/operators-attempt01
```

One invocation prepares `operators-12/` and `operators-20/`, each with
`operators.npz`, `B.npz`, `row-identities.json`, `model.json`, byte-exact source
`model-inputs.json` and `operator-assessment.json`. The assessment supplies
repo-relative `source_operator_directory`, `source_scalar_row_count`,
`removed_contact_row_ids`, `appended_contact_row_ids`,
`screws_per_main_panel`, the usual five output hashes, mass and dead-load
factor. The root child retains the clipping record, input pins, producer
snapshot and a final result receipt identifying both prepared assessments.

Original model inputs describe the unchanged physical contact faces;
the new row identities define the refined analytical sampling. The model
and assessment explicitly label that distinction. Parent remaps matching
saved strong-X forces only as a numerical seed, then owns a fresh A1-rear
nominal-clearance response under the existing laws and checks.

The useful comparison is resulting screw/contact sharing and recovered
between-point gaps under the same A1 action. One finer grid is not a
continuous-contact convergence result. No direction of peak-force change,
new capacity, hardware selection or release gate is presumed. Other contact
patches, representative-pose limits, unmeasured screw stiffness, plywood
fit and all existing authority limits remain in force.

## Completed operator preparation

Parent completed `rawlocal/patch-contact-refinement/operators-attempt01/`.
Both source count packets were processed in one invocation; each body's
44-column elastic solution was reused for both. The completed assessments
record exact retained H/D/e blocks and unchanged F/W arrays. Source geometry
accounting is byte-identical to the earlier geometry-only receipt.

| Completed numerical receipt | Value |
| --- | ---: |
| Main-panel physical DOFs / new scalar RHS | 6567 / 44 |
| Bottom-rail physical DOFs / new scalar RHS | 276 / 44 |
| Main-panel elastic KKT upper-force relative residual | 1.87459e-11 |
| Bottom-rail elastic KKT upper-force relative residual | 1.94596e-14 |
| Twelve-screw H relative reciprocity error | 8.73142e-11 |
| Twenty-screw H relative reciprocity error | 8.48489e-11 |
| Unchanged modeled mass | 224.9499553141194 kg |
| Unchanged dead-load factor | 1.1111358300342407 |

These are operator preparation receipts. Parent separately checked sources
and outputs, then executed the finite A1 responses and gap recovery below.
No peak screw force is inferred from operator preparation alone.

| Completed `operators-attempt01/` output | SHA256 |
| --- | --- |
| `inputs.json` | `e041212f2c0147511241bc152b8aa2c56bea4ad9fc80b0c283cdcf9a82864dfc` |
| `result.json` | `42eb5fe0c9d6504b982245433ea8b1b159fc2658810e1ac2712ccee351a08d54` |
| `operators-12/operator-assessment.json` | `19ed2f2c33e11b509a8a461a8607f472d37a271ed5ff23ccbf3cfadb976915e7` |
| `operators-20/operator-assessment.json` | `0dbbb18e69055656de618adaee0e3c33a3b39dd3833d64c4f313e3872454d817` |
| `operators-12/operators.npz` | `264d963c44b3d2de14e34fde989124a30ba73e9aa6db1a58497d204dfd471e31` |
| `operators-20/operators.npz` | `32cbea382aa6753baa62dc4f8eb20b13ff3ca3bb22b1ea9416f78469db0f4ddd` |
| `operators-12/B.npz` | `971fe1b93a79df89fb690c85f6ff2f6091e0e0ea136557e9de1e45c558739e92` |
| `operators-20/B.npz` | `96126d1c4200eba8e6b166636352cc83cd887b053b552fc951138a5c3a79622f` |
| `operators-12/row-identities.json` | `678b6fd01a406012814e408f52ee9ad21df7894ad6a3e12c585a57332a00e6ce` |
| `operators-20/row-identities.json` | `ecd47839bcd0fb483f04309df0dc62af096e8f53bbe28318670e68af0ff1430b` |

The completed assessments bind all five generated files, including the
explicitly annotated model and byte-exact source model inputs. The producer
snapshot remains byte-exact `0c4e711c…0e74b51`; its full hash appears above.

## Completed same-state sharing comparison

The parent ran **only A1-rear at nominal bolt clearances**, at the same
250 lb climber action, 300 N horizontal action and 100 mm hold lever as the
source strong-X packets. Both returned
`PASS_CONDITIONAL_LAWS_WITH_BOUNDED_SEATING`, with rigid rank 296 and the
existing bounded-seating qualifications. The 174 source pins matched in
each completed response. This finite result does not replace either
complete twelve-state source frame or its component force authority.

All values below refer to `main_lower_left` in that simultaneous case.
V is the norm of the two lateral screw components at the listed peak T;
it is not an independently selected maximum shear envelope.

| Quantity | Twelve: 22 cells | Twelve: 44 cells | Twenty: 22 cells | Twenty: 44 cells |
| --- | ---: | ---: | ---: | ---: |
| Peak screw T, N | 1213.615 | 1210.324 | 2180.721 | 2153.579 |
| Simultaneous V at peak T, N | 407.641 | 406.942 | 75.893 | 57.143 |
| Opening at peak screw, mm | 0.451212 | 0.449988 | 0.810774 | 0.800683 |
| Original `round_panel_lower_left_edge_2` T, N | 1213.615 | 1210.324 | 448.541 | 377.609 |
| Sum of panel screw tensions, N | 4036.845 | 4044.408 | 5112.820 | 5097.555 |
| Signed net outward reaction from all panel contacts, N | 2261.358 | 2268.921 | 3337.334 | 3322.069 |
| Bottom-rail contact compression sum, N | 1317.279 | 1326.775 | 2691.586 | 2653.327 |
| Active bottom-rail contact cells, force above 0.01 N | 6 / 22 | 8 / 44 | 8 / 22 | 13 / 44 |
| Largest individual bottom-rail contact force, N | 473.921 | 521.740 | 1488.348 | 1571.643 |

The governing screw remains `round_panel_lower_left_edge_2` in the
twelve-screw case and `hyp20_main_lower_left_edge_gap_1` in the twenty-screw
case. The peak changes are -3.291 N (-0.271%) and -27.141 N (-1.245%).
The refined twenty-screw contact peak is
`contact_59_refined_X2_00_0`; the refined twelve-screw contact peak is
`contact_59_refined_X2_07_0`. Individual cell forces are not directly
comparable pressure capacities because each new cell represents a smaller
area with a different centroid.

Signed total screw tension minus signed net contact reaction remains
**1775.487 N**, the same outward external panel-normal action, in every
column. Full six-component panel wrench balance is within 4.4e-12 N and
8.9e-9 N mm. Contact totals include kicker-edge directions and are not
unsigned pressure sums. This confirms coherent redistribution under the
chosen laws; it does not calibrate them against real hardware.

## Completed refined displacement/gap check

The parent reused the original recovery method with the 44 refined cell
centroids and half-spacing points. All 44 original q coordinates reproduce
within 1.14079e-10 mm for twelve screws and 1.18097e-10 mm for twenty.
Each state has 129 retained points: 44 centroids plus 85 additional samples.
No sample was excluded by the source circular holes.

| Recovered gap quantity, mm except count | Twelve: coarse | Twelve: refined | Twenty: coarse | Twenty: refined |
| --- | ---: | ---: | ---: | ---: |
| Largest original-centroid positive closure | 0.002656 | 0.005808 | 0.008254 | 0.017431 |
| Largest additional-point positive closure | 0.044593 | 0.005374 | 0.010851 | 0.028963 |
| Additional positive points above 1e-6 mm | 3 | 4 | 2 | 7 |

The refined twelve-screw largest additional witness is
`[-420.454368,49.419277,385.350195]` mm; the twenty-screw witness is
`[-893.652273,49.475624,385.417346]` mm. Both are X half-spacing points.
The latter is approximately 125.548 mm in X from A1 and 123.960 mm from
the added peak screw. Locations and sample sets change with refinement;
these maxima are not measurements at one fixed point or a continuous gap
bound. The twenty-screw additional closure remains larger than its sampled
centroid maximum, and its positive samples are not eliminated by this grid.

This establishes a **modest force sensitivity to this one X refinement**,
not a dominant explanation for the high screw tension. It also establishes
that continuous opposed-face contact has not been resolved by the sampled
model. Positive closure includes numerical penalty compression, not a
qualified wood indentation. These are representative saved poses, not gap
envelopes over the nonunique bounded seating motions. No further refinement,
law sweep, capacity assignment or physical geometry change follows from
this packet automatically.

## Response and recovery receipts

Paths below are relative to `rawlocal/patch-contact-refinement/` unless
explicitly labeled as a maintained parent adapter.

| Completed artifact / adapter | SHA256 |
| --- | --- |
| `frame-12-attempt01/comparison.json` | `cfb89955c1372099261144bfc2826ca306d7928543324804467bf4978e3532c2` |
| `frame-12-attempt01/response.npz` | `3799969b0ca2fd30377ed0657bb2a4673480484e5d167ba644f6fb03d66bda47` |
| `frame-20-attempt01/comparison.json` | `2a6df8b507dc0e5f62f65d385cde3c3660a2dc31611a45a33d43be79b9522813` |
| `frame-20-attempt01/response.npz` | `a15ee6efdf05c1910e336c2b0b79727da31d62f57bcd72c4c608d7204bc374e4` |
| `gap-attempt01/result.json` | `81fa19a86dcb597cce3a86eb75edd1bf760673b701473cced8c58b5b9a31f647` |
| `gap-attempt01/displacement.npz` | `1d027bb8cd9fc277e92abd685c01412a2efdedfd1d87589c721d2ace66115f39` |
| Maintained parent [patch_contact_frame.py](patch_contact_frame.py) | `8b35515f5322fbb395f3476b003880505f8a7ce1019f40b9e2843e21aca9d3b7` |
| Maintained parent [patch_contact_recovery.py](patch_contact_recovery.py) | `f4a289f16373a10cae859562e514a2d7ca8064691392c2e4c77b11c11a26d7b0` |
| Adapted recovery snapshot, bound by gap result | `0682097510f3430eb085470aa55694310a310e2fd7e5d34f31c33731c84d129b` |

The worker ran only the authorized lightweight clipped-area/first-moment
check and reconciled saved operator, response and gap results. Parent
executed operator preparation, the two finite frame comparisons and refined
gap recovery. No operator, frame, native or CAD run, software tests, review,
staging or commit was performed by this worker.
