# Repository working agreements

## Agent workflow

- Automated agents may edit and test locally at any time. Create or amend
  commits and publish only outside Monday–Thursday 07:30–18:00 America/Denver,
  accounting for daylight saving (07:30 is blocked; 18:00 is allowed).
  Both author and committer timestamps must fall outside those hours; delaying
  a push does not make a daytime commit timestamp compliant. Leave work
  uncommitted until allowed hours rather than assigning artificial timestamps.
  The owner explicitly exempted Labor Day, September 7, 2026, from this rule;
  do not infer exceptions for other holidays.
- Configure the local workflow guard with `git config --local core.hooksPath
  .githooks` after preserving any existing hooks. The guard applies to pushes
  from this configured clone; it does not enforce commit timestamps and is not
  agent identity detection or a scheduler. Agents must check both timestamps
  before publishing, including commits created elsewhere or rewritten.
- Preserve other contributors' work and verify remote state before publishing.
  History changes require explicit user direction, a local recovery reference
  and verification that only the requested metadata or content changed.

## Current hardware decision

Develop threaded inserts with machine screws for removable face and kicker
panels where receiver geometry and connection resistance support them. Retain
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

The current candidate is `round-insert-development`. It retains the round-bore
frame and all 56 attachment axes, replacing ordinary panel/kicker screws with
modeled E-Z LOK 801420-13 inserts and Dottie FMDD14114 machine screws. Keep the
eight complete leg bolt stacks and all ML24Z/SDS connections. The insert's
0.25 mm recess, 7 mm panel clearance and 17 mm receiver reserve are provisional
CAD assumptions, not released machining dimensions. Effective thread engagement,
actual installed resistance and plywood head bearing remain unqualified. Do not
transfer SPAX capacity or spacing acceptance to inserts. Keep the preceding
screw candidate and failed numerical trials available as historical evidence.

## Communication

Keep chat concise. Documentation, website text, code and commits use normal prose.
Preserve changes belonging to other agents, including untracked files.
