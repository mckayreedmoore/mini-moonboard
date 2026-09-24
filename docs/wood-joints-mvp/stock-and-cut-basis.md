# Wood-joint stock and cut basis

Status: **conditional stock and yield screen**, dated 2026-09-23. No wood has
been ordered, received, measured, inspected, cut, or drilled for this candidate.
This document binds only to the currently modeled WJ-03 outer-node blanks,
the WJ-05 center-backer trial, and the active WJ-04 workhorse geometry. It is
not a bill of materials, cut ticket, strength acceptance, or fabrication
release.

## Stock-path finding

The six WJ-03 solid connector parts and two diagnostic WJ-05 backers have
square 88.9 × 88.9 mm sections and differ only in their along-grain cut
lengths. A catalog-listed 4×4 No. 2 solid-sawn product has listed 88.9 ×
88.9 mm actual section and 8 ft length. Under the assumed 3.2 mm crosscut
kerf, one such stick has enough *length* for all eight modeled blanks, with
about 258 mm left before any end trim or defect loss. Crosscut-only parts do
not require regrading under NDS §4.1.7.2; final member dimensions, grade
identity, grain, moisture condition, and connection-zone condition still
need verification.

WJ-04 active cleat is 95.25 × 38.1 × 119.7 mm in local X × T × N, with grain
along N. A solid 2×6 is the direct stock lead: orient its 139.7 mm width along
X and its 38.1 mm thickness along T, rip X to 95.25 mm, then crosscut N to
119.7 mm. It needs one longitudinal rip, not a 4×6 or 6×6 resaw. The reviewed
retail listing gives a solid #2 Prime Douglas-fir KD 2×6 at 38.1 × 139.7 mm,
but it identifies its species only as “Douglas fir,” describes an
unspecified anti-stain treatment, and does not establish the final grade
after the nonstandard-width rip. NDS §4.1.7.1 requires structural lumber that
is resawn or remanufactured to be regraded. Until a valid post-rip grade or
inspection certificate, or another grade-supported source for the finished
section, is identified, this is a *dimensionally realizable raw-stock lead*,
not a qualified DF-L No. 2 cleat source.

The WJ-04 2×6 orientation also corrects the earlier 6×6 source suggestion:
the 95.25 mm X width fits within a 2×6's 139.7 mm width, while its T thickness
is already 38.1 mm. Do not carry the earlier 100 × 53.34 mm proposal into this
cut basis; it is not the active joint-contract geometry.

## Modeled blanks and grain

Dimensions below are nominal CAD blank dimensions before the recorded bores
or counterbores. Grain follows each part's longest modeled dimension. The six
outer-node parts come from [`wood_joint_frame.py`](../../mini_moonboard/wood_joint_frame.py);
the two center backers come from the [WJ-05 transfer trial](wj05-center-backer-transfer.md).

| Scope / part | Count | Blank dimensions (mm) | Along-grain axis | Stock basis |
| --- | ---: | --- | --- | --- |
| WJ-03 outer spine | 2 | 88.9 × 88.9 × 269.95 | Z | 4×4 solid-sawn, crosscut only |
| WJ-03 rear bridge | 2 | 383.2 × 88.9 × 88.9 | X | 4×4 solid-sawn, crosscut only |
| WJ-03 under-header link | 2 | 185.2 × 88.9 × 88.9 | X | 4×4 solid-sawn, crosscut only |
| WJ-05 center backer trial | 2 | 88.9 × 88.9 × 238.9 | Z | 4×4 solid-sawn, crosscut only |
| WJ-04 workhorse cleat trial | 1 | 95.25 × 38.1 × 119.7 (X × T × N) | N | 2×6 solid-sawn; rip X, then crosscut N; regrade after rip |

The first four rows total eight 4×4 cutoffs. The last row is one diagnostic
workhorse cleat, not a count for every similar station. None of these rows
defines the full connector or frame bill.

