# Ordinary-joint N+ actuation/map-binding decision draft — attempt01

Date: 2026-09-28  
Candidate revision: `led-clearance-2x6-runner-seated-blocks-v1`  
Status: **NOT_FREEZE_READY**

This append-only packet binds a possible bottom-center-right N+ diagnostic to
the exact current A00–A03 nut-fit maps. It is a decision draft, not a native
input freeze. `native_execution=false`, `mechanical_acceptance=false`,
`new_load_case_selected=false`, and `geometry_changed=false`. No solver was run
to prepare it. The source pins and structured binding are in
[`source-pins.json`](source-pins.json) and [`decision-draft.json`](decision-draft.json).
Run `sha256sum -c SHA256SUMS` from this directory and
`sha256sum -c docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/ordinary-joint-actuation-map-binding-attempt01-2026-09-28/SOURCE-SHA256SUMS`
from the repository root to verify packet bytes and source pins.

## Supported diagnostic shape

The candidate shape is the source-bound `n_plus` external-port characterization
in `ordinary-port-motion-attempt09-common-map/port_motion_n_plus.inp`
(SHA-256 `e94220362d6a4925dc71089b855f84daa540eb477103628291b319b4a9728def`).
It applies a relative joint coordinate `[0, 0, +N, 0, 0, 0]` through the two
full-cap, force-dual port projections: rail and principal each receive a
symmetric half-motion at the common datum, with rigid-offset translation
included. The reviewed port audit reports 12 equations/controls, zero
independent projection and motion-map errors, `3.3644e-12` maximum serialized
elimination error, `3.8675e-16` maximum random virtual-work relative error,
486 contact-surface equation references, no contact or nut dependent-DOF
collision, and no cleat restraint or port rigidization.

That file is an `NLGEOM *STATIC` linear ramp to 1.0 mm over one second. It is
not the proposed transient history. It failed before accepting the first
increment: contact-spring counts changed during 33 iterations and the pinned
CalculiX 2.21 process reached its 900-second timeout. No displacement, wrench,
contact, or accepted response state was produced. Do not rerun that static
deck, shrink increments by trial, or treat its prior static closure/work gates
as gates for a successor.

The follow-on shape supported by the post-run note is a new physical-mass
transient driven smoothly through the same two external-port coordinates. Keep
the cleat free and the reviewed mesh, source bodies, material/contact inputs,
all port projections, and all four nut equations unchanged. Stop at observed
resolved bore/face bearing and collect a short accepted post-onset sequence.
The roughly 1.3 mm relative-N value in the source note is a nominal geometry
target only; it is not service demand, a physical clearance measurement, a
required endpoint, or a conservative bound. No new physical history or load
case is selected here.

## Exact maps bound by this draft

The proposed N+ deck includes `nut-coupling.inp` and `rigid-carriers.inp`; all
four maps below are therefore instantiated and must remain in the preflight
map set. Whether every map carries measurable response in the future run is an
output question and cannot justify pruning one in advance.

| Map | Axis | Shaft / nut carrier | Shaft nodes | Terms per row | Direction, head to nut (global) |
| --- | --- | --- | ---: | ---: | --- |
| A00 | rail 1 | `M00_A00_BOLT_HEAD_PLUS_SHAFT_UNION` / `M03_A00_NUT` | 251 | 754 | `(0, -0.6427876097, -0.7660444431)` |
| A01 | rail 2 | `M04_A01_BOLT_HEAD_PLUS_SHAFT_UNION` / `M07_A01_NUT` | 258 | 775 | `(0, -0.6427876097, -0.7660444431)` |
| A02 | principal 1 | `M08_A02_BOLT_HEAD_PLUS_SHAFT_UNION` / `M11_A02_NUT` | 254 | 763 | `(-1, 0, 0)` |
| A03 | principal 2 | `M12_A03_BOLT_HEAD_PLUS_SHAFT_UNION` / `M15_A03_NUT` | 259 | 778 | `(-1, 0, 0)` |

The exact pivots, reference/rotation controls, and six dependent node:DOF rows
are carried in `decision-draft.json` from the source-bound map inventory. Each
map independently has rank six and near-machine-precision rigid-field
reproduction. Their support populations, pivots, dependent rows, and equation
coefficients differ; the source review does **not** establish exact
cross-axis transformed coefficient equivalence. Similar hardware, common rank,
or rigid-mode reproduction does not establish equivalence. The A00 native
known-answer fixture qualifies only A00/M03 under its small global-Y dynamic
body-force history; it does not qualify A01–A03 or this port-motion history.

