# Selected wood fasteners for the next hardware variation

2026-09-06. These are **actual product selections for design development**, not
permission to build, assigned connection capacities, or a claim that the existing
viewer already contains these products. Preserve `lower-transition-development`
and its generic hardware as the comparison baseline. No purchases were made.
This document closes the screw-family choice; product integration, nominal-fit
checks and structural qualification are distinct subsequent work.

## Complete mapping of the 164 existing screw positions

Counts and names come from the [transition connection schedule](../exports/lower-transition-development/lower-transition-development_connections.csv).

| Existing family | Count | Selected product / ordering part | Installation decision |
| --- | ---: | --- | --- |
| `panel_1..64`, `kicker_{left,right}_{bottom,top}_0..3` | 80 | GRK R4 Climatek #9 × 2 in, **103099** | Drive from climbing face; head top flush, no protruding head or open counterbore. |
| `cheek_splice_{left,right}_1..4` | 8 | GRK R4 Climatek #9 × 2½ in, **103101** | Flush head into outer plywood face; this is a plywood-face joint, not a sawn-lumber rating. |
| `analysis_edge_screw_{left,right}_1..6` | 12 | GRK R4 Climatek #10 × 3½ in, **02139** | Side-to-rail connection, receiving solid-wood side grain; flush outer head. |
| `rib_*_front` | 12 | GRK R4 Climatek #10 × 3½ in, **02139** | Head flush with front of backing batten before climbing panel installation. Supersedes SDWS16312 as this variation's product choice. |
| `clip_*_{batten,rail}_{1,2}` | 32 | Simpson **SD9112**, retail **SD9112R100**, with eight **US A21** angles | Four screws per purchased clip, two into each member; flat washer-head seating, no countersink or altered connector holes. |
| `transition_*_screw_{1,2}` | 20 | Simpson **SDS25112**, retail **SDS25112-R25** | Separately engineered custom 6 mm steel-to-wood detail; flat integrated washer on steel, no countersink. |

