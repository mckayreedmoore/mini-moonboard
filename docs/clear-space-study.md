# Support alternatives that clear the climbing space

Two separate designs address the diagonal knee projecting inside the climbing
area. The floor-rail candidate removes the raised knees. The exterior-brace
candidate moves all knee wood outside the panel edges while retaining
triangulation. Neither inherits the selected inboard-brace assembly's passing
forces. Each has its own actual geometry, native force cases, connection checks,
viewer export and fabrication schedule.

**Current result: all six corrected floor-rail cases meet all 25 listed
conditional criteria per case.** The refined floor-contact sensitivity also meets all 25 criteria;
the exterior-brace alternative is **not accepted** because its A12-left
response failed the numerical gate after three bounded solver attempts.
The existing compact spliced-knee design remains the preserved viable candidate.
The floor package completes the requested conditional design under the explicit
analytical limits below. The exterior CAD and dimensional packet are retained
for comparison only, not as construction instructions or a passing substitute. See the [side-by-side comparison](clear-space-comparison.svg).

## Geometry and practical differences

| Item | Floor rails | Exterior braces |
|---|---|---|
| Candidate | `compact-floor-rail-development` | `compact-exterior-brace-development` |
| Raised diagonal knee wood | None | Entirely outside panel edges |
| Added support stock | Two continuous single 2×6 floor rails | Two solid 4×6 rim-end pieces and two solid 2×6 leg-end pieces |
| Leg and inclined rim stock | Retained solid 4×6 | Retained solid 4×6 |
| Compact header/posts | Nominal 2×6 | Nominal 2×6 |
| Upper leg joint | Two centered ½-inch bolts per leg, 56 mm pitch | Same |
| Other bolts | Two ⅜-inch bolts at each rail end | Two ⅜-inch bolts at each brace endpoint, four per splice |
| Total complete bolt stacks | 12 | 20 |
| Panel/kicker SPAX screws | 66, including nine per kicker half | 66, including nine per kicker half |
| Commercial angles / specified SDS screws | 24 / 144 | 24 / 144 |
| Main-face datum above floor | 277 mm | 277 mm |
| Estimated modeled mass | 213.92 kg | 215.00 kg |

Mass uses closed mesh volumes at 600 kg/m³ wood/plywood and 7850 kg/m³ steel,
including modeled T-nut envelopes. Holds, hold bolts, LEDs and wiring are
excluded; these are estimates, not measured weights. See [weight notes](prototype-weights.md).

The floor rails are **1880 × 139.7 × 38.1 mm**, from world Y = −210 to
1670 mm and Z = 0 to 139.7 mm. They lie against the inward faces of the legs
and occupy the outside 38.1 mm strip within each panel edge. They remove the
raised diagonal obstruction but retain a 139.7 mm-high timber member at each
floor edge; account for that physical rail when placing pads and approaching
the board. These rails are part of the actual load path, not decorative trim
or a friction-driven tie added as a new floor qualification requirement.

The two outer posts move inward by 38.1 mm to provide full-section front
rail/post laps. Their header clips and four kicker screw axes move with them.
Each kicker receives an **open bottom/outside-edge clearance notch, 40.1 mm
wide × 141.7 mm high**, leaving 2 mm above and beside the rail. The outer
kicker screws are at world X = ±1162.05 mm and Z = 60 and 192 mm; the lower
screw is 17.05 mm from the new notch edge. The center-post and header kicker
rows stay fixed. The notch and shifted attachments are represented in current
CAD and must be represented in native panel geometry as well.

The exterior braces use independent, **square-ended, unnotched** pieces.
The 4×6 rim piece occupies the same exterior thickness band as the leg; its
2×6 partner lies farther outward, with the splice plane at absolute
X = 1308.1 mm. Their outermost timber is at absolute X = 1346.2 mm, so the
brace wood increases overall side width to 2692.4 mm before projecting
hardware. All knee wood is outside the ±1219.2 mm panel edges. This clears
the central climbing space at the cost of more exterior width and thicker
rim-end brace stock. There are no air-gap spacers, notched tabs, doubled
vertical members, or assumed composite action between the splice pieces.

The current exterior revision uses **51 mm splice pitch**. Both independent
pieces extend 20 mm farther into the overlap, giving lap stations from
`120 mm` to `knee length − 180 mm` along the brace datum. The square ends
remain entirely outboard. Use the revised member profiles and splice drilling
together; a wider bolt pattern alone does not supply the added end distance.

