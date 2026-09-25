# Conditional 1/4-20 Grade 5 bolt steel references

This calculation is a per-bolt material reference for the current ordinary
three-timber/four-bolt patch's **hypothetical** 1/4-20 SAE J429 Grade 5 cap
screw. The current hardware schedule has not selected that grade or a SKU.
Values do not establish delivered conformance, demand, load sharing, complete
joint capacity, or criterion closure. Source and method boundaries are in the
[bolt-resistance boundary note](../ordinary-bolt-resistance-boundary-attempt01/README.md).

## Inputs and calculation

The conditional project specification is Grade 5 with minimum yield stress
`Fy = 92,000 psi`, minimum tensile strength `Fu = 120,000 psi`, and proof
stress `Fp = 85,000 psi`. The Value Fastener technical sheet states these
values for Grade 5 hex cap screws from 1/4 through 1 inch. The nominal 1/4-20
thread tensile stress area is `At = 0.0318 in²` (20.516088 mm²), as recorded
in the existing quarter-inch hardware basis and its thread-area reference.
The area is a standard stress-area input, not the measured root or shank area
of a delivered bolt.

| Reference | Calculation | Per-bolt value | Meaning and limit |
| --- | --- | ---: | --- |
| Axial first-yield reference | `Fy × At` | **2,925.6 lbf (13.014 kN)** | Conditional direct tensile-yield reference at the nominal thread stress area. Not an allowable or complete-joint capacity. |
| Proof-load reference | `Fp × At` | **2,703 lbf (12.024 kN)** | Conditional proof reference. Proof load is not yield strength, ultimate strength, or an assigned design allowable. |
| Ultimate tensile reference | `Fu × At` | **3,816 lbf (16.974 kN)** | Conditional tensile ultimate reference; not a design resistance. K.L. Jack's 2009/10 J429 table rounds the 1/4-20 Grade 5 figures to 2,700 lbf proof and 3,800 lbf minimum tensile. |
| Commentary-derived `Fyb` scenario | `(Fy + Fu) / 2` | **106 ksi** | Approximate NDS Commentary model estimate only; not a standard minimum, test result, or guaranteed lower bound. |

The 92 / 120 / 85 ksi inputs are a condition to impose in a future
specification for an assumed conforming fastener. The `At`-based numbers are
unadjusted component references; no resistance factor, wood/member adjustment,
group factor, demand comparison, or combined tension/shear rule is applied.
The NDS `Fyb` estimate is listed separately because Appendix I Commentary's
approximation is not the NDS §12.3.6.2 test-derived route itself.

## Provenance

- [Value Fastener Grade 5/8 cap-screw technical sheet](https://www.valuefastener.com/documents/products/capscrewgr5-8.pdf):
  minimum yield 92 ksi, minimum tensile 120 ksi, and proof stress 85 ksi for
  1/4–1-in Grade 5 cap screws; checked online 2026-09-25.
- [K.L. Jack fastener technical data and charts](https://www.kljack.com/docs/default-source/technical-information/kl_jack_fasteners-technical_data_and_charts.pdf),
  catalog marked 2009/10, table “Cap Screws – SAE J429”: Grade 5 1/4-20 UNC
  proof load 2,700 lbf and minimum tensile strength 3,800 lbf.
- [Existing quarter-inch hardware source note](../../../../floor-rail-2x4-hardware.md)
  cites `At = 0.0318 in²` from its linked 1/4-20 thread-area reference. This
  is geometry only; no aluminum-stud material property is used.
- [SAE J429 current public record](https://saemobilus.sae.org/standards/j429_201405-mechanical-material-requirements-externally-threaded-fasteners)
  identifies revision J429_201405, while NDS-2024's bibliography cites J429
  (1999). The conditional scenario explicitly carries the numerical minima as
  project requirements; the supplier sources do not identify which J429
  edition their property tables reproduce.
- [NDS-2024 Appendix I Commentary](https://web-media.awc.org/wp-content/uploads/2021/12/17210019/AWC_NDS2024_withCommentary_20240719_AWCWebsite_Appendix.pdf)
  gives the approximate bolt estimate `Fyb ≈ (Fy + Fu) / 2`; the repository's
  source copy SHA-256 is
  `99b0a54e7133b3cf6dd156d8fe864c1717c951487bf5baa99c34da9a68a6bbb7`.
