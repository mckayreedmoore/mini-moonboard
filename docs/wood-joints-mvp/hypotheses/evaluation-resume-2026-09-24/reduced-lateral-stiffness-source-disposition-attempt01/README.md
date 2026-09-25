# Reduced lateral stiffness source disposition

**Prepared:** 2026-09-25. **Status:** viable for a declared, source-based
service-slip sensitivity; not a current-hardware property, lower bound,
capacity, or acceptance result. This note applies to the current WJ24 ordinary
patch at revision `b1e8707d` (`led-clearance-2x6-runner-seated-blocks-v1`),
not to historical WJ04 hardware or its 6-inch bolt example.

## Disposition

EN 1995-1-1:2004+A1:2008 §7.1/Table 7.1 supplies a practical reduced lateral
slip law for timber-to-timber joints made with bolts, including bolts with or
without clearance. It gives a serviceability slip modulus per fastener per
shear plane,

```text
K_ser = ρ_m^1.5 d / 23   N/mm
```

where `ρ_m` is mean density in kg/m³ and `d` is fastener diameter in mm. If
the two wood-member mean densities differ, §7.1(2) uses their geometric mean.
The standard says to add clearance separately to deformation. This is a
usable *conditional post-seating service-slip sensitivity* for the modeled
solid-wood laps and 6.35 mm bolt axes. It requires no matched product coupon
before running that labeled sensitivity.

The expression is from the 2004+A1:2008 edition only. BSI lists
EN 1995-1-1:2025 as published on 2025-11-30; therefore this calculation must
not be described as a current Eurocode rule without checking that edition and
the applicable national provisions. It is an empirical design expression,
not a measured stiffness for this candidate or a strength equation.

## Current-patch translation

The pinned clearance witness covers the three current wood bodies
`base_rail_bottom_right`, `bottom_center_right_cleat`, and
`base_principal_center_right`, and four bolt axes across two interfaces, with
two bolts at each interface. Its nominal envelopes are a 7.50 mm receiver
bore and 6.35 mm shaft. With the shaft initially centered in both receiver
bores, each bore contributes `c = (7.50 - 6.35)/2 = 0.575 mm` radial
clearance. The resulting **one-direction relative bore-center travel from
that centered state to opposing-side contact is `c + c = 1.15 mm` per bolt**.
Thus 1.15 mm is the two-bore relative travel, not one bore's radial clearance;
the full opposite-extreme-to-opposite-extreme span would be 2.30 mm. These are
nominal CAD-envelope values, not inspected holes, delivered-part offsets, or
drilling instructions. Centering is the witness's calculation reference
position, not an observed installed-bolt condition; the 1.15 mm is travel
available from that reference before the specified opposing-side contact.

For a declared translation direction in the timber shear plane, the minimal
bilateral branch law is `q_i = 0` while `|s_i| ≤ 1.15 mm`, then
`q_i = K_ser (s_i - sign(s_i) 1.15 mm)` after that bolt's clearance is taken
up. Here `s_i` is the signed relative slip evaluated at bolt axis `i`.
`K_ser` is per physical bolt/per shear plane. If the two bolts at one
interface have the same centered clearance and both engage, their parallel
translation tangent is `2 K_ser`. For the two equal interfaces in series on
the rail–cleat–principal route, the translation-only post-seating tangent is
`K_ser` and the witness's centered N-direction free travel sums to 2.30 mm.
These equivalent slopes are checks on bookkeeping only: retain springs at
each source bolt position for rotation and unequal contact activation.

For an active-set rotational sensitivity, resolve each bolt's slip at its
actual position, `s_i = e_s · (Δu + Δθ × r_i)`, where `e_s` is the declared
slip direction and `r_i` is measured from the interface datum. The tangent
about a declared rotation axis `e_θ` is
`k_θ = Σ_active K_ser [e_s · (e_θ × r_i)]²` (N·mm/rad). This is a
conditional active-set stiffness, not a universal rotational spring. The
clearance witness omits member rotation and does not establish a rotation
free-play bound. Applying the scalar `K_ser` isotropically in both in-plane
directions would be an additional model assumption; a one-direction branch is
the narrower sensitivity.

The current material map contains a DF-L No. 2 elastic scenario but no
source-bound mean density `ρ_m` for these boards. Keep `ρ_m` explicit and vary
it if response is materially affected. The existing 460/500/520 kg/m³ values
in the ordinary-joint method are analyst sensitivity points, not measured or
grade-specific bounds. For scale only, at the declared point `ρ_m =
500 kg/m³` and `d = 6.35 mm`, `K_ser = 3.087 kN/mm` per bolt per plane. Do not
turn this point into a material claim.

