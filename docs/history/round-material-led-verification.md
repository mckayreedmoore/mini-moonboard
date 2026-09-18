# AC fir plywood and current Mini LED kit verification

Checked September 11, 2026. This records the owner's clarified inputs without
changing the current solver batch, historical references or CAD dimensions.

## Retain the identified AC fir plywood

The supplied Lowe's link remains the purchase identity: item 12235 / model
119055. Its current listing identifies Douglas fir, A-face/C-back sanded plywood,
Exterior exposure, PS1-09 and 23/32 CAT. Listed actual thickness is 0.718 in
(18.2372 mm); the existing 23/32 category model is 18.25625 mm. Neither number
is a measurement of the delivered sheets. Keep this purchase as **AC fir**;
there is no basis here to substitute Structural I plywood.
[Lowe's exact product](https://www.lowes.com/pd/Roseburg-23-32-CAT-PS1-09-Square-Structural-Plywood-Douglas-Fir-Application-as-4-x-8/1000015973).

Roseburg's current exterior-core page describes its AC Fir sample as 23/32 in,
5-ply, sanded A face and touch-sanded C back. Its sanded-plywood brochure lists
both 5- and 7-ply versions at that category and describes western-wood core and
back veneers. Consequently, the family is identified, but the exact veneer
layup of the purchased lot is not. Do not treat AC fir as an all-Douglas-fir
marine layup or transfer the Structural I designation shown for different
products on the same page.
[Roseburg exterior-core products](https://www.roseburg.com/softwood-plywood/exterior-core/),
[Roseburg sanded-plywood brochure](https://www.roseburg.com/wp-content/uploads/2026/03/SandedPlywood_Brochure.pdf).

For analysis, use the sanded-plywood material category. APA's Panel Design
Specification is the appropriate panel-capacity reference; species group,
performance category and stress direction govern selection. APA identifies
species group in the trademark of non-span-rated sanded panels. Its general
strength-axis convention is the long sheet direction unless otherwise marked.
Track that original axis when cutting squares: a square's shape does not
identify its material orientation. Published face/back-group and construction
rules must be applied before assigning one set of panel capacities. The current
isotropic elastic model does not acquire orthotropic plywood qualification from
this product identification.
[APA plywood selection and design basis](https://www.apawood.org/engineered-wood-products/plywood-osb/plywood/),
[APA sanded-plywood guide](https://www.apawood.org/guides-tools-training/technical-document-library/product-guides/sanded-plywood/).

The Lowe's width fields are inconsistent: nominal 4 ft, listed actual 3.953 ft,
and listed industry minimum 3.99 ft. Preserve the required panel grid and retain
usable dimensions as a fabrication check. This listing inconsistency is not a
reason to discard the identified product or assume a smaller finished panel.
[Lowe's specifications](https://www.lowes.com/pd/Roseburg-23-32-CAT-PS1-09-Square-Structural-Plywood-Douglas-Fir-Application-as-4-x-8/1000015973).

## Current official LED purchase basis

Moon's current US Mini MoonBoard LED System product is SKU **60-171-V5**.
The listing mixes legacy two-string and three-string descriptions and contains
an inconsistent total in one contents bullet. Use the current V5 installation
guide's **three 50-LED strings** as the development configuration, consistent
with the existing selected route. The guide specifies the supplied 5 V system.
No later-version purchase assumption is supported by the reviewed official
product and guide pages.
[Current US Mini kit](https://us.moonclimbing.com/products/mini-moonboard-led-kit),
[V5 50-LED installation guide, November 2025](https://moonclimbing.com/media/moonboard-pdf/MB_LED_Installation_V5%2050%20LED%20Nov%202025.pdf).

The owner's clarified instruction is to use the current purchasable Moon kit.
That identifies the selected product without requiring another version question.
It does not by itself prove that a particular physical kit has been received;
retain any earlier ownership statement as historical context rather than a new
inspection result.

## What the schematics specify about spacing

The Mini panel specification fixes installed hole positions. The existing
project grid already follows that positional reference, including the panel
seam offset. The LED guide specifies nominal 13 mm panel holes and routing up
one column and down the next. Those are installed positions and topology.
[Mini metric panel specification](https://moonclimbing.com/media/moonboard-pdf/Mini_MoonBoard_Template_Guide_Metric.pdf),
[Moon build guide](https://moonclimbing.com/build-your-moonboard).

No physical inter-bulb wire/base pitch, connector length, cable diameter or
minimum bend radius was found in the reviewed current product page or V5
installation guide. The schematic's hole spacing must therefore remain distinct
from the available cable path between bulbs. A timber detour needs more cable
than the straight distance between installed hole centers. The guide's nominal
13 mm hole also does not establish the maximum connector envelope.
[V5 installation guide](https://moonclimbing.com/media/moonboard-pdf/MB_LED_Installation_V5%2050%20LED%20Nov%202025.pdf).

The repository already records an earlier owner-reported **approximately 12 in
(304.8 mm) bulb-base spacing** and **12.7 mm maximum harness diameter**. Retain
those as provisional physical-harness inputs, with their original provenance;
do not relabel them as manufacturer schematic dimensions. The 25.4 mm passages,
30 mm connector length, 4 mm cable diameter and 8 mm bend-radius model remain
explicit development choices where no corresponding product dimension is
available. See the existing
[round wiring reference](round-service-wiring-reference.json) and
[routing record](led-wiring-reference.json).

## Recommended input treatment

- Keep the purchased AC fir plywood and existing nominal thickness; carry the
  listed actual thickness as a sensitivity case, not a measured replacement.
- Use sanded-plywood directional properties in the next material-model revision;
  preserve original sheet axes and make any assumed species-group/layup case
  explicit. Do not label the current isotropic FEA as AC plywood qualification.
- Keep the V5 three-string routing and official fixed hole grid. Retain 304.8 mm
  as the earlier reported provisional cable-path budget; do not replace it with
  the hole-center spacing.
- Preserve measured-versus-assumed provenance. Product identification closes
  the selection question; unpublished component dimensions and material-lot
  properties remain bounded analysis/physical-fit inputs, not missing product
  choices to ask the owner to repeat.

## Active-route scope and the rest of the physical kit

Fresh visual review of printed pages 4–5 confirms one daisy-chained data path:
LED1 supplies A1, each 50-LED string connects to the next, and PWR1 supplies the
supplementary two-wire feed at the end of string two. The depicted procedure
does not distribute the three strings over separate controller outputs.
[Moon's corresponding 50-LED installation instructions](https://moonclimbing.com/build-your-moonboard).

The Mini drawing has 11 columns and 12 active LED positions per column. Its
kicker drawing has ten foothold holes and no additional LED row. The metric
schematic dimensions describe these installed positions: 200 mm columns,
100 mm hold-to-LED vertical offsets, and the additional panel-joint offset.
They do not dimension an uninstalled strand's wire length.
[Mini metric schematic](https://moonclimbing.com/media/moonboard-pdf/Mini_MoonBoard_Template_Guide_Metric.pdf).

Three 50-bulb strings minus 132 installed positions leave 18 unused bulbs by
arithmetic. The V5 guide instead says 16 spare bulbs and provides no resolution
of that discrepancy. No terminator specification was found. Retain the factory
unused tail; no cut or replacement terminator is prescribed here.
[V5 guide, printed pages 1 and 4–5](https://moonclimbing.com/media/moonboard-pdf/MB_LED_Installation_V5%2050%20LED%20Nov%202025.pdf).

The current CAD can retain its 132 active bulb envelopes and 131 successive
connections as an **active-route subset**. Completing the kit representation
requires separate modeling of the unused tail, A1 input lead, the power-feed
branch at index 100, extensions, controller and supply. The model's cylinders
at joins 50/51 and 100/101 are provisional connector envelopes; they are not
verified JST SM connector shapes or a complete representation of the power
branch. Those joins map to E2/E3 and I4/I5 by counting the existing route. None
of these omissions requires changing the active A1-to-K12 sequence, but they
prevent a claim that the displayed assembly contains the complete physical kit.
