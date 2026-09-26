# Current WJ24 four-bolt patch: Unified thread-coupling disposition

**Prepared:** 2026-09-25. **Status:** conditional class-fit calculation and
source audit; no physical thread-pair stiffness bound, hardware selection, or
capacity result. This note is for the current ordinary patch
`bottom_center_right_cleat / base_rail_bottom_right /
base_principal_center_right`. It does not use WJ04 as the current target.

## Result

The current four-bolt patch has four modeled **unthreaded 6.35 mm shaft
envelopes**, each 152.4 mm from underhead to tip with 127.0 mm nominal wood
grip. The geometry inventory contains four separate modeled nuts, but they
are solid display envelopes with no bore wall; the frozen contact manifest
intentionally emits no nut-bore/thread pair or bolt/nut engagement card. The
geometry therefore identifies neither a thread form nor a contact law.

The current ordinary hardware schedule has a **candidate** `1/4-20 UNC-2A`
bolt / `UNC-2B` nut family, not a selected or received pair. If that candidate
is conditionally assumed, two narrow results can be calculated from primary
sources:

* For an ideal 60-degree 2A/2B profile with zero lead/profile error and fixed
  relative rotation, the historical NBS H28 class endpoints imply a total
  axial flank-reversal comparator of **0.01613–0.14224 mm**. This does not
  determine which flank is initially seated or the one-direction free travel
  from an arbitrary initial phase.
* Matsubara and Teranishi's timber bolt model gives an equivalent bolt-side
  threaded-length component of **760.709 kN/mm** (1.31456 μm/kN at the generic
  200 GPa reference). Their equation is one term in bolt-body compliance in
  series; it is not a bolt-to-nut thread-contact law. It must not be reused as
  a connector between the current explicit bolt and nut bodies.

The closest primary source for a physical reduced thread-pair law is Lu et
al. (2019): a local thread-tooth bending/shear/radial compliance model with
axial load distribution. Its published closed-form profile substitutions
are for ISO metric threads. Its own FE sweeps include M6×1, M8×1.25 and
M10×1.5, but its experimental comparison reuses tensile data from Zhang et
al. (2016), whose tested pairs are M36 metric threads. Neither the FE
examples nor the M36 experiments are Unified 1/4-20 validation. The paper
reports its calculated stiffness values above the cited measured values and
supplies no error interval that could conservatively bound this WJ24 thread
family.
Therefore the accessible primary record does **not** justify a finite
physical tangent range for current Unified bolt/nut engagement. That is the
precise remaining model gap; it does not create a universal requirement for
a product-matched coupon before any diagnostic response calculation.

## What the four current stacks actually show

The frozen geometry input is
[`ordinary-patch-inputs-attempt01/inventory.json`](../ordinary-patch-inputs-attempt01/inventory.json),
SHA-256 `70b396e636175abcad7467dc145029d7126c1ea7dff1d053a61f8c5321e1c1d3`.
It identifies these four physical bolt axes:

| Axis | Shaft envelope | Modeled nut interval from underhead |
|---|---:|---:|
| `bottom_center/clip_horizontal_bottom_right_1/rail_1` | 6.35 mm × 152.4 mm | 131.064–136.8044 mm |
| `bottom_center/clip_horizontal_bottom_right_1/rail_2` | 6.35 mm × 152.4 mm | 131.064–136.8044 mm |
| `bottom_center/clip_horizontal_bottom_right_1/principal_1` | 6.35 mm × 152.4 mm | 131.064–136.8044 mm |
| `bottom_center/clip_horizontal_bottom_right_1/principal_2` | 6.35 mm × 152.4 mm | 131.064–136.8044 mm |

The bolt, nut, and two washers per axis are distinct analysis bodies. The
contact-deck manifest pin is
[`ordinary-patch-contact-deck-attempt01/contact-manifest.json`](../ordinary-patch-contact-deck-attempt01/contact-manifest.json),
SHA-256 `50f7d8c9b85197f43732d49d13e75240fa6d5423673d28274e278829878a594d`.
It records four intentional nut-bore omissions, 35 geometric contact pairs,
zero engagement/tie cards, and a “solid cylindrical display envelope; no
modeled internal bore wall” for each nut. Thus the body mesh can carry steel
body deformation where modeled, but it has no thread surface or physical
bolt/nut axial connection to transmit force. A whole-body rigid tie would
invent that transfer.

