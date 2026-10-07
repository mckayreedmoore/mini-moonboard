# Thin-frame steel and washer component methods

The question is how to compare fresh, signed fitting and physical-shaft actions
against the thin candidate's steel and washer limits without borrowing a strut
assembly rating or historical joint demand. The maintained helper is
[`scripts/thin_bolted_steel_resistance.py`](../../../../../scripts/thin_bolted_steel_resistance.py).
Its [input and component report](steel-resistance-methods-v4.json) binds the
occupied v4 source, SHA-256
`8174841bf64914570397ee6d960c5602f74097e2e412e5910502811bc5b9405c`.
It preserves 36 fittings, 72 flange ports, 58 new and twelve starting physical
shafts, fourteen shared new shafts and 140 washer ends. All release and
complete-joint acceptance flags remain false.

## Material and product applicability

[Eaton's catalog](https://www-dev.eaton.com/content/dam/eaton/products/support-systems/strut-systems-%26-accessories/strut-fittings-and-accessories/strut-fittings-catalog-section.pdf),
PDF pages 0 and 5, supports the conditional general ASTM A1018 minimum
`Fy = 33 ksi = 227.527 MPa` and nominal `7/32 in` thickness, `1⅝ in` width,
`9/16 in` holes, `1⅞ in` pitch and `13/16 in` end offset. Its rated strut
assembly uses different hardware and support. Those loads and recommended
torque are not transferred to this wood connection.

The current [B103ZN SKU](https://www.eaton.com/us/en-us/skuPage.B103ZN.html)
still describes two 4.12-inch legs and ¼-inch thickness; the v4 scenario uses
the catalog's 4⅛/1⅝-inch legs and general 7/32-inch thickness. The
[B104ZN SKU](https://www.eaton.com/us/en-us/skuPage.B104ZN.html) gives conflicting
description/specification dimensions and 0.64 lb versus the catalog's 0.78 lb.
The catalog PDF text is available, but screenshot calls returned text
references without an accessible image. Neither the individual drawing's
dimension datums nor the actual bend, thickness limits or tolerances have
been visually authenticated. The helper does not reconcile these conflicts.
No catalog `Fu` is supplied.

[Bolt Depot #3051](https://boltdepot.com/Product-Details?product=3051)
supplies the fourteen small SAE washer proposals: OD 1.055–1.092 in,
ID 0.526–0.546 in and thickness 0.074–0.121 in. Resistance diagnostics use
the published minimum thickness, **1.8796 mm**, and all four OD/ID tolerance
corners. Its Grade 8, tempered medium-carbon steel and dimensional-standard
labels do not supply numeric washer yield strength. The occupied maximum
thickness, 3.0734 mm, is not used as a resistance minimum. Larger washer
dimensions remain occupied scenarios without authenticated minimum dimensions.

## Implemented comparisons and their limits

The nominal flat-leg method transforms every attachment and compression-contact
force and couple into one flange basis. Cuts include the full assumed flat leg,
all factory-hole boundaries and centers, contact/load stations and 33 samples
between successive markers. A central hole leaves two side ligaments:
`A=(b-d)t`, `Zout=(b-d)t²/6` and `Zin=t(b³-d³)/(6b)`. Axial and both bending
stress extrema are summed with a transverse-shear envelope in the same section.
The result is a sampled nominal first-yield diagnostic. Continuous extrema,
actual heel geometry, torsion, notch concentration, local instability and
complete contact/prying remain separate gaps.

For orientation only, the ideal unsupported gross flat-leg normal-force
first-yield markers at the assumed flat start are **614.625 N** for either long
beam leg, **770.020 N** for the B104 post leg and **3164.009 N** for the B103
short post leg. They are not complete angle capacities or allowable joint loads.
Wood backing and contact can change the flange's actual signed section actions.

Hole bearing and tearout use the published deformation-considered component
equations `min(2.4dtFu,1.2Lc tFu)`, reproduced in
[AISC's primary tearout research](https://www.aisc.org/globalassets/aisc/research-library/denavit-et-al.-2021---final-report---tearout---2021-07-03.pdf).
Every retained factory hole limits a signed clear ligament. The source was
available through its indexed primary extract; direct PDF access returned 403.
The [2016 primary specification](https://www.aisc.org/globalassets/aisc/publications/standards/a360-16-spec-and-commentary_march-2021_linked.pdf)
indexed extract supplies the ASD divisor 2. These are component references;
exact-product `Fu` and applicability are missing. The helper therefore reports
coefficients or required `Fu`, not a fabricated steel strength.

Block shear requires caller-supplied, authenticated gross/net shear and net
tension areas, distribution factor, `Fy` and `Fu`. The implemented J4-5 equation
and ASD divisor 2 are reproduced in the
[2025 AISC primary paper](https://ej.aisc.org/index.php/engj/article/download/1342/1333/1371),
printed page 60. No complete candidate failure path is assigned from a generic
formula. The fixture uses the independently published 207-kip LRFD example in
the [2017 primary paper](https://ej.aisc.org/index.php/engj/article/download/1117/1116),
printed page 189, only to verify arithmetic.

The bolt API combines simultaneous axial force, shear, bending and torsion at
one explicitly identified solid-circle section. It reuses the existing direct
T/V material helper and adds circular-section elastic stress envelopes. Loaded
shank/root diameter, area, property basis, actual thread occupancy and
same-section moments are mandatory inputs. A nominal diameter or point-pin
zero does not establish a physical shaft section or zero bolt bending. Nut
stripping, head/nut pull-through and thread stress concentrations remain open.

For each washer end, a linear full-annulus pressure field can carry its own
same-state `T` and two transverse moments. Both head/nut and support-face
pressures must remain nonnegative. Negative pressure requires unilateral
contact recovery. A nonzero moment never receives a combined yield index from
the separate axisymmetric axial calculation.

The axial washer calculation solves a free-edge annular plate under opposing,
prescribed uniform head/nut and support pressures. It includes the intentional
central support opening, so a smaller washer ID does not create wood or steel
inside the bore. General plate equations, free-edge conditions and moment
relations come from [MIT's primary plate handout](https://ocw.mit.edu/courses/2-080j-structural-mechanics-fall-2013/de27f1d8f647ff995771d4b8d48d34bc_MIT2_080JF13_Recitation5.pdf).
Shear is differentiated directly and checked against the pressure integral;
rounded source coefficients and OCR simplifications are not a precision oracle.
For the assumed 22.225-mm circular head/nut footprint, the worst small-washer
corner requires **0.103326 MPa of bending yield strength per N of axial force**.
The smaller 19.05-mm circle raises this to **0.158982 MPa/N**. The report also
includes an 18.6944-mm circle sensitivity, based only on the minimum AF of
the [unselected #2586 nut comparison](https://boltdepot.com/Product-Details?product=2586).
The [#397](https://boltdepot.com/Product-Details?product=397) and
[#401](https://boltdepot.com/Product-Details?product=401) bolt comparisons have
¾-inch AF heads. None of these AF dimensions authenticates a circular bearing
patch: head/nut chamfers, hex loading and the minimum bearing-face circle
remain required inputs. The larger frozen proxy footprint is not transferred
to a smaller actual product.
This is a prescribed-pressure diagnostic. Thickness/radial-width is about
0.27, actual bearing circles/chamfers and non-axisymmetric end moments remain
unverified, and the model excludes contact compliance, local 3D stresses,
preload and nonlinear response. It establishes no actual washer capacity.

The two small wood-face washers have a **391.039-lbf** full-annulus perpendicular
wood-bearing reference using minimum OD and the larger washer/bore opening.
This reuses the project's 625-psi DF-L No. 2 reference. It does not replace
actual grain-angle, contact-pressure, splitting or complete-joint checks.

## Finite fitting compliance

`fitting_condensed_stiffness` reuses the frame helper's 3D Timoshenko beam and
rectangular-torsion primitives. Two centroid-strip legs meet at the nominal
heel; that internal six-DOF node is condensed to twelve global DOFs at the two
actual wood-face flange holes. Exact small-motion offsets connect each hole
to the steel centroid. Generic `E=200000 MPa, nu=0.3` is a response scenario.
Gross section and full-leg net-side-ligament section are alternative
sensitivities. Actual curved-heel and localized-hole flexibility is unresolved,
so these are not guaranteed physical upper/lower bounds.

With a 100-N beam-port force along the post axis and the post port fixed, the
B104 gross/net scenarios give **0.520171/0.795556 mm** displacement; B103 gives
**0.252909/0.386802 mm**. An independent Castigliano calculation matches within
2×10⁻¹² relative error. Six rigid motions, matrix reciprocity and net-section
softening are checked. This steel component adds no bolt friction or shaft-axis
rotation constraint. The frame producer must freeze and bind its own primitive
and the chosen stiffness scenario before its demands are consumed.

## Reproduction and current consumer boundary

The eighteen focused fixtures check same-section arithmetic, all retained-hole
ligaments, published block-shear arithmetic, pressure admissibility, the existing
clamped-annulus benchmark, independent radial-equilibrium shooting, zero
bending under identical opposing pressures, tolerance/census gates, flange
datum ownership, and finite-angle compliance. The direct Python environment
uses the existing lockfile; `uv`'s default cache is read-only in this sandbox.

```sh
.venv/bin/python -m pytest -q tests/test_thin_bolted_steel_resistance.py
.venv/bin/ruff check scripts/thin_bolted_steel_resistance.py tests/test_thin_bolted_steel_resistance.py
.venv/bin/python -m scripts.thin_bolted_steel_resistance
```

The output refuses overwrite. For a distinct fresh-demand report, use
`--demands SOURCE --out NEW_OUTPUT`. The source must authenticate this candidate
and occupied v4 hash and contain `attachment_actions` and
`flange_contact_actions`. Consume **one source-bound parameter state per file**:
its top-level case, accessory placement and stiffness/clearance/section
parameters must describe every included action. Validate this contract before
calling the frozen producer. The consumer separates case/accessory identities
and rejects duplicate case/flange actions; do not merge partial action sets
from different parameter scenarios. Each action belongs to its actual flange hole datum;
an opposite plate cannot use the common shared-shaft origin without transporting
the wrench. Unequal B104/B103 forces are not split equally. Point-pin moment
zeros remain idealized method values. Statically feasible force allocation is
not a unique compatible physical demand field.

The helper, focused fixtures and component report stay active. No raw run,
native solve, geometry revision, archive, pruning or hardware purchase occurred.
The fitting identity/tolerances, `Fu`, washer/bolt property and thread-section
bases, actual end moments, contact/prying and complete failure paths remain the
exact inputs needed for complete hardware acceptance.

The larger-washer reuse audit found no applicable saved plate coefficients for
the 126 remaining ends. The existing
[ordinary-end inventory](../../mvp-resume-2026-10-01/upper-corner-screw-layout/washer-top-side-fine-reference.md)
records Bolt Depot 15025 and 15023 profiles as mismatches with the earlier
quarter-inch, 5/16-inch and retail-fender plate recipes. Their published minimum
dimensions also differ from this candidate's occupied maximum envelopes.
Reuse the analytical method and the frozen small-washer unit responses within
their stated inputs; do not transfer earlier washer forces or passes. Fresh
frame demand comparisons can call `compare_flange_actions` directly and bind
this issued report without recomputing unchanged unit responses.

The separate [fresh-state consumer](../../../../../scripts/thin_bolted_steel_demands.py)
implements this reuse path. Its twenty-three focused fixtures passed: they
reject unconverged or numerically regularized physical fields, residuals outside
the bounded producer criterion, altered parameter identities, mixed action states,
missing/duplicate ports or contacts, and nonfinite vectors. It requires all 72
candidate flange actions and all 288 flange corner contacts, including zeros,
in one state. The producer must declare a generalized residual criterion no
larger than `1e-5 N`; the consumer also checks all 62 stored body and global
force/moment closure vectors under declared criteria no larger than `1e-4 N`
and `0.1 N·mm`. Generalized rotational coordinates use a 1000-mm scale, so
`1e-5 N` in such a coordinate corresponds to `0.01 N·mm` before these separate
physical wrench checks. Before comparing steel actions, it also invokes and
source-binds the independent
[JSON equilibrium/contact audit](../../../../../scripts/thin_bolted_equilibrium_audit.py),
which reconstructs the signed source loads and body/global wrenches and
authenticates the complete contact/body census without CAD or a solve. Its
input validity checks do not prove unique demand, mesh refinement or physical
product applicability.

For the 14 small-washer proposal ends, all on single-attachment shafts, the
consumer reuses the issued unit coefficients at the same fresh axial action.
It records the signed receiver-force projection on the flange inward axis,
the opening restraint and any closing component separately. Required washer
`Fy` is shown for the opening-component reference and the absolute-projection
diagnostic under each of the three assumed circular bearing footprints;
neither establishes actual bolt tension or a delivered bearing circle. A
closing shaft force retains the unresolved capture/bilateral-spring-artifact
flag. Only the two wood-side ends receive a full-annulus wood-bearing
reference. Actual own-end moments remain unknown, combined washer indices
remain null, and no zero moment is credited.

The first issued
[A12-rear steel comparison](steel-demands-a12-rear-v4.json) remains a **failed
support-geometry experiment**, not a candidate demand or capacity check. Its
source state credited four raw leg-foot corners that are absent after the
38.1-mm runner recess, including about 2057.728 N on the left and 501.157 N on
the right. Independent body/global arithmetic closes that declared model but
does not authenticate those support regions. Preserve the source state,
arithmetic receipt and comparison bytes. The 72 nominal flange diagnostics
had maximum sampled first-yield index 0.556839; the 14 small-washer axial
diagnostics had maximum opening component 204.631 N and required `Fy`
33.8346/32.5327/21.1436 MPa under the three assumed circle scenarios. These
numbers belong only to that raw-footprint experiment. A separately pinned
finished-footprint state and independently authenticated floor support gate
are required before the next candidate demand comparison. The frozen method
and unit coefficients remain reusable within their inputs.

The distinct [cap-head face reference](cap-head-face-reference-v4.json) changes
only the assumed circular bearing diameter to **17.145 mm** for the 12 small
steel-supported head washers. ASME B18.2.1-2012 section 4.3 specifies a washer
face diameter with a minus-10-percent tolerance from maximum head width; for
the half-inch cap-screw scenario, 0.750 in × 0.9 gives this diameter. Its gaging
plane is 0.004 in toward the head from the bearing plane. This standard
dimension does not authenticate the actual pressure footprint. Table 10 permits
an underhead fillet diameter up to 13.97 mm, above the small washer's entire
13.3604–13.8684-mm ID envelope; actual fillet/chamfer/seating needs reconciliation.
[ASME standard, manufacturer-hosted copy](https://www.wanhong-fastener.com/wp-content/uploads/2025/04/ASME-B18.2.1-2012.pdf)

The reused plate method gives a worst four-corner unit coefficient
**0.1934005321 MPa/N** at the published minimum 1.8796-mm washer thickness.
The [separate producer](../../../../../scripts/thin_bolted_cap_head_reference.py)
and its 10.6-kB report preserve this changed input without repeating the prior
three circle scenarios. No nut-face dimension, actual bolt tension, numeric
washer yield, own-end moment or complete washer capacity follows from it.

The separately issued
[finished-floor A12-rear comparison](steel-demands-a12-rear-finished-floor-v4.json)
binds corrected source state `thin-v4-84ad844f63afddc032cf922c` and the
independent finished-support gate. All eight finished face proofs and the
numerical body/global closure pass that gate. The 72 nominal flange
diagnostics have maximum sampled yield index **0.5388935** (122.6128 MPa at
the 33-ksi scenario), at the B104 base-left beam flange. The largest required
`Fu` for the bearing/tearout component reference is **7.796513 MPa**, not an
authenticated fitting strength. The 14 small-washer references have maximum
opening component **186.860 N** and no closing component. Required `Fy`
maxima are 30.8963/29.7074/19.3074 MPa under the three assumed circle
diagnostics; the **head-only** 17.145-mm scenario gives **1.443686 MPa** at
7.464749 N. The two wood-side small-washer annulus references reach 0.107426.
Nut bearing footprints, actual washer yield/seating, own-end moments/prying,
physical common-shaft behavior and first-order geometric applicability remain
unqualified. This one case does not establish candidate or complete-joint
capacity; all release flags remain false.

The [finished-floor writer](../../../../../scripts/thin_bolted_finished_floor_steel.py)
and issued comparison stay frozen. Its three focused fixtures passed. Review
identified that its support and component steps read the source separately;
the issued source hash and state were independently confirmed to match the
audited corrected field. The separate
[input-binding adapter](../../../../../scripts/thin_bolted_finished_floor_steel_bound.py)
guards future cases with input hashes before/after, the component report's
source pin and the initially audited state identity. Three new mutation
fixtures passed; no unchanged force comparison was repeated. Use the adapter
for later independently gated states. Its aggregation mode collects governing
summaries from issued state reports without merging or superposing their
actions.

The separate
[common-shaft consumer](../../../../../scripts/thin_bolted_common_shaft_steel.py)
accepts the new 132-body schema only through its independently source-bound
support, load and equilibrium gate. Its 308 physical radial actions and 140
own end captures replace the old paired wood/fitting arrows. Each of the 72
steel ports is independently reduced to a signed force and full free moment
at its frozen entry datum; no equal sharing or opposite-host force is inferred.
The frozen flange API admits these free moments. Its flat-strip stress envelope
omits torsion, so an affected row is explicitly an incomplete yield comparison.
The own washer references use each capture's unilateral axial force, including
separate head and nut forces on a shared shaft. The 17.145-mm circle remains
head-only. Actual washer pressure, own-end moment/prying, material yield and
head/fillet/nut seating remain unresolved.

The consumer independently replays every exported shaft cut from the physical
point forces, free couples and all own metal-role gravity points, including
head gravity outside the nominal under-head beam interval. It authenticates
the shaft axis, basis, pressure-face/tip span, mesh and elastic diameter, and
requires every uniform, mesh and both-sides-of-load sample. Simultaneous
`N, V1, V2, T, M1, M2` enter the existing circular-section stress envelope;
uncorrected element `Kq` actions do not enter that comparison. Caller-supplied
root/body circle sensitivities require an explicit diameter and geometric basis.
No delivered thread-root diameter or tensile-area-equivalent root is assigned.

The separate **conforming SAE J429 Grade 5 scenario** uses minimum tensile
yield 92,000 psi (634.3177 MPa) for the quarter-to-one-inch range. The same
primary vendor table lists 120,000-psi minimum tensile strength and 85,000-psi
proof strength; these are distinct properties. This conditional yield input
is neither delivered-product qualification nor NDS bolt bending yield `Fyb`.
[Fastenal fastener reference guide, inch-series Grade 5 row](https://www.fastenal.com/content/merch_rules/images/fcom/content-library/Fastener%20Reference%20Guide.pdf)

Twenty-seven new known-answer and rejection fixtures passed, covering signed
wrench transport, unequal shared sides, each own washer capture, simultaneous
circular-section stresses, preserved flange torsion and independent cut replay.
No prior unit coefficient, CAD query or coupled solve was repeated. The new
consumer awaits a separately accepted physical common-shaft state; its method
fixtures do not establish candidate capacity. All release flags remain false.

The [frozen common-shaft method receipt](common-shaft-steel-method-v4.json)
preserves those 27 fixtures and the reviewed component helper. Subsequent
review found that its pinned audit compared the producer's complete own-end
geometry dictionary with a head/nut string. That original gate cannot admit
the actual producer export. The separate
[export audit](../../../../../scripts/thin_bolted_common_shaft_export_audit.py)
authenticates the complete dictionary, then adapts only the checked label on
a copy for the preserved arithmetic audit. The new
[consumption adapter](../../../../../scripts/thin_bolted_common_shaft_steel_bound.py)
uses this corrected gate and reuses every frozen wrench, cut, washer and stress
method. Twelve focused adapter fixtures pass, including dictionary preservation,
state/gate/caller-input mutation rejection, and admitted state/case/accessory
labels on every aggregate, shaft-cut row and nested cut. The raw physical
action tables used by component methods remain unchanged. The driver already
exports these labels; this guard changes no mechanics.

The separate [flange torsion extension](../../../../../scripts/thin_bolted_flange_torsion.py)
adds the omitted uniform-torsion stress to each simultaneous nominal section
action. It preserves the original reports and uses the exact rectangular
Saint-Venant torsion constant, rather than a polar second moment. Its positive
odd-integer series has an explicit tail upper bound; subtracting that upper
sum gives a conservative lower bound for `J`. The exact series is recorded in
[author-hosted primary research, equation 3](https://zhaolab.stanford.edu/sites/g/files/sbiybj21256/files/media/file/part-ii.pdf).
The governing stress-function relations and freely warping, long-prismatic
assumptions follow [MIT Unit 10, pages 5–6 and 13–21](https://ocw.mit.edu/courses/16-20-structural-mechanics-fall-2002/e888339011c834eb2a02bd365fa25052_unit10.pdf).

For a rectangle with long side `b`, short side `t`, coordinates `y,z`, and
twist rate `θ′`, the conventional single Prandtl series is

`φ = 8 G θ′ t²/π³ Σodd (-1)^((n−1)/2) cos(nπz/t) (1−Cₙ)/n³`,

where `Cₙ = cosh(nπy/t)/cosh(nπb/(2t))`. This is the isotropic specialization
of [Wang 2024, equation 7](https://pmc.ncbi.nlm.nih.gov/articles/PMC11467641/).
The equation was available in the primary search excerpt; the full-page
browser request encountered an access challenge. Differentiating gives each
shear-vector harmonic a coefficient `8 |Gθ′| t/(π²n²)` multiplied by
`[-sin(nπz/t)(1−Cₙ), cos(nπz/t)Sₙ]`, with
`Sₙ = sinh(nπy/t)/cosh(nπb/(2t))`. Since `0 ≤ Cₙ ≤ 1` and `|Sₙ| ≤ Cₙ`,
that vector factor has norm at most one. Absolute convergence and
`Σodd 1/n² = π²/8` therefore prove the pointwise ideal-field bound
`|τT| ≤ |Gθ′|t = |T|t/J ≤ |T|t/Jlower`.

The existing simultaneous axial/bending bound `σmax` and rectangular transverse
shear bound `τVmax = 1.5 sqrt(V1²+V2²)/A` then give
`VM ≤ sqrt(σmax² + 3(τVmax + τTbound)²)` at every point in that declared
section field. This triangle bound does not claim that separate component
maxima occur at one point. At 41.275 × 5.55625 mm, `J` is bracketed by
**2159.77059869–2159.77059879 mm⁴**, and the gross torsional shear bound is
**0.00257261119 MPa per N·mm**. Eighteen new fixtures pass: independent published
square/rectangular benchmarks, the thin-rectangle limit, scaling, tail brackets,
a 96 × 96 Gauss torque integral, free-surface stresses and simultaneous actions.
[Published rectangular benchmarks, table 1](https://www.iieta.org/node/2622),
[independent 2 × 0.5-mm benchmark, supplementary page 1](https://zhaolab.stanford.edu/sites/g/files/sbiybj21256/files/media/file/supplementary_material_jam-22-1117.pdf)

At a factory-hole station, the gross calculation explicitly fills the opening.
The separate proxy divides the remaining section into two independent equal
rectangles at equal twist, retaining the frozen nominal net-section normal and
transverse shear fields. At the maximum 14.2875-mm removed chord, this proxy
gives **0.00486106238 MPa per N·mm**; its sharing is an assumption, not a bound
on the actual connected holed plate. The formed angle's hole/heel concentrations,
short-leg warping restraint, bimoment and open-angle load introduction remain
unqualified. Short connection warping can add normal stresses; the gross
Saint-Venant proof does not cover those stresses.
[Primary short-connection discussion, pages 63–65](https://ej.aisc.org/index.php/engj/article/download/1147/1146)
The extension closes the six-action ideal gross-rectangle method omission,
not the actual fitting-strength gate. It changes no washer property, geometry
or release flag and performs no whole-frame solve. The
[frozen torsion method receipt](flange-torsion-method-v4.json) binds the helper,
18 fixtures, exact unit coefficients and proof. Independent review verified
the primary equations, torque integral and stress bound and found no blocker
within this declared scope. MIT's opposite stress-function sign convention
leaves the torsional constant and stress-norm proof unchanged.

```sh
.venv/bin/python -m scripts.thin_bolted_steel_demands --demands SOURCE --out NEW_OUTPUT
.venv/bin/python -m scripts.thin_bolted_cap_head_reference
.venv/bin/python -m scripts.thin_bolted_finished_floor_steel_bound --demands SOURCE --out NEW_OUTPUT
.venv/bin/python -m scripts.thin_bolted_finished_floor_steel_bound --aggregate STATE_REPORTS --out NEW_SUMMARY
.venv/bin/python -m scripts.thin_bolted_common_shaft_steel_bound --demands PHYSICAL_SHAFT_STATE --out NEW_OUTPUT
OPENBLAS_NUM_THREADS=1 .venv/bin/pytest -q tests/test_thin_bolted_common_shaft_steel.py
.venv/bin/python -m scripts.thin_bolted_flange_torsion --method-report --out NEW_METHOD_OUTPUT
.venv/bin/python -m scripts.thin_bolted_flange_torsion --components ACCEPTED_COMPONENT_REPORT --out NEW_TORSION_OUTPUT
```
