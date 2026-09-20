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

## Decision boundary

Before costing or rating a specific joint, freeze its bolt diameter/head type,
measured bearing-face span, two exact washers, nut height/grade, required thread
projection and thread runout, finish, and source-documented bolt specification.
Then check the full stack against CAD access and all wood/fastener limit states.
No listing supplies a complete joint rating, and no drilling is authorized.
