# Preserved working-agreement history

This is the chronological decision log formerly kept in `AGENTS.md`. It is
**not** current construction authority. Selected candidate, claim boundary and
shop packet are in [`AGENTS.md`](../../AGENTS.md) and
[`current-candidate.json`](../../current-candidate.json). Do not transfer
acceptance from a preserved candidate because this file still says “current”
or “selected.”

The text below is retained verbatim as the 2026-09-17 working-agreement
snapshot so later agents can reconstruct why a constraint exists.

---

# Repository working agreements

## Current hardware decision

Use the selected structural wood screws for face and kicker panels now.
Reserve space for a possible future insert/machine-screw conversion where
receiver geometry and connection resistance support it. Retain
existing through-bolts/nuts and manufacturer-specified structural screws in
commercial brackets. Do not claim inserts are installed, qualified or build-ready
before the model, hardware schedule and checks are updated. Existing screw-based
variants and their evidence remain historical screw-based designs.
Keep a single-2x6 development baseline even when tests fail; record failures
and enlarge members selectively or revise connections. Do not double-stack
vertical 2x6s or introduce built-up vertical substitutes. Paired horizontal 2x6
rails are now permitted to give adjacent face panels separate screw receivers;
provide each rail's connections and do not assume composite action. Prefer square-cut principals and open
LED access over the former lower housing and continuous relieved backing.
Reserve possible future insert space around panel screws without predrilling it.
The first revised layout/render keeps all lumber, including the header, single
2x6 even when bearing fails; larger stock remains a later option.

The preserved all-2x6 baseline is `single-2x6-development`: one center
principal/post and one middle rail per bay. Earlier square-2x6 variants retain
paired seam framing despite their single-stock descriptions. Check assembled
adjacency as well as individual stock sizes; do not call those variants unstacked.

The preserved `selective-2x6-development` retains nine single 2x6 members and
selectively uses four single 3x6 shared receivers and one single 2x10 header.
This addresses fit defects only; no strength or floor qualification transfers.

The preserved `paired-rail-base-development` replaces the two 3x6 middle rails
with four independently clipped 2x6 rails and adds an ML24Z between the center
principal side and header top. Center principal/post remain single 3x6 stock.
The header's rearward load transfer remains unresolved. The render still uses
ordinary panel screws; the insert direction above requires a separate modeled
and checked hardware revision. Historical results do not qualify this assembly.

The preserved `vertical-principal-development` removes middle rails and adds
four independent full-height 2x6 principals with aligned single 2x10 posts and
explicit connections. Top rail, split bottom backing and header remain. Retain
existing gussets and bolts until actual joint-force analysis justifies changes.
The four face panels retain unconnected horizontal seam edges between framing;
do not tie those edges in analysis or transfer older strength/floor acceptance.

The preserved `split-center-development` replaces the single center principal
and post with two separated 2x6 principals and full-depth 2x10 posts. All eight
posts now support the full header depth. Keep the center service corridor open;
the adjacent panel edges have 50.95 mm overhang and remain independently acting.
Through-bolt heads, nuts and washers are individually selectable; this does not
change the bolt count or qualify the joint. Build readiness requires current
frame/connection/panel and actual floor checks; geometry passes are insufficient.

The preserved `infill-panel-development` adds 71 panel screws to that frame,
for 151 panel/kicker screws. Infill is uniform within each panel/principal line,
with intervals at most 150 mm between the original endpoint screws. The rule
does not bridge independent panel seams. Retain raw wood, old axes, the center
service corridor and complete bolt stacks. More screws do not establish equal
load sharing or connection adequacy; retain current numerical and resistance gates.

The preserved `angle-base-development` implements the owner's requested gusset
replacement: two direct ML24Z outer-rim/header angles with twelve specified
SDS25112 screws replace both plywood gussets and their eight bolts. Eight leg
bolts and all 151 panel/kicker axes remain. Fresh-build geometry omits the old
gusset bores; this is not a drilled-stock repair. Current joint/frame resistance
is unqualified. Ordinary bolts are steel gray; explicit clearance failures stay
red, and neither color is a strength rating.

The preserved `horizontal-service-development` uses four horizontal service
rails in place of the four added intermediate principals and posts.

The preserved `round-bore-service-development` replaces the open
wire grooves with enclosed round passages and uses 56 ordinary panel/kicker
screws: twelve per main panel and four per kicker, with mirrored attachment
positions. Leg bolts retain complete stacks with heads outside and nuts inside.
Keep the owned Roseburg plywood; Structural I is an optional reference
alternative, not a replacement purchase instruction. Use the matching schedules
and evidence. The preserved grooved-frame and higher-count screw comparisons
do not qualify this geometry or load path; insert development and actual
frame/connection/panel/floor qualification remain open.

