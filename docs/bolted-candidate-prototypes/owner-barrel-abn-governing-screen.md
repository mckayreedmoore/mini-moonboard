# ABN trial barrel governing-joint screen

Status: **both nominal end orientations fit; current hypothetical
principal/header screen fails; complete design EVIDENCE-BLOCKED.** No purchase,
drilling, or fabrication release.

## Retail evidence

[Amazon ASIN B01N3QW1JS](https://www.amazon.com/dp/B01N3QW1JS) identifies ABN
part `7015_10PACK` as a ten-pack of 1/4-20, 10 mm diameter × 16 mm long,
off-center, zinc-plated alloy-steel cross dowels. Amazon currently reports no
featured offer and says the item is unavailable. No steel grade, heat
treatment, minimum yield/ultimate strength, thread class, tolerance, proof
load, or connection rating is published.

Amazon does not dimension the offset. A
[same-geometry reseller listing](https://www.noon.com/uae-en/50-cross-dowels-barrel-nuts-1-4-20-16mm-x-10mm-zinc-plated-off-centered-cnc/Z8D593A3030DC081A4881Z/p/)
states 6 mm from an end to the thread axis. Product photos appear to show one
slotted end and the cross-hole nearer the opposite plain end. Therefore 6 mm,
which end is the datum, and slot-end orientation remain retail-family inference,
not controlled ABN dimensions.
The geometry cannot be frozen before measuring a sample.

## CAD answer

Current vertical-principal CAD already uses a 5.9944 mm insertion-end-to-thread-
axis offset. Substituting nominal ABN dimensions of 10 × 16 mm and using the
retail-family 6 mm value changes that pose by only 0.0056 mm. But retail evidence
does not prove whether 6 mm is measured from slotted or plain end. Keeping the
bolt/thread axes fixed gives two nominally clear cases:

- 6 mm end proximal: 13.05 mm recess, 29.05 mm bore depth, and 9.05 mm
  far-side stock;
- 10 mm end proximal: 9.05 mm recess, 25.05 mm bore depth, and 13.05 mm
  far-side stock;
- 14.05 mm nominal radial X ligament;
- 31.5514 mm minimum raw-face clear ligament;
- 70 mm clear wood between the two barrel bores; and
- unchanged minimum complete-thread endpoint 16.704 mm past the thread axis.

Both nominal collision screens pass. Neither orientation is selected. This is
a fit result only. Bore tolerances, actual offset convention, slot access,
removal, and adverse-cut stock remain uncontrolled.

## Governing demand update

Old 220–301 N row proxies are no longer governing once one-sided contact,
clearance, twist compatibility, and unequal row sharing are included. Current
screening ladder is:

| Screen | Per-row tension |
|---|---:|
| Old static witness | 220.48 N |
| Old pre-compatibility sensitivity | 301.49 N |
| Isolated ±My at reference stiffness | 318.32 N |
| Isolated governing ±Mx row | 496.39 N |
| Accepted-default combined screen | 733.84 N |
| Governing valid-subset combined screen | 846.71 N |

Two-row tension reaches 1,156.37 N. Rear-row share ranges from 16.4% to 97.0%,
so a 50/50 assumption is unsafe. These remain old-topology screens, not fresh
48-pair design demands. Seventy-five soft-response cases left the fixture's
small-motion domain, so 846.71 N is not a bounded upper design action.

## Wood screen

Using nominal 10 × 16 mm ABN geometry, current DF-L No. 2 basis, the 36.551 mm
minimum grain-end ray, and the 846.71 N row action:

| Mode | Reference | Capacity / action | Result |
|---|---:|---:|---|
| Adapted projected-area bearing | 424.18 N | 0.501 | Fail |
| Adapted FPL-form bearing | 345.89 N | 0.409 | Fail |
| Individual two-plane reference | 1,685.66 N | 1.991 | Reference-only |
| Header washer bearing | 920.57 N | 1.087 | Narrow reference-only |
| Face-cell pressure | 4.309 / 5.013 MPa | 0.860 | Fail screen |

The two-plane value is not adopted for the 40-degree, blind, two-row group.
The 1,245.159 mm² split plane has no adopted tension-perpendicular resistance,
and group tear-out remains unenumerated. Nominal parallel net sections are
large, but cannot override splitting or oblique group action.

Result: current principal/header arrangement **fails this hypothetical screen**
for wood bearing and concentrated face pressure. This becomes a design NO-GO
only if the 846.71 N action and adapted resistance methods are adopted. They are
not: demand is not fresh or bounded, and resistance analogies are not qualified.
ABN's offset does not add strength.

## Explicit hypothetical S355 sensitivity

The [2022 Fabbri, Minghini, and Tullini study](https://sfera.unife.it/retrieve/9559c37b-7c3c-4ee0-b1a9-19090373d783/Fabbri_Tullini_Minghini_2022%20-%20pre-print.pdf)
tested custom centered 20 × 50 mm S355 or class-12.9 barrels, M12 rods, and
50 × 50 mm high-density beech LVL under axial grain-parallel load. Its 20–67 kN
joint peaks and measured stiffness do not transfer to this 10 × 16 mm slotted,
offset barrel in DF-L under twist and oblique action.

Assuming only for sensitivity that the ABN body behaves as S355 with 355 MPa
yield, nominal illustrative requirements at 846.71 N are:

- female-thread shear: `19.62 × gamma` MPa;
- lobe average shear: `43.17 × gamma` MPa; and
- lobe bending: `199.14 × gamma × Kt` MPa.

Nominal S355 bending margin is `1.783 / (gamma × Kt)`: 1.19 at `gamma=1`,
`Kt=1.5`, but 0.89 at `Kt=2`. Reusing the prior generic ±0.016-inch adverse
geometry sensitivity raises bending demand to
`269.96 × gamma × Kt` MPa; margin becomes 0.88 at `Kt=1.5` and 0.66 at `Kt=2`.
That tolerance is not an ABN tolerance, but it shows the small offset barrel is
not robust to modest stress concentration. “Alloy steel” supplies no actual
S355 lower bound.

## Finite decision

- Nominal geometry: **PLAUSIBLE in both orientations**, pending sample
  measurement and datum confirmation.
- Actual ABN metal: **EVIDENCE-BLOCKED**.
- Governing principal/header strength: **conditional NO-GO under current
  hypothetical action and resistance screen**.
- Complete screw-free frame: **EVIDENCE-BLOCKED**; fresh demands and closed
  moved-post/backer load paths still do not exist.

Do not freeze this SKU for structural-frame use unless a changed joint reduces
bounded row demand below an adopted wood resistance with tolerance margin, or
wood/barrel geometry changes and is rerun. Required sample measurements are
OD, length, both end-to-axis distances, slot width/depth, 1/4-20 thread gauge,
and finished-bore fit.

Executable calculation:
[`scripts/owner_barrel_abn_governing_screen.py`](../../scripts/owner_barrel_abn_governing_screen.py).
