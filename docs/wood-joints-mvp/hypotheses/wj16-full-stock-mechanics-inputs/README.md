# Full-stock ordinary-joint mechanics inputs

Status: bounded input report, 2026-09-24. Parent ran the
[producer snapshot](producer.py.snapshot) against the retained
[WJ16 composition](../wj16-integrated-static/README.md) in 0.04 seconds.
The [report](mechanics-inputs.json) covers the lower and upper right inner
G7 joints: eight physical bolts, forty modeled hardware components, and four
wood interfaces. It does not cover the whole frame or run a native solve.

All eight bore axes reconcile with the pinned producer's location, direction,
127 mm wood grip, and ordered receivers. The report distinguishes the wood
head-seat plane from the bolt under-head plane and the occupancy-bore start.
Each member has an explicit source or producer grain direction; reported end
and edge distances are projected finished-solid bounds, not signed loaded-edge
checks.

The source contact planes agree with the interface datums within 0.00000023 mm,
with opposing outward normals. Measured finished cleat face areas are
10,552.972707 mm² at each lower interface and 7,637.052707 mm² at each upper
interface. These are coplanar cleat areas after represented cuts. Actual
two-member overlap, pressure distribution, opening, tolerances, and contact
stiffness remain unresolved.

The provisional six-inch bolt's 127 mm minimum smooth body is measured from
under the head. The far wood face is 128.2954–129.032 mm from that datum at
the nominal wood grip and catalog washer-thickness bounds. Thus equality of
smooth-body length and wood grip does not establish full smooth-shank coverage
of the far wood layer. Shear-plane section, thread transition, and nut
engagement require distinct checks; the grip-gaging bound is not a published
first full-form thread location.

Actual six-case demands, material and hardware resistance, contact and bolt
stiffness, group action, and complete-joint behavior remain open. Every release
and native-readiness flag is false. Five focused regression tests passed,
including wrong-axis, receiver/station, and translated-contact-plane rejection.

[Execution bindings](execution.json) link this report to the archived WJ16
composition and static diagnostic. [SHA-256 values](sha256.json) preserve the
report, execution record, producer, and tests. The live entry point is
`scripts.wood_joint_wj04_full_stock_mechanics_contract.build_mechanics_contract(g16)`.