The preserved insert candidate is `round-insert-development`. It retains the round-bore
frame with 56 attachments, replacing ordinary panel/kicker screws with
modeled E-Z LOK 801420-13 inserts and Dottie FMDD14114 machine screws. Its lower
service rail and attachment axes now align at slope station 1134.2 mm; kicker
rows are 60 and 140 mm. Upper service rails and their attachment axes align at
1278.25 mm; upper principal/rim axes, including center screw #4, stay fixed. Keep the
eight complete leg bolt stacks and all ML24Z/SDS connections. The insert's
0.25 mm recess, 7 mm panel clearance and 17 mm receiver reserve are provisional
CAD assumptions, not released machining dimensions. Effective thread engagement,
actual installed resistance and plywood head bearing remain unqualified. Do not
transfer SPAX capacity or spacing acceptance to inserts. Keep the preceding
screw candidate and failed numerical trials available as historical evidence.

## Communication

Keep chat concise. Documentation, website text, code and commits use normal prose.
Preserve changes belonging to other agents, including untracked files.

## Current simplified screw candidate

The owner selected `round-structural-development`: 56 SPAX XFT08P-2000
#8 x 2-inch panel/kicker screws, retaining ML24Z/SDS screws and complete leg
bolt stacks. Keep the aligned lower/upper service rails and fixed upper
principal attachment rows. Enlarge enclosed LED passages to 38.1 mm (1.5 inches)
only in nominal 2x6 stock; retain 25.4 mm in other members. Reserve future
insert space geometrically without cutting insert pilots or installing inserts.
A later conversion must establish installation/repair and resistance details;
space alone does not qualify it. Preserve preceding designs and evidence.
The owner does not require physical floor measurements/tests. Record explicit
installation/floor assumptions and analytical limits without treating that
scope choice as measured friction or a floor qualification.

The separate `round-reinforcement-development` combines provisional fabricated
steel base shoes with ten added kicker/header screws and 142 modeled owned-type
Escape T-nuts. It is not the selected or build-ready design. The shoes replace
only two outer ML24Z angles and twelve SDS screws, add sixteen complete bolt
stacks and bearing plates, and require explicit 9.525 mm rim bearing-end trims.
Eight original leg stacks and the other 22 ML24Z connections remain. Each
independent kicker has nine screws; total panel/kicker count is 66. Geometry
checks and conditional force witnesses do not qualify steel, welds, wood or
plywood. Keep published US hold-bolt kit guidance separate from installed bolt
geometry: wood uses 3.5-inch countersunk bolts; plastic kits contain 2.5- and
3.5-inch cap heads without a per-hold mapping. Hold recess positions, T-nut
barrel/thread display assumptions and retention screws remain unresolved.

## Floor scope clarification, 2026-09-12

The owner excludes floor-friction qualification from the current assessment.
Use an explicit no-slip support assumption for member/connection calculations;
do not add a friction test or a friction-driven tie as a release prerequisite.
This does not verify floor properties or imply an installed anchor. The two
exploratory reinforced-frame stiffness cases do not establish a climber failure
weight or prove their proposed member/attachment redesigns necessary. See
`docs/reinforced-assumption-review.md` for the response-model limitations.

## Leg-only scope clarification, 2026-09-12

The owner accepts the panel construction as the design basis and explicitly
excludes another frame comparison. Current verification concerns the single
2x6 rear support legs, including their integral attachment assumptions. Do not
reopen panel, T-nut or floor-friction qualification as prerequisites for this
task. See `docs/leg-only-assessment.md` for the conditional member result and
the remaining leg-specific checks; this scope choice is not a whole-frame rating.

## Completed leg assessment, 2026-09-12

The owner authorized explicit assessment assumptions for later confirmation.
`docs/leg-completion-decision.md` records the resulting negative connection
decision: the single 2x6 member passes the selected full-contact pressure cases,
but the existing four-bolt joint and isolated smooth-bolt hardware candidate
do not pass the lateral connection check. The candidate in
`mini_moonboard/leg_smooth_hardware.py` is modeled and fit-checked, not selected
or qualified for construction. Do not equate owner approval of assumptions
with an established zero joint moment, or describe a nominal-pin model as an
installed hinge. Preserve the earlier axial-only results as historical evidence.

## Larger-bolt investigation, 2026-09-12

