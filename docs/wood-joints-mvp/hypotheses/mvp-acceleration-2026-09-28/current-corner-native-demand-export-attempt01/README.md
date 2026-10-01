# Current five-member corner demand exporter

This packet consumes one source-bound model and a passing
`current_springa_frame_physical_response_audit/v1` JSON. It does not launch a
solver or parse raw native result fields; it hashes the adjacent DAT file only
to bind the audit to its execution record. The current a12-rear frozen input is pinned
to the case manifest and corner owner contract. No audited response is
available for it, so [preflight.json](preflight.json) is intentionally blocked
and contains no force rows.

From the repository root, run the input-only preflight:

```sh
python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-corner-native-demand-export-attempt01/produce.py
```

After a response auditor output passes every pinned gate, pass that exact model
and response pair:

```sh
python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-corner-native-demand-export-attempt01/produce.py \
  --model PATH/TO/FROZEN/CASE/model.json \
  --response PATH/TO/PASSING/RESPONSE-AUDIT.json \
  --output PATH/TO/CASE-CORNER-DEMAND.json
```

The exporter verifies the response schema and status, case identity, exact
model-file and canonical model-record hashes, deck/data hashes, six response
audit root gates, all corresponding increment gates, per-increment global
balance, five-corner-body balance, source owner points/bases, and independent
five-member force/moment closure with the response force-rounding intervals.
It also binds the response deck and DAT hashes to the adjacent `model.inp` and
`model.dat`, checks both against `execution.json` and `freeze.json`, requires a
terminal zero-return native execution and matching parent authorization, and
requires the last accepted increment to reach load factor 1.0. If an adjacent
parent terminal assessment explicitly rejects usable demands, the exporter
blocks as well.
If any gate or inventory match is absent, it writes only the blocker names and
source hashes; it does not copy any response force values into a blocked
report.

A passing report keeps each source interface action on both members at its
source points and translates moments to the source descriptor midpoints for
the five-body equilibrium table. New bolt-axis actions are shown per physical
bolt and per lateral plane. BG003 remains two separate continuous
three-member bolts; its two plane actions and one tie for each bolt are
retained individually. Bolt/group wrenches are demand resultants at source
shaft-center datums, and are not capacity sums.

The report also retains all contact cells and their modeled average pressure,
all incoming and onward routes, all four corner post/floor normal and paired
no-slip tangent ownership rows, the six washer-seat actions, and the geometry
only splitting/net-section inputs. Existing resistance packets and helper
hashes are carried as conditional references. No adjusted resistance,
interaction, DCR, seat pressure distribution, splitting capacity, or complete
joint acceptance is calculated. The 12 original LEG/FLOOR-RUNNER arrangements
stay separate and their unchanged resistance checks are not reopened.

The first available input is a12-rear, one of six authenticated cases. Its
report cannot establish the remaining cases or the required stiffness,
engagement, material, accessory, and floor sensitivities. Even a passing
numerical demand report is only an input to pending conditional joint checks;
it does not qualify the design, floor support, hardware, fabrication, or
climbing use.
