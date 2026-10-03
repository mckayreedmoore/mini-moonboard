# Existing-evidence qualification register

This register maps all **47 frozen obligations** in [criteria.json](../../../criteria.json)
to the existing numerical evidence, its applicability and the exact missing
modeled comparisons. The owner permits reported exceedances; numerical
completion does not require every comparison to pass. Missing comparisons
remain missing. No authority, criterion, model, hardware inventory or release
flag is changed here.

The [producer](qualification-register.py) exposes `build(output)` and only
authenticates and joins saved data. It imports the frozen authentication
utilities from [closure.py](all-joint-splitting/closure.py), without calling any
mechanical function or historical producer pipeline. No native, CAD, frame,
test or review-loop execution is part of this register.

The producer contains 51 literal seed hashes and expands the existing consumed
source and receipt artifact closures. Its output guard accepts only a fresh
immediate child of the owned raw folder, before any source consumption or write.

## Separate 104 and 108 sources

| Source | Frozen evidence and scope |
| --- | --- |
| Reviewed 104-axis working source | [Working register](working-joint-register.md), machine `rawlocal/working-joint-register/attempt03/register.json`: 24 blocks, 104 physical bolts, 66 Hillman screws; 624 bolt-axis states and 648 lateral-interface states. Register SHA-256 `c34745395481038e32c7474de1798882263de7e54a7cc494949948b4a5e3464c`. |
| Current 108-axis proposal | [Conditional package](knee-bridge-working-package.md), machine `rawlocal/knee-bridge-working-package/attempt02/manifest.json`: 108 bolts/nuts, 216 washers, 66 screws, 50 bodies and 44 timber blanks; 648 bolt/case records and 396 screw/case records. Manifest SHA-256 `4c0d10a86a6018813b5f8efcd7f438662037e458ef3f2ce535d1e0860ca25bd0`; receipt `5fa8cc849e4a2fa042a1cffa6d2957d4163597c7999dbcef1f57563dfdd83e7b`. |
| All-joint splitting demand source | [Latest splitting packet](all-joint-splitting/README.md), commit `af6e03b069324df1063b5e89e7f11af0987f6411`: 30 duties, 44 timber sides, 528 body/case/direction states. Checks SHA-256 `91124cdd68bd440d5221047f77d81b47f13cbcf06e68093f3ebc6c5091a74fb9`; receipt `1c037ed5f138cf738f4f4ca8628e377ef2ffbcf332419f496a5b03aab7d759b9`. This is the reviewed 104-source census, with separately linked 108 spine evidence. |
| Frozen obligations | 36 legacy obligations plus 11 candidate obligations. SHA-256 `fd1df5f106b944d21bc237d0ff789eb30437640ce81cb3e059c7e21f3a531784`. All source statuses remain `pending`. |

The 108 proposal adds two transverse internal bolts to each outer knee spine,
at grain stations 100 and 250 mm. These are same-body axial ties, with no new
global lateral receiver interface. Existing 104 bolt axes and the current 66
screw axes stay at their proposal-package stations. Canonical axis IDs and fit
aliases remain bound by that package; no new holes are inferred here.

Both sources retain **250 lb × 2 downward, signed 300 N horizontal and the
original 100 mm hold lever**, recorded gravity and the proportional 25 kg
equipment allowance. The proposal mass is **225.197914143181 kg**, with dead
factor **1.1110134616260479** and net mass delta **+0.247958829061 kg**. Its fresh
frame comparison is `c3a8ff024fb494032d947aedfd6f00cda8698587b8751b2cec66e4b3af243729`.
Original local forces, permanent-load results and splitting demands keep their
own source scopes; small fresh force changes do not transfer acceptance.

## Completed comparisons and explicit exceptions

Every index uses its own declared reference and same-state witness. Separate
maxima are not combined into a joint capacity.