The authorized larger-bolt/wider-pattern search is recorded in
`docs/leg-bolt-pattern-decision.md`. No passing candidate was found within its
bounded four-bolt parallelogram search; no new drilling or hardware is selected.
The corrected calculation uses diameter-dependent perpendicular wood bearing
and group action. Do not reuse the earlier diameter-only sensitivity as a
capacity qualification or present the tested family as all possible connections.

## Wider single-stock preference, 2026-09-12

The owner permits larger dimensional-lumber support legs and prefers no custom
steel fabrication. Preserve the older single-2x6 baseline. The preliminary
six-bolt option in `docs/wider-leg-feasibility.md` uses single 2x8 legs and
matching single 2x8 outer rims with six 1/2-inch bolts per leg. Its passing
lateral/placement screen is not a selected or construction-qualified design;
The subsequent actual-CAD assessment is recorded in
`docs/wider-leg-decision.md` and `docs/wider-leg-review/README.md`.
Catalog hardware and nominal CAD fit are complete, but the actual rear rim
loaded-edge distance fails and the full-foot-pressure sensitivity fails lateral
resistance. Keep this candidate unselected. The assumed 2x prying bound and
BP1/2 plate yield floor remain unverified; do not call the detail build-ready.
Do not introduce doubled vertical stock or assume custom plate washers have
been accepted for this option.

## Criterion-source clarification, 2026-09-12

`docs/wider-leg-criteria-review.md` and `docs/wider-leg-criteria-sources.md`
audit the wider-leg criteria. NDS specifies 4D loaded-edge distance for
perpendicular loading; using it for this oblique joint is a conservative
screen, not an explicit oblique minimum. Whole-foot endpoint pressure is a
limiting sensitivity, not established normal contact. Preserve the historical
numbers while applying these qualifications to their interpretation. Numerical
weight crossings are conditional resistance limits, not safe climber ratings
or physical failure predictions; they do not qualify edge geometry or prying.

## Shoe-free candidate and pad allowance, 2026-09-12

The owner requests a separate single-2x6 support-leg candidate without custom
steel base shoes, retaining accepted panel/T-nut construction. Restore the
preceding commercial base-angle connections and fresh timber bearing geometry;
do not leave shoe clearance gaps or shoe drilling. The requested kicker datum
is 150 mm exposed above a 5-inch (127 mm) pad allowance: 277 mm from floor to
main-face datum, compared with the preceding 225 mm. Extend floor-supported
members appropriately; do not float the frame or treat the pad as a support.
Retain historical variants. Whole-frame analysis should use published material
properties and investigate specific shortcomings before enlarging members;
previous reinforced load results do not qualify this changed assembly.

## Preferred compact 4×6 revision, 2026-09-13

The owner now prefers the solid-4×6 direction and requires at least two bolts
per leg, with three the first candidate. `compact-thick-development` uses three
½-inch bolts per leg, 4×6 rims flush with panel edges, shortened horizontal
rails, and a nominal 2×6 header/posts. The owner explicitly asks to make the
2×6 base work before considering 2×8. The candidate retains 7 mm of rear
inclined-member overhang to limit its end cuts; preserve the 277 mm kicker and
accepted panel/T-nut/no-slip-floor scope. No doubled vertical stock or custom
fabricated steel is introduced.

The compact three-bolt upper-hold case is numerically accepted but fails its
conditional lateral reference (3.185); the former single-pivot pass does not
transfer. Two compact-base cases meet the listed header/end-cut comparisons.
Keep the earlier baseline and pivot evidence. See `docs/compact-thick-study.md`
for current results and the unresolved joint load path; do not call the new
viewer default build-ready or release its drilling.

## Selected spliced-knee DIY candidate, 2026-09-13

The current selected direction is `compact-spliced-knee-development`, superseding
`compact-thick-development` as the current authority. Preserve older candidates
and failed trials as history. Retain solid 4×6 legs/rims and the compact 2×6
base, with two centered ½-inch upper bolts per leg at 56 mm pitch. Four
independent unnotched diagonal 2×6 pieces form two spliced knees: four ⅜-inch
lap bolts per side and two ⅜-inch bolts at each endpoint, 20 complete bolt
stacks overall. This diagonal splice does not introduce doubled vertical
stock; no composite action is assumed.

Use `docs/compact-splice-study.md`, `docs/compact-spliced-build-package.md` and
`docs/current-diy-completion-record.md` for the current evidence, instructions
and final completion gates. Final release follows the remaining assembled-case
and consistency results, not a prior candidate's pass. The endpoint remains
engineer-unreviewed DIY under explicit loads, catalog hardware, lumber material
and no-slip floor assumptions. Do not add external review or a floor test as a
new gate, claim an unconditional rating, or retain historical three-bolt failure
as the selected model's decision.