The current hardware-coverage record maps these exact four axes to family
`candidate_ordinary_48`: 1/4-20 × 6 in Grade 5 K.L. Jack `25C600HCS5Z` and
`25CNFH5Z` are catalog leads, with 2A/2B class listings; no item/lot is
selected. The 6.35 mm CAD cylinder itself is only an unthreaded occupancy
envelope. A 1/4-20 scenario is consequently conditional on declaring that
thread family; the drawing does not prove it.

For scale, the modeled nut's gross axial thickness is 5.7404 mm, or 4.52
nominal 1/4-20 pitches. K.L. Jack's listed “3/4 in thread length” is 19.05
mm. If it is provisionally placed as a full-form start reference measured
back from the 152.4 mm bolt tip, that reference is at 133.35 mm from the
underhead datum. Its overlap with the *gross modeled nut envelope* would be
only `136.8044 − 133.35 = 3.4544 mm` (2.72 pitches), leaving 2.2860 mm of the
gross nut envelope before that reference. This arithmetic is a warning about
what must be resolved, **not** a fit verdict: the catalog/reference thread
length is not an item-specific tolerance on first full-form thread, and the
nut's active internal thread interval excludes unknown entry/exit chamfers.
The current hardware note requires matched functional engagement evidence;
it does not treat catalog length or this intersection as proof of a pass or
failure.

## Conditional clearance calculation

Assume only for this comparator a matched 1/4-20 UNC Class 2A external and
Class 2B internal thread. NBS Handbook H28 (1969), Part I lists pitch-diameter
limits `d2 = 0.2127–0.2164 in` and `D2 = 0.2175–0.2224 in`. Its Section 9
relates ideal Unified 60-degree functional diameter change to axial pitch
error by `ΔE = 1.7321 Δp`. Inverting the ideal flank geometry gives
`b = (D2 − d2) / 1.7321`, or `b = 0.0161307–0.1422435 mm`. This is the **full
reversal band between opposite flank contact states**, with rotation fixed,
at least one full-form engaged turn, zero lead/angle/profile errors, and no
coating outside the class dimensions. It is not measured WJ24 initial
clearance. For an unknown no-preload phase, travel to the first flank in one
direction can be anywhere from zero to the full band. If rotation is not
restrained, `Δz = p Δθ/(2π)` with `p = 1.27 mm/rev`; class fit alone then does
not bound axial movement.

The values are a historical reference-limit scenario until checked against
the numeric tables in current ASME B1.1-2024. The public ASME record confirms
the standard governs Unified thread forms, series, classes, allowances and
tolerances, but its freely visible preview does not publish those table
values. The existing
[current thread-fit note](../../../current-thread-fit-travel.md) contains
the same comparator and its full assumptions; this artifact binds it to the
actual four-stack current patch geometry.

## Why the existing `K_th` number is not thread coupling

Matsubara and Teranishi (2022), Eq. 4, define bolt stiffness by a series
partition:

```text
1/K_b = 1/K_th + 1/K_s + 1/K_cyl + 1/K_hd
K_th  = A_s E_b / L_th
L_th  = 0.85 d
```

With the current conditional nominal geometry `d = 6.35 mm`, 1/4-20 stress
area `A_s = 20.5296315 mm²`, and the project's generic steel reference
`E_b = 200,000 N/mm²` from the
[generic elastic-material scenario](../../steel-elastic-material-scenario.md),
this gives `K_th = 760,708.9 N/mm` and
`C_th = 1/K_th = 0.00131456 mm/kN`. The calculation is reproducible in the
[prior scenario record](../../current-engagement-analytical-attempt01/calculation.json),
SHA-256 `80f73199d77e7d6147d6e4d8a74018c151a45a89070882c6c888a5440d0b44eb`.

The source places `K_th` **inside the bolt's own serial extension model**;
`A_s E_b/L_th` is the effective axial extension stiffness assigned to the
bolt threaded length. It does not include a stiffness law for opposing nut
teeth, flank contact, 2A/2B fit, or thread load sharing. The published tests
compare total timber-joint tightening stiffness and do not isolate this term
or validate it at Unified 1/4-20. The prior nominal calculation can remain a
named bolt-side response sensitivity. It cannot be attached between the bolt
and nut generalized coordinates and called the engagement tangent while the
bolt body is also elastic: that changes the component boundary and double
counts or misplaces the bolt compliance.