Before a joint run, the coordinator must either:

1. independently show exact transformed equation/coefficient and carrier
   equivalence for each active map to a previously qualified map, including
   support membership, controls, pivots, dependent rows, RHS, and work-dual
   behavior; or
2. qualify each distinct active map with matched direct, map-only, and
   map-plus-carrier cases under a predeclared applicable method/history,
   checking full U/V, six controls, equation residuals, carrier kinematics,
   mass/energy, and response parity.

For the four-map N+ deck, absent a successful equivalence proof, this means
the three not-yet-qualified maps A01–A03 remain separate work. The current
map-scope decision estimates nine serialized comparisons if all three need
qualification; that estimate is not a measured runtime/output result. Do not
turn this into a blanket four-map prerequisite for a different, source-bound
case that demonstrably activates fewer maps.

## Still unresolved before any freeze

The source records do not select the following. They must be explicitly
resolved and source-bound in a successor freeze; this packet does not infer or
choose values:

- transient ramp shape, duration, endpoint/event cap, initial/minimum/maximum
  timestep, and any rate-comparison history;
- numerical force/moment balance, work/energy, kinetic-energy, momentum, and
  rate/timestep acceptance limits for the transient;
- signed and near-zero thresholds for bore pairs `WJCP_020`–`WJCP_027`, and
  the operational definition of first *resolved* bearing;
- exact-equivalence proof versus separate qualification of each distinct
  active A01–A03 map;
- whether the run is component characterization or a physical transient.
  No source-bound simultaneous six-component physical port history or time
  basis is present. A displacement-controlled diagnostic cannot be called a
  service-demand result;
- resource/timeout limits for the new transient and the applicable pinned
  solver build. The failed static run used CalculiX 2.21; T02 capture attempt09
  targets pinned CalculiX 2.23. Do not assume those builds are mechanically
  interchangeable.

The observable set should include the full-cap port motion and both signed
`SOF` port wrenches at the common joint datum; all cleat pose/displacement and
velocity outputs; all 35 contact-pair gaps, states, and actions; specific
signed bore-pair observations for WJCP_020–WJCP_027; accepted/rejected
increments; bolt/interface actions; member equilibrium; opening, slip, and
rotation; elastic, contact, and kinetic energy; external work; and momentum
terms. Use the maintained patch-wrench/equilibrium accounting within its
declared scope. Require at least two accepted states after first resolved
bearing, but do not require all eight bore pairs to bear simultaneously.

The T02 capture sidecar is bounded instrumentation, not a joint acceptance
oracle. It cannot prove geometric search completeness, first local contact,
unmapped-point force/work, or whole-model energy balance; missing observations
remain unavailable, not zero. Any stop for source/output defect, invalid
capture, solver termination, minimum-step failure, or frozen resource/time
limit leaves the diagnostic unresolved. Do not add cleat restraint, artificial
stabilization, preload, friction, gap changes, or physical tuning to continue.

## Execution gates

T02 contact-capture attempt09 is frozen and passes its offline tests, exact
source replay, three independent reviews, and parent audit; it has not had a
production build or native coupon run. Its next gate is pinned Docker runtime
access, fresh parent readiness, the required external/native authorization,
and a durable parent-owned run-once ledger. Then build the reviewed attempt09
patch in its pinned CalculiX 2.23 image and run its single bounded method
coupon. Require the preregistered accepted-time/generation/face/state joins,
force/work known-answer checks, resource/stop limits, and byte-identical
standard solver outputs. A pass qualifies capture method only.

T03's separate frozen `shared_slave_penalty` attempt07 coupon also remains
unrun. It requires pinned runtime, fresh parent readiness/authorization, and
durable run-once tracking; its pass would qualify only its small static
topology. It does not accept the full dynamic joint. The current live queue
and status say Docker socket access is denied in this environment, no local
CalculiX or alternate runtime is available, and readiness/authorization remain
false. Do not run until those gates are freshly satisfied. T03 ordinary-joint
execution additionally needs its own immutable input/history freeze and run-once
record after the unresolved decisions above are settled.

All four map bindings and the current T02/T03 state are recorded in
`decision-draft.json`; `source-pins.json` identifies the bound files and
`SOURCE-SHA256SUMS` provides a reproducible source-byte check. A source pin
mismatch means this draft must be reviewed again; it never authorizes editing
the source or silently refreshing a hash.