## Current exterior finish and bolt installation

Current exports and construction schedules use `compact_spliced_trimmed`,
wrapping `compact_spliced_installation`; the six-case native definition remains
frozen in `compact_spliced_knee_frame`. Keep all 20 bolt tips facing away from
the central climbing space: 16 were reversed, four were already outward. Knee
ends are flush to adjoining host depth faces. Rear-leg tops retain 18 mm normal
projection beyond the rim to preserve end distance. Do not remove that reserve
to make a visually flush top without rechecking the joint. The current trim
assessment uses retained native forces/stiffness/gravity with an explicit small
exterior-tail approximation; do not claim an identical native mesh or six new
trimmed solves. Preserve both installation/trim evidence and baseline archives.

## Unbraced 2x12 alternative, 2026-09-13

The owner accepted the current braced/trimmed assembly as a viable candidate.
Keep it selected. Separate `compact-2x12-leg-development` and
`compact-2x12-staggered-development` trials replace the legs with single 2x12s,
remove both knees and use four half-inch bolts per leg against retained 4x6
rims. Their fresh A12 rearward cases fail conditional bolt lateral resistance
at 1.949 and 2.079 respectively. The staggered pattern fixes the original row's
127 mm cross-grain layout violation, but does not fix the force shortfall.
These are preserved failed alternatives, not released drilling or viewer defaults.
See `docs/compact-2x12-study.md`. Retain current kicker screw axes and all nine
screws per half; `docs/kicker-screw-placement-review.md` records the tight upper
post end distance and installation checks.

## Current lower kicker row

Current exports and schedules use `compact_spliced_kicker`, wrapping the preserved
trimmed design. Four lower post screws move from Z112 to Z60 mm, at unchanged
X positions; upper post and header axes remain fixed. Retain all 66 panel screws
and 20 bolt stacks. This fresh-stock drilling revision keeps the accepted panel
scope and local placement checks; frozen native cases retain the previous axes.
Do not transfer a claim of six fresh frame solves to the relocation.


## Flush floor-beam direction, September 14, 2026

The owner prefers outboard tapered runners with whole kickers and requests
front/rear runner ends flush to posts/legs, lower side rims flush to posts,
and rear-leg tops flush to side rims. Move bolts and angle brackets as needed
for a supported detail. `compact-floor-flush-development` is the current
selected development direction; preserve preceding designs and native evidence.
Its upper pair is relocated at 56 mm pitch, retaining twelve total bolt stacks.
Removal of 7 mm rim and 18 mm leg-top reserves requires current geometry and
resistance checks. Receiver fit is insufficient; the initial flush rim end-cut
screen fails. Taper-method applicability and omitted runner/leg contact remain
explicit completion gates. Use `docs/tapered-runner-completion-plan.md` and
`docs/floor-flush-build-package.md`; do not claim construction release or transfer
the earlier six-case pass.

## Selected spliced flush-top direction, September 14, 2026

The owner superseded the tapered-runner/flush-floor direction with a narrow
revision of the preserved spliced-knee assembly. The selected development is
`compact-spliced-flush-top-development`: retain solid 4x6 legs/rims, the compact
2x6 base, four independent spliced-knee pieces, all 20 complete outward-facing
bolt stacks, the lower kicker row and the 7 mm rear rim reserve. Remove only the
18 mm rear-leg-top projection and relocate the two half-inch upper bolts per leg
at 56 mm pitch to preserve placement in the flush top.

This is fresh-stock geometry. Do not transfer the six native
`compact-spliced-knee-development` passes or the later trim approximation to
the relocated joint. Require current receiver/washer fit, end/edge distances,
six fresh no-slip assembled cases, member/connection/contact resistance and a
matching export/construction package before conditional completion. Preserve
the prior spliced-kicker package and all floor-runner, floor-flush, uncut and
taper evidence as historical. The selected hybrid has no floor runners and no
1:12 side taper. Do not reintroduce the taper qualification as its gate.

The six fresh assembled cases meet their 21 listed bolt/splice, member, contact
and geometry criteria, but those criteria omit retained ML24Z/SDS connection
separation and independent flange-couple applicability. Treat that commercial-
angle issue as an open completion gate; do not call the current development
package a fabrication release.

## Returned flush floor-runner direction, September 16, 2026