| Comparison | Supported result | Applicability boundary |
| --- | --- | --- |
| [84 other bolts](knee-bridge-other-bolts.md) | 504 states; 432 applicable lateral references below one, peak **0.953004650**. | **72 end-grain states have null lateral ratios**. Fresh axial action is recorded but not checked by this lateral-only worksheet. |
| [Four corners](knee-bridge-corner-references.md) | All 96 fresh bolt states; lateral/path/mean-seat/smooth-steel peaks **0.813981 / 0.160370 / 0.768962 / 0.318736**. | Declared finished paths, rigid timber/contact laws and smooth-shank proxies; no complete group/splitting or hardware rating. |
| [Four continuous knee shafts](knee-bridge-continuous-shafts.md) | All 24 fresh loaded states balance; 96 placements and interface fits. Smooth steel **192.368797 MPa / 0.303269** against the 92 ksi hypothesis. | Isolated shafts do not establish common knee timber poses or full-frame motion. |
| [Two modified spines](knee-bridge-joint-replay.md) | 2,352 normal-transfer and 5,124 grain cuts; reported reference comparisons pass. Peak tie **1038.983907 N**. | Static internal axial allocations; changed-hole stiffness, shared deformation and complete anchorage/splitting are unqualified. |
| [Bridge washer envelope](knee-bridge-working-package.md) | Fresh peak tie is below saved **1060.656605 N** envelope; conservative stress index **0.697914**. | Fixed geometry, linear elastic plate, zero gap/no preload, concentric **M=0** only. |
| [42 unchanged timbers](knee-bridge-members.md) | 252 balances, 53,784 traces; 33,912 bore-free references. At C_D=1.25, restrained normal/face-shear/component-bound peaks **0.518822 / 0.817219 / 0.951344**. | **19,872 gross-method local/profile traces remain null**. End-only kernel retains 8,293 outside-domain traces. Opening-family results overlap these exclusions and must be matched by station/method. |
| [Physical top rail](knee-bridge-top-rail.md) | All 144 C_D=1.25 physical-pressure traces below one; sufficient bound **0.976501495**. | At **C_D=1**, bound **1.220626869**, with 14 exceeding traces per shear metric. C_D=1.25 point-placement bound **1.184430475** remains a separate diagnostic. Duration and placement are declared assumptions. |
| [Remaining opening sections](knee-bridge-remaining-sections.md) | 4,344 finite limits: 1,968 header-cleat, 2,304 remaining-block and 72 paired-header. All reported references below one. | Nominal ligament sharing, end continuity and twist assumptions; no continuous maximum, local concentration or splitting capacity. |
| [Panel head reference](head-reference-basis.md) | Fresh demand **1871.246254 N**, simultaneous lateral **726.729538 N**, upper-left `edge_2`, A12-rear. Favorable documented head references **930.222–984.128 N** are exceeded. | Reference exceedance is complete evidence, not an observed Hillman failure or product rating. Withdrawal, steel/lateral interaction and compatible panel/contact sharing remain separate. |
| [104-source splitting census](all-joint-splitting/README.md) | Complete demand/path inventory: 27 finite compression cleat directions, 13 positive cleat directions with aligned bolts, eight without parallel bolts; all 40 receiver directions retain point-placement diagnostics. | Existing tensions are already counted. Alignment supplies no spare capacity; zero lower bound supplies no fracture pass. Fresh all-joint 108 resistance is not established. |
| [Nominal proposal fit](../assembly-package/knee-bridge-fit.md) | 58,296 saved-scene pairs plus 1,176 mutual new-stack paths; zero overlap/undecided. | Nominal enclosures and straight paths; tools, tolerance and loaded movement are separate. |

The C_D=1.25 comparison retains the recorded **at most seven cumulative full-peak
days** hypothesis. The coefficient-5 member alternative remains a non-adopted
diagnostic, peak **1.054429** at C_D=1.25. The original permanent C_D=0.9 packet
remains complete at its original 104-source scope, with no current proposal
pass transferred.

## All 47 obligations

“Supported” means the stated finite comparison only. “Null” means a method is
inapplicable or a resistance is absent; it is never zero utilization. A row
with evidence and missing checks is partial coverage. All formal statuses stay
pending. N identifiers resolve to the bounded groups below.

