# PB-02 ordinary-store stock and cut-yield sidecar

Status: **length-feasible example for one right post and two cleats only**.
This is a stock screen for the latest [link-edge trial](simple-center-link-edge-probe.md),
read on 2026-09-20. It is not a full-frame bill, a local stock or price check,
or a fabrication release. No contact or purchase was made.

## Exact retailer listings checked

Dimensions below reproduce each retailer's *listed* values, not measured
delivered stock. “Minimum” means the field explicitly labeled industry
standard minimum on the listing; a blank means no such value was published.

| Source and exact listing | Grade/species/treatment evidence | Nominal; listed actual; listed minimum |
| --- | --- | --- |
| [Home Depot #300874740, model 279542](https://www.homedepot.com/p/4-in-x-4-in-x-8-ft-2-Premium-Grade-Dimensional-Lumber-279542/300874740) | 4×4 No. 2 Douglas fir; listing Q&A says untreated; store variation noted | 4×4×8 ft; 3.5×3.5 in × 8 ft; minimum unpublished |
| [Lowe's item 92331, model 637630](https://www.lowes.com/pd/4-in-x-4-in-x-8-ft-Douglas-Fir-Lumber-Common-3-562-in-x-3-562-in-x-8-ft-Actual/1000028905) | 4×4 #2 & Better Douglas fir, green; says “anti-stain treated,” so chemical treatment status is **ambiguous** for an untreated-only requirement | 4×4×8 ft; 3.562 in thickness, 3.5625 in width, 8 ft length (overview rounds both to 3.562 in); minimum 3.562×3.562 in × 8 ft |
| [Lowe's item 330568, model 20496 KDDFL](https://www.lowes.com/pd/2-in-x-4-in-x-8-ft-2-Douglas-Fir-Kiln-Dried-Lumber/5003667531) | 2×4 #2 Douglas fir, kiln dried; dimensional-lumber listing says AWPA standards: no, but does not explicitly state “untreated” | 2×4×8 ft; 1.5×3.5 in × 8 ft; minimum 1.5×3.5 in × 7.72 ft |
| [Lowe's item 45116, model 5240-8](https://www.lowes.com/pd/Top-Choice-2-x-4-x-8-ft-Douglas-Fir-Lumber-Common-1-562-in-x-3-562-in-x-8-ft-Actual/1000009810) | 2×4 #2 & Better Douglas fir, green; treatment status not explicit | 2×4×8 ft; 1.562×3.562 in × 8 ft; minimum 1.562×3.562 in × 8 ft on the full listing |

The Home Depot [2×4 FIR #2 model 2x4x8KDDF](https://www.homedepot.com/p/2-in-x-4-in-x-8-ft-FIR-2-Standard-Grade-Dimensional-Lumber-2x4x8KDDF/328469665)
lists 2×4×8 ft nominal and 1.5×3.5×96 in actual, but its accessible
listing calls the species only “FIR.” It is not evidence of exact Douglas fir
or DF-L species. The Home Depot [#2 Grade Fir model 15005](https://www.homedepot.com/p/2-in-x-4-in-x-8-ft-2-Grade-Fir-Dimensional-Lumber-15005/323425314)
also says species may vary by region. Neither is counted as an exact 2×4
species match. No listed numeric price was available without selecting a
store/ZIP; “Get Pricing & Availability” is not a price. No price estimate is
made. These are online catalog records, not proof of stock at any location.

## One-post cut-yield calculation

The modeled [trial](simple-center-link-edge-probe.md) uses one right post
88.9×88.9×238.9 mm, one side cleat finished 88.9×56.8×183 mm from an
88.9×88.9×183 mm 4×4 blank, and one rear cleat 88.9×38.1×460 mm from 2×4.
The side cleat **requires a lengthwise rip from 4×4**. An uncut 2×4 is only
38.1 mm thick in the listed kiln-dried option, below the 56.8 mm modeled
depth. Grain runs along each cut length.

Example allowance: one **3.2 mm crosscut kerf per separated piece**, including
the final separation from the long remainder; one **3.2 mm rip kerf** on the
side blank. This is an assumed blade allowance, not a specified or verified
tool. End trim, squaring, defect rejection, and planing loss are **0 mm in
this arithmetic** and must be added if needed. 8 ft = 2438.4 mm; the Lowe's
kiln-dried 2×4 listed minimum of 7.72 ft = 2353.056 mm.

| Stick | Cuts and kerf | Consumed | Uncut length remainder |
| --- | ---: | ---: | ---: |
| One 8 ft 4×4 | 238.9 + 183 + 2×3.2 mm | 428.3 mm | **2010.1 mm** |
| One 8 ft 2×4 | 460 + 3.2 mm | 463.2 mm | **1975.2 mm** |
| Lowe's kiln-dried 2×4 at its listed 7.72 ft minimum | 460 + 3.2 mm | 463.2 mm | **1889.856 mm** |

These remainders are uncut stock length, not usable yield for another
specified PB-02 part. The two 4×4 pieces cannot be co-located in the same
length: each cut requires its own longitudinal segment. With an exactly
88.9-mm-depth 4×4 blank, the rip removes 88.9−56.8 = 32.1 mm total,
including 3.2 mm blade kerf, leaving a **28.9 mm nominal offcut width**.
The rip also creates sawdust along 183 mm; no volume/weight waste is claimed.
Run `.venv/bin/python scripts/simple_center_stock_yield.py` to reproduce the
length and rip arithmetic.

## Section and procurement limits

The Home Depot 4×4 lists an 88.9×88.9 mm *actual* section, matching the CAD
numbers, but publishes no minimum section or tolerance. The Lowe's green 4×4
minimum 3.562 in is 90.4748 mm, so making the 88.9-mm CAD X width and post
depth would require additional sizing cuts and would alter the rip offcut.
The listed Lowe's kiln-dried 2×4 section is exactly 38.1×88.9 mm, matching
the rear cleat on paper; its published minimum length still easily supplies
460 mm. The green Lowe's 2×4 at 1.562×3.562 in is larger and likewise needs
sizing for an exact 38.1×88.9 mm section. Species stamps, chemical treatment,
actual dimensions, straightness, defects, and section after cutting must be
checked on the delivered piece. A straight full-depth 183-mm rip through
4×4 also depends on saw capacity and safe workholding. The prior CAD fit,
fastener and load-path gaps remain open. No drilling or fabrication follows.
The catalog's "Douglas fir" wording alone does not verify the DF-L
design-species group assumed by the conditional connection calculations;
the delivered grade stamp and applicable grading rules must be checked.