The [GRK product page](https://www.grkfasteners.com/grk-products/structural-framing-screws/r4-multi-purpose-screw)
lists those three ordering parts in 110-, 100- and 50-screw packs respectively,
with T25 drives and Climatek coating. These are catalog-orderable identities,
not a claim about a particular local store's stock. The current mapping needs
80/8/24 screws respectively, before spares. Do not substitute stainless R4,
trim-head, deck or drywall products by nominal size alone.

## Published GRK geometry, not guessed head geometry

The [manufacturer customer drawing, dated 11/01/2023](https://www.grkfasteners.com/getattachment/9a082069-c76f-4f86-9d32-76965836742c/GRK-R4-Customer-Drawing-%281%29.pdf?ext=.pdf&lang=en-US)
was visually inspected. It gives nominal inch dimensions without tolerances:

| Product | Overall L | Thread TL | Head D | Head-rim H | Shank ds | Major d1 | Root d2 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| #9 × 2 | 2.00 | 1.30 | .329 | .061 | .128 | .173 | .112 |
| #9 × 2½ | 2.50 | 1.57 | .329 | .061 | .128 | .173 | .112 |
| #10 × 3½ | 3.50 | 2.00 | .368 | .069 | .142 | .193 | .124 |

Exact conversions: lengths 50.8/63.5/88.9 mm; thread lengths
33.02/39.878/50.8 mm; #9 head/shank/major/root =
8.3566/3.2512/4.3942/2.8448 mm; #10 =
9.3472/3.6068/4.9022/3.1496 mm. **H measures the rim, not the entire tapered
underhead seat.** The drawing does not dimension the taper angle, teeth, CEE
reamer maximum diameter or complete head recess profile. Overall L starts at
the top of the head; do not add a second head length to the installed screw.

For first geometry integration, reserve an explicitly **project-assumed**
Ø10 × 5 mm head/seat envelope for both R4 sizes, and a Ø12 × 50 mm straight
driver corridor. These are conservative design allowances, not guaranteed
manufacturer maxima, machining instructions, or a substitute for head bearing
geometry. Use the nominal thread envelope for interference work, separately
from the wood bore; do not open the receiving wood to thread diameter.
Represent the complete underhead recess as unresolved within that reserved
space. A nominal 90° cone may illustrate it only if labeled assumed; it must
not become an approved countersink drawing. Recheck thin plywood's remaining
section and panel-to-batten seating when the real recess is finalized.

The [manufacturer-hosted ESR-3201](https://www.grkfasteners.com/getmedia/4d618504-92ab-4fb2-8001-4e72bf1fe7bf/ESR-3201.pdf?ext=.pdf)
retrieved here is the July 2023 edition, renewal July 2025: not verified current
approval. It limits covered wood products, requires mixed-load/group checks,
and does not establish this purchased Roseburg plywood detail. Its #9 × 2½ length is 2⅜ in
versus the drawing's 2½; #9 × 2 thread length is 1¼ versus 1.30 in. Treat the
former as 60.325–63.5 mm for penetration/tip screening and the latter as
31.75–33.02 mm pending the purchased generation's markings. For #10 × 3½,
the report distinguishes 2 in thread from a historical 2⅜ in alternative.
Do not combine the larger length/strength from different generations.

No SDWS spacing or capacity credit transfers to GRK. The old
[SDWS screen](front-rib-fastener-selection.md) remains historical evidence,
not this new product's installation schedule. Unselected species/grade,
plywood properties, reliefs and neighboring mixed screw groups still govern
the later connection design. The user's offcut-test waiver remains unchanged.

## US A21 plus SD9112: select the combination, retain geometric uncertainty

The [2026 US connector catalog](https://ssttoolbox.widen.net/content/orplhjaqw1/pdf/C-C-2026.pdf),
printed pp. 314 and 380, identifies A21 as 18-gauge galvanized steel with
nominal 2 × 1½ in legs and 1⅜ in width, and permits four #9 × 1½ in SD screws.
Use all four specified holes. The directional connection arrangement matters;
one clip does not automatically provide bidirectional catalog resistance.

The [2025 US fastener catalog](https://ssttoolbox.widen.net/content/07il60awb7/pdf/C-F-2025.pdf),
printed pp. 70–71 and 131, supplies:

| Product | Length | Thread length | Thread OD | Shank OD | Integrated washer OD | Drive |
| --- | --- | --- | --- | --- | --- | --- |
| SD9112 | 1½ in / 38.1 mm | 1⅛ in / 28.575 mm | rounded 4.5 mm | .130 in / 3.302 mm | .370 in / 9.398 mm | ¼ in hex |
| SDS25112 | 1½ in / 38.1 mm | 1 in / 25.4 mm | .250 in / 6.35 mm | .235 in / 5.969 mm | .500 in / 12.7 mm | ⅜ in hex |

SD9112R100 is a 100-pack with mechanically galvanized finish;
SDS25112-R25 is a 25-pack with Double-Barrier coating. Replacement bits are
BITHEXR14-R1 and BITHEXR38-R1. Axial head heights and full socket outside
profiles were not dimensioned in the recovered catalog.

Project allowances for SD9112: Ø10.5 × 6 mm whole head and Ø14 × 50 mm
straight tool corridor. These replace the old Ø3.75 × 30 mm shaft/Ø10 × 3 mm
head exploration. The 38.1 mm screw length must be positioned from its bearing
datum, not copied onto the old arbitrary start. Verify point exit, perpendicular
crossed fasteners, seating and LED/wire paths at all 32 locations.

The [existing UK-model reconstruction](mid-batten-clip-study.md) remains only a
geometry proxy: its hole centers, Ø4.3434 holes and sharp bend are not newly
certified US production dimensions. Keep that distinction on exported parts.
Reserve a **project-assumed 2 mm inner-bend exclusion** and 1 mm external
connector allowance for the initial layout; an accurate US drawing can replace
them later. Neither is a tolerance limit. Do not drill out, re-bend or trim a
purchased A21 to satisfy the model. A failed conservative screen triggers a
local layout revision, not a reduction of these allowances after the result.

## SDS25112 in custom 6 mm steel: explicit engineered detail

Select SDS25112-R25 for all twenty transition screw positions, with its own
integrated washer and **no added loose washer**. Proposed machining is a
Ø7 mm through-hole in the custom steel, deburred, with a flat bearing land;
no countersink. This is a project drawing decision, not a Simpson hole rule.
Its nominal 38.1 mm underhead length leaves 32.1 mm penetration after 6 mm
steel; the nominal 25.4 mm threaded tail includes the point and is not wholly
effective withdrawal length. Into 38.1 mm backing, nominal point cover is
6 mm before tolerances. This arithmetic is not a capacity or fit result.

Reserve Ø14 × 7 mm for the whole head and Ø18 × 50 mm for the driver as
**project-assumed allowances**, not manufacturer geometry. The larger screw,
bore and tool can invalidate the transition candidate's tight top clearances.
Rebuild the steel holes and wood installation detail, rerun actual-member,
head/tool, panel-face and LED checks, and retain failures. Do not reuse the
old Ø4.826 mm screw or Ø10 mm head result.

This is a custom steel-to-solid-wood connection requiring its own mixed-demand,
head bearing, steel hole bearing/tearout, net-section, screw bending and wood
splitting/withdrawal checks. **No A21/SD9112 or other thin-connector approval
is inherited.** The [SDS manufacturer page](https://strongtie.com.au/products/sds-strong%E2%80%91drive-heavy-duty-connector-screw)
confirms the product family and intended connector/wood applications, but does
not rate our 6 mm plate assembly. Neither a generic lag-screw minimum nor
catalog screw strength alone qualifies it.

## Handoff boundaries

All 164 frame-screw positions now have an identified product decision.
The baseline's 114 bolt assemblies, hold bolts, T-nut flange-retaining screws
and harness components are outside this document's screw-family count.
The separate hardware integration must preserve those inventories, replace
only named families, model recesses and tools honestly, and publish new
test/export evidence before describing this selection as installed CAD.
FEA connection demands remain unqualified; none of these product decisions
turns the failed numerical section-recovery evidence into a board-strength
result or structural approval.
