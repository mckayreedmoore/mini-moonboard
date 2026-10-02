# Retained washer support on saved receiver solids

## Result status

The parent completed **24 nominal concentric head/nut seats**, **72 inward
annulus probes** and **144 saved seat-force states** on eight current receiver
STEP solids. All nominal annuli are fully supported to the calculation
tolerance: supported fractions range from **0.9999999999996958** to
**0.9999999999996971**. Four upper-leg head seats use the current corrected
side-member solids. The nominal concentric seat-support gap is addressed.

| Conditional washer family | Seats | Supported nominal annulus area | Peak uniform-pressure scenario | Pressure / conditional Fc-perp |
| --- | ---: | ---: | ---: | ---: |
| 3/8-inch, Bolt Depot 15023 | 16 | 395.657468 mm² | 0.897572 MPa | 0.208291 |
| 1/2-inch, Bolt Depot 15025 | 8 | 779.566923 mm² | 1.240219 MPa | 0.287806 |

The governing ties remain K12-right, front-right bolt 2 at 355.131153 N and
upper-leg-right bolt 2 at 966.833771 N, respectively. Pressure assumes
concentric uniform compression without preload. The existing dimensional
report's null actual-pressure and acceptance fields remain frozen. Loaded
displacement/tilt, actual hardware geometry, washer metal transfer and joint
acceptance remain unresolved; no delivered observation is claimed.

## Method and sources

[retained_washer_support.py](retained_washer_support.py) reads the frozen
[dimensional report](retained-washer-attempt01/checks.json), the current
retained-bolt register at `/tmp/mini-moonboard-retained-frame-bolt-current-resistance-basis-2026-10-01.json`,
and [axis-features.json](../current-finished-feature-register-2026-10-01/axis-features.json).
For `base_side_left` and `base_side_right`, support geometry comes from the
current [top-corner proposal](top-corner-correction/proposal.json), SHA-256
`5932768c7a7d91535f69a90787b32222eb4d165ac6353d3e2ed4daf9e248e2b2`, using
its exact `proposal_step_sha256` overrides. The other six receiver solids use
the dimensional report's saved STEP files. The original side STEP bindings
remain datum and interval references; corrected side solids are validated as
single valid solids without requiring preserved face counts.
The producer pins the report SHA-256 as
`55ad4689489bc965cde1d182a68c5171723a835180966f2b0e9fed2229faa2e1`, register
SHA-256 as `c3250f067c4590ee43f7ec7a5765d056d87e6ff5adb42837ed27710d9b4d4eb1`,
and feature register SHA-256 as
`bebb4274cdecfb6ad0b0f26850d85a16570c245ea9f7d478c0b05c12b4513e19`. It
rechecks every source hash carried by the dimensional report, pins the proposal
and its two side overrides, and records an exact snapshot of its own producer.

For each axis, the source datum and direction come from the feature register;
the receiver intervals and seat-to-member assignment come from the dimensional
report's retained register. Head center is `datum + direction * minimum
interval`, with inward direction along the axis. Nut center is `datum +
direction * maximum interval`, with inward direction opposite the axis. Before
intersection, the local bore interval must lie inside the signed STEP vertex
bounds. Its selected exterior endpoint must equal the corresponding global
bound, and an outward planar face must match that station and inward
direction. The opposite endpoint need not equal the whole-member bound where
a recess removes wood along the bore. Any source conflict or incorrect
exterior face binding stops the run.

The report-bound minimum washer OD and maximum washer ID define each nominal
annulus. The producer constructs inward annular probes at 0.01, 0.05, and
0.1 mm and intersects each probe with its unchanged assigned STEP solid. It
reports intersection volume divided by probe depth as depth-averaged supported
area, plus the fraction of nominal annulus area. The result covers nominal
concentric CAD placement; it does not cover displacement or tilt.

For each saved force state, tie divided by supported area is reported only as a
uniform-pressure scenario. Zero supported area leaves that pressure undefined.
No metal transfer or washer resistance is assigned. Saved CAD support is not
a delivered observation, actual inspection, wood-bearing acceptance, complete
joint acceptance, or physical release. No geometry is changed. All 47 criteria
remain pending, all eight release flags remain false and Actual/Disposition
cells stay blank.

## Execution evidence

Completed local output is `retained-washer-support-attempt02/support.json`,
SHA-256 `72ecad11051f7a72695f83561bb12503bfd79a44d3c3f6eeac2de476e3bc3448`.
All **19 source bindings** match. The exact executed producer and snapshot
SHA-256 is `82be4183871273ca74f5de490652a7f3f43729b65830894d9d55dd66805f8a5f`.
Raw geometry results and snapshots are local ignored evidence.

Attempt01 stopped at `rail_rear_bolt_left_1/nut` because the initial code
incorrectly required both local bore endpoints to equal whole-member bounds.
The local leg interval is `[40.132, 90.932] mm`; whole-member projections are
`[2.032, 90.932] mm`. Its nut exterior station agrees, while the opposite
bound includes stock beyond the rear recess. The corrected gate checks
interval containment and only the selected exterior bound. The stopped
producer and `retained-washer-support-attempt01/stop.json`, SHA-256
`30fe2da5815ea7135591eea0d288c8caaf21bdfbbfbc9c4379460aaab32c21b3`,
remain preserved. This was an implementation gate error, not a geometry or
physical failure.

The parent serialized saved-STEP execution through the idle native-slot
lock. No scene regeneration, native/frame solve, software tests or review
agent was used. Ruff passes.

## Parent execution

Run once in a fresh output directory:

```sh
.venv/bin/python docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/retained_washer_support.py --output docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/retained-washer-support-attempt03
```

The ignored output contains `support.json` and the producer snapshot. Parent
owns CAD execution and result integration.