| Frozen obligation | Existing evidence / applicability | Missing modeled groups |
| --- | --- | --- |
| `actual_angle_lateral_CD_1` | Fresh lateral comparisons supported; 72 end-grain nulls; new internal ties are axial only. | N01–N03 |
| `additional_group_reduction_sensitivity` | 104-source row-factor sensitivity 0.962538; fresh corner adjusted references have their own scope. | N02 |
| `local_parallel` | Fresh finished corner path peak 0.160370 and named grain sections supported; not every host/ligament. | N08, N09 |
| `supplemental_EC5_splitting` | EC5 loaded-edge scalar inapplicable to complete opposing/crossed groups; demand census complete, resistance null. | N04 |
| `sampled_net_member` | Bore-free, explicit opening-family, rail and spine comparisons supported; exclusions persist. | N07, N08 |
| `header_gross_full_length_stability` | Saved member kernels retain full strong/beam spans and assumed weak restraints. | N11 |
| `base_bearing_average` | No complete current active-contact-area bearing comparison. | N05 |
| `base_bearing_quarter_area_sensitivity` | Current adopted quarter-active-area comparison absent. | N05 |
| `base_end_notch_shear` | Cut/profile identity available; notch-specific shear applicability unresolved. | N07, N19 |
| `group_spacing` | Axis geometry available; complete all-group rule applicability absent. | N03 |
| `catalog_washer_bounds` | Families/nominal lands recorded; central partial ring stays distinct. | N09 |
| `directional_edges` | Finished corner and bridge facts available; signed both-host oblique rules incomplete. | N03 |
| `steel_direct` | Fresh corners, continuous shafts and internal axial proxies supported; other-axis steel comparison absent. | N10 |
| `washer_bearing` | Fresh corner/bridge references supported; original partial-ring and annulus scopes retained. | N09 |
| `washer_bending` | Original 48-end retail suite supported; fresh bridge M=0 envelope supported; general fresh T/M join absent. | N09 |
| `receiver_fit` | Nominal installed receiver/shaft fit supported; tolerance/motion scope partial. | N18 |
| `overlap_contact` | Twelve frame-law states and named unilateral local witnesses supported. | N04, N05, N13 |
| `all_machining_represented` | 50 effective STEP bindings; filled-bore gross compliance explicitly approximate. | N19 |
| `sampled_member_stability` | Restrained kernel supported conditionally; end-only domain nulls preserved. | N11 |
| `all_bolt_centres_sampled` | All 108 axes and 648 case records bound; force inventory is not section/resistance coverage. | N08 |
| `angle_rated_force_components` | Replace ML24Z method with complete timber/bolt duty resistance; zero angles is no pass. | N02, N04, N09, N10 |
| `floor_rail_wood_bearing` | No-slip frame laws retained; current wood-bearing comparison absent. | N06 |
| `actual_kicker_cutouts` | Kerf-right outlines/current 66-axis policy preserved; both support paths partial. | N15, N19 |
| `taper_native_actual_taper` | Saved rear-recess recipe; exact finished/native identity absent. | N19 |
| `taper_native_matches_cad_taper` | No exact finished native/CAD surface-match comparison. | N19 |
| `taper_actual_mesh_volume` | Drilled STEP/filled-bore retained volumes available; finished native-mesh comparison absent. | N19 |
| `taper_taper_at_least_one_in_ten` | Recorded depth/run 38.1/457.2 mm gives 1:12 geometric identity. | N19 |
| `taper_intended_stock_and_runout` | Recorded 4×6 rear-leg stock and runout, conditional delivered cuts. | N19 |
| `taper_taper_bounds_sampled` | Start/end and trace inventory available; applicable disturbed-section bounds incomplete. | N07, N08 |
| `taper_actual_net_section_normal_resistance` | Intact profile references available; disturbed net-section applicability null. | N07, N08 |
| `taper_sampled_rectangular_shear_torsion` | Intact rectangle comparisons supported; bored/disturbed slices excluded. | N07, N08 |
| `taper_taper_region_unbored_torsion_applicable` | Retained/new bores require explicit runout applicability; no unbored transfer. | N07, N19 |
| `component_layouts` | 24 block duties plus six retained pairs mapped to physical sides. | N02, N04, N17 |
| `flush_face_normal_contact` | Reconciled frame/local witnesses partial; old six-face count is not current completeness. | N04, N05 |
| `flush_face_wood_bearing` | Named fresh seat/band references supported; complete flush/base area census absent. | N05, N09 |
| `flush_sampled_taper_top_clearance` | Nominal fit/bounded seating supported; old 18-monitor count does not supply current tolerance/motion coverage. | N18 |
| `complete_load_path_coverage` | Duty graph and finite transfers available; full path resistance remains partial. | N04, N10, N14, N15 |
| `center_kicker_receiver_paths` | Both inner-edge receiver inventory/current screw moves recorded; complete transfer partial. | N15 |
| `connector_body_behavior` | Finite solid-block comparisons supported; plywood-layer connector method inapplicable, panel behavior separate. | N04, N08 |
| `housing_and_finished_sections` | Actual bore/recess/relief methods partial; no new housing study is required. | N07, N08, N19 |
| `complete_joint_actions` | Fresh simultaneous corner/shaft/static-spine wrenches supported. | N04, N09, N10, N13 |
| `joint_stiffness` | Gross-frame/rigid-local approximations declared; actual changed-hole/shared-pose effects unqualified. | N11, N13 |
| `installed_clearance` | Nominal complete-scene proposal fit supported; tolerance/motion scope partial. | N18 |
| `assembly_and_removal_access` | Straight routes and conditional captured-nut/wire sequences supported; turning/counterhold incomplete. | N16 |
| `demountable_transport` | 50 individual bodies retained; same-spine ties join no transport bodies; zero routine structural wood-thread removal. | No absent numerical comparison inferred. |
| `ordinary_n_envelope` | Datum-bound installed-hardware comparison absent. | N17 |
| `hardware_source_count_cost` | Conditional 108/108/216 order and 66 screws bound; dated prices/unknown terms explicit. | Unknown commercial/product facts; no invented numerical experiment. |