Both alternatives incorporate the [base-angle placement correction](compact-base-finish-review.md):
the outer angles move 29.15 mm forward to Y = −105.85 mm, leaving 19.05 mm
between their footprints and both header depth edges. All twelve relocated
SDS screws retain full nominal receiver penetration. The inclined rim ends
retain their **7 mm rear projection**. A fully flush cut fails the retained
quarter-depth end-cut comparison by 4.970 mm after the 3 mm allowance; the
current projection retains 0.393 mm of margin. Rear-leg tops also retain the
existing 18 mm projection normal to the rim rear face for bolt end distance.

## Finite assessment and current results

The analysis applies a 250 lb climber load with a **2.0 downward multiplier**
(approximately 2224 N downward), plus the horizontal component below. It
retains the accepted panel construction, explicit no-slip floor assumption,
recorded material properties and specified hardware basis. The multiplier
is a static design action; these calculations are not a physical fall test
or a safe climber weight rating.

| Case | Hold | Horizontal action | Corrected floor result | Exterior result |
|---|---|---|---|---|
| `a12-rear` | A12 | +300 N Y | 25/25 met; bolt .825 | Listed criteria met; bolt 0.707473 |
| `a12-forward` | A12 | −300 N Y | 25/25 met; bolt .759 | Listed criteria met; bolt 0.588735 |
| `a12-left` | A12 | −300 N X | 25/25 met; bolt .812 | Numerical gate failed; diagnostic only |
| `k12-right` | K12 | +300 N X | 25/25 met; bolt .800 | Not run; numerical gate stopped batch |
| `k12-rear` | K12 | +300 N Y | 25/25 met; bolt .818 | Not run; numerical gate stopped batch |
| `a1-rear` | A1 | +300 N Y | 25/25 met; bolt .128 | Not run; numerical gate stopped batch |

**The first six floor cases omitted the kicker clearance notches in their
native panel representation. Those results are superseded diagnostics, not
acceptance evidence for the notched candidate.** The six corrected reruns now meet the listed criteria and match their current
source and geometry identities. A separate A12-rear floor-contact sensitivity
doubles the rail support grid from 7×2 to 14×2 cells per rail. It also meets
all 25 listed criteria and is reported separately from the six-case maxima
below. Contact-state seeds only accelerate
finding the new equilibrium; they do not transfer acceptance between cases.

| Governing comparison | Corrected floor: six accepted cases | Exterior: two accepted cases only, not qualification |
|---|---:|---:|
| Actual-angle bolt lateral demand/reference, CD = 1 | 0.825 | 0.707; incomplete case set |
| Additional bolt-group reduction sensitivity | 0.825 | 0.707; incomplete case set |
| Local parallel-grain wood comparison | 0.475 | 0.557; incomplete case set |
| Supplemental splitting comparison | 0.325 | 0.419; incomplete case set |
| Sampled net-member and stability comparisons | 0.442 net; stability gates met | 0.459 net; only two cases |
| Header, bearing and end-notch comparisons | 0.264 header; 0.066 quarter-area bearing; 0.258 end notch | 0.429 header; 0.083 quarter-area bearing; 0.173 end notch; only two cases |
| Catalog angle rated force components | 0.615 | 0.563; only two cases |
| Complete receiver and placement checks | Met in all six cases | Geometry fits; numerical acceptance incomplete |
| Overall listed-criteria decision | 25/25 met in all six cases | NOT ACCEPTED: A12-left numerical gate failed |

The corrected floor cases also give a maximum floor-rail wood-bearing ratio
of 0.00273, direct steel ratio of 0.119, washer-bearing ratio of 0.101, and
washer-bending ratio of 0.237. Minimum directional edge/end reserve is
**0.325 mm after the adopted allowances**; minimum component-spacing margin
is 3.673 mm. Preserve the scheduled dimensions and allowances. The separately
reported actual-angle full-thread-root sensitivity with additional group
reduction reaches **1.038**, so the passing nominal-diameter route depends on
the specified full-body/thread-transition conditions; fully threaded substitutes
do not inherit the passing result.

The A12-rear **14×2 floor-contact refinement** changes the actual-angle bolt
ratio from 0.825218 to **0.823977** (−0.1503%) and maximum panel displacement
from 17.11368 to **17.09250 mm** (approximately −0.124%). The listed-criteria
decision is stable in this sensitivity. Maximum timber displacement changes
from 6.92862 to **6.90291 mm** (approximately −0.371%). The maximum local floor-cell wood-bearing
ratio changes from 0.00096966 to **0.01582899**, approximately **16.3 times**
the coarse value, although still below 1. Local pressure is therefore **not
converged**; the small change in global deflection and bolt demand does not
establish a converged pressure distribution or measured floor behavior. This
records the finite sensitivity and its limits without introducing a new floor
qualification campaign.

