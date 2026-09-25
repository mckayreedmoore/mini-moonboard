# Independent review: reduced lateral stiffness source disposition

**Reviewed:** 2026-09-25. **Disposition:** supports a narrowly labeled
conditional service-slip sensitivity. No material correction is needed.

## Pins reviewed

- Source note: `README.md`, SHA-256
  `97e710dd3ed6745847ac35135d1b1bda52798f1296239325cdfe35dd207e8823`.
- Candidate source inventory: SHA-256
  `07af4c3eb642cf3887595fe4415eb65404cdcf74d66c5c7bb182847ef21c2d78`.
- Ordinary-patch inventory: SHA-256
  `70b396e636175abcad7467dc145029d7126c1ea7dff1d053a61f8c5321e1c1d3`.
- Contact classification: SHA-256
  `18bdf1b9736ce6ca2cf2b3dd0488a7651da05f35e531605fd465e7b502363f13`.
- Current material map: SHA-256
  `9e1cbc8945d33683de3cb71ba716581919f508466d8a27b181865da4cc675fd4`.
- Centered clearance witness: SHA-256
  `c53577c623f11aa6688816c2ada049762cfbb80ba0beccd3bf01540c0c783cc`;
  record SHA-256 `23580bd67ab56ea2c7ad02884fbd89a3fb9ad31661db0623cd726beb6c7f5a52`.

## Findings

The quoted historical EC5 equation and its scope are correct: EN 1995-1-1:2004+A1:2008 §7.1/Table 7.1 gives `K_ser = ρ_m^1.5 d / 23` in N/mm, per fastener per shear plane under service load, and expressly lists “bolts with or without clearance.” It defines `ρ_m` as mean density in kg/m³ and `d` in mm, prescribes the geometric mean where the two joined wood members have different mean densities, and says clearance is added separately to deformation. The table does not give a lower diameter cutoff that excludes a 6.35 mm bolt; that diameter remains a declared model input, not proof of a conforming delivered bolt or hole. The linked BSI Knowledge record identifies the 2025 edition and gives 30 November 2025 as its publication date. The note correctly keeps the 2004 formula edition-specific and directs the reader to check the applicable edition and national provisions.

I independently checked the stated translation arithmetic. For a 7.50 mm nominal receiver and 6.35 mm nominal shaft, each radial gap is 0.575 mm. A freely translating pin between two centered receiver bores permits 1.15 mm relative center travel from that reference to opposing-side contact; the reverse extreme-to-extreme span is 2.30 mm. Adding the two 1.15 mm interface travels in the stated two-interface series route gives the 2.30 mm centered N-direction travel. With two active equal bolts per interface, the translation tangent is `2 K_ser` per interface; two identical such interfaces in series reduce to `K_ser`. These are correct conditional idealizations for the witness geometry, not installed clearances or measured slip.

The active-set rotational expression is also consistent with the stated one-direction spring law. Differentiating each bolt's spring slip `s_i = e_s · (Δu + Δθ × r_i)` gives `k_θ = Σ K_ser [e_s · (e_θ × r_i)]²` for the active bolts. Its units are N·mm per radian (radians dimensionless). The note correctly limits this to a selected datum, direction, active set, and assumed spring arrangement; the translation-only witness does not establish rotational free play. The explicit warning against adding this reduced spring in parallel with modeled bolt-to-bore contact and bolt bending prevents counting the same lateral transfer twice. It also keeps gross member compliance and face opening/compression separate.

The density boundary is sound. No source-bound mean density for the current wood is supplied, and the 460/500/520 kg/m³ values remain analyst sensitivity points. NDS specific gravity `G` is a separate dimensionless wood-property input; it is not the Eurocode mean density `ρ_m`, and the note does not silently convert one into the other. At the illustrative `ρ_m = 500 kg/m³`, `d = 6.35 mm` point, the formula gives 3,086.746 N/mm per bolt per plane (3.087 kN/mm rounded), matching the note.

The 1.15 mm nominal diametral gap is separately and accurately compared with the historical EC5 §10.4.3(1) limit of 1 mm; the 0.15 mm exceedance is disclosed rather than hidden in the spring law. The comparison to NDS 2018 §12.1.3.2's 1/32–1/16 in range is also arithmetically sound: 1.15 mm is about 0.0453 in and lies within that range. Neither comparison is represented as evidence of actual drilled holes or installed clearance. The NDS `γ = 180,000 D^1.5` warning correctly identifies the term as group-action `C_g`, not a slip modulus.

## Use boundary

This is a defensible source-based sensitivity for post-seating lateral service slip in a declared timber-to-timber model. It is not a current Eurocode adoption finding, a measured material or hardware property, a physical lower/upper bound, a capacity, or an accepted joint response law. The absent source-bound `ρ_m`, actual hole/shaft sizes and offsets, rotational free play, nonlinear behavior outside the service-slip regime, and any individual-joint capacity remain unresolved. No extra material coupon is needed merely to run a clearly declared sensitivity, but its result cannot be promoted to current-part evidence.

References checked: [EN 1995-1-1:2004+A1:2008, §7.1/Table 7.1 and §10.4.3(1)](https://www.phd.eng.br/wp-content/uploads/2015/12/en.1995.1.1.2004.pdf); [BSI Knowledge record for EN 1995-1-1:2025](https://knowledge.bsigroup.com/products/eurocode-5-design-of-timber-structures-general-rules-and-rules-for-buildings); [AWC 2018 NDS Chapter 12](https://awc.org/wp-content/uploads/2021/10/AWC_NDS2018-withCommentary_20210928_AWCWebsite_Chapter12.pdf); [AWC 2024 NDS errata](https://web-media.awc.org/wp-content/uploads/2025/03/31134949/2024-NDS-Errata-and-Addenda-03.28.25.pdf).