## Exact missing modeled comparison groups

These are existing evidence gaps. They are not new acceptance criteria or an
instruction to perform tests, select hardware, drill holes or run solvers.
The API preserves each as a missing result with `result: null` and identifies
its supporting source references.

| ID | Missing comparison / exact scope | Owner |
| --- | --- | --- |
| N01 | Fresh Ceg lateral references for 12 end-grain axes × six cases; retain adjusted group/detailing limits. Original 104 results cannot replace the 72 current nulls. | Parent |
| N02 | Current adopted additional group-reduction sensitivity and applicable group resistance for current groups, six retained pairs and two internal pairs. Existing scenario row factors are not universal oblique/crossed-group factors. | Parent |
| N03 | Signed spacing/end/edge applicability on both finished hosts of all 108 axes, including header/end-grain axes and four new ties. First-ray zero-direction nulls and fit clearances do not pass detailing. | Parent |
| N04 | Supported simultaneous transverse placement, host transfer and applicable anchorage/splitting resistance across all 30 duties/44 sides under current forces. Six header/inner-frame cleats have unbridged `v` paths; two original spine `v` paths have the separate proposal route. Thirteen positive aligned cleat envelopes still need supported host bypass; 40 receiver point envelopes need physical group/cut placement. New leaves require their own receipts. | Splitting peer |
| N05 | Current base/flush contact average bearing plus adopted quarter-active-area sensitivity, using signed contact actions and supported areas. Washer-seat means do not supply these checks. | Parent |
| N06 | Current no-slip floor-runner wood bearing using signed floor reactions/footprints. Finite friction, anchors and floor tests are outside the adopted assumptions. | Parent |
| N07 | Rear-leg recess/base-end notch shear, tapered net normal/shear/torsion and bore/runout applicability at actual sections. Recorded geometry does not supply disturbed-section resistance. | Parent |
| N08 | Residual finished bore/passage/end-profile sections outside named current finite families, including local ligament transfer and method applicability. Match the saved section inventory to current results; neither 19,872 gross-method exclusions nor 131 stale finished-section matches is a count of physical failures. | Parent |
| N09 | Fresh supported washer/wood and metal T/M comparisons at endpoints outside fresh corner/bridge coverage; explicit fresh-envelope join for the original 48-end retail suite and central supported-ring route. Short-block anchorage and complete supported pressure remain separate. | Parent |
| N10 | Simultaneous axial/lateral/bending steel reference for the other 84 existing axes. Their 504 fresh states currently have lateral-only references; corners/isolated shafts/new ties are already covered by their own declared proxies. | Parent |
| N11 | Current whole-frame stability/motion and full-length header/member restraint applicability. Bounded nominal seating, a representative pose and assumed braces do not establish these results. | Parent |
| N12 | Current proposal permanent C_D=0.9 member/contact/joint comparison with fresh gravity/geometry. Original permanent evidence retains its 104-source scope. | Parent |
| N13 | Shared two-shaft/three-receiver knee deformation, proposed internal-tie compatibility and changed six-bore stiffness. Reuse completed isolated fields/placements; their existence does not solve shared timber poses or feedback. | Common knee deformation peer |
| N14 | Current 66-screw/panel resistance and compatible load transfer: head pull-through, withdrawal, lateral/steel interaction, panel/contact sharing and relevant panel bending. All 396 forces and one balanced governing path do not complete these comparisons. Head-reference exceedance stays visible. | Parent |
| N15 | Both kerf-right inner kicker edges and current 66-axis receiver/backer load paths, including owner moves, under supported simultaneous transfer. An unchanged panel outline or receiver name supplies no connection resistance. | Parent |
| N16 | Modeled full turning, counterhold, installation and reverse-removal stroke envelopes for the stated sequences and four proposed stacks. Existing straight paths/captured-nut/wire routes stay complete within scope. | Parent |
| N17 | Named-datum local-N connector/installed-hardware comparison against 139.7 mm and dimensioned exceptions. Nominal purchased length and blank extents do not supply it. | Parent |
| N18 | Complete modeled tolerance-aware installed/flush/taper-top clearance, retaining nominal fit evidence and separate loaded motion scope. | Parent |
| N19 | Machining completeness, exact finished/native taper surface and volume identity, affected sampling and unbored-torsion applicability. Filled-bore gross compliance is explicitly an approximation; no exact native/CAD pass is inferred. | Parent |