Ratios at or below 1 meet their stated comparison. Numerical acceptance,
actual receiver fit, directional edge/end distances, group spacing, represented
machining, sampled bolt stations and contact inventory are separate gates.
Checks include all actual upper, endpoint and splice bolts; they do not replace
the upper joint with an ideal pin. The floor model includes explicit
compression-only rail/floor cells and a no-slip tangential support assumption.
The exterior model includes actual independent brace sections and
compression-only contact across the bolted splice faces.

The original exterior A12-rear trial, with 40 mm splice pitch, failed its
component-spacing comparison by **7.625 mm** despite an actual-angle bolt
lateral ratio of **0.707785**. That trial is preserved at
`fea/results/clear-space-exterior-trials/40mm-splice/a12-rear/`. Its strength
result does not qualify the 51 mm pattern and extended overlap. The revised A12-rear and A12-forward cases meet their listed criteria using
their own fresh forces. A12-left did not produce an accepted numerical
response after three bounded attempts, including an alternative floor-contact
initialization that cycled for 23 iterations. Its archived status is
`INVALID_RESPONSE_DIAGNOSTIC_ONLY`; its forces must not be used as a resistance
pass or physical failure prediction. The batch stopped there, so K12-right,
K12-rear and A1-rear were not run. The exterior alternative clears the climbing
space geometrically but **has not demonstrated the required passing case set**.
The two accepted-case maxima above are diagnostic comparisons only, not
qualification of that alternative. This finite investigation is closed with
that negative numerical decision; no further exterior solve is promised.

The resistance assessment reports actual-angle lateral resistance at CD = 1,
additional group-action sensitivity, direct steel stress, washer bearing and
bending, local wood action, supplemental EC5 splitting, net sections, member
stability, header bearing/end cuts and the catalog angles' rated force
components. Full thread-root resistance is reported separately as a sensitivity;
the specified nominal-diameter route requires the supplied bolt inspections in
[the hardware schedule](clear-space-hardware.md).

**Commercial-angle unlisted separation and independent flange couples remain
unqualified.** Rated force-component checks do not establish invented capacities
for those actions, and their recorded values do not become qualified when other
ratios pass. Across the six corrected floor cases, maximum recorded unlisted
separation is **170.73 N** at `clip_angle_base_right` in K12-rear; maximum
absolute independent flange parallel couple is **14.72 N·m**, on that same
angle’s beam flange in that case. These are demands, not allowable capacities
or passing margins. The maxima include all 24 angles in every case. No additional panel campaign, floor-friction measurement, or external
review is introduced here. The endpoint is a finite, engineer-unreviewed DIY
assessment under the stated load, material, hardware and installation assumptions,
with those explicit analytical limits retained.

## Candidate-specific fabrication packages

The floor directory is the completed conditional fabrication package. The
exterior directory is an **unaccepted dimensional reference only**, retained
to review the evaluated concept; do not build from it. Do not combine floor
bolt coordinates with exterior profiles or earlier inboard knee schedules.

| Artifact | Floor rails: conditional fabrication package | Exterior braces: NOT ACCEPTED reference only |
|---|---|---|
| Stock blanks | [stock.csv](clear-space-floor-construction/stock.csv) | [stock.csv](clear-space-exterior-construction/stock.csv) |
| All connection axes | [connection-axes.csv](clear-space-floor-construction/connection-axes.csv) | [connection-axes.csv](clear-space-exterior-construction/connection-axes.csv) |
| Bolt dimensions | [bolt-hardware.csv](clear-space-floor-construction/bolt-hardware.csv) | [bolt-hardware.csv](clear-space-exterior-construction/bolt-hardware.csv) |
| Member bolt datums | [bolt-member-datums.csv](clear-space-floor-construction/bolt-member-datums.csv) | [bolt-member-datums.csv](clear-space-exterior-construction/bolt-member-datums.csv) |
| Panel attachment axes | [panel-attachment-axes.csv](clear-space-floor-construction/panel-attachment-axes.csv) | [panel-attachment-axes.csv](clear-space-exterior-construction/panel-attachment-axes.csv) |
| Panel hold/LED axes | [panel-hole-axes.csv](clear-space-floor-construction/panel-hole-axes.csv) | [panel-hole-axes.csv](clear-space-exterior-construction/panel-hole-axes.csv) |
| Exact stock profiles | [stock-profiles.json](clear-space-floor-construction/stock-profiles.json) | [stock-profiles.json](clear-space-exterior-construction/stock-profiles.json) |
| Timber wiring passages | [timber-passages.json](clear-space-floor-construction/timber-passages.json) | [timber-passages.json](clear-space-exterior-construction/timber-passages.json) |
| Artifact/source identity | [manifest.json](clear-space-floor-construction/manifest.json) | [manifest.json](clear-space-exterior-construction/manifest.json) |

