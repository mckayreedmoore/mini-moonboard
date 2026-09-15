# Support alternatives that clear the climbing space

Two separate designs address the diagonal knee projecting inside the climbing
area. The floor-rail candidate removes the raised knees. The exterior-brace
candidate moves all knee wood outside the panel edges while retaining
triangulation. Neither inherits the selected inboard-brace assembly's passing
forces. Each has its own actual geometry, native force cases, connection checks,
viewer export and fabrication schedule.

**All six current exterior cases meet all 25 listed conditional criteria.** The separate 5×5 A12-left leg-foot-grid sensitivity also
meets all 25 criteria. The corrected floor-rail design retains its six passing
cases and refined contact sensitivity under its original no-slip assumption.
The exterior evidence uses assumed μ = 0.4, collocated per-cell Coulomb friction;
it does not establish measured floor properties or transfer to the floor-rail model.

These are conditional analytical results under the loads, material, hardware
and installation assumptions below, not unconditional qualification or a safe
climber rating. The revised exterior is selected as the current conditional candidate. The
prior compact spliced-knee design and preceding failed trials remain references.
See the [side-by-side comparison](clear-space-comparison.svg).

## Geometry and practical differences

| Item | Floor rails | Exterior braces |
|---|---|---|
| Candidate | `compact-floor-rail-development` | `compact-exterior-brace-development` |
| Raised diagonal knee wood | None | Entirely outside panel edges |
| Added support stock | Two continuous single 2×6 floor rails | Two solid 4×6 rim-end pieces and two solid 2×6 leg-end pieces |
| Leg and inclined rim stock | Retained solid 4×6 | Retained solid 4×6 |
| Compact header/posts | Nominal 2×6 | Nominal 2×6 |
| Upper leg joint | Two centered ½-inch bolts per leg, 56 mm pitch | Two ½-inch bolts per leg, revised 64 mm pitch and thicker round washers |
| Other bolts | Two ⅜-inch bolts at each rail end | Two ⅜-inch bolts at each brace endpoint, four per splice |
| Total complete bolt stacks | 12 | 20 |
| Panel/kicker SPAX screws | 66, including nine per kicker half | 66, including nine per kicker half |
| Commercial angles / specified SDS screws | 24 / 144 | 24 / 144 |
| Main-face datum above floor | 277 mm | 277 mm |
| Estimated modeled mass | 213.92 kg | 215.11 kg |

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
current projection retains 0.393 mm of margin. Floor-rail rear-leg tops retain the
18 mm projection normal to the rim rear face; the current exterior revision
increases that projection to 24 mm for its revised upper joint.

## Finite assessment and current results

The analysis applies a 250 lb climber load with a **2.0 downward multiplier**
(approximately 2224 N downward), plus the horizontal component below. It
retains the accepted panel construction, recorded material properties and
specified hardware basis. Floor-rail cases use the explicit no-slip assumption;
current exterior cases use assumed μ = 0.4 with collocated per-cell friction. The multiplier
is a static design action; these calculations are not a physical fall test
or a safe climber weight rating.

| Case | Hold | Horizontal action | Corrected floor bolt ratio, no-slip | Current exterior bolt ratio, μ = 0.4 | Exterior criteria |
|---|---|---|---:|---:|---|
| `a12-rear` | A12 | +300 N Y | .825 | 0.707702 | 25/25 |
| `a12-forward` | A12 | −300 N Y | .759 | 0.942397 | 25/25 |
| `a12-left` | A12 | −300 N X | .812 | 0.985043 | 25/25 |
| `k12-right` | K12 | +300 N X | .800 | 0.969421 | 25/25 |
| `k12-rear` | K12 | +300 N Y | .818 | 0.698719 | 25/25 |
| `a1-rear` | A1 | +300 N Y | .128 | 0.095861 | 25/25 |

All six corrected floor cases meet 25/25 criteria. Each exterior value above
comes from its own current archived assessment.

**The first six floor cases omitted the kicker clearance notches in their
native panel representation. Those results are superseded diagnostics, not
acceptance evidence for the notched candidate.** The six corrected reruns now meet the listed criteria and match their current
source and geometry identities. A separate A12-rear floor-contact sensitivity
doubles the rail support grid from 7×2 to 14×2 cells per rail. It also meets
all 25 listed criteria and is reported separately from the six-case maxima
below. Contact-state seeds only accelerate
finding the new equilibrium; they do not transfer acceptance between cases.

| Governing comparison | Corrected floor: six accepted cases |
|---|---:|
| Actual-angle bolt lateral demand/reference, CD = 1 | 0.825 |
| Additional bolt-group reduction sensitivity | 0.825 |
| Local parallel-grain wood comparison | 0.475 |
| Supplemental splitting comparison | 0.325 |
| Sampled net-member and stability comparisons | 0.442 net; stability gates met |
| Header, bearing and end-notch comparisons | 0.264 header; 0.066 quarter-area bearing; 0.258 end notch |
| Catalog angle rated force components | 0.615 |
| Complete receiver and placement checks | Met in all six cases |
| Overall listed-criteria decision | 25/25 met in all six cases |

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

### Exterior refinement and earlier trials

