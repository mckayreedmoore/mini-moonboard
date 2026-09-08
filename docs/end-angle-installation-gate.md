# End-angle installation qualification gate

The [relocated-bolt ML23Z trial](backing-end-relocated-trial.md) clears nominal
hardware collisions. **It is not selected:** the applicable connection rating
and installation limits remain unresolved. Further cosmetic CAD/export work
should not be treated as closing this gate.

## Current primary-source check

Checked September 8, 2026:

- [IAPMO ER-280](https://ssttoolbox.widen.net/content/csrmqmxwl7/pdf/IAPMO_UES_ER280.pdf),
  revised April 28, 2026, valid through January 31, 2027. Sections 3.2.2, 4.1
  and 4.2 and Table/Figure 13 establish material, installation and ML conditions.
  The baseline wood provisions include assigned specific gravity at least 0.50,
  moisture at most 19% for sawn lumber, and main-member thickness at least the
  specified fastener length unless the stated reduced-penetration provision is
  addressed. The trial's nominal 38.1 mm receivers equal the 38.1 mm screw length;
  actual stock dimensions still matter. This report does not supply a complete
  rating for this climbing-frame arrangement.
- [ICC-ES ESR-2236](https://icc-es.org/wp-content/uploads/report-directory/ESR-2236.pdf),
  reissued January 2026, renewal January 2027. Section 4.1 distinguishes tested
  screw connections from NDS-designed connections and requires all applicable
  limit states. Table 4A/4B footnote 4 gives axial-screw minimum edge and end
  distances of 25.4 and 63.5 mm. The backing trial provides 22.225 mm to its
  nearest S edge and at least 35.9029 mm to its X end. It therefore does not
  meet those two conditions for the generic axial-screw route. Generic screw
  steel strength is not wood-connection strength.

File SHA256 identities, with vendor files retained locally only:

```text
ER-280:  bd1c189e6d02407bb14fadcf3e5fea170a78d93a86b0ad58897d3a2fc994772e
ESR-2236: fa4c7b7787c8690a10952bbd1dd7227ebba5ea422fd179f1b74c7c87443ab519
```

## Decision boundary

The generic screw-route shortfall is **not proof that the separately evaluated
ML23Z installation fails**. Connector-specific testing may establish a different
supported application, but that must be demonstrated for the proposed member
arrangement and load direction. Do not invent a favorable combination of generic
SDS values and ML angle geometry. The earlier SCL beam-fastening recommendations
also cannot be transferred to these solid-lumber angle joints.

The [supplemental ML letter](https://ssttoolbox.widen.net/content/iczmiabsx6/pdf/L-C-MLZ25.pdf)
provides directional values and installation figures, not a general combined-load
rule for this frame. In the trial, the bend/F1 axis follows board slope S;
outward backing retention is normal to that axis. F1 is not the desired
board-normal retention rating. The figure interpretation below resolves a
conditional direction mapping; installation applicability still must be
established before assigning a connection allowable.

## Loaded-backing interpretation of the installation figure

The September 8 follow-up compares the letter's page 2 single/end figures with
the actual trial flange and screw directions. Treat the backing rail as the
projecting loaded member, and the side rim as the supporting member. The backing
ends at the rim, with its grain along X. Its angle sits on its rear (+N) face;
the backing-flange screws enter along -N. The supporting rim's grain runs S.
This is a **single/end installation analogy**, not the bearing-table shortcut.

Under that interpretation:

| Manufacturer arrow on the loaded member | Trial direction | ML23Z single/end DF/SP value |
| --- | --- | ---: |
| F1, either direction along the bend | ±S | 405 lbf |
| F2, projecting member pulling away from its supporting member | +X at left end, -X at right end | 300 lbf |
| F3, transverse movement away from the angle-bearing face | -N at both ends | 300 lbf |
| F4, opposite transverse movement | +N at both ends | 500 lbf |

This sign mapping is our interpretation of the published arrows and modeled
contact faces, not an application approval from Simpson. Mirror the rim-end
direction X, not the common backing normal N. Do not apply both positive and
negative F2 values: the opposite direction is member-end bearing, a separate
load path rather than a published negative-F2 rating.

Consequently, the relevant published value to investigate for outward backing
retention is **F3 = 300 lbf (approximately 1,334 N) per ML23Z**, conditional on
the single/end installation being applicable. The 405 lbf F1 and 500 lbf F4
values are not outward-retention substitutes. Nor can two end connectors be
assigned twice 1,334 N as a backing capacity without a valid load-transfer model.

The remaining applicability questions are specific: minimum member dimensions
and the trial's edge/end distances, cross-grain behavior of the supporting rim,
combined directions, and repeated screw removal. The letter requires the
designer to consider mechanical reinforcement where cross-grain bending or
tension cannot be avoided; it does not establish that this particular rim
needs none. The generic axial-SDS spacing shortfall above remains separate
from the connector-specific evaluation route.

## Prepared supplier/reviewer question — not sent

Can an ML23Z connect the rear face of a 38.1 mm-thick × 88.9 mm-high solid
Douglas-fir/larch backing rail to the inside face of a 38.1 mm-thick side rim,
using all four SDS25112 screws? Backing grain runs X across the board; rim grain
runs uphill S. The two contact planes are X/S and S/N, with the bend along S.
The backing can load outward along −N, with additional S/X actions not yet
resolved. The proposed backing screw axes have 22.225 mm nearest S-edge distance
and 35.9029 mm minimum X-end distance; use the actual staggered factory holes.

Our interpretation is the single/end figure with backing -N mapped to F3,
±S to F1, and backing end separation mapped to F2. Please confirm or correct
that interpretation and identify applicable allowable loads, required member
dimensions and edge/end/spacing limits;
combined-load and cross-grain requirements; and whether any repeated removal
and reinstallation of the backing-flange SDS screws is supported. If not,
what listed connector/fastener arrangement supports the required removable
interface? The current trial retains the central backing bolts and relocates
one base-gusset bolt per side; qualification of that changed bolt group is a
separate requirement.

No inquiry or purchase has been made. A supported answer or an independently
designed alternative is needed before promoting this trial into the current
design. Actual panel-to-backing demands remain analytical work, not something
the supplier's rating alone supplies.
