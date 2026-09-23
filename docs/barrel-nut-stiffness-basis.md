# Barrel-nut stiffness basis and evidence gap

This is a local-source audit for the 46-pair
`compact-floor-flush-bolted-development` candidate. It does not select a
spring value, run a native solve, contact a supplier, qualify a joint, or
release drilling, fabrication, or climbing. The current response inputs of
1,000 N/mm axial, 500 N/mm lateral, and 100 multiplied by contact area are
conditional numerical assumptions, not measured or published properties.

## Finding

The repository contains useful constituent calculations and ordinary
dowel-connection analogies, but no defensible lower-and-upper stiffness bounds
for the complete bolt–thread–barrel–wood joint. It also contains no defensible
areal stiffness for the timber contact faces. The present evidence therefore
does **not** close `bn_stiffness_clearance_basis`.

Three source-bounded calculations remain useful as transparent sensitivities:

| Response term | Computable local result | Why it is not a candidate bound |
| --- | --- | --- |
| Bolt steel in axial tension | 24,646–47,177 N/mm using a 4.8006 mm typical-root sensitivity, or 43,123–82,544 N/mm using nominal 6.35 mm shank area | Purchased bolt root, threaded/free length, steel modulus, thread runout and load path are not controlled. Thread, barrel, washer-seat and receiver-wood compliances act in series. |
| Ordinary lateral dowel slip | 3,940.354 N/mm from corrected 2024 NDS group-action modulus; 2,723.847–3,273.791 N/mm from an EC5 service-slip analogy at assumed 460–520 kg/m³ | Buried cross-dowel joint is not the ordinary continuous-dowel joint represented by either expression. Density range, fit, clearance, load level and cyclic state are not verified. |
| Timber face compression | `K_face = A / (L1/E_n1 + L2/E_n2)` for two elastic compression paths in series | Effective depths, face-normal moduli for both members, growth-ring axes, seating/gaps, active area, pressure spread, moisture and load state are missing. |

These values can define named diagnostic points. They cannot define an
acceptance sweep or turn a resulting force into a design demand.

## Axial constituent arithmetic

The installed-stack ledger gives modeled seat-to-assumed-barrel-axis lengths.
Using the already recorded sensitivity `K = EA/L`, `E = 205,000 N/mm²`, and
areas based on either a 4.8006 mm typical thread root or the 6.35 mm nominal
shank gives:

| Stack family | Pairs | Modeled length `L` (mm) | Root-area `EA/L` (N/mm) | Shank-area `EA/L` (N/mm) |
| --- | ---: | ---: | ---: | ---: |
| `BN-BASE-CENTER` | 2 | 101.651 | 36,503 | 63,867 |
| `BN-BASE-OUTER-SIDE` | 4 | 109.751 | 33,809 | 59,154 |
| `BN-BOTTOM-CENTER` | 4 | 109.751 | 33,809 | 59,154 |
| `BN-BOTTOM-OUTER-RAIL` | 4 | 150.551 | 24,646 | 43,123 |
| `BN-HEADER-CENTER` | 4 | 78.651 | 47,177 | 82,544 |
| `BN-HEADER-OUTER-POST` | 4 | 103.100 | 35,990 | 62,970 |
| `BN-LOWER-CENTER-RAIL` | 4 | 109.751 | 33,809 | 59,154 |
| `BN-LOWER-OUTER-RAIL` | 4 | 150.551 | 24,646 | 43,123 |
| `BN-TOP-CENTER` | 4 | 109.751 | 33,809 | 59,154 |
| `BN-TOP-OUTER` | 4 | 120.551 | 30,780 | 53,854 |
| `BN-UPPER-CENTER-RAIL` | 4 | 109.751 | 33,809 | 59,154 |
| `BN-UPPER-OUTER-RAIL` | 4 | 150.551 | 24,646 | 43,123 |

This is exact arithmetic on provisional model dimensions, not a verified
component range. The complete axial law would require, at minimum,