The passing current geometry uses 51 mm splice pitch with extended overlap,
64 mm upper-leg bolt pitch, 24 mm leg-top projection and thicker round washers.
A12-left gives bolt ratio **0.985043** and washer-bending ratio **0.757756**.
Its separate 5×5 leg-foot sensitivity gives bolt ratio **0.961255** and normal
foot-bearing ratio **0.569322**, versus **0.203852** with the 3×3 grid.
Foot bearing uses actual horizontal cell area and the angle between vertical
compression and leg grain under NDS 3.10.3. The 625 psi perpendicular-grain
screen is diagnostic, not the governing actual-angle capacity. Tangential
traction remains in independent member shear/combined-action checks.
The pressure change does **not** establish a converged physical pressure field;
small global-response changes cannot substitute for pressure convergence.

The original 40 mm splice trial failed component spacing. The later no-slip
batch stopped at A12-left contact cycling. Correcting the friction-cell
collocation produced a converged response, exposing bolt lateral 1.029 and
washer-bending 1.595 shortfalls in the preceding 56 mm upper joint. These are
historical failures, not results of the current 64 mm/24 mm revision. See the
[contact investigation](exterior-knee-contact-verification.md) and preserved
`fea/results/clear-space-exterior-trials/pre-coulomb-64mm-revision/`, other `clear-space-exterior-trials/` and
`exterior-cells04-verified/` archives for those distinct geometries and responses.

The separate [runner recess study](floor-runner-recess-study.md) obtained a
converged A12-rear response and met 31 of 33 criteria. Actual cut-member ratio
was 0.5666; local notch resistance remains unqualified. Its artificial full-height
50.8 mm continuous-band diagnostic reached 1.1458 above the recess and is not
evidence that the actual cut section failed. No further recess cases followed
that first design gate. Neither that trial nor the [recess concept](floor-runner-leg-recess.md)
qualifies a modification to the preserved floor-rail assembly.

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

The exterior directory is the selected conditional fabrication package, regenerated and checked against the passing revised sources and hardware identities. The floor package remains a separate conditional alternative. Do not combine floor
bolt coordinates with exterior profiles or earlier inboard knee schedules.

| Artifact | Floor rails: conditional fabrication package | Exterior braces: selected conditional package |
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
links above are current. The exterior export and packet have also been regenerated and verified against the current revision.

## Selected exterior assembly detail

Use the exterior stock profiles and drill sheets together: the 64 mm upper
pattern and 24 mm top projection require fresh stock, not extra holes in the
preceding 56 mm joint. Fit the independent exterior knee pieces directly to
their adjoining rims/legs and splice faces without spacers or composite-action
assumptions. Retain the 51 mm splice pitch and prescribed square ends. All
20 bolt stacks retain flat washer seating and outward threaded ends. The eight
upper washers require 3.0–3.3528 mm delivered thickness and the scheduled
outside/bore dimensions; inspect supplied bolt shanks and runout against the
[hardware requirements](clear-space-hardware.md). Retain all 66 SPAX screws,
144 specified SDS screws and the independent panel seams. The kicker remains
whole and the legs have no floor-runner recesses in this selected candidate.

## Preserved floor-rail conditional assembly guidance

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

The six accepted floor cases are in `fea/results/clear-space-floor/`. The six current exterior cases are in `fea/results/clear-space-exterior/`. The earlier two accepted no-slip cases and rejected A12-left diagnostic are preserved under `fea/results/clear-space-exterior-trials/pre-coulomb-64mm-revision/`. The original revised-run archives remain under `fea/results/exterior-revised-cells04/`, with the
5×5 sensitivity under `fea/results/exterior-revised-grid5/`. Current case
completion is reported above. Archives retain source/geometry identity, native report
and `assessment.json`. Superseded
notch-omitted floor reports remain historical diagnostics and must not occupy
the role of corrected current acceptance evidence.

`scripts.clear_space_batch` generates the finite serial case set and stops at
a numerical or listed-criterion failure. `scripts.clear_space_results` checks
actual recorded forces and geometry. `scripts.clear_space_exports` binds the
standalone viewer status to the current six cases; `scripts.clear_space_construction`
generates the matching dimensions and checksums. The corrected six-case floor decision and refined A12-rear contact sensitivity
are complete. The refinement is archived separately at
`fea/results/clear-space-floor-refinement/a12-rear/`. All six current exterior cases and the separate 5×5 sensitivity meet their listed criteria. The prior braced
baseline remains available.

## Software and artifact verification

The current default suite passes **518 tests**, with 15 historical tests
explicitly deselected. Ruff passes for the changed analysis, model, export and
test code. All four clear-space exports and construction packets have been
regenerated and checked against fresh builds. The original floor, 2×4 floor
and recessed-floor STL inventories match their preceding geometry exactly;
only the exterior stock and upper drilling change. Historical weight rows are
preserved, and the revised exterior mesh mass is 215.11 kg.

Browser checks pass for all four refreshed variants: 725 original-floor meshes, 725 recessed-floor meshes, 735 2×4-floor meshes and 767 exterior meshes. They verify complete outward bolt stacks, exterior knee position, outboard recessed runners, retained kicker screw locations, base clip clearances and the selected 64 mm upper pattern. CadQuery smoke testing also passes.
These software and geometry checks do not override the engineering decisions
and analytical limits above.
