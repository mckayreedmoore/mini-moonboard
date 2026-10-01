# T07/T08 fit and option crosswalk — attempt01

**Status:** source-bound identity and comparator crosswalk only. This joins
T07 `current-fit-transport-closeout-attempt02` to T08
`current-hardware-material-cost-closeout-attempt01` for candidate
`compact-floor-flush-wood-joints-development`, revision
`led-clearance-2x6-runner-seated-blocks-v1`. It makes no new product or tool
selection; candidate bolt/nut/washer/spacer options and tools remain
unselected, while the 66 screw axes retain the existing Hillman 42605 policy.
All 170 physical fit/access/reversible-operation/support and transport outcomes
remain unresolved.

The [machine-readable crosswalk](option-crosswalk.json) contains one row for
each of the 92 candidate bolt axes, 12 retained starting frame-bolt stacks, and
66 fixed Hillman 42605 panel/kicker axes. Each row has exact JSON record
pointers and canonical-record hashes into both T07/T08 registers; it joins
candidate leads by stable T08 catalog-lead IDs, retained arrangements by the
selected-baseline Bolt Depot reference IDs, and panel axes to the fixed Hillman
purchase policy. Its `source_hashes_verified` list includes all transitive
T07 source pins and all 35 T08 source pins, as well as the reviewed packet
files. The producer re-hashes and checks these before writing.
The linked T08 material/cost register remains pending; it records no candidate
product selection or current candidate total, and its price observations do
not qualify a product for fit or transport.

## What the current records support

For 92 candidate axes, T08 supplies per-axis catalog-lead IDs, conditional
nut/washer/spacer IDs where actually assigned, a model length/grip, and null
delivered shank, thread-interval, matched-nut interval, and selected-product
fields. The linked lead records retain their published spec and thread text;
some state nominal hex/head or washer/nut dimensions. These are lead-level
comparators only. T07 links each candidate to its modeled head/washer/nut/
shaft path screens and the synthetic 7/16-in FACOM profile with sampled poses.
The proxy has no selected wrench, real jaw engagement, hand/workspace,
counterhold, tolerance, matched thread, support or capture proof. Where an
axis has no T08 nut/washer lead IDs, the crosswalk does not assign the shared
conditional accessory pool to it.

For 12 retained stacks, T08 preserves the selected-baseline Bolt Depot
references: `#407/#2573/#15025` for the four 1/2-in leg bolts,
`#367/#2571/#15023` for the four front 3/8-in bolts, and
`#368/#2571/#15023` for the four rear 3/8-in bolts. Its source rows and the
matching retained-axis CSV rows include nominal/model dimensions, while T08
still says ownership/delivery is unverified and a current-candidate recheck is
required. T07’s per-axis access study applies a synthetic 7/16-in FACOM tool
proxy. For the #407 leg-bolt reference the T07 tool proxy is 7/16 in while the
pinned source describes the bolt hex as 3/4 in; the separate 3/4-in Wera
profile is only an unapplied comparator. For the 3/8-in refs the pinned T08
axis rows do not bind a precise head-across-flats dimension to an actual tool.
None of these proxy results clears fit or access.

All 66 panel/kicker rows keep the owner-purchased Hillman/Fas-n-Tite 42605
policy and the lead-hole plus face-countersink instruction. The pinned local
purchase note says #10 x 2-1/2 in, #2 Phillips drive, and names the Kobalt
80277 #10 pilot/countersink set. That set is the pilot/countersink choice; it
does not identify a #2 Phillips driver or show driver/hand clearance. T07’s
receiver-axis envelope is a historical CAD proxy, not actual Hillman
dimensions. The receipt amount and Hillman structural-property map remain
outside T08.

## Exact missing inputs

The row-level `missing_data` fields name the needed source for every axis. In
summary, candidate stacks need final product/lot identities; dimensioned
records or traceable measurements for the bolt thread transition/shank, matched
nut active thread/chamfer, washer/spacer dimensions and tolerances; selected
tools and current assembled-scene workspace; and a supported capture/reverse
sequence. The retained axes additionally need current WJ24 product/ownership
confirmation and current-candidate rechecks. The Hillman axes need exact
42605 lot dimensions/tolerances, a selected #2 Phillips driver/access screen,
and the checklist-recorded pilot/countersink offcut trial. These are named
source requirements, not requests to assume a clearance or select hardware.

## Reproduction

From the repository root:

```sh
python3 docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-fit-transport-option-crosswalk-attempt01/build_crosswalk.py --write
python3 docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-fit-transport-option-crosswalk-attempt01/build_crosswalk.py --check
```

`--check` reconstructs both outputs from the pinned T07/T08 packets, verifies
the transitive local-source hashes, enforces exact 92/12/66 identity joins,
and fails if any per-axis physical status is no longer unresolved. This
crosswalk is an evidence join, not a fit or engineering acceptance.