The owner returned to `compact-floor-flush-development`; it supersedes the
spliced flush-top branch as current development authority. Preserve all spliced
geometry and six-case evidence as history without transferring acceptance.
The selected floor-runner assembly retains solid 4x6 legs/rims, compact single
2x6 base members, two outboard 2x6 runners, whole kickers, the 1:12 rear recess,
twelve outward-facing bolt stacks, 24 ML24Z angles and 66 panel/kicker axes.
Use `docs/floor-runner-mvp-master-plan.md` and
`docs/floor-runner-mvp-criteria.md` for current scope and gates.

Six fresh no-slip cases converge and pass all 36 frozen adopted criteria;
`docs/floor-runner-mvp-evidence.json` authenticates the aggregate and
`docs/floor-runner-mvp-angle-demands.json` preserves all 24 station demands in
each case. A12-forward needed one-contact-at-a-time search after three rejected
bulk-search attempts; only its converged fourth result supplies force evidence.
Preserve the old
finite-friction A12-left case as historical evidence. Its projected-seat scalar
is a non-adopted sensitivity; do not delete it or use it as a release gate.
Retained-section, bearing, contact, gross/net member, bolt and listed ML24Z
criteria remain adopted. Unlisted ML24Z separation and independent flange
couples remain disclosed manufacturer-unqualified actions, not invented passes.
No fabrication release or unconditional rating is established.

The September 15 public-product search found no catalog-only larger ML angle or
screw substitution that closes the gate. ML26Z/ML28Z/ML210Z add screws but do
not add a bearing F2 or moment/couple rating; substituting another screw loses
the published ML assembly. For the current floor-runner MVP, follow
`docs/floor-runner-mvp-master-plan.md`: listed interactions must pass, while
unlisted actions remain disclosed without assigned capacity. Written
manufacturer applicability is not an additional FR-8 prerequisite. Any
physical replacement changes connection geometry or stiffness and requires
current CAD/resistance checks and fresh affected cases.
See `docs/compact-spliced-flush-top-angle-options.md`.

## Purchased panel screws, September 15, 2026

The owner purchased Lowe's item 755741, Fas-n-Tite/Hillman model 42605 #10 ×
2 1/2-inch ceramic-coated deck screws, for the 66 panel/kicker locations. Record
them separately from the 144 Simpson SDS25112 screws in the 24 ML24Z angles;
they do not address the open ML24Z separation or flange-couple gate. Public
information supplies nominal retail identity but no product-specific structural
design values or complete geometry. CAD intersections confirm all 66 axes enter
the 139.7 mm wide dimension of nominal 2x6 receivers: nominal penetration after
the 18.25625 mm panel is 45.24375 mm, leaving 94.45625 mm before the rear face.
Use the purchased screws within the owner's accepted panel-construction scope,
but do not transfer SPAX resistance/stiffness. The viewer now shows 66 nominal
Hillman-length/#10-body visuals; exact head/thread geometry is unknown, while
the native response retains its recorded proxy stiffness. Do not equate either
proxy with product-specific resistance. See
`docs/current-panel-screw-purchase.md`.

## Current crash-pad arrangement, September 15, 2026

The viewer uses two owner-built 48 × 72 × 5-inch pads side by side. Their
center seam runs front to back. Each owner-reported stack is two 0.5-inch black
1.7 lb/ft³ nominal-density polyethylene layers, a 3-inch 44-ILD polyurethane core, and two
more 0.5-inch polyethylene layers. Pads remain a selectable viewer-only
placement preview, excluded from CAD inventory, frame mass, floor support and
structural calculations. Do not describe the DIY stack as impact-certified.
See `docs/current-crash-pad-construction.md`.

## Bolted candidate hidden-frame scope, September 20, 2026

For the separate `compact-floor-flush-bolted-development` lane, the owner
directly approved changing hidden frame members as needed for a factory-made
connector design. This supersedes the earlier center-support-only movement
limit in that lane. Keep the selected `compact-floor-flush-development`
geometry and evidence untouched, and preserve the climbing surface, panel
outlines, and all 66 main/kicker screw locations in the new design. The
physical width basis is kerf-right, including narrower kicker blanks; their
edge support must be rechecked after any hidden-frame change.

Factory connectors remain mandatory; ordinary cut/drilled steel and
manufacturer inquiries remain excluded. This is scope permission, not
acceptance of Simpson HL angles, MiTek braces, changed timber, a new load
path, a procurement list, or any drilling operation. G1 and G2 stay open
until a complete installed joint and its applicable resistance evidence
exist. The earlier BR904/AB205 studies remain historical fixed-geometry
screens, not conditions that every new factory fitting must satisfy.
