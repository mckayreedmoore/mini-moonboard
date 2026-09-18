# Round insert load and model analysis

The insert candidate has no qualified resistance or accepted structural load
rating. The historical screw results are useful for diagnosing assumptions;
they do not establish the forces, stiffness or resistance of the new inserts.
The selected development hardware is E-Z LOK 801420-13 with Dottie FMDD14114
machine screws, at 48 face-panel and eight kicker-panel stations.

## What the completed screw cases establish

The three original round-bore cases and the three independent F10 load probes
retain native input, output and source snapshots. The diagnostic force direction
is correct: force on the timber opposite the screw insertion direction is
withdrawal. In the original F10 solution the highest recovered withdrawal is
1550.65 N. Its loaded upper-left panel has 1966.4 N total tensile attachment
force and 205.4 N total compressive attachment force. The largest value is not
an absolute-value error that mislabeled compression as withdrawal.

| F10 probe | Maximum screw withdrawal, N |
| --- | ---: |
| Original: twice 250 lb weight, 300 N horizontal, 100 mm front standoff | 1550.6 |
| Once 250 lb weight; other assumptions retained | 849.5 |
| Zero horizontal force; other assumptions retained | 1413.3 |
| Zero front standoff; other assumptions retained | 1293.4 |

These are independent assumption probes, not alternative rated loads. Removing
the front standoff retains the physical offset from the front face to the shell
midsurface. It does not remove the entire moment applied to that midsurface.
The zero-standoff case actually increases maximum panel displacement from
25.52 mm to 26.14 mm, illustrating that displacement and one fastener's axial
force need not move together.

[Replay script](../fea/round_panel_load_diagnosis.py) additionally sums each
independent panel's applied wrench and its recovered spring reactions. It
reports print-rounding intervals rather than silently using global reaction
output tolerances for forces reconstructed from displacement differences.
Those intervals do not explain all local residuals: the loaded F10 panel has
approximately 0.85 N residual in its global Y force component, and other probes
reach approximately 2.1 N. Global foot-reaction balance passes. Local recovery
therefore failed in the historical method; the correction is validated below, and its observed discrepancy is
far too small by itself to explain a 1550 N attachment demand. No local force
acceptance is inferred from the global check.

## Model changes required before insert demand can be trusted

The historical model uses the same isotropic 7000 MPa modulus for timber and
plywood. It assigns 1000 N/mm independently in three global directions to
panel screws, bracket screws and leg bolts. It treats angle bodies as rigid.
The purchased product is now identified as Roseburg AC Douglas-fir Exterior
PS 1-09 plywood, Lowe's item 12235/model 119055. APA's compatible family tables
provide conditional resistance and stiffness minima across permitted layups;
an unknown five- versus seven-ply layup does not by itself prevent their use.
Species group and original sheet-axis orientation still require an explicit
basis. The separate tabulated axial and bending minima cannot both be matched
by one homogeneous shell modulus. The current isotropic 7000 MPa value is
therefore still an assumption. Insert stiffness, slip, bolt clearance,
fastener preload and panel-to-timber bearing pressure are also uncalibrated.
[Verified material sources](round-material-led-verification.md),
[conditional APA family bounds](round-ac-plywood-bounds.md).
Full foot cross-sections are clamped; the model can therefore
supply moments and lateral reactions unavailable from an unanchored floor.

The previous bilateral panel springs also carry all panel compression at the
screw stations. Real panels can seat on timber between the screws. This is a
material omission in a model used to interpret local prying; its error is not
known to be conservative.

[New runner](../fea/round_insert_frame.py) constructs the insert candidate afresh
and introduces normal-only, compression-only panel seating springs over actual
raw timber support. It samples existing member stations and three locations
across each supported width, including the header behind the kicker. The final
runner rejects sample points inside the modeled insert receiver cuts and
records every discarded tributary. Discarding the whole sample cell can
overestimate the removed contact area; the five-sample comparison is required. Each
tributary area is clipped to its own panel footprint. Coincident independent
seam edges keep independent panel degrees of freedom; no spring ties the panel
edges directly. A scalar projection transfers only displacement normal to the
panel and preserves rigid motions, including the shell-to-backside offset.
Tangential friction and preload remain absent.

