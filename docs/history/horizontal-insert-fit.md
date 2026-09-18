# Prospective inserts in horizontal service framing

The existing [insert reference](panel-insert-reference.json) provides a development
pair: E-Z LOK 801420-13 and Dottie FMDD14114. This diagnostic reuses that recorded
geometry; it does not select an installation or replace the current wood screws.
Commercial SDS bracket screws and structural through-bolts remain unchanged.

Every current panel/kicker screw receives a full solid 12.1412 mm diameter by
17 mm deep prospective receiver reservation. Actual modeled service cuts and
grooves participate in the test. A groove crossing this volume fails even when
an insert-shaped annulus would fit. No pilot or insert hole is cut by this tool.
The prospective machine-screw head is also checked against neighboring wood
and existing fastener envelopes, excluding its own panel and receiver.

The final [v2 report](../fea/results/horizontal-insert-fit-v2/report.json) and
[87-location schedule](../fea/results/horizontal-insert-fit-v2/schedule.csv)
record **87 passing prospective fits, zero failures and zero installed inserts**
for `horizontal-service-development`. All full solid reservations and tested
neighboring head clearances passed with the modeled service grooves present.
The report binds this result to source hashes, including the LED wiring,
ML23Z, ML24Z and insert references. A geometry or reference change requires
another assessment; this result does not transfer automatically to a revision.

```sh
uv run python -m fea.horizontal_insert_fit \
  --model mini_moonboard.horizontal_service_frame \
  --output fea/generated/horizontal-insert-fit-next
```

Use the actual revised module with `--model` when grooves or base geometry change.
The exclusive output directory contains a source-bound JSON report and CSV with
every screw identity, receiver, reserve and failure. These are prospective fit records,
not installed hardware or production drilling schedules.

At the recorded panel thickness, gross receiver reach is 13.49375 mm nominal
and 11.96975 mm at minimum screw length, before any insert recess. Effective
thread engagement remains unknown. Insert recess, countersink seating within
the plywood, actual driver approach and connection resistance require closure;
see [the earlier selection limits](panel-insert-selection.md). Neither this fit
nor reserved material establishes withdrawal, lateral, cyclic or repair capacity.
