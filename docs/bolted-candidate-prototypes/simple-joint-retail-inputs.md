# PB-01 simple-joint retail inputs (source inventory only)

Checked 2026-09-20. These are ordinary Home Depot/Lowe's online listings, not a
selected, tested, or approved structural fastener stack. Prices and availability
depend on store/ZIP and can change. No purchase or manufacturer contact occurred.

## Two diagnostic grips

| Path | Wood-only nominal grip | Conversion | Length implication |
| --- | ---: | ---: | --- |
| Rail-to-cleat | 38.1 + 57.15 = 95.25 mm | 3.750 in | 4 in leaves only 6.35 mm; investigate 5 in |
| Upright-to-cleat | 38.1 + 200 = 238.1 mm | 9.374 in | 10 in leaves only 15.9 mm |

Bolt length is measured under the head and must also cover washer thicknesses,
full nut engagement, suitable thread projection, manufacturing tolerances, and
any countersink or nonflat face. A 10-in bolt's 15.9-mm residual is especially
small. Threaded length and unthreaded shank location must suit the actual grip.
Neither length is specified for construction on this arithmetic alone.

## Bolt leads

| Retail listing | Identifiers | Visible price / pack | Source-bound notes |
| --- | --- | --- | --- |
| [Home Depot Everbilt galvanized 3/8-16 × 5-in hex bolt](https://www.homedepot.com/b/Hardware-Fasteners-Bolts-Hex-Bolts/3-8-in/5-in/A307/N-5yc1vZc2c0Z1z0sfy6Z1z1bterZ1z1btld) | Model 805606 | $2.21 / 1 | HD filter says A307; product-specific grade and thread length still need confirmation. |
| [Home Depot Everbilt zinc 3/8-16 × 5-in hex bolt](https://www.homedepot.com/p/204645573) | Model 800906; Internet 204645573 | $1.11 / 1 on category page | A307 category lead; product-specific grade/thread length not established here. |
| [Lowe's Hillman galvanized 3/8-16 × 5-in hex bolt](https://www.lowes.com/pd/Hillman-3-8-in-x-5-in-Galvanized-Coarse-Thread-Hex-Bolt/3058911) | Item 67309; model 811593 | $2.07 / 1; $1.86 each at 25+ | Listing calls grade “all-purpose,” not a verified ASTM grade; partially threaded. |
| [Home Depot Everbilt galvanized 3/8-16 × 10-in carriage bolt](https://www.homedepot.com/p/204633646) | Model 805086; Internet 204633646; SKU 348175 | $4.06 / 1 | Supplier Q&A says ASTM A307 Grade A; square neck requires a compatible wood seat. Thread length not verified. |
| [Home Depot Prime-Line galvanized 3/8-16 × 10-in carriage bolts](https://www.homedepot.com/p/310499925) | Model 9064160; Internet 310499925 | $26.58 / 10 ($2.66 each) | Listing explicitly says ASTM A307A and ASME B18.5; nuts/washers excluded. Thread length not shown. |
| [Lowe's Hillman zinc 3/8-16 × 10-in hex bolt](https://www.lowes.com/pd/Hillman-3-8-in-16-x-10-in-Standard-SAE-Hex-Bolt/3036218) | Item 59068; model 190231 | ZIP-dependent; 1 | Page says Grade 1, not A307; no usable displayed price or thread length. |

The 10-in A307 carriage bolts are genuine ordinary retail leads, but neither
is a cleared 238.1-mm stack. A carriage head/square neck differs from the
trial hex-head geometry and needs its own seating, washer, and access model.
The Lowe's 12-in Hillman hex-bolt 50-pack, model 811604, is [marked no longer
sold](https://www.lowes.com/pd/Hillman-3-8-in-x-12-in-Coarse-Thread-Hex-Bolt-50-Count/4261921).
This bounded search found no readily priced, product-specific A307 3/8-in
extra-long hex bolt at these retailers; it did find the A307 carriage leads.

## Nut and washer leads

| Retail listing | Identifiers | Visible price / pack | Selection caveat |
| --- | --- | --- | --- |
| [Home Depot Everbilt galvanized 3/8-16 hex nut](https://www.homedepot.com/p/204274098) | Model 804060; SKU 538744 | $33.66 / 100 | Grade 2, hot-dip zinc per listing; 100-pack price is not a one-joint cost. |
| [Lowe's Hillman galvanized 3/8-16 hex nut](https://www.lowes.com/pd/Hillman-3-8-in-x-16-Galvanized-Steel-Hex-Nut/3037535) | Item 67341; model 810509 | $0.32 / 1 | Listing says ASTM A153 coating; mechanical nut grade not verified on page. |
| [Lowe's Hillman hot-dip galvanized 3/8-in flat washer](https://www.lowes.com/pd/Hillman-1-Count-0-400-in-x-Hot-Dipped-Galvanized-Standard-SAE-Flat-Washer/3037541) | Item 67390; model 811072 | $0.33 / 1 | Outside diameter/thickness and wood bearing adequacy need checking. |
| [Home Depot Everbilt galvanized 3/8-in flat washer](https://www.homedepot.com/b/Hardware-Fasteners-Washers/Galvanized/3-8-inch/N-5yc1vZc276Z1z1bm6hZ1z1bt70) | Model 807290 | $31.75 / 100 | Nominal fit only; bearing area/thickness not established. |
| [Home Depot Everbilt galvanized 3/8 × 1-1/2-in fender washer](https://www.homedepot.com/p/314519970) | Model 813096; Internet 314519970 | $12.69–$17.28 / 50 on separate page views | 1.5-in OD equals nominal 38.1-mm member width: zero edge margin; thin-fender bending unverified. |
| [Lowe's Hillman zinc 3/8 × 1-1/4-in fender washer](https://www.lowes.com/pd/Hillman-2-Count-3-8-in-x-1-1-4-in-Zinc-Plated-Standard-SAE-Fender-Washers/999996020) | Item 755759; model 885527 | $1.78 / 2 | OD 1.25 in; listing says 0.062-in thick. Bearing/bending still unverified. |

The washer must be selected by wood compression and washer bending, not just
diameter or store availability. A washer on each exposed wood face is a
diagnostic assumption, not a final count. Mixed finishes in this table are
alternatives, not one compatible bill of materials.

## Conditional grain-N 4×4 cleat trial: 127-mm upright grip

If the grain-N 4×4 cleat pose survives geometry and mechanics checks, its
upright wood grip is 38.1 + 88.9 = 127 mm (exactly 5.0 in). A 5-in bolt leaves
no length for washers, nut, or thread projection. A 6-in bolt leaves 25.4 mm
before those items and tolerances; that is a sourcing lead, not a stack check.

| Retail hex-bolt lead | Identifiers | Visible price / pack | Standard and thread evidence |
| --- | --- | --- | --- |
| [Home Depot Everbilt galvanized 3/8-16 × 6-in](https://www.homedepot.com/p/204645579) | Model 805626; SKU 214256 | $2.36 / 1 on product page; category showed $2.24 | HD A307 category includes it. [Supplier Q&A](https://www.homedepot.com/p/questions/Everbilt-3-8-in-16-x-6-in-Galvanized-Hex-Bolt-805626/204645579/2) claims 6-in thread length, but no dimensioned drawing was found; verify before use. |
| [Home Depot Everbilt galvanized 3/8-16 × 6-in, 15-pack](https://www.homedepot.com/p/204281475) | Model 805620 | $31.86 / 15 ($2.12 each) | HD A307 filter includes it; thread length not specified on pack listing. |
| [Lowe's Hillman galvanized 3/8-16 × 6-in](https://www.lowes.com/pd/Hillman-3-8-in-x-6-in-Galvanized-Coarse-Thread-Hex-Bolt/3824903) | Item 67310; model 811597 | $2.33 / 1 | Product specifications explicitly say A307 and “Full Thread: No”; thread length not stated. Its Q&A shows a thread-length question but not its answer. |
| [Home Depot Everbilt zinc 3/8-16 × 6-in, 25-pack](https://www.homedepot.com/p/204273569) | Model 800910 | $32.18 / 25 ($1.29 each) | Product specifications explicitly say A307; thread length not stated. Different finish from galvanized leads. |

This bounded Lowe's/Home Depot search did not find an ordinary 3/8 × 6.5-in
**hex** bolt listing; a 6.5-in carriage bolt is not the same head/seat geometry.
All prices and local availability need ZIP/store recheck. Resolve the actual
bolt shank/thread geometry, washer/nut stack, access and joint limit states
before any selection, purchase, or drilling.

## Conditional 4×6 cleat stock check

The 4×4 CAD trial has 88.9 mm along X, placing a centered rail-bolt axis only
44.45 mm from that end. A 4×6 could increase this distance **only if** its long
face is oriented along X; bolt placement, edge/end distances, wood properties,
access, and the complete joint would all need a new check. Retail actual sizes
also differ, so neither product can silently replace the CAD's 88.9-mm stock.

| Retail lumber listing | Species / grade | Listed actual size | Price / status |
| --- | --- | --- | --- |
| [Lowe's 4×6×8 green lumber](https://www.lowes.com/pd/4-in-x-6-in-x-8-ft-Douglas-Fir-Lumber-Common-3-562-in-x-5-625-in-x-8-ft-Actual/1000028917) | Douglas fir, #2 & Better; model 637637, item 92730 | 3.562 × 5.625 in × 8 ft | “Get Pricing & Availability”; no visible price without ZIP/store. No “no longer sold” notice on this listing. |
| [Lowe's 4×4×8 green lumber](https://www.lowes.com/pd/4-in-x-4-in-x-8-ft-Douglas-Fir-Lumber-Common-3-562-in-x-3-562-in-x-8-ft-Actual/1000028905) | Douglas fir, #2 & Better; model 637630, item 92331 | 3.562 × 3.562 in × 8 ft | “Get Pricing & Availability”; no visible price without ZIP/store. |
| [Home Depot 4×6×8 S4S lumber](https://www.homedepot.com/p/202084523) | Douglas fir, No. 2 & Better S4S; model 0405438, SKU 603775 | 3.5 × 5.5 in × 8 ft | No visible price or confirmed local stock; page says product may vary by store. |
| [Home Depot 4×4×8 lumber](https://www.homedepot.com/p/202083082) | Douglas fir, #2 Premium; model 328329, SKU 441856 | 4×4×8 nominal; actual size not verified here | No visible price; not a same-grade cost comparator. |

Thus ordinary untreated #2-or-better Douglas-fir 4×6×8 **is listed online**;
the search did not establish current local availability or a 4×6/4×4 cost
delta. Separately, [Lowe's above-ground pressure-treated Douglas-fir
4×6](https://www.lowes.com/pd/Severe-Weather-4-in-x-6-in-x-8-ft-2-and-Btr-Douglas-Fir-Above-Ground-Pressure-Treated-Lumber/5001634919)
is a different treatment/fastener case, and [Home Depot's #2 Hi-Bor
4×6](https://www.homedepot.com/p/202087810) is pressure-treated, not an
untreated substitute. A Lowe's #2 SYP ground-contact 4×6 listing is [marked
no longer sold](https://www.lowes.com/pd/Severe-Weather-Common-4-in-X-6-in-x-8-ft-Actual-3-5-in-x-5-5-in-x-8-ft-2-Treated-Lumber/50113120).
None of these listings establishes a viable bolted joint or authorizes a buy.

## Conditional 4×6 grain-N cleat trial: 177.8-mm upright grip

If the 4×6 grain-N cleat geometry is retained, its proposed upright wood-only
grip is 38.1 + 139.7 = 177.8 mm (7.0 in). A 7-in bolt has no remaining length
for washers, nut or thread projection. An 8-in bolt leaves 25.4 mm before
those items and tolerances; this does not establish a complete usable stack.

| Retail 3/8-16 × 8-in hex-bolt lead | Grade evidence | Visible price / pack | Thread caveat |
| --- | --- | --- | --- |
| [Home Depot Everbilt galvanized](https://www.homedepot.com/p/204645581), model 805636, SKU 214966 | Listed in HD's [A307-filtered 8-in category](https://www.homedepot.com/b/Hardware-Fasteners-Bolts-Hex-Bolts/3-8-in/8-in/A307/N-5yc1vZc2c0Z1z0sfy6Z1z1bterZ1z1btk0) | $2.93 / 1 | Exact threaded length not found in the product listing. |
| [Lowe's Hillman galvanized](https://www.lowes.com/pd/Hillman-3-8-in-x-8-in-Galvanized-Coarse-Thread-Hex-Bolt/3824905), item 67311, model 811601 | Product specification explicitly says A307 | $2.83 / 1 | Partially threaded; no dimensioned thread length visible. |
| [Home Depot Everbilt zinc](https://www.homedepot.com/p/204273582), model 800930 | Product specification explicitly says A307 | $41.40 / 25 ($1.66 each) | Listing gives 6-in thread length; shank/thread transition still needs checking against final grip. |
| [Home Depot Prime-Line hot-dip galvanized](https://www.homedepot.com/p/310465220), model 9060208 | Listing explicitly says ASTM A307A and ASME B18.2.1 | $12.56 / 10 ($1.26 each) | Thread length not shown; page calls it hot-dip galvanized but a specification field says “Uncoated,” so finish needs reconciliation. |

These are ordinary online retail listings, not proof of local shelf stock.
Verify thread runout, both washers, nut engagement and projection, finish,
access, and every joint limit state before choosing any bolt. No approval to
buy or drill follows from the 8-in length or A307 label.

## Decision boundary

Before costing or rating a specific joint, freeze its bolt diameter/head type,
measured bearing-face span, two exact washers, nut height/grade, required thread
projection and thread runout, finish, and source-documented bolt specification.
Then check the full stack against CAD access and all wood/fastener limit states.
No listing supplies a complete joint rating, and no drilling is authorized.
