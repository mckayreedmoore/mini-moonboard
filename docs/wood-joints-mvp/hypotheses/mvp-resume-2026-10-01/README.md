# Conditional MVP-E resumed on the replacement account

The owner directed resuming work and creating a goal on October 1, 2026.
The revised active goal is a simpler coherent working model and conditional
shop package for `compact-floor-flush-wood-joints-development`, starting from
reviewed revision `led-clearance-2x6-runner-seated-blocks-v1`. Complete the
bolted joints, six-case calculations, applicable member/fit/operation checks
and cost/assembly documentation with panel assumptions explicit. Retain
unresolved formal qualification and physical-release flags false. No formal
criterion is closed by this restart record.

## Current analytical working model for the MVP goal

Use the [four-upper-screw packet](upper-corner-screw-layout/README.md) for
the continuation's joint, member and panel calculations. It combines the
existing two-corner correction and all 88 independent bolt clearances with
the owner's October 2 authorization to move the upper screws upward. Four
axes move; two center receivers change to `base_rail_top`. The 66-screw count,
104 structural bolts and 50 bodies remain unchanged. This selects an
analytical packet for the goal, not a physical candidate or fabrication
release. Reviewed source solids retain their old holes; new stations are a
coordinate overlay with filled-bore elastic stiffness and explicit local
section exclusions.

| Required input | Current analytical source / SHA-256 |
| --- | --- |
| Physical rows and elastic projections | `upper-corner-screw-layout/operators-attempt02/`; operator assessment `1a82cd2adbfece3942bf8c90f593f1e21a150adb65db625135aadd258fd5024a` |
| Complete six-case zero/nominal calculation | `upper-corner-screw-layout/frame-250-attempt02/comparison.json`; `bea6cbc330af3cdb20499d774a8f6bb24481d687c3150adb01ede18e4c1d50ca` |
| Saved simultaneous responses | Same packet `response.npz`; `0625196497b0dbc7b297724d7b9947f7c7c61bb282cd4d9681705629302c76c7` |
| Conditional shop coordinates | [66-axis overlay](upper-corner-screw-layout/shop-addendum.md); 62 unchanged and four moved axes |

The load remains 250 lb × 2 downward, signed 300 N horizontal at one hold,
the inherited 100 mm face lever, recorded gravity and separate 25 kg
accessory allowance. All six zero-gap and six nominal-gap states meet their
declared equilibrium, finite connector, no-slip floor and method-domain
checks. Nominal rank remains 296/297 with bounded, nonunique fixed-force
seating. This establishes usable simultaneous forces within the model;
strict stability, a motion envelope and dynamic qualification remain open.

On October 2 the owner directed using reasonable working assumptions and
simplifying the remaining MVP work. Keep this existing load source; hold
dimensions and further lever variants are not prerequisites. The working
joint model uses first-order geometry, rigid timber receivers, the existing
K20 compression-only contacts, smooth partially threaded bolt envelopes
and declared concentric washer lands. Continue the finite joint checks
under those assumptions. Product qualification and physical release retain
their recorded status.

### Replays using this one force source