Floor-specific cuts are in [kicker-notch-cuts.csv](clear-space-floor-construction/kicker-notch-cuts.csv),
with [left](clear-space-floor-construction/kicker_left-notch-sheet.svg) and
[right](clear-space-floor-construction/kicker_right-notch-sheet.svg) dimensioned
sheets. Each directory also contains individual joined-member SVG drill/profile
sheets and the retained end-trim detail. Use numerical dimensions rather than
scaling the drawings. The floor export and construction packet have been generated together and their
links above are current. The exterior export and packet identify the concept
as not accepted; their dimensional completeness does not resolve its numerical
gate or authorize construction.

## Floor-rail conditional assembly guidance

1. Use the complete floor-rail package and verify its final result and manifest.
   Use the [retained material basis](leg-material-basis.md) and
   [candidate hardware requirements](clear-space-hardware.md). The stock CSV
   describes blank envelopes; the profile and member sheets specify actual ends.
2. Establish floor datum Z = 0 and main-face datum Z = 277 mm. The 127 mm pad
   allowance plus 150 mm exposed kicker is a clearance convention; pads do not
   support any structural timber. Retain the header/rim and leg-top reserves.
3. For floor rails, fit both full-length rails and inward-shifted outer posts,
   including their shifted header clips. Cut each prescribed kicker notch and
   verify its 2 mm clearance. Transfer the relocated outer kicker screw axes
   from this candidate's sheet; do not reuse the old outer-post drilling.
4. Retain the two upper bolts per leg and install both specified two-bolt rail
   end connections. Keep rail, post and leg faces in their modeled direct
   contact without spacers. Do not add exterior knees or mix their bolt
   schedules into the floor-rail load path.
5. Align the scheduled through-bores, seat both washers flat on solid wood and
   orient all nuts and threaded ends outward. Use the scheduled 4-, 6- or
   8-inch Grade 5 bolts as applicable. Inspect actual full-body length,
   transition, nut seating and complete exposed threads against the hardware
   document; a nominal length alone does not prove suitability.
6. Install all six specified SDS25112 screws in each commercial angle and the
   66 specified SPAX panel/kicker screws. Occupied CAD screw diameters are not
   pilot-bit instructions. Keep the independent panel seams and wiring access;
   no insert pilots or inserts are added. Verify the revised base clips stay
   completely on the header and arrange pads around the actual side geometry.

## Evidence and reproducibility

The six accepted floor cases are in `fea/results/clear-space-floor/`. The
exterior archive at `fea/results/clear-space-exterior/` contains two accepted
cases and the rejected A12-left diagnostic; it does not contain a complete
passing six-case set. Archives retain source/geometry identity, native report
and `assessment.json`. Superseded
notch-omitted floor reports remain historical diagnostics and must not occupy
the role of corrected current acceptance evidence.

`scripts.clear_space_batch` generates the finite serial case set and stops at
a numerical or listed-criterion failure. `scripts.clear_space_results` checks
actual recorded forces and geometry. `scripts.clear_space_exports` binds the
standalone viewer status to the current six cases; `scripts.clear_space_construction`
generates the matching dimensions and checksums. The corrected six-case floor decision and refined A12-rear contact sensitivity
are complete. The refinement is archived separately at
`fea/results/clear-space-floor-refinement/a12-rear/`. The exterior investigation
ends with an unaccepted numerical result and preserves its geometry and
dimensions for comparison. The selected prior braced baseline remains available.

## Software and artifact verification

The default suite passed 467 tests, with 15 historical tests deselected; Ruff
and the CadQuery smoke test passed. Both new candidates were exported from
empty directories. Every earlier floor CAD/viewer artifact matched its clean
rebuild; its provenance manifest was refreshed for the completed tooling. The
preserved selected spliced-knee export also passed its clean-rebuild check.

Browser checks verified 725 floor meshes and 767 exterior meshes, complete
outward bolt stacks, 60 mm lower kicker screws, the 19.05 mm base-clip edge
clearance and retained 7 mm rim reserve. The exterior model displays its
NOT ACCEPTED status. Both dimensional packets passed source/artifact checksum
verification; exterior sheets explicitly prohibit using them as a build release.
These software and geometry checks do not override the engineering decisions
and analytical limits above.
