# Remaining 54 candidate bolts: finished-solid washer-seat screen

October 1, 2026 UTC. This primary-authored packet covers **54 bolts and 108
outer seats** on the reviewed `led-clearance-2x6-runner-seated-blocks-v1`
revision of `compact-floor-flush-wood-joints-development`. It changes no model,
hardware, load or native result. The full run returns `GEOMETRY_EXCEPTIONS`
and exit 1: **107 seats pass the declared geometry screen; one does not**.
That is a geometry exception, not an adopted strength failure or joint pass.

## Coverage and method

The source-pinned partition excludes the six primary-corner bolts already
covered by the [nominal](../corner-washer-support-2026-10-01/README.md) and
[eccentric](../corner-washer-eccentric-support-2026-10-01/README.md) packets,
and the two disjoint sixteen-axis upper cohorts owned by the parallel
upper-block study. Six plus 32 plus 54 equals all 92 candidate axes. The
twelve retained frame arrangements remain separate. This packet neither
claims completion of the upper owner's 64-seat study nor inherits its results.

The checker derives the head and nut seats from the authenticated source
underhead datum and receiver intervals, then imports their **26 actual
finished member STEP solids**. It checks each model/manifest/STEP binding,
solid validity, face count and round-trip volume. The report records every
imported STEP hash. Source ambiguity stops execution. There are 52
two-receiver bolts and two three-receiver bolts; the latter have only outer
washers. The actual outer-seat bores are 7.5 mm diameter at 76 seats and
7.3 mm at 32 seats. They are distinct from the conditional 6.35 mm smooth
bolt-body scenario.

Each seat must have a matching exterior plane and coaxial cylindrical bore in
the finished solid. Three centered annuli are checked at inward and outward
depths 0.01, 0.05 and 0.1 mm: the CAD washer (18.6436 mm OD, 8 mm ID), the
plain catalog minimum-area corner, and the plain catalog outer-envelope
corner. The catalog bounds are 0.727–0.749 in OD and 0.307–0.327 in ID.
The fraction tolerance is `1e-7`.

For eccentric coverage, a continuous swept annulus must be contained in timber
inward and clear outward at all three depths. Its inner radius is the actual
bore radius; its outer radius is the maximum washer radius plus both nominal
bolt/bore and washer/body radial plays. The two outer radii are 10.9652 and
11.0652 mm. This extends the pinned geometric method; it does not treat
discrete offset samples as a directional bound. Circle-intersection
hole-only areas are explicitly marked inapplicable wherever the swept region
is not contained. The boolean check remains failed at such a seat.

## One unsupported seat

| Item | Observed modeled result |
| --- | --- |
| Axis and seat | `center_principal_right_2`, nut side |
| Finished receiver | `base_principal_center_right` |
| Seat point, mm | `(50.95, -90.30983137880766, 367.0102220661388)` |
| Own bore | 7.3 mm diameter |
| Centered CAD annulus supported | 90.5046351763% |
| Plain minimum-area annulus supported | 90.6001120577% |
| Plain outer-envelope annulus supported | 90.0597697729% |
| Eccentric swept-annulus containment | 86.7210768952%; full containment fails |
| Outward overlap | Zero at the declared probe depths |

The nearby finished-solid cylinder has radius 19.05 mm and an X-directed
axis through `(49.95, -72.95548222202, 348.17694481884)` mm. Direct source
inspection identifies the same coordinates, direction and diameter as
`bore_base_principal_center_right_072`, the retained **F1–G1 service passage**.
This member is not in the kerf-right translation set. The original passage
is 38.1 mm diameter; a historical barrel-candidate 25.4 mm alternative is
not the current wood-joint geometry and is not adopted here.

The axis separation is 25.6098763474 mm. The passage edge is consequently
6.5598763474 mm from the bolt center, inside the CAD washer's 9.3218 mm
outer radius. The centered annulus loses about **21.1486664 mm²** of its
222.7262122 mm² projected area. An independent circle oracle can compute
this as `I(19.05, 9.3218, d) - I(19.05, 4, d)`, where `I` is the area shared
by two disks and `d` is the axis separation. The inner disk does not overlap
the passage. The missing BREP volume at 0.1 mm depth is approximately
2.11486664 mm³, consistent with that footprint.

The affected finished STEP SHA-256 is
`9053a7210a781e919038a4a823f867325dd5c78907bd028d8b9e76dc0b46df58`.
The other 107 seats meet the declared centered and swept geometry gates.
Their result remains conditional on the stated nominal body and catalog
envelopes.

The full-annulus and hole-only pressure assumptions cannot be transferred to
the affected seat. Completion requires an applicable partial-support
contact/washer-metal/wood resistance treatment with authenticated demands,
or a reported and separately reviewed geometry/hardware option before any
model change. This screen supplies neither treatment. It does not waive the
exception or direct a cut, axis move or washer substitution.

## Reproduction and limits

The checker SHA-256 is
`a3cedb8e6fddf9d4080afd82cf12cf3e5a39658868baa478ad1f14eee7d07967`.
It imports the exact pinned base and eccentric production methods and checks
their hashes, existing input pins, both upper exclusion hashes and all STEP
bindings. These local authenticated evidence artifacts are required to
replay; they are not newly committed result data.

From the repository root:

```sh
.venv/bin/python docs/wood-joints-mvp/hypotheses/remaining-candidate-washer-seats-2026-10-01/check_support.py --self-test
.venv/bin/python docs/wood-joints-mvp/hypotheses/remaining-candidate-washer-seats-2026-10-01/check_support.py --check > /tmp/remaining-washer-seats.json
```

The self-test must succeed. The current full check must exit **1**, with the
single named exception and all 108 seats covered. Raw JSON stays local.
Self-tests exercise the pinned full-support, edge, neighboring-bore,
embedded/reversed seat and outward-obstruction fixtures and reject ambiguous
source intervals. Independent review is recorded separately.

There is no delivered-shank minimum, tilted-bolt or real-seat tolerance
bound, physical inspection, pressure distribution, washer bending capacity,
wood resistance, thread engagement, adopted criterion pass, native response,
six-case completion or complete joint acceptance in this packet. Its swept
enclosure is geometric and intentionally conservative. Actual/Disposition
shop cells remain blank. The conditional MVP-E goal remains active.