`1/K_joint = 1/K_bolt + 1/K_thread + 1/K_barrel + 1/K_washer-seat + 1/K_receiver-wood + ...`

plus any initial thread, bore and seating play. The [hardware evidence
ledger](barrel-nut-hardware-evidence.md) leaves the bolt complete-thread
interval, barrel female-thread interval and axis, barrel material/wall
properties, washer product, and actual engagement unknown. Consequently even
the steel-only values are not verified upper bounds for delivered joints.
The repository's [axial series-model citation][axial-series] supports separate
series components; it does not supply a transferable stiffness for this
hardware.

## Lateral slip and clearance

The [corrected 2024 NDS Section 11.3.6.1][nds-errata] group-action expression
recorded in the repository is `gamma = 180,000 D^1.5 lb/in`. At `D = 0.25 in`, this is
22,500 lb/in or 3,940.354 N/mm. Its normative role is group action, not a
general three-dimensional spring law.

The USDA/FPL [Wood Mechanical Fasteners][fpl-fasteners] paper reproduces the
EC5 service expression `Kser = rho_mean^1.5 d / 23` per fastener per shear
plane. At `d = 6.35 mm`, the repository's assumed density points of 460, 480,
500 and 520 kg/m³ give 2,723.847, 2,903.406, 3,086.746 and 3,273.791 N/mm.
Those densities are sensitivities, not measurements or statistical bounds.
Assigned NDS specific gravity 0.50 cannot be substituted for mean density.

The modeled 7.50 mm machine bore and 6.35 mm nominal shaft also imply a
nominal centered radial dead zone of `(7.50 - 6.35)/2 = 0.575 mm`. Actual
one-sided travel can range differently because bolt diameter, finished hole,
initial shaft position, moisture, damage and drilling tolerance are not
controlled. Neither published slope includes that dead zone. Barrel rotation,
barrel-bore fit, local wood crushing and reversed/cyclic slip remain additional
terms. The [NDS applicability review](bolted-candidate-prototypes/owner-barrel-nds-applicability.md)
therefore permits these formulas only as conditional lateral submodels, not as
complete-joint bounds.

## Timber contact arithmetic and unit correction

The candidate material record gives `E_L = 1,600,000 psi = 11,031.612 N/mm²`.
The USDA [Wood Handbook Chapter 5][fpl-ch5] clear-wood ratios give sensitivity
values `E_T = 0.050 E_L = 551.581 N/mm²` and
`E_R = 0.068 E_L = 750.150 N/mm²`. These mixed-source values are proxies, not
graded-lumber lower or upper bounds.

Current trial-cut face areas have four exact totals across the 24 stations:
5,055.451, 5,234.213, 10,828.845 and 12,330.973 mm². For a one-member elastic
column, those data only permit the symbolic cross-grain range

`K_face = (2,788,488 to 9,250,074) / L_effective N/mm`,

where the low numerator combines the smallest area with `E_T` and the high
numerator combines the largest area with `E_R`. No source fixes
`L_effective`, and a real two-member interface requires the series expression
shown above. Longitudinal/end-grain paths, pressure spread and partial opening
must be treated by their actual station orientations rather than folded into
this cross-grain sensitivity.

The current code names the contact input `contact_n_per_mm2`, but multiplies
it by tributary area in mm² to obtain a spring in N/mm. Its physical unit is
therefore **N/mm³**, an areal stiffness, despite the field name. At the current
value 100, total nominal face springs are 505,545–1,233,097 N/mm. In a
one-member cross-grain-column analogy, 100 N/mm³ silently implies an effective
depth of 5.516 mm at `E_T` or 7.501 mm at `E_R`. No repository evidence selects
either depth. The field/unit mismatch must be corrected or explicitly migrated
before evidence is generated.

## Exact evidence blocker

No combination of current citations and geometry yields candidate-specific
stiffness bounds because all three load paths lack necessary inputs:

- axial: controlled bolt/thread/barrel/washer geometry and material,
  engagement, preload or snug condition, seat and receiver-wood compliance;
- lateral: finished shaft/hole tolerance distribution, initial bearing
  position, barrel restraint, member density, grain-direction response and
  reversed/cyclic load-slip behavior; and
- contact: both members' face-normal properties, effective compression depths,
  actual seating/gaps, active-area evolution and partial-opening law.

Using 1,000/500/100 as if measured, using steel `EA/L` as complete axial
stiffness, or treating NDS/EC5 lateral values as upper and lower bounds would
invent evidence. No structurally accepted native response should be based on
those choices; explicitly conditional diagnostics remain conditional.

## Minimum coupon measurements needed to close the gap

Before testing, freeze a qualification protocol and exact hardware/wood lot.
Either test every family/critical variant or justify an enveloping family map.
At minimum that map must address the single-bolt principal/header joint,
two-row post/header joint, recessed outer-header joint, short-overlap outer
rail, N = 42 mm left rail row, and 2 mm top-outer bore extension.

For every specimen, record exact SKU/lot and measured bolt, complete-thread,
barrel, washer, bore, pocket, engagement and seating geometry; lumber
species/grade, density or mass/volume, moisture, dimensions, grain and growth
ring orientation, defects, and installation/reassembly history. Record the
installation method and any bottoming, barrel rotation or initial gap.

Measure synchronized force and **relative member motion independently of
crosshead travel**. Required channels are interface separation, two in-plane
slip directions and relative rotation; head/washer seating and barrel
translation/rotation need separate observation where practical so component
compliances can be identified. Force and displacement resolution, calibration,
fixture compliance and fixture reactions must be recorded.

Predeclare load windows and extract, for both directions where applicable:

- initial positive and negative dead zones;
- engaged tangent and secant stiffness over stated force/slip intervals;
- unload/reload stiffness, hysteresis and residual set;
- changes after predeclared assembly cycles and conditioning; and
- axial, both lateral grain directions, reversed, and combined eccentric
  force/moment response using the actual contact face and member load path.

Raw synchronized force–displacement data, specimen measurements, photos and
failure/damage observations must be retained. Qualification bounds need a
predeclared specimen count, lot sampling, conditioning and statistical method.
Because both stiff and soft joints can govern force redistribution, the output
must provide supported lower **and** upper response envelopes, not only a mean
or lower characteristic strength. An exploratory coupon without that protocol
can guide the next model but cannot close this gate.

## Repository sources audited

- [Published stiffness basis](bolted-candidate-prototypes/simple-center-published-stiffness-basis.md)
  and its reproducible calculation,
  [`scripts/simple_center_published_stiffness_basis.py`](../scripts/simple_center_published_stiffness_basis.py).
- [Candidate material record](bolted-candidate-material-basis.json), including
  recorded 2024 NDS Supplement digest and actual-stock inspection gaps.
- [Installed-stack audit](bolted-candidate-prototypes/owner-barrel-integrated-stack-audit.md),
  [hardware ledger](barrel-nut-hardware-evidence.md), and
  [station register](barrel-nut-stations.json).
- [Load-test readiness](bolted-candidate-prototypes/owner-barrel-load-test-readiness.md)
  and [NDS applicability review](bolted-candidate-prototypes/owner-barrel-nds-applicability.md).

No new web search, supplier contact, physical observation, or native solve was
performed for this audit.

[nds-errata]: https://web-media.awc.org/wp-content/uploads/2025/03/31134949/2024-NDS-Errata-and-Addenda-03.28.25.pdf
[fpl-fasteners]: https://www.fpl.fs.usda.gov/documnts/pdf2016/fpl_2016_rammer001P.pdf
[fpl-ch5]: https://www.fpl.fs.usda.gov/documnts/fplgtr/fplgtr282/chapter_05_fpl_gtr282.pdf
[axial-series]: https://link.springer.com/article/10.1186/s10086-022-02038-1