## Limits on use

- Apply this as a reduced bolt-mediated lateral slip law only where it
  replaces that local bolt/bore/bearing-and-bending transfer path. Do not add
  it in parallel with explicit bolt-to-bore contact and bolt bending, which
  would double-count the same lateral mechanism. It does not replace gross
  timber-body compliance, unilateral timber-face compression/opening, or
  their separate contact paths.
- `K_ser` describes lateral service slip. It does not establish behavior
  beyond service load or any bolt, timber, washer, nut, splitting, embedment,
  or joint capacity. Do not infer resistance from `K_ser × displacement`.
- It is independent of the separate axial thread-engagement law. It supplies
  no axial, opening, friction, preload, or thread-fit restraint; physical
  axial engagement remains unresolved, and full-height nut engagement/fit
  stays a separate receiving gate.
- The 2004 Eurocode detailing clause §10.4.3(1) limits a timber bolt hole to
  1 mm over the bolt diameter. The current nominal CAD envelope is 1.15 mm
  over and sits 0.15 mm outside that clause. AWC NDS 2018 §12.1.3.2 instead
  gives a 1/32–1/16 in oversize range, which contains the nominal 1.15 mm
  difference; neither modeled dimensions nor this comparison establishes a
  delivered hole. Keep the geometry gap separate from the tangent and verify
  the governing standard before any detailing claim.
- AWC NDS 2024 `γ = 180,000 D^1.5` is a group-action `C_g` coefficient, not a
  slip spring. Do not substitute it for `K_ser`.
- The direct rail-to-principal face has its normal orthogonal to cleat
  longitudinal N, so normal-only face contact does not close this N-direction
  load path. The sensitivity does not authorize adding friction or preload.

## Source and input provenance

Primary references:

1. [EN 1995-1-1:2004+A1:2008](https://www.phd.eng.br/wp-content/uploads/2015/12/en.1995.1.1.2004.pdf), §7.1/Table 7.1 (service slip modulus, per fastener/per shear plane, clearance separately; density rule) and §10.4.3(1) (bolt-hole detailing). This is the historical edition used for the sensitivity.
2. [BSI, BS EN 1995-1-1:2025 catalogue record](https://knowledge.bsigroup.com/products/eurocode-5-design-of-timber-structures-general-rules-and-rules-for-buildings), edition publication date 2025-11-30.
3. [AWC NDS 2018 Chapter 12](https://awc.org/wp-content/uploads/2021/10/AWC_NDS2018-withCommentary_20210928_AWCWebsite_Chapter12.pdf), §12.1.3.2 (bolt-hole size).
4. [AWC 2024 NDS errata](https://web-media.awc.org/wp-content/uploads/2025/03/31134949/2024-NDS-Errata-and-Addenda-03.28.25.pdf), §11.3.6 group-action `C_g` coefficient correction.

Current input pins, relative to the repository root:

| Evidence | Path | SHA-256 |
|---|---|---|
| Candidate source inventory | `docs/wood-joints-mvp/source-inventory.json` | `07af4c3eb642cf3887595fe4415eb65404cdcf74d66c5c7bb182847ef21c2d78` |
| Current patch input inventory | `docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/ordinary-patch-inputs-attempt01/inventory.json` | `70b396e636175abcad7467dc145029d7126c1ea7dff1d053a61f8c5321e1c1d3` |
| Current patch contact classification | `docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/ordinary-patch-contact-classification-attempt01/classification.json` | `18bdf1b9736ce6ca2cf2b3dd0488a7651da05f35e531605fd465e7b502363f13` |
| Current patch material map | `docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/ordinary-patch-materials-attempt01/material-map.json` | `9e1cbc8945d33683de3cb71ba716581919f508466d8a27b181865da4cc675fd4` |
| Centered clearance witness | `docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-clearance-seating-attempt01/geometry-witness.json` | `c53577c623f11aa6688816cd2ada049762cfbb80ba0beccd3bf01540c0c783cc` |
| Canonical witness record | `geometry-witness.json:record_sha256` | `23580bd67ab56ea2c7ad02884fbd89a3fb9ad31661db0623cd726beb6c7f5a52` |

The geometry witness is translation-only and marks the model free of assigned
stiffness, force transfer, loads, friction, preload, or capacity. It reports
no native solve. No CAD, mesh, or native solver run was made for this
disposition.
