# Custom Block Final-Size Classification Screen

Status: conditional source screen. It does not change `scenario.json` or
establish an actual grade.

## Scope

This screen covers the four custom block members in the current timber cut
inventory:

| Member group | Proposed finished cross section | Classification screen |
| --- | ---: | --- |
| Center principal cleats | 83.9 × 139.7 mm | Nominal 3.5 × 6 is a candidate; CF unresolved |
| Outer inner-frame blocks | 88.9 × 133.35 mm | No Table 3 nominal class established |

The center members are `center_principal_cleat_left` and
`center_principal_cleat_right`. The outer members are
`knee_outer_left_inner_frame_block` and
`knee_outer_right_inner_frame_block`.

The dimensions are section envelopes. This screen does not calculate net
sections around holes, seats, notches, or other cuts.

## Standard-size screen

ALSC's current Voluntary Product Standard PS 20-25 defines nominal size as a
label that exceeds the dressed dimensions (§2.16, printed p. 10). It defines
dimension lumber as nominally 2 in. to under 5 in. thick and at least 2 in.
wide (§3.4.2, printed p. 11). Section 5.2 says dressed sizes equal or exceed
the minimum sizes in Tables 1 through 4; Table 3 gives these dry minimums for
dimension lumber (printed p. 14):

| Table 3 nominal class | Minimum dry dressed size |
| --- | ---: |
| 3 × 6 in. | 63.5 × 139.7 mm (2.5 × 5.5 in.) |
| 3.5 × 6 in. | 76.2 × 139.7 mm (3 × 5.5 in.) |
| 4 × 5 in. | 88.9 × 114.3 mm (3.5 × 4.5 in.) |
| 4 × 6 in. | 88.9 × 139.7 mm (3.5 × 5.5 in.) |

**Center cleats:** 83.9 × 139.7 mm cannot be nominal 3 × 6 because the
83.9 mm dressed thickness exceeds the 76.2 mm nominal thickness. Nominal
3.5 × 6 is a dimensional candidate: nominal dimensions 88.9 × 152.4 mm are
greater than the proposed dressed dimensions, and the proposed dimensions
meet the Table 3 dry minima of 76.2 × 139.7 mm. This is a candidate only;
the nominal class is not established for the remanufactured piece.

**Outer inner-frame blocks:** 88.9 × 133.35 mm cannot be nominal 4 × 5
because its 133.35 mm width exceeds the 127 mm nominal width. Nominal 4 × 6
has dry minimum dressed dimensions of 88.9 × 139.7 mm, so the proposed
133.35 mm width is undersized. Table 3 lists nominal widths 5 and then 6 in.,
with no 5.5 in. class; the actual 5.25 in. width exceeds nominal 5 while the
nominal 6 dry minimum is wider than this piece. The cited standard classes do
not yield a supported nominal designation for this section; keep it
nonstandard and unresolved.

## NDS size-factor applicability

The 2024 NDS Supplement Table 4A base row for DF-L No. 2 is the existing
scenario's `2 in. & wider` row (printed p. 34). Table 4A's CF table (printed
p. 32) lists thickness groups `2 in. & 3 in.` and `4 in.`; it has no
3.5 in. thickness column. Therefore, even if nominal 3.5 × 6 is selected as
the center-cleat scenario class, this screen has no published Table 4A CF or
Cfu mapping for that thickness. Do not assign a factor by rounding to the
2-and-3 or 4 in. column.

The earlier 4 × 5 hypothesis and its CF = 1.4 route for the outer blocks are
rejected: the proposed actual width is greater than that nominal width. No
alternate CF row is supported for the nonstandard outer section. NDS base
reference values may be looked up conditionally by species and grade, but
they do not resolve either custom section's size adjustment.

These are reference-value and size-class questions, not adjusted resistance
results. No adjustment or FEA elastic constant is assigned here.

## Grade and remanufacture boundary

PS 20-25 states that ripping, resawing, or surfacing graded lumber negates its
original grade, mark, and design values (§7.3.7–7.3.7.1, printed p. 21).
For specified nonstandard sizes, §6.1.6 (printed p. 17) says inspection is
made accordingly and other certified grading-rule provisions apply. Section
8.1.4 (printed p. 21) addresses inspection service for standard grades in
nonstandard sizes, subject to the purchase/sale contract.

Those provisions do not assign DF-L No. 2 to these pieces or define their NDS
nominal-size/CF mapping. WWPA lists No. 2 in its Structural Joists & Planks
category but directs users to its current grading-rules book. PLIB's current
WCLB No. 18 (2024) page lists the framing-grade, design-value, and surfaced-
size sections, while the embedded rule PDFs request a password. The public
rule text reviewed here does not settle these exact remanufactured sizes.

For MVP-E, a hypothetical final DF-L No. 2 grade can remain an explicit
analytical premise with receiving/inspection fields null. It cannot inherit
the source-stock grade. The center candidate still lacks a published CF
mapping, and the outer piece still lacks a supported NDS nominal class and
CF. Thus these custom members cannot be called base-property `inputs_ready`
from this screen alone. Check-specific adjustment inputs remain separate.

No actual final grade, post-rip inspection, certificate, receiving
conformance, or regrade is claimed. Physical observations remain blank.

## Primary sources

1. ALSC, *Voluntary Product Standard PS 20-25*, §§2.16, 3.4.2, 5.2/Table 3,
   6.1.6, 7.3.7–7.3.7.1, and 8.1.4:
   <https://alsc.org/uploaded/PS%2020-25%20Final.pdf>
2. WWPA, “Dimensional Lumber,” category and grading-rules reference:
   <https://www.wwpa.org/western-lumber/structural-lumber/dimensional-lumber/>
3. AWC, 2024 NDS Supplement Chapter 4, Table 4A, printed pp. 32 and 34:
   <https://awc.org/wp-content/uploads/2026/08/AWC_NDS2024-Supplement_20240719_Chapter-4-Reference-Design-Values_Website-1.pdf>
4. PLIB, *WCLB Standard Grading Rules No. 18 (2024)*, current publication
   page and section list:
   <https://plib.org/resources/publications/standard-no-18-2024/>
5. WWPA, publications list for the current grading-rules book:
   <https://www.wwpa.org/resources/>
