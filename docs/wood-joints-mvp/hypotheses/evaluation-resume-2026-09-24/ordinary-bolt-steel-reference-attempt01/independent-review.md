# Independent review: conditional ordinary-bolt steel reference

Reviewed 2026-09-25. This review is pinned to the boundary note SHA-256
`ced3e90ffc9cdcc81a33a846e13fa7d503b7d1d1997db1a44748e8b49554634f` and
steel-reference note SHA-256
`8f14fbd47e1571ff8dae3a2907fc8c46f49b2a61216cc2c6525b7e4c87dae310`.

The material boundary and numerical references are sound for a **conditional
MVP-E engineering input**. I found no correction needed. This does not select
the catalog candidate or establish actual-product conformity, an NDS lateral
resistance value, or joint capacity.

The [Value Fastener Grade 5 cap-screw sheet](https://www.valuefastener.com/documents/products/capscrewgr5-8.pdf)
states minimum yield strength 92 ksi, minimum tensile strength 120 ksi, and
proof stress 85 ksi for 1/4–1 in Grade 5 hex cap screws. Its dimensions cite
ASME B18.2.1-2012, but the sheet does not state a J429 edition; it also notes
that yield properties may be tested on machined specimens when the machine
cannot fully test the parts. The [K.L. Jack 2009/10 catalog](https://www.kljack.com/docs/default-source/technical-information/kl_jack_fasteners-technical_data_and_charts.pdf)
independently lists 2,700 lbf proof and 3,800 lbf minimum tensile strength for
1/4-20 Grade 5 cap screws under SAE J429, while disclaiming completeness and
validity. These documents support explicitly declared minimums in a project
specification, not a claim about a J429 edition's controlling table or a
delivered part. The note correctly leaves the edition choice and later
conformance distinct and does not make physical receipt an MVP-E prerequisite.

I checked the area and arithmetic. The [NIST Handbook 28 Supplement's Unified
tensile stress-area relation](https://nvlpubs.nist.gov/nistpubs/Legacy/hb/nbshandbook28supp1963.pdf)
gives `0.03182099247 in²` for 1/4-20, which rounds to the reference
`At = 0.0318 in²` (`20.516088 mm²`). Applying the stated rounded area gives:

| Reference | Recomputed per bolt |
| --- | ---: |
| `92 ksi × At` | `2,925.6 lbf = 13.013717 kN` |
| `85 ksi × At` | `2,703 lbf = 12.023543 kN` |
| `120 ksi × At` | `3,816 lbf = 16.974414 kN` |

The reported rounded values agree. The K.L. Jack figures are consistent
rounded corroboration; proof, yield, and ultimate are kept as separate
references. `At` is a nominal threaded stress area, not a measured delivered
root/shank area, an allowable, or a resistance factor calculation.

The NDS distinction is also correct. [NDS-2024 Chapter 12](https://awc.org/wp-content/uploads/2026/08/AWC_NDS2024_withCommentary_20250328_WebsiteChapter-12-%E2%80%93-Dowel-type-fasteners.pdf)
§12.3.6.2 says `Fyb` used for reference lateral design values is based on
yield from ASTM F1575 or tensile yield from ASTM F606. [ASTM F606/F606M-26a](https://store.astm.org/f0606_f0606m-26a.html)
§1.2 says product standards specify property requirements and applicable
tests, so the test-method standard alone does not assign this bolt's property.
[Appendix I Commentary](https://web-media.awc.org/wp-content/uploads/2021/12/17210019/AWC_NDS2024_withCommentary_20240719_AWCWebsite_Appendix.pdf)'s approximate relation
`Fyb ≈ (Fy + Fu)/2` yields 106 ksi from the scenario minima, but is expressly
an approximate model estimate, not a standard minimum, test result, or lower
bound. The separate 45 ksi example is tied to the stated larger-fastener scope
(`D ≥ 3/8 in`) and is not transferred to this 1/4-in bolt. The official AWC
Chapter 12 source is pinned in the boundary note (SHA-256
`5fc837523ff10acc097a162718700a9b4ba64e627d2b0023439146d42fe4ee2a`); the
official Appendix PDF retrieved for this review has SHA-256
`99b0a54e7133b3cf6dd156d8fe864c1717c951487bf5baa99c34da9a68a6bbb7`.

The conditional specification remains distinct from normative/test-derived
NDS `Fyb`; choosing that resistance method and separately defining nut,
washer, thread-bearing, demand, and load-sharing inputs remain open work.

## Documentation integration addendum

Reviewed the final integration at `bolt-resistance-basis.md` SHA-256
`c81cdbccc1f712870ba2e10b652bba6fc43060a341a83d75c07182293f5627b2` and
`representative-fastener-resistance-method.md` SHA-256
`2597018b9ec69a29e8fccd295cc42a953b6904c71d504acf62560e892c015069`. The
conditional source notes above remain pinned at their stated hashes.

The edits make the material boundary consistent across both method documents:
the 92/120/85 ksi values are identified as explicit project minima sourced
to the supplier's Grade 5 sheet, with candidate/lot conformance held separate.
The 106 ksi value remains only the NDS Commentary's approximate
`(Fy + Fu)/2` estimate; the text expressly excludes its use as a guaranteed
lower bound or an NDS/project pass without separate method review. This
matches NDS-2024 §12.3.6.2's test-derived F1575/F606 basis and Appendix I's
non-mandatory commentary, as cited in the first review above.

The edits also preserve the helper's fail-closed actual-evidence behavior and
name its current `certified_min_yield_mpa` API limitation. Both material and
shear-plane areas now identify a conditional-scenario or actual-part basis.
They allow a
separately labeled MVP-E property scenario without changing that helper,
criteria, or delivered-conformance status. For geometry, the source-class
thread-root assumption is explicitly conditional; product/drawing or
measurement evidence is scoped to actual-candidate thread-location, nut-fit,
full-body-`D`, and smooth-shank claims. The final grip-screen wording permits
declared MVP-E assumptions, so it does not create a blanket receipt or
measurement prerequisite. No further correction is needed.