The initial penalty is 100 N/mm³ times tributary area. This is a numerical
parameter, not measured wood bearing stiffness. Sampling, contact penalties,
local machining and pressure maxima are not converged. The retained timber
prism model excludes insert pilots and local thread/notch stresses; starting
from the current candidate does not remove that approximation.

## Focused next comparisons

1. Run F10 with and without the new panel seating contact on the same fresh
   insert model and compare signed attachment forces, contact reactions,
   complementary contact status, global and per-panel wrench balance.
2. Run C6 and C10 with contact to check whether the controlling load location
   changes. Keep the same prescribed full-vector load for the comparison.
3. Change panel-attachment stiffness alone to 100 and 10000 N/mm, retaining
   bracket/bolt stiffness at 1000 N/mm. These bounds are exploratory, not a
   measured confidence interval. Separate axial and lateral stiffness remains
   a later refinement requiring an actual connector basis.
4. Refine contact samples and vary the penalty before accepting a contact
   result. Assign measured/grade-supported orthotropic panel properties and a
   compatible timber basis before interpreting material failure. A modulus
   change alone cannot qualify plywood strength.
5. Close the independent floor and connection load-path checks. Clamped-foot
   results cannot be repackaged as an unanchored floor pass.

## Exact insert resistance gate

The manufacturer's product page identifies 801420-13 as a zinc, flush,
1/4-20 × 13 mm insert for soft wood. It does not provide a usable minimum full
thread depth. Its installation guide requires the matching drill size and
places the flush style below the surface; the nominal 0.25 mm development
recess is not a manufacturer-specified machining tolerance.
[E-Z LOK product](https://www.ezlok.com/ezhex-insert-801420-13),
[E-Z LOK installation](https://www.ezlok.com/e-z-hex-drive-insert-installation).

More decisively, E-Z LOK states that it does not offer Hex Drive testing results
because installation variables affect performance. The metal-insert and
knife-thread test tables on the same page concern other product families and
cannot establish this insert's wood withdrawal resistance.
[E-Z LOK mechanical testing](https://www.ezlok.com/testing).

The open inputs are effective female/male thread overlap; zinc thread
stripping; external-thread withdrawal and lateral behavior in the actual
receiver species, grain direction and pilot; edge splitting; machine-screw
head pull-through in the owned Roseburg plywood; cyclic assembly/loading; and
combined actions. The old SPAX values and the nominal insert's larger diameter
supply none of these missing design resistances. Actual installation-specific
qualified test data or a different documented connector is required.

A wood connection design also requires the applicable adjustments to its
reference values; an unadjusted table value is not automatically a usable
capacity. [American Wood Council manual](https://web-media.awc.org/wp-content/uploads/2022/01/17210413/AWC-2018-Manual-1810.pdf).

BS EN 12572-2 addresses bouldering-wall structural integrity, surface elements
and panel insert resistance. Its public overview does not supply enough
numerical clauses to replace the current analyst-selected loads with a claimed
standard-compliant design basis. The normative standard and its applicable
load/test scope must be obtained and applied explicitly; a generic 2× body
weight multiplier is not proof of compliance.
[BSI standard overview](https://knowledge.bsigroup.com/products/artificial-climbing-structures-safety-requirements-and-test-methods-for-bouldering-walls).

## First native contact diagnostic: rejected

The first F10 insert/contact run converged its contact active set after 22
cycles and passed global force/moment equilibrium. It failed the printed-MPC
check: the maximum residual interval remained about 0.000335 mm from zero,
exceeding the existing 0.00001 mm criterion. The report correctly leaves
`contact_diagnostic_checks_passed` false. Its apparent 1548.5 N peak recovered
attachment withdrawal is therefore not accepted as insert demand.

The failed equations involve scalar contact projection from S8 nodes. The
CalculiX 2.21 manual explains that shell `*NODE PRINT` values average the
expanded shell's outer nodes. This suggests a distinction between printed
average displacement and the spring/MPC's internal displacement. It is a
specific recovery hypothesis to test, not permission to loosen the tolerance.
[CalculiX 2.21 manual, pages 110–111](https://www.dhondt.de/ccx_2.21.pdf).

[The focused coupon](../fea/shell_spring_output_probe.py) uses one shell, four
springs and a separate fixed support for each spring. The unique support's
native reaction gives an independent force check. It compares direct shell
attachment with a separate MPC-connected node, so the next change can be based
on observed native output instead of an assumed force formula. The failed
full-frame result is preserved independently of subsequent corrections.

## Output recovery defect reproduced and corrected

The four native coupons reproduce the discrepancy for both corner and midside
shell nodes. A direct spring's force inferred from original shell-node output
can differ from its own native support reaction by roughly 1.5 N. A separate
three-dimensional proxy node reproduces the native force, while its MPC appears
violated if checked against the original shell-node output.

The correction reads the actual expanded solid's opposite faces from 3D FRD
output and the native `.12d` expansion map. Their mean reproduces the mechanical
translation. The helper authenticates original node/element identity, shared
face pairs, midpoint coordinates, normal direction and thickness. Original
output remains unchanged; reconstructed values retain the half-sum of the
actual printed face-value rounding intervals.

All four recovered coupons pass each spring's independent native-reaction
check and all MPC checks. Maximum recovered force differences are 0.002 N
for the corner coupon and 0.0004 N for the eight-node coupon, within the actual
print intervals. The proxy MPC residual intervals contain zero; no equation is
excluded and no acceptance tolerance is relaxed. Corrupted node identities and
mismatched DAT/FRD output are rejected by regression tests.

[Recovery implementation](../fea/shell_surface_recovery.py),
[native coupon archive](../fea/results/shell-spring-output-v2.tar.gz),
[replay tests](../tests/test_shell_surface_recovery.py).

The corrected insert runner requests the additional expanded displacement
output and uses this recovery for spring forces and MPC validation. Historical
screw archives remain unchanged. Their raw-output defect is demonstrated, so
the original table above describes recovered values from the earlier method,
not corrected or qualified insert resistance.


The final masked comparison below uses corrected recovery and preserves its
native outputs for replay. Its numerical checks pass for the five completed
cases while substantial attachment demand remains.

## Final attempted comparison: five of eight cases completed

The masked v3 batch completed the following five finite cases. Each passes
authenticated native replay, global equilibrium, all MPC checks, contact
complementarity and all six independent panel wrench checks. Loads remain the
same analyst-selected twice-250-lb vertical load plus 300 N horizontal load
at a 100 mm front standoff, and the panel attachment stiffness is
an arbitrary surrogate rather than a measured property of the selected insert.

| Case | Attachment stiffness (N/mm) | Maximum panel displacement (mm) | Largest signed withdrawal (N) |
| --- | ---: | ---: | ---: |
| F10 with seating contact | 1000 | 25.044 | 1548.822 |
| F10 without seating contact | 1000 | 25.523 | 1550.858 |
| C6 with seating contact | 1000 | 19.434 | 1087.948 |
| C10 with seating contact | 1000 | 16.323 | 450.599 |
| F10 with seating contact | 100 | 36.342 | 879.413 |

Seating changes F10 peak withdrawal by only about 0.13% in this model. Changing
the arbitrary attachment stiffness from 1000 to 100 N/mm reduces that peak by
43.2% while increasing displacement. Neither observation establishes the
actual insert stiffness or a qualified demand. The retained timber-prism
surrogate and uncalibrated plywood constitutive assumptions also remain.

The 10000 N/mm F10 probe was rejected during cycle 00: its DAT and FRD
original-node displacement intervals disagree. Its native files and sources
are preserved; no demand result is accepted and the gate was not relaxed.
The five-sample contact refinement and lower-penalty probes were not started.
Thus three planned cases remain incomplete, the full-matrix numerical gate is
false, and contact discretization/penalty convergence is not established.
The three-sample mask discards 60 points and 48,695.894 mm² of whole tributary
area at receiver openings; this can overremove contact area and is not exact
void integration.

[Authenticated partial comparison](../fea/results/round-insert-sensitivity-v3.json)
records all five assessments, controlled input-difference checks, and the
reproduced rejection. [Archive manifest](../fea/results/round-insert-frame-v3/manifest.json)
identifies six native archives: five completed cases and the rejected probe.
Insert resistance, demand qualification and build readiness remain false.