## Smallest reduced physical law worth pursuing

Lu et al. (2019), Eqs. 1–58, is the closest primary-source path that treats
the threaded pair locally. It adds thread-tooth bending, shear, root
inclination/root shear, and radial deformation, then computes the axial
thread-load distribution. One relation defines the local axial stiffness per
unit engagement length as

```text
k_u(x) = 1 / ((δ_b1(x) + δ_n1(x)) sin β)
```

where the bolt/nut tooth deformations `δ_b1` and `δ_n1` are profile- and
material-dependent, `β` is the helix angle, and the integrated distribution
gives the connection tangent. The derivation explicitly includes the bolt
and nut axial member areas/moduli in its force-distribution equation. That
provides a viable *reduced* architecture without a whole helical mesh:
distributed local thread springs between the two elastic body meshes, so
bolt/nut body strain stays in their solid bodies; or a condensed threaded
subassembly whose internal body compliance is removed from those bodies.
It avoids both a whole-joint tie and adding a bolt-only `K_th` spring.

This is not ready for a numeric WJ24 coefficient. Lu et al. explicitly
derive their numerical substitutions for ISO thread-profile ratios, use
M6×1.0, M8×1.25 and M10×1.5 in FE sweeps, and compare the model against
published M36 metric tensile tests; their calculated values are above those
measurements. A source-backed Unified adaptation would
need the actual B1.1 profile/root/crest geometry in the article's general
beam variables, not a silent substitution of its ISO constants. It would
also need a declared material pair, thread friction assumption/range, full
form overlap and fit/phase, and a justified model-error range. The current
candidate provides a possible 1/4-20 class pair but not a received matched
geometry, thread boundary, nut active-thread interval, or friction state.

The simple nominal ratios show why the published comparisons do not bound
the current pair. Conditional 1/4-20 has `D/P = 6.35/1.27 = 5.0`. Lu's own
FE examples are M6×1.0 (`D/P = 6.0`), M8×1.25 (`6.4`) and M10×1.5 (`6.67`);
its reused tensile experiments are M36×4 (`9.0`). The gross modeled nut
ratio is `5.7404/6.35 = 0.904`; the illustrative K.L. Jack catalog-reference
overlap is only `3.4544/6.35 = 0.544`. Lu's FE cases use active-length ratios
`L/D = 1.017`, `0.813` and `0.900`; its main M36×4-20 test has
`L/D = 20/36 = 0.556`. The modeled gross-nut ratio lies in the FE range, but
current full-form overlap is unmeasured and may be near the shorter
illustrative value. Size ratio, thread profile, material, friction, and actual
overlap remain outside a demonstrated Unified validation/error envelope.
Ratio similarity alone is not an error bound.

This does **not** require a same-product test for every response calculation.
A published dataset or a validated general profile model applicable to a
standard-defined Unified pair can support a conditional law. The current
accessible papers do not supply that applicability/error bound. A
product-matched local compliance test is one way to close it if no applicable
published/model route becomes available, not a universal gate.

## Disposition and exact missing facts

For this current patch, keep physical axial thread transfer
`UNRESOLVED_AXIAL_ENGAGEMENT`. A class-fit gap comparator can be used only as
a named sensitivity. The 760.709 kN/mm value can be used only as the existing
bolt-side equivalent-extension sensitivity. Neither is a physical
bolt-to-nut tangent, conservative bound, capacity, or proof that every one of
the four stacks engages.

To form a finite reduced thread-pair law without a full helical mesh, the
minimum inputs are:

1. A declared thread family/class for this scenario and primary profile data
   for both the Unified external and internal forms. A current standard limit
   set is needed for a current-standards claim; a product/lot need not be
   selected for a clearly conditional scenario.
2. Functional full-form overlap boundaries for bolt and nut after runout and
   chamfers, for each actual stack, plus initial thread phase or a bounded
   phase variable. The listed 0.75 in `LT` reference is not that boundary.
3. A selected load branch and relative-rotation condition; if rotation is
   free, preserve the helix kinematics instead of capping translation at the
   pitch-diameter reversal band.
4. A Unified-profile tooth law whose validation covers the relevant size,
   engagement ratio, material/friction assumptions, and elastic load range,
   with an error interval or other defensible applicability bound.
