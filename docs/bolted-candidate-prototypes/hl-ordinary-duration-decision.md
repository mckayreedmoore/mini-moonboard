# HL ordinary-duration decision — 2026-09-20

**Decision:** No numerical ordinary-duration HL33 or HL53 allowable load is established by
the public sources checked. The [current Simpson C-C-2026 catalog][simpson] p. 315 gives
DF/SP *single-connector* uplift/F1 values only at **(160)**: HL33 740/1,040 lb and HL53
740/1,310 lb. Its straps/ties note on p. 288 says those wind/earthquake-increased loads
must be reduced when other loads govern, but gives no HL-specific (100) row or conversion.
Indoor climbing-frame demand cannot acquire wind/earthquake duration merely because the
catalog numbers carry that label. No acceptance or drilling decision follows.

**Why `published load ÷ 1.6` is not an established HL rating:** [2024 NDS §2.3.2 and
Table 2.3.2][nds2] assign `C_D = 1.0` to normal/occupancy live load, `0.9` to permanent
load, and `1.6` to ten-minute wind/earthquake load; §2.3.2.2 requires checking the
critical load combination. [2024 NDS §§11.2.3, 11.3.2][nds11] apply `C_D` to *wood
connection reference values*, not metal-part strength. [NDS Appendix B.3][ndsb] confirms
that exclusion. NDS §2.3.2.1 excludes `E`, `E_min`, and deformation-based `F_c⊥` from
`C_D`; it supplies no conversion for a connector's test deflection limit. Simpson's
[catalog p. 11][simpson] says connector allowable loads can be governed by tested
ultimate with a safety factor, 1/8-in deflection, or NDS
fastener calculations. The HL page does not identify the controlling mechanism for
either direction or publish an ordinary-duration test/deflection result.

Mechanism distinction:

- **NDS wood-fastener strength:** A `1.0/1.6` ratio applies to that *wood component* if
  its (160) value was formed solely by `C_D = 1.6`, with other factors and geometry fixed.
- **Steel/bolt/angle strength:** `C_D` does not act on metal strength. Check its limit
  without a `1.6` increase; division does not identify the actual limit.
- **Assembly test or deflection:** HL publishes no controlling test mode or ordinary-
  duration deformation basis. A blanket ratio cannot establish these limits.

Thus `740/1.6 = 462.5`, `1,040/1.6 = 650`, and `1,310/1.6 = 818.75 lb` are **arithmetic
sensitivities only**, not verified ordinary-duration HL capacities. They would be a
conservative *strength* lower bound under an additional, unverified condition: every
non-NDS-strength limit remains valid at ordinary duration and the (160) wood component
is exactly a `C_D = 1.6` adjustment of its reference value. The needed exact-HL
mode breakdown and ordinary-duration test/deformation applicability are absent.

**Supported next route without contact:** Use the (160) values only as a rejection screen
in the catalog's stated uplift/F1 directions: demand above one of those values cannot
pass that direction at a lower ordinary-duration rating. For a positive screen, obtain
public exact-model evidence that establishes an ordinary-duration value or the governing
component limits; alternatively choose catalog hardware with a published (100) value
for the actual installation. Then check the wood/bolt connection under 2024 NDS at the
applicable duration and species, the metal limit without `C_D`, and any test/deflection
limit separately; take the minimum supported limit. Also apply Simpson's member, fastener,
pairing, and load-axis rules. The current HL evidence does not provide that complete route
or an F2/moment/interaction rating.

[simpson]: https://ssttoolbox.widen.net/content/orplhjaqw1/pdf/C-C-2026.pdf
[nds2]: https://web-media.awc.org/wp-content/uploads/2021/12/17210153/AWC_NDS2024_20231129_AWCWebsite_Chapter2.pdf
[nds11]: https://web-media.awc.org/wp-content/uploads/2021/12/17205958/AWC_NDS2024_20250124_AWCWebsite_Chapter11.pdf
[ndsb]: https://web-media.awc.org/wp-content/uploads/2021/12/17210019/AWC_NDS2024_withCommentary_20240719_AWCWebsite_Appendix.pdf