## Catalog stock evidence

Catalog pages are leads only. They do not prove local inventory or delivered
dimensions, grade stamp, species group, moisture, treatment, grain quality,
straightness, or condition of any connection zone. Pages were reviewed
2026-09-23; their prices and availability are location-specific.

| Needed stock | Reviewed listing | Listed properties | Remaining check |
| --- | --- | --- | --- |
| WJ-03/WJ-05 4×4 | [Home Depot #279542, 4×4×8 ft No. 2 Premium](https://www.homedepot.com/p/4-in-x-4-in-x-8-ft-2-Premium-Grade-Dimensional-Lumber-279542/300874740) | Douglas fir; No. 2; 3.5 × 3.5 in actual; 8 ft actual; supplier answer describes it as untreated; product may vary by store | Listing does not state DF-L species-group stamp, minimum section, or moisture condition. Verify the actual grade mark/certificate, delivered section, treatment, and moisture before assigning the source material basis. |
| WJ-04 2×6 | [Lowe’s model 720966-8, 2×6×8 ft No. 2 Prime Douglas-fir KD](https://www.lowes.com/pd/Top-Choice-2-in-x-6-in-x-8-ft-Douglas-Fir-Lumber-Common-1-5-in-x-5-5-in-x-8-ft-Actual/1000571215) | Douglas fir; No. 2 Prime; kiln-dried; 1.5 × 5.5 in actual and listed minimum; 8 ft length; page says “anti-stain treated” and “Meets AWPA Standards: No” | Exact DF-L group and treatment identity are not listed. More importantly, the cut 95.25 mm width is remanufactured stock: obtain applicable post-rip grade evidence before using structural reference values. |

The [ALSC lumber program](https://alsc.org/) describes PS 20 grade marking
and its accredited inspection system. NDS §4.1.2.1 requires lumber using
reference design values to be identified by a recognized grading/inspection
agency grade mark or inspection certificate. A retailer's category label
alone does not establish that evidence. The WJ-03 part descriptors currently
say “DF-L No. 2 assumed; delivered stock unobserved” in
[`wood_joint_frame.py`](../../mini_moonboard/wood_joint_frame.py); WJ-08 must
define and authenticate this candidate's material basis. The separate bolted
candidate material record does not automatically apply to this lane. If WJ-08
adopts the WJ-03 assumption, the catalog descriptions still need delivered
stock evidence for DF-L, grade, moisture, treatment, dimensions, and each
connection zone.

## Crosscut yield for the eight known 4×4 blanks

Assumption for arithmetic only: one 3.2 mm kerf per separated cutoff,
including the cut that frees the last piece. Source length is 8 ft = 2438.4
mm. The starting stock end is assumed square and usable; no end trim, defect
exclusion, surfacing, moisture-change, or dimensional allowance is included.

| Cutoffs | Count | Length each (mm) | Total length (mm) |
| --- | ---: | ---: | ---: |
| Rear bridges | 2 | 383.2 | 766.4 |
| Outer spines | 2 | 269.95 | 539.9 |
| Center backers | 2 | 238.9 | 477.8 |
| Under-header links | 2 | 185.2 | 370.4 |
| **Total finished blank length** | **8** | — | **2154.5** |

| Yield arithmetic | Length (mm) |
| --- | ---: |
| Finished blank lengths | 2154.5 |
| Eight assumed crosscut kerfs at 3.2 mm | 25.6 |
| Stock consumed in this arithmetic | 2180.1 |
| One listed 8 ft stick | 2438.4 |
| Theoretical uncut remainder | **258.3** |
| Remainder after one extra 3.2 mm end-square cut | **255.1** |

For reference, the six outer parts alone consume 1695.9 mm including six
assumed kerfs, and the two backers consume 484.2 mm including two. Combining
these known trial blanks on one stock length gives the 258.3 mm remainder
above. This is only a straight-length yield result. One checking defect, a
short board, shrinkage, a sizing cut, or a rejected connection zone may use
that remainder or require additional stock. It does not set purchase quantity.

Example cut order, subject to placing each piece in sound usable stock:
383.2, 383.2, 269.95, 269.95, 238.9, 238.9, 185.2, 185.2 mm. Reorder to
keep knots, checks, wane, splits, or other disqualifying features out of each
joint zone. Use a crosscut setup rated for the actual 88.9 mm section and
support the long board and cutoff. Do not use an unsupported freehand cut or
assume a saw has capacity for a full 4×4 merely from its nominal blade size.

## WJ-04 one-cleat rip and crosscut

For one diagnostic cleat from the listed actual/minimum 2×6 section:

1. Confirm the board's grade mark/certificate, species group, treatment, and
   actual 38.1 × 139.7 mm or larger section. Condition and measure it for the
   dry-service design basis. Reject a board that is below 38.1 mm in T, cannot
   yield 95.25 mm in X, or has unusable grain/defects in the cleat zone.
2. Mark the long stock direction as N/grain. Rip one longitudinal edge with
   a guarded rip saw and supported infeed/outfeed to make X = 95.25 mm while
   retaining T = 38.1 mm. The nominal X offcut is 41.25 mm after an assumed
   3.2 mm rip kerf.
3. Crosscut one 119.7 mm length along N using a supported stop setup. The
   assumed 3.2 mm separation kerf makes the length consumed by one blank
   122.9 mm, leaving 2315.5 mm of nominal uncut 8 ft stock before any end
   square or defect loss.
4. Preserve source-board identity and the post-rip grade/certificate with the
   cutoff. If post-rip grading evidence is not available, stop this material
   route; do not carry the original 2×6 grade onto the ripped cleat by
   assumption.

The example requires a long, supported edge rip before crosscutting; ripping
119.7 mm short blocks on a table saw is not a suitable substitute. A 3.2 mm
kerf is not a saw selection or cut tolerance. Record the actual blade kerf,
set finished-part dimensional tolerances, and check final net geometry in
WJ-07 before any fabrication route is released. The modeled WJ-03 bores and
WJ-05 backer counterbores are excluded from this blank-yield calculation.

## Material and release boundaries

- The 4×4 route is based on whole-section crosscuts only. NDS regrading
  exemption for crosscutting does not waive grade-mark/certificate
  identification, defect review, or checks of the final net section. NDS
  §4.1.3.2 classifies nominal 4×4 as Dimension; if the candidate adopts this
  material basis, use the corresponding 2024 NDS Supplement Table 4A family,
  not the Posts and Timbers table. This screen assigns no design values.
- The WJ-04 2×6 route changes the stock cross-section. NDS §4.1.7.1 requires
  structural stock resawn/remanufactured this way to be regraded. This is a
  specific material-evidence gate, not a blanket outside-engineering review.
- Product wording “Douglas fir” does not, by itself, prove the required DF-L
  species-group mark. Product wording “kiln-dried” does not prove delivered
  moisture or dry-service suitability. Product wording “anti-stain treated”
  does not identify the treatment chemistry or its design-value treatment.
- If the delivered species group, grade, treatment, dimensions, moisture, or
  connection-zone condition does not fit the adopted material basis, hold the
  affected stock path and resolve that mismatch before use. Do not invent
  design values or transfer a different species/grade basis.
- No hole, counterbore, pilot, drill bit, hardware dimension, or station
  operation is released by this stock screen. No physical receiving values
  have been observed; all observation fields remain blank.

Standards references: [2024 NDS, American Wood Council](https://awc.org/resources/2024-nds/)
(§§4.1.2.1, 4.1.3.2, 4.1.7.1–4.1.7.2) and [2024 NDS Supplement](https://awc.org/resources/2024-nds-supplement/)
(Table 4A Dimension Lumber). Do not mix NDS editions or treat reference values
as final member/connection capacities.