## Required interpretation and model-change decisions

The head-reference deficit is a recorded analytical exception. Retaining the
current 66-screw model leaves that exceedance visible. A claim that the same
reference is satisfied would require a justified supported sharing/reference
change; this register neither invents extra screws nor chooses a change.

The physical top-rail comparison supports the current geometry only under its
recorded pressure placement and C_D=1.25 assumption. C_D=1 exceedance and the
point-placement sensitivity remain results. They do not independently
prescribe an enlarged rail.

The four proposed spine ties establish a particular static normal-transfer
route. They do not bridge the six other unaligned cleats, qualify all receivers
or establish elastic compatibility. Original-point opening bounds cannot
prescribe further holes: supported boundary placement and simultaneous host
transfer can change those cut demands. Existing bolt tension cannot be reused
as spare reinforcement.

The simple model retains dry DF-L No. 2, declared wood/steel properties,
partially threaded smooth-bearing envelopes, first-order local geometry,
rigid local timber, declared K20 unilateral contacts, nominal ligament sharing
and no-slip floor support. No preload/interface friction is credited. The
6.5-inch Grade 5 bridge stock recipe is conditional; 8 inches remains a fit
bound. Delivered profiles, actual wood/floor, hardware properties and tool
operation are unobserved limits. None becomes a blanket physical test or
external-sign-off prerequisite here. Actual/Disposition cells remain blank.

## API, authentication and retained scope

The frozen `build(output)` requires a fresh immediate child of
`rawlocal/qualification-register/`. It checks source and receipt artifact
hashes before reading results and rechecks them before/after publication.
Any changed source, conflicting pin, missing consumed file or altered
obligation inventory stops the build; no changed receipt is adopted.

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python \
  docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/qualification-register.py \
  --output docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/qualification-register/attempt01
```

Outputs are `qualification-register.json`, `receipt.json`, the producer
snapshot and an ignore marker. The JSON contains all original definitions,
47 ordered dispositions, 19 missing-check groups, exact evidence pointers,
separate 104/108 sources, the 30-duty geometry extension map and saved
finished-section applicability inventory. The receipt binds consumed sources
and outputs. The return value reports producer, register and receipt hashes.

Only this new producer and this new document belong to this worker. No Luna
helper was used. Parent owns stability, permanent load, serialized heavy work,
integration and final validation. Peers own common knee deformation and new
all-joint splitting leaves; their unfinished outputs are not consumed.
The current proposal, reviewed source and all consumed historical packets
remain active references. No raw evidence is pruned, archived or repacked;
foreign tracked/untracked work is preserved. No staging or commit occurs.

### Preparation integrity incident

The initial freeze-population command reused its producer destination variable
inside a source-read loop. Its final `write_text` therefore wrote producer text
into `rawlocal/knee-bridge-washer/attempt02/receipt.json`. The producer API had
not run. That command made no original byte copy; the parent recovered the
receipt byte-exact from a verified archive and preserved the bad bytes at
`/tmp/mini-moonboard-washer-receipt-corruption-preserved-1791047411.bin`.

The restored receipt was rehashed against the original frozen
`041067657335395f4b1723a237e11574a0ed0b3efcba4e95f32e25db77d3630f` before
resuming consumption. The corrected preparation command performs reads only
and emits hashes; a separate patch names the exact owned producer path.
No source-file destination can be selected by its loop variable. Changed
receipt bytes were never adopted or repinned, and restoration required no
mechanics rerun. Subsequent edits use explicit patches to the two owned files.