5. The exact connector/body boundary. For a distributed law, keep axial bolt
   and nut body strains in the explicit steel solids and put only local tooth
   compliance in the distributed springs. For a condensed connector, remove
   the compliance of body segments that the connector replaces.

Until those are supplied, a tighter number would be an analyst-selected
spring or an unverified model transfer. No capacity is inferred from either
stiffness calculation; stripping, proof, shear, pullout and complete-joint
resistance require separate source-backed strength checks and actual
engagement.

## Sources and frozen input pins

Primary sources:

1. National Bureau of Standards, [Handbook 28 (1969), Part I](https://nvlpubs.nist.gov/nistpubs/Legacy/hb/nbshandbook28-1969p1.pdf),
   §§ 6 and 9: Unified 2A/2B class dimensions and 60-degree functional-diameter
   / lead-error relation. The existing local calculation records the exact
   table endpoints used.
2. National Bureau of Standards, [Handbook 28 Supplement (1963), Part I](https://nvlpubs.nist.gov/nistpubs/Legacy/hb/nbshandbook28supp1963.pdf):
   nominal Unified tensile stress-area equation used for `A_s`; it does not
   prescribe this elastic equivalent spring.
3. [ASME B1.1-2024, Unified Inch Screw Threads](https://www.asme.org/codes-standards/find-codes-standards/b1-1-unified-inch-screw-threads-un-unr-thread-form):
   current thread-form, series, class and dimensional standard record; no
   compliance law.
4. Matsubara and Teranishi, [“Evaluation of elastic stiffness in bolted
   timber joints for applying turn-of-nut method”](https://link.springer.com/article/10.1186/s10086-022-02038-1),
   *Journal of Wood Science* 68 (2022), Eqs. 4–10 and test scope: supports a
   serial bolt-extension/washer-embedment method, not an isolated Unified
   bolt/nut interface law.
5. Lu et al., [“Stiffness Calculation Model of Thread Connection Considering
   Friction Factors”](https://onlinelibrary.wiley.com/doi/10.1155/2019/8424283),
   *Mathematical Problems in Engineering* (2019), Eqs. 1–58 and §§ 3–5: local
   ISO thread-tooth compliance, FE sweeps at M6/M8/M10, and model comparison
   against M36 tensile tests with model values above the measurements.
6. Zhang, Gao and Xu, [“A new computational method for threaded connection
   stiffness”](https://journals.sagepub.com/doi/10.1177/1687814016682653),
   *Advances in Mechanical Engineering* 8 (2016): primary experimental source
   reused by Lu et al.; its tensile specimens are M36 metric thread pairs, not
   1/4-20. The profile equations are stated for ISO metric threads.
7. K.L. Jack [25C600HCS5Z bolt](https://www.kljack.com/products/25c600hcs5z/)
   and [25CNFH5Z nut](https://www.kljack.com/products/25cnfh5z/) catalog leads,
   as recorded in the project sourcing follow-up; leads only, not selected or
   received hardware. ASME [B18.2.1-2012 (R2021)](https://www.asme.org/codes-standards/find-codes-standards/b18-2-1-square-hex-heavy-hex-askew-head-bolts-hex-heavy-hex-hex-flange-lobed-head-lag-screws)
   defines the `LT` thread length as a calculation reference, not a delivered
   start-position tolerance.

Frozen local inputs used here:

| Input | SHA-256 |
|---|---|
| Four-bolt geometry inventory | `70b396e636175abcad7467dc145029d7126c1ea7dff1d053a61f8c5321e1c1d3` |
| Ordinary patch contact manifest | `50f7d8c9b85197f43732d49d13e75240fa6d5423673d28274e278829878a594d` |
| Current WJ24 hardware coverage JSON | `011dcf33c8a99d5072623db06388ffc0e409c8824be15015e68b454c31e7305d` |
| Current ordinary hardware basis | `72ffabef1e449234622f4682eaefcde787abc1b56fbe8814b1e843d1581d1ecc` |
| Current hardware sourcing follow-up | `7a82ef19662c76b07902dc44f320c379382c2dd0142b726a707880587a7f8033` |
| Conditional thread-fit calculation | `206ff1dae7d83b739d5af909e27309b2d8e2f1dda399c190f07a4def9898c43b` |
| Prior bolt-side tangent calculation | `80f73199d77e7d6147d6e4d8a74018c151a45a89070882c6c888a5440d0b44eb` |

No CAD, current model input, native result, or solver configuration was
modified or run for this disposition.
