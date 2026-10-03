# BG001 three-case paired resultant references

This source-pinned screen extends the existing BG001 A1 single-bolt method to
both physical BG001 bolts across all 21 authenticated case/load-factor states
in the complete corner register. It keeps the bolts and receiver actions
paired in every state. The six final-load comparisons below are raw,
unadjusted individual-bolt references, not adjusted design values or joint
acceptance.

| Case | Bolt | Y/Z resultant (N) | Load-to-grain angle | Conditional `Fe` in each receiver (psi) | Governing mode / raw reference (N) | Raw demand/reference | Same-state axial tie (N), separate |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| A1 rear | 1 | 108.896 | 11.421° | 5543.826 | IV / 767.897 | 0.14181 | 44.483 |
| A1 rear | 2 | 146.049 | 44.567° | 4967.786 | IV / 667.352 | 0.21885 | 47.001 |
| A12 rear | 1 | 301.657 | 30.092° | 5258.374 | IV / 712.070 | 0.42363 | 64.966 |
| A12 rear | 2 | 335.061 | 39.522° | 5069.461 | IV / 682.661 | **0.49082** | 18.473 |
| K12 rear | 1 | 24.877 | 74.388° | 4517.183 | IV / 592.680 | 0.04197 | 56.542 |
| K12 rear | 2 | 68.767 | 85.405° | 4455.874 | IV / 574.085 | 0.11978 | 13.978 |

The maximum is A12 rear, bolt 2, at load factor 1.0: 335.061 N over a 682.661 N
unadjusted individual-bolt Mode IV reference. Its same-state axial tie is
18.473 N and remains separate. It is not combined with lateral demand. The
42 full records in [`screen.json`](screen.json) retain both action/reaction
vectors, the same-state tie vectors, all six yield modes and mode references,
per-receiver angles and `Fe`, and the signed geometry rays for each bolt in
each case/load-factor state. In every record the force pair closes, the source
Y/Z resultant reproduces, the tie pair closes, and Mode IV is independently
checked against its closed-form equation. A1 at factor 1.0 reproduces the
original A1 screen before the other two cases are accepted.

## Applicability and detailing interpretation

The resultant method carries over from A1 without a topology change. Both
receivers retain proposed grain `+Z`, both bolt axes are global `+X`, and the
reported lateral forces lie in `Y–Z`, normal to those bolt axes. The proposed
wood basis remains DF-L No. 2 at SG 0.50, with recorded parallel/perpendicular
`Fe` endpoints of 5600/4450 psi; the same NDS angle equation is applied to
each receiver separately. The conditional single-shear basis remains a
full-body smooth 1/4-inch shank, 38.1 mm of bearing in each receiver, zero gap,
and `Fyb = 45,000 psi`. The actual lumber and delivered bolt are unobserved.
No end-grain factor applies to this BG001 geometry because the modeled bolt
axis is perpendicular to the proposed grain in both receivers.

No lateral-yield method input differs from A1: receiver roles and lengths,
proposed grain, bolt axis, diameter, gap, `Fe` endpoints and conditional `Fyb`
are unchanged. The case and load factor change the signed resultant direction
and magnitude. This screen carries forward A1's raw reference arithmetic only;
it does not carry forward an oblique-grain `CΔ` overlay.

Every state has both a nonzero force component parallel to proposed grain and
a nonzero cross-grain component. The force angle varies from 11.421° to
85.405°. On the post the grain-parallel component points toward `g+`; on the
spine its opposite action points toward `g−` in every case. The transverse
component selects the edge ray. Bolt 1 keeps the post `e+` / spine `e−` loaded
edge throughout; bolt 2 reverses between A1 rear (`post e+`, `spine e−`) and
A12/K12 rear (`post e−`, `spine e+`). Thus the edge ray cannot be carried
between cases as a fixed sign. The pinned finished-profile query gives these
distances at three through-thickness stations:

| Bolt | Receiver | Loaded grain-end ray / distance | Possible edge rays `e− / e+` |
| --- | --- | ---: | ---: |
| 1 | Post | `g+` / 67.45 mm | 38.10 / 101.60 mm |
| 1 | Spine | `g−` / 31.75 mm | 44.45 / 95.25 mm |
| 2 | Post | `g+` / 25.40 mm | 38.10 / 101.60 mm |
| 2 | Spine | `g−` / 73.80 mm | 44.45 / 95.25 mm |

The distances are finished-CAD profile measurements, not observations of
stock. For context, the NDS-2024 parallel-softwood-tension Table 12.5.1A
endpoint is 7D (44.45 mm), its half-factor endpoint is 3.5D (22.225 mm), and
the perpendicular/parallel-compression full and half endpoints are 4D
(25.40 mm) and 2D (12.70 mm). They are numeric endpoint comparators only for
these oblique grain directions. The pinned NDS-2024 Chapter 12 PDF is
specification text without Commentary C12.5.1.2, so its oblique-grain
end-distance interpolation is not verified here and no `CΔ` factor is
applied. The official 2018 Commentary is historical context only; this result
does not promote older commentary language to a 2024 provision.

For the cross-grain rays, all selected and opposite edge distances exceed the
Table 12.5.1C numeric values 4D loaded and 1.5D opposite edge (25.40 and 9.525
mm). This is a geometric comparison of signed rays only; it does not establish
oblique-direction detailing compliance or splitting resistance. The
§12.5.1.2(b) equivalent-shear-area provision concerns load angled to the
fastener axis. The actions here are bolt-normal, so that provision does not
resolve their separate obliquity to grain.

The method uses NDS-2024 §12.3.4 Equation 12.3-11 for the bearing strength at
the resultant angle, followed by all six unadjusted §12.3.1 yield modes. The
parallel and perpendicular `Fe` endpoints are preserved; the helper matches
them at 0° and 90°. Ratios compare one bolt's Y/Z resultant to its own minimum
single-shear reference. No capacities or axes are summed, and no independent
maxima are assembled into a synthetic state.

The exact report, signed-register, method, material, hardware-basis, grain-map,
geometry and profile-query digests are in [`source-pins.json`](source-pins.json).
The NDS-2024 Chapter 12 PDF source identity is SHA-256
`5fc837523ff10acc097a162718700a9b4ba64e627d2b0023439146d42fe4ee2a` at the
official [AWC PDF URL](https://awc.org/wp-content/uploads/2026/08/AWC_NDS2024_withCommentary_20250328_WebsiteChapter-12-%E2%80%93-Dowel-type-fasteners.pdf).
The official [2018 NDS Commentary](https://awc.org/wp-content/uploads/2021/10/AWC_NDS2018-withCommentary_20200827_AWCWebsite_Commentary.pdf) is
listed as historical context only.

## Remaining limits

These comparisons omit `CΔ`, `Cg`/group action, load-duration and other
adjustments, bolt/washer tension interaction, axial seat resistance, and
splitting, row/group tear-out, net-section, member shear, and complete-joint
transfer. The actual mixed-direction group factor remains unavailable because
the current row-alignment helper rejects the source resultants. A reference
ratio below 1.0 is not an adjusted design DCR or a pass. This does not qualify
the original LEG/RUNNER arrangements or authorize a geometry change.

Reproduce from the repository root with:

```sh
OPENBLAS_NUM_THREADS=1 .venv/bin/python docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-corner-complete-resistance-register-attempt01/produce.py --verify
OPENBLAS_NUM_THREADS=1 .venv/bin/python docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-bg001-three-case-resultant-reference-attempt01/produce.py --verify
```
