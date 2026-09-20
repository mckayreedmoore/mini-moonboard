# Hardware-first connector screen (conditional scope)

Status: source-verified concept research, not an owner-approved frame change,
connector selection, resistance verdict, purchase list, or drilling release.
The owner's earlier instruction limited movement to the center box supports;
the later Astra handoff reports broader permission. Confirmation of which
scope governs is pending. The selected candidate, 66 panel/kicker screw axes,
panel outlines, and archived evidence have not changed.

## Documented factory-hardware shortlist

The [Simpson C-C-2026 p. 315 HL sheet](https://dhcsupplies.s3.us-east-2.amazonaws.com/Documents/simpson-strong-tie/hl-angles.pdf)
was inspected as a page image. Its tabulated DF/SP loads have the shown
`160` duration label; they are not adopted board ratings. A single connector
is the table basis. Both sides are required for F1 lateral resistance in
both directions; uplift may be doubled for two connectors, but lateral may
not. The angle must be centered on a member face at least as wide as the
angle, and the `3`/`5` series requires a minimum 3.5-in wood thickness.
Structural-quality through bolts must be at least ASTM A307 Grade A.

| Model | Width × leg length | Bolts, total | DF/SP uplift / F1, lb | Retail identity |
| --- | --- | --- | --- | --- |
| HL33 | 3.25 × 2.5 in | 2 × 1/2 in | 740 / 1,040 | [Home Depot HL33-R](https://www.homedepot.com/p/100375377); `-R` equivalence not yet verified |
| HL35 | 3.25 × 5 in | 4 × 1/2 in | 740 / 1,310 | [Home Depot HL35-R](https://www.homedepot.com/p/100374913); `-R` equivalence not yet verified |
| HL53 | 5.75 × 2.5 in | 4 × 1/2 in | 740 / 1,310 | [Home Depot HL53](https://www.homedepot.com/p/205227146), exact model |

The HL table labels D1–D4 nominal hole-position dimensions, but the generic
illustration does not by itself establish a full shop hole-center tolerance
schedule for every model. Confirm the exact occupied factory pattern and
received variation before any wood drilling. The listed uplift/F1 directions
do not cover arbitrary flange moments, separation, mixed actions, or joint
stiffness; each demands its own applicable route if present.

For comparison, the [MiTek B-series table](https://www.mitek-us.com/wp-content/uploads/2020/12/B_-BL.pdf)
states a 3-in minimum member thickness, ASTM A307-or-better bolts, and
single-brace F1/F2 values that already include a 60% wind/seismic increase.
It requires braces on both sides for F1 in both directions. B66 uses four
3/8-in bolts, with 710/335 lb F1/F2; B88 uses six 3/8-in bolts, with
620/305 lb. These values are not adopted for the board's load duration.
The [Home Depot UB88 listing](https://www.homedepot.com/p/313507573) and
the existing `mitek-b66-retail.json` record provide a manufacturer/retailer
model cross-reference, but the inspected B88 drawing does not dimension all
hole centers. The previously checked Lowe's B66 listing was no longer sold.

## Smallest-change concept to investigate if broader scope is confirmed

Start with HL35 on solid 4×6 actual 3.5 × 5.5 in receiving stock for
*both sides* of the center principal/header and center post/header duties:
the center principal, header, and center post all require a thick receiving
member under the catalog detail. Keep the current
panel-bearing faces and panel screw axes fixed while allowing extra timber
depth behind them; do not assume the substituted solids fit adjacent members.
HL35 has a narrower face width but a longer leg than an HL53-on-4×8 route,
while offering four
specified bolts and a directly cataloged wood-joint load basis. An opposing
HL35 pair is a *conditional concept* for reversible F1, not a verified joint.
The center assembly needs its own upper/lower flange orientation, actual
factory-hole layout, bolt stacks, oblique-end/edge distances, support for
the kerf-right kicker edges, and disassembly access. If those fail, compare
one B88-on-solid-thick-member concept; do not default back to BR904 simply
because its earlier prototype is further along.

This screen changes no raw geometry. It does not establish that a 4×6 can
replace both 2×6 pieces without moving other support, that the old twelve
frame bolts remain viable, or that either catalog's isolated load directions
cover the simultaneous joint wrench. No fabrication action follows.
