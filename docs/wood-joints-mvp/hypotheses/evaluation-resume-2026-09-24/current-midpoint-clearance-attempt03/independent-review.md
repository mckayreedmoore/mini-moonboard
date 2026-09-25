# Independent review

The attempt03 midpoint report and README agree with the frozen execution and
current geometry inputs. I reviewed the generated records and source hashes
read-only; I did not run CAD or native mechanics.

## Provenance

The report SHA-256 is
`a7f7b15200421ad2f6527cf2248f70e7f424164a357a2e69afdf48ad538582e4`,
the producer SHA-256 is
`6915e1213cf425b1f459594c55c403679f3fab18915cb6d976aa2cae0adae806`,
and the README SHA-256 is
`4555b46984dd81fd392df784b16fbf3d9dddc097409e16b6e9ae211d8edda94f`.
The completed execution record binds the report, producer, and raw
`geometry-snapshot.json` SHA-256
`0b92357af648604ee8ce42d2f8906e0a4e5498e9e4b835a07938b81dc151d187`.
The snapshot's canonical JSON digest also matches the report's
`50d3d65c6f5eeddbd8df8bf068c7f338754c831c7cc49b25ccc4f4a878902a7a`.

The current revision report and verification hashes match the report:
`148f97623573558cd6a6c53f8a5399f2b30549d6aa1ed13c326dfe1bc3e9d695` and
`73c47a32d02480b61e95ef8f5f5854f7d38c5430137eb7b0183012ae9995751c`.
The source inventory file matches `07af4c3eb642cf3887595fe4415eb65404cdcf74d66c5c7bb182847ef21c2d78`,
and all nine source-code hashes listed in `report.json` match their files.
The stored wrapper SHA-256 is
`9aecf5fa0007a630cd298d1f4c87f103a6557b92dd82eac2f87886f146d7c2b9`;
it checks the producer and snapshot hashes, uses the supplied live
`g24_outer_2x6`, and calls the screen without rebuilding geometry. Its
execution record reports completion in 7.27 seconds and the correct
attempt03 output path.

## Results and scope

The 491 site IDs are unique and their counts recompute to 120 horizontal and
121 vertical LED midpoints, 120 horizontal and 121 vertical T-nut midpoints,
and 9 horizontal kicker T-nut midpoints. Recomputing the summaries from the
site-level hit rows matches every reported group:

| Group | Timber sites | Flange sites | Structural hardware sites | Existing T-nut/LED overlaps |
| --- | ---: | ---: | ---: | ---: |
| LED / horizontal | 14 | 12 | 0 | 0 |
| LED / vertical | 21 | 20 | 0 | 121 T-nuts |
| T-nut / horizontal | 15 | 12 | 0 | 0 |
| T-nut / vertical | 1 | 0 | 0 | 121 LEDs |
| Kicker T-nut / horizontal | 0 | 0 | 0 | 0 |

Each of the four LED midpoint sites adjacent to G2 reflects the recorded
`(1405.0, 199.2) mm` datum, a +5 mm X change from the baseline. The probe
dimensions match the pinned historical screen: a provisional full-disk flange
of 25.4 mm diameter and 1.86 mm rear thickness, plus an 11.1125 mm diameter,
50.8 mm long rear projection. Reported first timber-intersection depths from
the projection start plane are 0, 10, 16.9458, and 20 mm at the named sites in
the README; I found no discrepancy in those row-level records.

This is a historical nearest-neighbor hypothetical grid, with no diagonal or
extrapolated edge sites. The tested 904 obstacle shapes are 44 timber solids,
460 candidate-stack components, 60 retained frame-bolt components, 66 panel
screw-axis solids, 142 existing T-nuts, and 132 existing LED bodies. The
report records 12 display-only source-axis proxies, 36 retained-bolt
tool/withdrawal envelopes, and 142 hold-hole/rear-projection envelopes as
excluded. It also excludes 131 modeled wire spans and plywood from the
midpoint obstacle scope; the source inventory has six plywood panels and the
current geometry has five panel-replacement bodies.

The results are geometric envelope intersections, not physical blockage,
future-product compatibility, an accepted hold layout, or joint evaluation.
The flange/projection dimensions are provisional and omit flange holes and
supports. The screen does not cover panel fit, wiring, service access, future
hold bodies, retainers, tools, or installation method. `joint_evaluations_run`
and `candidate_accepted` remain false.