| Scope | Fresh result under its recorded assumptions | Evidence |
| --- | --- | --- |
| Both top outer corners | First-order physical bore, washer and face forces balance all 12 block / 24 host states; maximum whole-cleat moment residual 0.004500 N mm | [Current first-order forces](upper-corner-screw-layout/corner-first-order.md) |
| Right common rigid block | Fresh lateral/path/mean-seat/smooth-bolt indices 0.813949 / 0.160367 / 0.768962 / 0.318740 | [Same-state component replay](upper-corner-screw-layout/corner-first-order-components.md) |
| Left common rigid block | Fresh actual-left lateral/path/mean-seat/smooth-bolt indices 0.722296 / 0.142295 / 0.666554 / 0.279901 | [Same-state component replay](upper-corner-screw-layout/corner-first-order-components.md) |
| Bottom outer corners | First-order transfer closes 12 block / 24 host states; all 48 fresh bolt records have conditional component indices below one, with 45/92 ksi lateral maxima 0.397806 / 0.278217 | [Bottom transfer](upper-corner-screw-layout/bottom-corner-transfer.md), [same-state components](upper-corner-screw-layout/bottom-corner-components.md) |
| Remaining eligible bolts and lower service | 92 included axes in the remaining method; separate four-axis service result 0.007468 | [Methods and exact exclusions](upper-corner-screw-layout/bolted-replay.md) |
| Header joints and end-grain routes | 72 header bolt states, 36 interfaces and 42 balances; individual end-grain reference 0.052042 | [Header replay](upper-corner-screw-layout/header-replay.md) |
| Retained pairs and washers | Row-factor sensitivity 0.962538; ideal washer wood indices 0.208053 / 0.264300 | [Retained replay](upper-corner-screw-layout/bolted-replay.md#retained-pairs-and-washer-families) |
| Four continuous knee bolts | All 24 loaded states close three receiver wrenches; same-state smooth steel / 92 ksi 0.303443; 96 existing placements retained | [Completed loaded-shaft method](upper-corner-screw-layout/knee-contact-entry.md) |
| Members | 264 balances and 55,176 cuts; declared normal/stability index 0.628421; top-rail shear/torsion exception **1.021524** | [Member replay](upper-corner-screw-layout/member-replay.md) |
| Central partial nut seat | Maximum signed tie 22.952333 N; supported-ring mean-pressure index 0.218668, with actual nut/washer transfer open | [Central replay](upper-corner-screw-layout/bolted-replay.md#bottom-corners-and-central-partial-seat) |

Peaks belong to separate states and are not added. These replays preserve
each method's applicability limits and false complete-joint flags. The
[earlier joint register](joint-register.md) is a historical force index.
The completed [current register](upper-corner-screw-layout/joint-register.md)
maps 24 blocks, 104 bolts and 66 screws to these new vectors: 624 bolt-axis
states, 648 bolt-interface states and 396 screw states. It authenticates
246 consumed bindings, with one inherited helper receipt explicitly
attested through its preserved snapshot and a metadata-only source change.
No additional mechanics solve was needed.

### Remaining decisions

The original single-hold packet retains 1871.251 N nominal panel-head demand
with 726.611 N simultaneous shear. The [head worksheet](upper-corner-screw-layout/head-reference-basis.md)
now reuses the prior Hillman 42605 retailer-nominal 9.017 mm head; favorable
duration-adjusted references are 930.222 N with the declared countersink
reduction and 984.128 N without it. Those are conditional design references,
not measured product breaking loads. Hillman stiffness, plywood properties,
backing/contact fidelity and combined resistance remain explicit panel
assumptions. The [finite hand/foot comparison](upper-corner-screw-layout/paired-load-comparison.md)
returns eight states before contact cycling; it does not replace this
complete source or the 250 lb requirement. Both 140 lb comparisons also
remain incomplete.

The [purchased-panel material check](upper-corner-screw-layout/panel-material-fidelity.md)
confirms a flexible layered operator matching conditional APA AC-plywood
targets. Roseburg product identity is known; Group 1, face-grain placement
and transverse elastic proxies remain hypotheses. No demonstrated product
contradiction was found. The separate rigid/elastic diagnostic identifies
local bending and compliance as sharing questions, not a lower accepted load.
The owner reports cutting full sheets into approximately square halves.
Cross lamination does not make panel bending stiffness equal in both
directions, and a square cut retains the original face-grain direction.
Both directional operators now have complete six-case calculations:
the original slope-grain operator remains this joint replay's source;
the [width-grain comparison](upper-corner-screw-layout/panel-orientation-comparison.md)
has nominal peak panel tension 1280.799 N. Neither calculation establishes
the actual cut panels' grain orientation or requires recutting them.
The separate 20-main-panel-screw/98-total comparison also completes all
twelve states, with a 2180.721 N nominal lower-left peak; it does not select
a new screw inventory or demonstrate that screw count alone improves sharing.

The top-rail 1.021524 shear/torsion reference exceedance remains unresolved
for the current 100 mm force lever. The completed
[50 mm lever sensitivity](upper-corner-screw-layout/load-lever.md)
preserves the full forces and completes twelve frame states. Nominal peak
screw tension falls to 1707.613 N and lateral force to 1126.477 N; the
declared head/wood reference deficit remains. The targeted
[top-rail replay](upper-corner-screw-layout/top-rail-limit.md)
returns a 0.960773 face ratio and 1.118391 same-cut component upper bound.
The sensitivity is not adopted and does not establish an all-section pass.
Local disturbed stresses, elastic timber/two-group resistance, washer/head/nut
transfer, continuous-knee contact and actual shank/thread profiles retain
their stated limits. The completed left and right rail/side pairs supply compatible
local bolt responses at the unchanged source group wrenches. Their combined
rigid-block accounting does not feed redistribution back into the frame.
The later [independent cleat traction recovery](upper-corner-screw-layout/cleat-traction.md)
identified a fixed-axis geometric-tension moment discrepancy in the old
local branch. The simpler [first-order corner replay](upper-corner-screw-layout/corner-first-order.md)
omits geometric shortening and preload stiffness consistently. Both actual
corners now complete all six local cases with independently balanced bore,
washer and face forces; maximum whole-cleat moment residual is 0.004500 N mm.
These new actions are the continuation's local timber-force source. The
integrated frame and old numerical packets remain preserved.
The [fresh same-state component replay](upper-corner-screw-layout/corner-first-order-components.md)
covers all 48 local bolt states. Its conditional maxima are 0.813949 lateral,
0.160367 finished path, 0.768962 mean washer pressure and 0.318740 smooth
steel / 92 ksi. The [actual cleat section inventory](upper-corner-screw-layout/corner-timber-sections.md)
now uses those balanced physical actions: 25,224 signed cut limits retain
the paired-bore ligaments and their full bending and torque demands. The
[finite bore-wall map](upper-corner-screw-layout/corner-bore-wall.md) preserves
each transverse force and full moment on supported cylindrical walls and
returns eight deciding cuts under an explicit cosine pressure hypothesis.
The [nominal net-section calculation](upper-corner-screw-layout/corner-net-section.md)
now completes those eight cuts and 24 retained regions under the recorded
end-bridge/common-strain and shear-sharing assumptions. Its largest tension,
compression, bending and same-state shear/torsion indices are respectively
0.078053, 0.028558, 0.043033 and 0.241977. Regional forces and moments recover
the complete signed source wrench; these nominal comparisons do not assign
notch, splitting or whole-group capacity.
The [washer free-edge calculation](upper-corner-screw-layout/upper-right-washer-edge.md)
repairs the earlier approximation defect at one fixed 709.053 N / 2.292 Nm
end witness. Its two prescribed resolutions give 510.595 / 512.232 MPa
elastic plate stress proxies with decreasing free-edge residuals. This
conflicts with the expressly hypothetical 250 MPa yield input; actual
washer yield and resistance remain unknown. No delivered hardware failure
or stronger-hardware requirement is inferred from that hypothesis alone.
The completed [exact-product source check](upper-corner-screw-layout/washer-product-basis.md)
confirms that the existing washer listings provide dimensions and low-carbon
steel wording, without a numerical minimum yield. The nearby standard head
gage circle is not a guaranteed installed flat contact circle. Those facts
preserve the analytical material/footprint assumptions rather than converting
the stress proxy into a product capacity or a new procurement minimum.

The owner's requested [retail thick-washer comparison](upper-corner-screw-layout/retail-washer.md)
now completes both prescribed resolutions at the current first-order
707.884 N / 2.432 Nm rail-end witness. The single declared 25.4 mm OD,
8.3058 mm ID and 2.5 mm thickness gives 206.790 / 207.205 MPa stress proxies;
the finer result is 0.828821 of the assumed 250 MPa yield. The saved finished
face supports the enlarged concentric annulus. This is one conditional
hardware option; actual retail dimensions, yield and installed fit remain
unmeasured, and the 208-washer census is unchanged.

The [assembly package](assembly-package/README.md) remains the dimensional,
transport, stock, purchasing and operation basis, read with the four-axis
overlay above and its [current-joint addendum](assembly-package/current-joint-addendum.md).
Its 104-stack dimensional specifications and nominal longer-
bolt fit do not depend on the changed panel forces. Loaded operations and
the central-seat demand use their explicit force-source scopes. Priced
hardware terms total $189.58 when the retained increment is counted once;
missing order terms remain listed. Actual/Disposition cells stay blank.

All 47 formal criteria remain pending and all eight release flags false.
Selected-baseline authority and historical packets are preserved. This
integration adds no native run, hardware substitution, software tests or
agent review loop. Parent owns shared staging, execution and the returned
register leaves. Both top common-block calculations and their component
replays are complete within the explicit rigid-cleat assumptions. Separate
workers completed the [24-block duty map](upper-corner-screw-layout/remaining-block-duties.md)
and [group applicability worksheet](upper-corner-screw-layout/block-group-resistance.md).
All 48 exterior host cuts admit the complete local group footprint, so
their whole-host wrenches remain reusable after the bounded redistribution.
Interior group tractions and local splitting resistance remain separate.
Current bounded implementations address those cleat tractions, the four
continuous knee bolts, one partial central seat and six header duties.
The [central-seat transfer](upper-corner-screw-layout/central-seat-transfer.md)
now demonstrates a conditional static compression route through the supported
10 mm ring at 0.942288 MPa, with signed algebraic coupon checks. Nut/washer
coverage, centering and material properties remain explicit hypotheses.
The [remaining twelve-block section calculator](upper-corner-screw-layout/remaining-net-sections.md)
now completes 2,304 recorded opening-section limits under the same nominal
sharing assumptions. All evaluated comparisons are below their stated
references, with peak normal diagnostic sum 0.001798 and regional
shear/torsion bound 0.032202. Source forces, actual finished bores and
member identities remain unchanged.
The [header input contract](upper-corner-screw-layout/header-local-transfer.md)
preserves all 394 simultaneous header actions per case and the six existing
disconnected paired-bore sections for the remaining local transfer work.
The [loaded knee method](upper-corner-screw-layout/knee-contact-entry.md)
is now complete for four shafts and six cases. An exact forward clearance-entry
step resolves the earlier low-load iteration stops without changing the
physical model. Ten accepted states are reused and fourteen new states close
independent receiver force and moment balances. This finite K requirement
has no remaining state; local wood and delivered hardware retain their own
recorded scope.

The concise [joint MVP disposition](upper-corner-screw-layout/mvp-joint-disposition.md)
collects the completed finite checks, conditional shop links and the two
remaining panel-head/top-rail reference exceptions. Use it for the current
working decision; preserved preparation notes and historical force tables
do not add new prerequisites or replace the current source.

## Preserved previous working model and ownership

The following section retains the former `two-receiver-frame-attempt03`
selection and its then-current summaries. Its numerical claims are history
for this goal; use the explicit analytical source and fresh replays above.

The current force source is `two-receiver-frame-attempt03/`: comparison SHA-256
`0ff0dfc00c112a906910641141fd242f4a58295aa3324ca569132a3fa2d388a5`, response
SHA-256 `774c3bbddf8061f6b9d1cfdd5f22efbeb1025bd57431a249912ae8e60a731f52`.
All six zero-gap and six nominal-gap states conditionally pass declared
force-balance, connector-law and floor-law checks. The 88 independent
two-receiver candidate bolts have modeled radial gaps; four continuous
candidate bolts and twelve retained bolts remain at zero gap. Each nominal
state has finite fixed-force seating bounds, rank 296/297: seating is bounded
but nonunique, with neither strict tangent stability nor a motion envelope
established. See [bounded clearance](bounded-clearance.md) and the
[main summary's current component table](../../README.md#current-working-model).
The [retained-pair sensitivity](retained-group-checks.md) now preserves all
36 pair/72 bolt states and gives 0.9613 for the governing front-left reference
after division by the smallest of four declared row factors. The actual
oblique-group factor is not adopted.

The [retained-washer calculation](retained-washer-checks.md) binds all 24
exterior roles and 144 current seat states to their separate catalog
diameters and saved bores. Ideal full-support wood-pressure ratios peak
at 0.208291 for 3/8-inch and 0.287806 for 1/2-inch stacks. The subsequent
[current saved-STEP support check](retained-washer-support.md) confirms all
24 nominal concentric annuli at three shallow probe depths, including four
head seats on the corrected side-member copies. Loaded shift/tilt and washer
metal acceptance remain open; actual-inspection fields are unchanged.

The [continuous knee-bolt construction](knee-bearing-checks.md) now recovers
24 static bearing/shear/bending states and 96 normalized endpoint fields.
All 72 actual receiver wrenches match; peak nominal bearing/steel indices
are 0.359589/0.592568. Static endpoint fields fit the declared nominal
bounds. Actual bore-wall compatibility, common-bolt clearance, thread
sections and adjusted complete-joint resistance remain open.

The [common-shaft placement calculation](knee-bore-fit.md) finds 96 explicit
straight-shaft witnesses across the four continuous bolts and both saved
gap states. Total-motion fits retain at least 0.435309 mm radial margin;
their largest scalar projection error is 0.006500 mm. This indicates no bore
enlargement from the stated geometry model. It does not supply loaded bore
reactions or change the four source zero-clearance laws.

The [central-seat comparison](partial-seat-bearing.md#current-catalog-washer-opening-comparison)
now uses the catalog quarter-inch washer opening with current forces.
At maximum ID 8.3058 mm, the supported 10 mm outer circle gives a
conditional uniform-pressure ratio of 0.214602, replacing 0.1424875 for
that washer-opening hypothesis. Actual nut/washer transfer remains open.

Current panel references retain an unresolved strength exception. At A12-rear,
`round_panel_upper_left_edge_2` carries T=1836.884 N and V=807.662 N. Generic
lateral references are 386.752/463.413 N; the favorable combined index is
2.724895 at K12-rear, `round_panel_upper_right_rim_4` (V=1274.054 N,
T=625.635 N). Conditional head references are 277–629 N and generic withdrawal
references 711–1073 N. These comparisons establish no measured Hillman rating
or physical failure. On October 2 the owner challenged the mounting
representation using the official assembly's described four-per-edge,
shared-corner pattern. The [mounting comparison](panel-attachment/official-pattern-comparison.md)
and [force direction/load basis](panel-attachment/force-direction-and-load-basis.md)
are now the first step: establish layout/backing and sharing fidelity before
treating an edge keeper or revised panel fastener as necessary. The owner
then authorized a [four-upper-screw relocation comparison](upper-corner-screw-layout/README.md).
Its complete 250 lb dynamic calculation retains a 1871.251 N nominal axial
peak, above the declared generic head references. Both 140 lb comparisons
currently stop on contact branch cycling; partial states establish no full
envelope. This child revision does not replace the current force source or
transfer component acceptance. Its [fresh member replay](upper-corner-screw-layout/member-replay.md)
now checks 264 balances and 55,176 cut traces: the normal/stability references
remain below one, while top-rail face shear/torsion is 1.021524.
The [fresh bolt replays](upper-corner-screw-layout/bolted-replay.md) cover
top corners, the remaining-bolt methods, end-grain and lower service with
that same source. The [head-reference correction](upper-corner-screw-layout/head-reference-basis.md)
confirms that the quoted values are design allowances and explicitly include
plywood grade/net thickness; even the favorable declared 1.6-duration
scenario remains below the saved 1871.251 N demand. The
[66-axis shop overlay](upper-corner-screw-layout/shop-addendum.md) records
the four authorized moves without changing guide authority or drilling
instructions. These child records preserve the current source above.
[Panel records](panel-attachment/README.md)
and the [lateral comparison](panel-attachment/lateral-reference.md) retain
assumptions and source detail. The [edge-restraint proposal](panel-attachment/edge-restraint-proposal.md)
now specifies 20 mm corner margins on all four main panels. Its 48 static
allocations retain zero main-panel screw credit; the largest minimum corner
L1 load is 1083.408 N. Keeper profiles, frame attachments, resistance and a
compatible response are unestablished. The [one-stock RSS alternative](panel-attachment/fastener-alternative.md)
also misses the existing strength/applicability screen. Neither proposal is
selected. Earlier six-joint and softer-law values remain
historical; see the [preserved comparison](panel-attachment/README.md#earlier-all-outer-source-returned-compatible-stiffness-sensitivity)
and [component record](top-corner-component-checks.md).

A separate [current-frame 100 N/mm sensitivity](panel-attachment/README.md#all-two-receiver-100-nmm-sensitivity-attempt09)
now completes all twelve states with the same 88 bolt clearances, unchanged
lateral stiffness and original model-domain gates. Its modeled-gap peak
withdrawal is 906.577 N at upper-right `edge_2`, with 1022.807 N simultaneous
lateral force and 9.065770 mm representative opening. The largest declared
head reference is 628.941 N; favorable same-state combined loading peaks at
3.006796 elsewhere. This unmeasured law is not selected, supplies no motion
envelope and transfers no component acceptance from the baseline.

The other current strength exception is the top-rail face-shear/torsion proxy:
1.039209 against the declared 180 psi allowance. Its governing cut is
52.189 mm beyond the cleat contact footprint; the pointwise stress field in
this local transfer run is not established. No fix is adopted. See the
[member stability record](member-stability.md).

The [current header-action replay](header-joint-checks.md#current-bounded-replay--attempt02final)
has zero first-ray distances below 4D and no adopted actual detailing failure:
70 states have zero in-plane action; the two directional states reach the
±X faces at 26.95 mm, above 4D = 25.4 mm. The earlier BG045 Y-edge exception
remains historical and does not require an axis move from this force set.
The [header placement calculation](header-endgrain-placement/README.md) now
covers all twelve axes and 72 signed states. Applicable translational
end/edge/spacing checks clear; the two active loaded edges retain 1.55 mm
above 4D. No axis move follows from these states. Local splitting,
eccentric load transfer and torque resistance remain unresolved.

The [header load-path calculation](header-local-transfer/README.md) now
attributes 1,092 physical point wrenches exactly to the saved operator.
The target interfaces contribute negligible Y action; existing Z through-bolts
load their own header seats inward. The actual Y withdrawal path belongs to
the kicker screws, with 290.233 N maximum nominal point force. One connected
finished-section probe places the complete nominal receiving segment on the
bending tension side, at least 26.712 mm from the zero-normal-stress plane.
That location question is resolved. Local combined Y transfer/resistance and
actual metal/seat behavior remain conditional; no complete joint pass follows.

Pane %25 completed its original panel packets. At model capacity, a bounded
helper completed the generic lateral screen; no panel implementation is active.
Pane %22 owns `assembly-package/hardware_length_fit.py` and
[hardware-length-fit.md](assembly-package/hardware-length-fit.md). The parent
completed its saved-source screen for twelve proposed longer bolts: 48,190
pairs separate by conservative bounds, and two exact STEP pairs have zero
intersection and 18.158 mm minimum distance. No added tip or headward-increment
pair remains undecided. Full nut/thread/tool operations are outside that screen;
no length or hardware is selected. Other bounded/native helper tasks are
complete or closed.

The published [conditional hardware and shop package](assembly-package/README.md)
reconciles 50 bodies, 104 bolts, 104 nuts, 208 washers and 66 separate Hillman
screws. Its priced subtotal is $158.46 plus missing terms, not a complete cost.
The [dated catalog update](assembly-package/catalog-costs.md) supplies a
separate $31.12 retained-hardware increment, giving $189.58 of combined
priced terms if counted once. Missing terms and supplier profile conditions
remain explicit.
All 47 criteria remain pending, all eight physical-release flags remain false,
and all Actual/Disposition cells remain blank. Formal qualification remains
HOLD. No review loop, new native solve or software tests were run for this
update. The parent owns integration, longer-bolt execution, shared staging and
commits.

## Preserved restart and earlier calculations

At intake, the parent rechecked all 176 files in the preserved handoff snapshot:
every size and SHA-256 matched. The workspace was dirty on `master` at
`f05130c157982b9fc9d1a35690f5167d79ae63f8`. The native ledger has 60 registered
runs and its slot was observed idle; its SHA-256 remains
`fd99fa971acb8f63e0447d616ba0552a4553bb680888e1f688aea381ce029d7c`.
These observations are not execution reservations.

The current account's read-only quota RPC reports 2% included weekly usage,
ordinary usage allowed, no reached-limit type, and reset time 1791080461.
This supersedes the former account's 99% observation for scheduling only.
Credits and paid/API fallback remain prohibited. Recheck usage before heavy
execution and stop at included exhaustion.

The owner reports one existing agent working on the upper-left joint. That
agent retains its joint files and decisions. No former secondary assignment
is resumed by this record. The parent owns remaining calculations and
integration. The upper-left joint remains with its existing owner.

## Current owner direction: simple MVP model, no agent review loop

Later on October 1, the owner explicitly stopped the recurring agent review
loop and directed work toward a simple working MVP model, with improvements
afterward. This supersedes the review-loop schedule recorded earlier in this
restart and the recurring independent-review workflow in the active goal.
The six temporary reviewers have been closed; their existing reports and
source archives are preserved. No additional review round is scheduled.

Use current geometry, recorded loads and existing material references for
direct statics, member and bolted-joint calculations. State each simplifying
assumption and use engineering error tolerances appropriate to its purpose.
Report real load-path or resistance failures and required geometry changes.
Do not make export-precision investigations, detailed contact meshes or
provenance-tool development prerequisites for every ordinary calculation.
The STI17 build/coupon and stress-provenance implementation are parked
method work; neither has executed a production freeze or native run.

The parent has now produced a [simple frame calculation](simple-model.md)
with all six independent static scenarios, simultaneous bolt demands and
basic lateral references. The next priority is the complete load path and
wood/bolt group behavior of the two top outer corners before further diameter
sizing. They remain distinct from the existing owner's upper-left service
joint. No reviewed geometry or axis has changed.

The parent then completed [six-case top-corner action and section screens](top-corner-checks.md):
24 complete receiver states, 30 whole-body balances, 120 cleat section traces
and both-edge host splitting characteristic references. The side-bolt
couples remain the immediate concern; local bore paths, rail-pair adjustments
and complete washer/joint behavior remain open. This calculation required
no native execution or independent review round.

The next [local calculation](top-corner-local-checks.md) covers 32 finished
bore shear planes and 48 simultaneous local bolt states. The largest
declared parallel path ratio is 0.1954; the largest ideal washer wood-pressure
ratio is 0.5892. Rail end and group-factor scenarios are calculated explicitly.
The side-bolt lateral concern persists, so the next parent task is a local
correction carrying its actual couple and ordinary stock/hardware constraints.
The read-only account check now reports 9% included weekly usage, ordinary
usage allowed and no reached-limit type; paid/API fallback remains prohibited.

The parent prepared an [isolated top-corner correction](top-corner-correction.md):
two full 4×6 cleats, four 5/16-inch side bolts at 67.85 mm pitch, four moved
axes and four longer rail grips. All twelve side-pair lateral wrenches are
preserved across the six cases. With diameter-specific wood bearing, peak
106 ksi-hypothesis ratios are 0.811 left and 0.930 right; the 45 ksi
sensitivity still exceeds one. Two proposed cleat and two side-host STEP
copies retain the reviewed source artifacts. Wood/panel collision queries
and sixteen straight tool-approach scenarios find no modeled conflict in
their stated scope. Changed normal contact/tie transfer, whole-frame
redistribution, the bolt-property basis and complete joint resistance
remain open. No reviewed scene or authority file has changed.

The owner then made resolving unfinished joints the parent's main priority.
One bounded helper completed the [no-Hillman-withdrawal frame check](no-withdrawal-frame-checks.md);
the existing upper-left service-joint owner remains separate. All six cases
stop on upper-panel normal equilibrium. A representative A12-rear linear
statics check is infeasible even with all floor tangents retained. The source
frame therefore needs a supported panel withdrawal load path; the original
parametric screw springs cannot be removed while retaining static balance.
The peak original individual screw demand is 1922.134 N. The parent confirmed
the contact directions against the overhanging source geometry and recorded
the [next panel-joint task and a generic withdrawal reference](panel-joint-priority.md).
This is a specific unresolved panel-joint requirement.

The parent completed [coupled normal transfer for both proposed top outer corners](top-corner-contact-checks.md):
all twelve local states meet force/moment balance and unilateral spring laws.
Peak bolt tensions are 348.223 N left and 385.839 N right; affine edge contact
pressures are 2.63295 and 2.89535 MPa under the stated rigid-cleat/fixed-host
scenario. Original lateral demands and self-weight remain fixed, so frame
redistribution and complete joint resistance stay open. The right side-bolt
fixed-demand screen needs at least 91.746 ksi Fyb before further adjustments;
92 ksi supplies only about 0.14% arithmetic margin and is not adopted here.
No review loop, native solve or physical release was added.

The original A12 raw-H comparison remains STOP with 27 force-interval
failures. Missing frame cases, complete joint resistance, compatibility and
all 47 criterion dispositions remain open. All physical release flags stay
false and observation cells stay blank. Preserve all former frozen inputs,
failed outputs, consumed markers and referenced `/tmp` files.

## Service-joint and Hillman integration

The owner directed ingesting the service-joint worker's latest work and the
previous Hillman work. The parent checked 203 distinct saved-source bindings
and recorded the [integrated decisions and calculations](service-and-hillman-integration.md).
The latest coupled left-service worksheet supports retaining its reviewed
geometry: at modeled clearance, peak bolt shear/tension are 9.376/12.814 N
and local movement/rotation are 0.5575 mm/0.1054°, within that study's explicit
twice-recorded three-case scope. Complete joint acceptance remains HOLD.

Both parent frames include all 66 Hillman axes, and their station/receiver
mapping matches the previous receiver-transfer packet. The parent then reused
the worker's circular-gap method on the top-right corner across all six
independent full static cases, on reviewed and isolated proposed geometry.
All 24 returned states meet balance/law gates. The proposed nominal-gap
right-corner Grade 5 individual reference peaks at 0.7904, while zero-gap
remains 1.1593. The nominal-gap local movement/rotation peaks at
2.3276 mm/0.9645°; its complete resistance and motion compatibility are open.
Stronger hardware remains an option, with no selection made. The model keeps
panel stiffness and withdrawal assumptions explicit and transfers no product
rating or complete-joint pass from the previous Hillman work.

The isolated corrected whole-frame calculation also meets its balance/law
gates in all six zero-gap scenarios, with peak body translation 4.374 mm.
Its exact calculation snapshot and outputs are preserved in
`corner-frame-attempt01/`. This does not resolve the original native raw-H
failure or authenticate the three missing native cases. The parent changed
no worker packet, reviewed scene, authority file or native ledger and invoked
no new agent review or software tests during this integration.

The subsequent [both-corner frame and component worksheet](top-corner-component-checks.md)
includes both proposed corners' clearance in one model, with changing floor
branches and all 66 conditional Hillman paths. All twelve frame states meet
their balance/law gates. Six-case component references peak at 0.7012 left
and 0.7992 right for the conditional Grade 5 scenario. Finished tangent-path
and washer wood-pressure comparisons are below one; combined steel, washer
metal, complete splitting/group behavior and functional motion remain open.
The worksheet binds the worker's final panel-sharing packet without rerunning
its historical screw force records. The external worker now owns the lower-left
outer service cleat; two bounded parent helpers handle remaining-joint screens
and hardware fit, and a third computes same-state member screens. No recurring
review loop is used.

The worker's lower-left outer assessment is now complete and ingested without
rerunning its 84 states. The parent has then included both left outer service
clearances with the two top corners in all six working cases. All twelve
zero/gap states pass frame-law gates; updated top-corner conditional Grade 5
individual ratios are 0.7071/0.8035, and concurrent steel-allowance scenarios
give 0.7158/0.8148. Lower-left local movement is 0.5291 mm with 4.952 N shear
and 13.791 N tension peaks. Complete qualification remains HOLD.

The [hardware fit and assembly worksheet](top-corner-hardware/assembly-fit.md)
now reconciles both corner stacks, removable through-bolt operation, quantities
and observed listing costs. Turning/counterhold, full shaft extraction and
actual delivered profiles remain explicit missing inputs. The Grade 5 side
package includes a 50-bolt purchase with 46 surplus; its $127.12 observed
subtotal cannot be compared as an eight-bolt unit price with the $27.68
Grade 8-side/Grade 5-rail listing scenario. Neither option is selected.

The [same-state member screen](member-checks.md) covers 264 whole-member
balances and 54,888 two-sided cut traces across all six cases. Applicable
elementary normal/shear references peak at 0.5415/0.3735 in the top rail;
finished connection regions, torsion and stability remain separate checks.
Clipped-tip beam singularities are non-applicable in a corrected child packet;
their actions and prior results remain preserved.

The [central-footprint worksheet](partial-seat-bearing.md) finds a fully
supported declared 10/7.3 mm ring at the center-principal right nut seat.
At 82.628 N peak tension its conditional mean wood-pressure ratio is 0.5227.
Actual nut/washer transfer remains missing; the original partial-seat
exception is not closed. No axis, passage or hardware changed.

The [remaining-joint worksheet](remaining-joint-checks.md) covers 80 other
candidate axes and 12 retained axes, with 576 simultaneous signed plane
states. Its governing eligible axis is the bottom-left outer `side_1` in
A1-rear: 682.380 N shear and 207.852 N tension together. The conditional
92 ksi individual lateral-reference ratio is 0.7890; the 45 ksi sensitivity
is 1.1282. No bolt or member enlargement is selected. Complete bottom-left
joint transfer is the next local priority, followed by the 12 end-grain axes
and four continuous three-receiver bolts with explicit separate-method gaps.
The partial nut-seat pressure stays null in the general table; the parent's
central-footprint scenario remains separate.

## Work completed during this restart

The first two STI17 source-review passes found and the parent fixed the
manual-pin typo, missing exact coupon payload guard, PATH-resolved timeout,
missing final build-review binding, freeze/review races before reservation,
unbounded swap allowance and repeated review-record acceptance. The old
targets, inputs and findings remain in their separate pass folders. Current
checks pass 27 tests, 48 subtests and Ruff. The last source-review target is
[pass 3](sti17-source-review-pass3/source-review-target.json), SHA-256
`008ba73850288a620561a26558001f913079a7e904b85d029d16e07b1dd0fcf7`.

The separate [stress provenance checker](../orthotropic-stress-frame-provenance-preparation-2026-10-01/README.md)
is now implemented and passes 22 synthetic tests and Ruff. Its exact eight-file
source target and input archive are in
[the first checker review](stress-provenance-source-review-pass1/source-review-target.json),
SHA-256 `e27297f27f2e1941c75adf571d482eeb8605c063c673bcc37c7af60168277226`.
The production freezer and scoped hard-stop launcher remain pending. Neither
the checker nor its test fixtures reserve a run or authenticate a real native
execution.

The immutable base-image read-only probe matched the original binary,
matrix writer and timeout utility hashes and confirmed absence of the STI17
copy and binary; its receipt is [runtime-readonly-preflight.json](runtime-readonly-preflight.json).
No isolated build, new image, production freeze or native run has started.
Other owners' repository and viewer work is preserved.

## Publication scope

The owner subsequently directed committing and pushing work as it progresses.
The first mechanics publication contains approximately 301 kB of maintained
calculation sources, existing result summaries and the isolated proposal's
small SVG. It excludes unfinished producers and the parked review archives.
Frozen JSON, response arrays, STEP copies and raw runs remain at their original
ignored local paths under the repository's evidence-retention policy. This
commit is a source-and-summary publication, not a complete remote backup of
those local evidence files. Reproduction still requires the referenced frozen
inputs and pinned dependencies. No source witness, temporary file or other
owner's work is deleted, reformatted or substituted by publication.

Subsequent incremental publication includes the completed four-joint integration,
same-state steel allowance, conditional hardware fit and the three unchanged
source/summary files transferred by the lower-left worker. Bulky generated
outputs remain ignored and preserved. Shared staging and commit hooks stay
with the parent while bounded calculation helpers work in separate files.
