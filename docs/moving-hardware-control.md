# Free bolt/washer contact control

The centred and separated-pose catalog-clearance fixed-step controls pass their
complete quiet output gates. Moving-contact behavior remains unqualified. The
earlier rejected attempts below are preserved evidence, not the current
stationary status. These tests do not establish bolt-product suitability,
plywood joint capacity or permission to build/climb.

The first quiescent attempt, `quiescent-an9hdwot`, stopped during input parsing
with native exit 201, before any accepted state or contact response. Its frozen
deck, source, log and failed terminal record are preserved. The owned container
was removed successfully. Source `nodes.f:140,150,160` reads only the first
20 characters of each coordinate; the emitted 22-character value
`-3.751665644813329E-12` was truncated to an incomplete exponent. This is an
export-format failure, not a structural or contact result. The corrected export
must bound coordinate field widths and bind subsequent mass/output analysis
to the actual serialized coordinates, recording its small rounding error.

The corrected attempt `quiescent-mgxeu8y1` reached one accepted state at
1e−8 seconds, then repeatedly cut back increment 2 to the 1e−11-second minimum.
The original 120-second cap stopped it with exit 124; captured terminal state
was stopped, not OOM-killed, and owned-container cleanup succeeded. No moving
case was launched. At the accepted state, washer speed reaches 9.3677 mm/s
and core speed 6.3820 mm/s, both exceeding the 0.01 mm/s quiet limit.
Displacements remain below 1e−6 mm. Bore penetration reaches 1.76855e−5 mm,
above its 1e−6 mm limit; summed bore-contact energy alone is 1.65350e−5 N·mm,
above the 6.83659e−6 N·mm quiet energy limit. Head-contact energy is about
1e−13 N·mm. The partial DAT lacks the final total-contact-energy scalar and
pair CF blocks, so impulse qualification is unavailable.

The [published evidence and portable diagnostic](../fea/results/moving_hardware_control/README.md)
retain both attempts and reproduce the four first-state gate failures from
the original output, with thresholds bound to the frozen launch inputs.

This localizes the principal observed artificial response to the nominally
zero-clearance curved bore. The maximum coordinate-rounding change is only
5.00009e−11 mm; it is not a plausible explanation for the much larger reported
penetration. These are rejected numerical diagnostics, not physical hardware
or board-strength failures. A [catalog-backed washer-bore correction](candidate-hardware-audit.md#washer-bore-model-correction-identified-by-the-quiet-control)
is the next geometry step. Preserve the failed trial and requalify the quiet
case before moving contact; do not relax its gates to obtain a pass.

The selected station-1 hardware comes from the actual locked-thread stitch
variant: one fused bolt/head/nut solid and one separate inner annular washer.
The eleven-body mesh completed in 7.05 seconds, with 131,695 nodes and 62,987
C3D10 elements. The two control bodies contain 19,769 nodes and 10,218 elements.
The original fourteen-body evidence remains unchanged. No mesh nodes are
merged across independent bodies. Local coordinates subtract the stitch's
global starting point; this does not move one body relative to the other.

The washer is the slave in both ordinary surface-to-surface penalty pairs:
its cylindrical bore against the exposed shank, and its head-facing annulus
against the head underside. Their nominal radial and axial clearances are zero.
There are no restraints, ties, mortar, gravity, preload, friction or applied
forces. In particular, no artificial pinning is used to suppress free-body
motion. Perfectly fused nut/core retention is a numerical idealization, not a
model of real threads or tightening.

## Requested numerical settings

| Setting | Value |
| --- | --- |
| Generic elastic steel E / Poisson ratio | 210,000 N/mm² / 0.3 |
| Assumed density | 7.85e−9 tonne/mm³ |
| Linear contact penalty | 100,000 N/mm³ |
| Quiescent initial velocities | Zero for both bodies |
| Moving washer velocity; core velocity | (−100, 100, 0) mm/s; zero |
| Procedure | NLGEOM, implicit DYNAMIC, ALPHA=0; omit EXPLICIT |
| Initial / maximum / minimum increment | 1e−8 / 1e−7 / 1e−11 seconds |
| Initial diagnostic duration | 2e−6 seconds |

These are diagnostic assumptions, not measured material properties. The washer
mass and 183.2133 mm² head bearing area imply an approximate penalty-contact
timescale of 6e−7 seconds; even the selected maximum increment requires a later
refinement check. Initial velocity supplies the moving case's kinetic energy;
there is no load amplitude and no subsequent external work.
Actual accepted increments come from the retained STA, not from assuming that
the solver uses each requested increment unchanged. Its impact logic reduced
the second increment repeatedly in this trial.

## Predeclared interpretation gates

Let `m` be the source-reconstructed native four-point washer mass, with
`P* = m sqrt(100² + 100²)`, `E* = m (100² + 100²)/2`, and `H* = 57.15 P*`.
Record this reference mass and its provenance; do not substitute a fitted scale
after seeing the response. Moments are compared about the fixed initial washer
centre, local (1, 0, 0) mm.

- Quiescent: maximum nodal displacement ≤1e−6 mm; speed ≤0.01 mm/s;
  kinetic/strain/contact energy magnitude sum ≤1e−4 E*; each pair's cumulative
  impulse magnitude ≤1e−4 P*; maximum penetration ≤1e−6 mm.
- Moving: each body's contact-impulse residual ≤1e−3 P* and angular-impulse
  residual ≤1e−3 H*; assembly momentum drift ≤1e−4 of the respective scale;
  total energy drift ≤1% E*. Native mass/kinetic-energy reconstruction retains
  the established 5e−6 comparison limit, with zero-energy comparisons requiring
  an explicitly stated absolute normalization.
- Require each pair's impulse ≥1e−3 P* and core kinetic energy ≥1e−4 E*;
  otherwise the short event is inconclusive, not a successful transfer test.
- Only after the first moving case qualifies, halve its maximum increment;
  endpoint momentum and pair impulse changes must be ≤1% P*.

Every accepted state must have complete nodal and requested contact output.
Trapezoidal impulse integration and its timestep sensitivity must be explicit;
endpoint force times elapsed duration is not an impulse audit. The native pair
`CF` resultants cover washer force and moment because the washer is slave in
both pairs. Do not substitute reported static `RF` for dynamic body balance.
Opposite core force and assembly angular-momentum checks must be verified, not
inferred as proof merely from equal-and-opposite resultants.

`printoutcontact.f` in the retained upstream 2.21 source constructs pair force
and moment about the origin from current slave integration-point positions.
Its empty-contact statistics divide by zero area: primary force/moment may be
zero while ancillary centroid statistics are nonfinite. Any parser exception
for that case must require verified zero area and zero primary resultants;
nonfinite primary forces are never accepted. Contact pressure/sign conventions
must be checked against the actual emitted fields.

The quiescent case must qualify before the moving case is launched. Independently
meshed nominally zero-clearance cylinders can create apparent penetration and
artificial energy. A failed gate stops escalation and remains archived. Solver
completion by itself is not output qualification; none of these controls
releases the complete eleven-body stitch experiment or validates the board.

## Catalog-clearance quiescent control

The catalog-consistent correction is a **quiet-only preparation**: keep both
bodies centred and give both zero initial velocity. Its first bounded solve
timed out; no contact response is qualified. The provisional washer
bore is 10.9982 mm, the lower published FW38 bound; 25.4 mm OD and 2 mm thickness
remain declared dimensions within its published ranges, not measurements of a
purchased washer.

The washer bore radius is now 5.4991 mm, while the shank remains 4.7625 mm.
Surface selection must use those different radii: the washer bore and its
head-facing annulus change; the core shank and head-underside annulus do not.
Keep complete quadratic face/node selections and independently verify their
CAD bounds and areas. The core head surface still has area 183.2133 mm², but
the centred washer/head overlap is only `π(9² − 5.4991²) = 159.4669 mm²`.
Reference washer mass and diagnostic scales must be recomputed from the new
serialized mesh before any solve.

The centred radial gap is exactly `(10.9982 − 9.525)/2 = 0.7366 mm` for these
declared dimensions. At 100 mm/s, free lateral travel in 2 μs is only
0.0002 mm; nominal gap closure would take 0.007366 s, or 7.366 ms. Consequently,
the earlier short moving case cannot exercise both interfaces with this
centred geometry. The 100 mm/s components used in `P*`, `E*` and `H*` remain
named diagnostic reference scales; they do not prescribe motion in the quiet
case or imply that a moving deck has been prepared. Any later moving fixture,
initial pose and duration require a separate explicit design decision.

Quiet qualification requires the entire requested time window, complete body
U/V at every accepted STA state, native body mass/energy totals, native total
contact energy, and complete pair CF force/moment histories. Apply the
predeclared displacement, speed, energy, penetration and cumulative-impulse
limits; a timeout, missing tail or isolated accepted state cannot qualify it.
The existing partial diagnostic can establish failures but cannot establish
this success.

A genuinely inactive bore is expected and is not a failure. Empty contact-point
tables are acceptable only when complete native counts, pair statistics and
zero resultants establish inactivity; absent or truncated blocks are not zero
contact. Preserve the existing narrow allowance for nonfinite ancillary
statistics only with verified zero contact area and finite zero primary
force/moment components. Do not require a nonzero bore impulse in this quiet
case: the two-interface transfer requirement belongs to a later moving test.

### First catalog-clearance attempt

Export `stitch-joint-geometry-df3e0965` and mesh `mesh-7amycoem` contain eleven
independent bodies, 131,443 nodes and 62,935 C3D10 elements. The selected
two-body control has 19,734 nodes and 10,215 elements. Preparation
`control-muorg377` recomputed reference washer mass as
6.463769626219888e−6 tonne from the serialized coordinates. This is a
source-derived normalization, not yet a qualified native output comparison.

Frozen solve `quiescent-ggs6anor` exited 124 at its original 120-second cap;
the captured owned container was stopped and removed successfully. Its STA
records 19 accepted increments, ending at 2.00705e−8 s, far short of the
requested 2e−6 s. The increment repeatedly halves until reaching 1e−11 s.
The solver log reports zero displacement increments and residual force in
these accepted iterations, unlike the preceding zero-clearance trial. That
observation does not establish complete-window quiet qualification. Preserve
this attempt separately; do not restart it or treat the timeout as a strength
failure.

Read-only inspection of the terminal DAT found complete body U/V tables for
all 19 accepted states, with every reported component zero. Reported body
kinetic/internal energy and total contact energy are also zero. Both pair CF
blocks are complete for the first 18 states; the last state's bore CF block
is missing at EOF. Earlier bore blocks report zero primary force/moment and
zero area, with nonfinite ancillary quantities for the inactive interface.
These observations explain why missing final output must not be silently
treated as another zero-contact state. They are not a portable full-window
qualification or a moving-contact test.

### Source-based next diagnostic: fixed increments

The retained [unmodified CalculiX 2.21 source archive](../fea/results/native_dynamic_control/control-ajgbgzoh.tar.gz)
contains `frozen/native-source/nonlingeo.c:1454`, which initializes `energyref`
from the initial energy sum. `checkimpacts.f:98–113` divides by that reference
when `emax <= 0`. For exactly zero initial and current energies, the resulting
zero-over-zero ratios can make the comparisons false and select the halving
branch at `checkimpacts.f:171–185`, including its minimum-increment clamp.
This is a source-based explanation consistent with the retained zero-output
history; the internal ratios were not instrumented.

A separately frozen, bounded stationary diagnostic using
`*DYNAMIC,DIRECT,ALPHA=0` is the next proposed route. `dynamics.f:117–119` sets
`idrct=1`; the subsequent maximum-increment clamp in
`checkconvergence.c:418–421` applies only when `idrct=0`. DIRECT still calls
`checkimpacts` through `checkconvergence.c:256–278`; it does **not** disable all
impact logic. Forced-size and divergence paths remain, and direct-increment
divergence can terminate the calculation (`checkconvergence.c:354–358,582–588`).

Choose and freeze the fixed increment and run bounds before that diagnostic.
Do not add artificial velocity or reference energy, weaken tolerances, or
restart the timed-out bundle. Actual STA increments and complete native
output must still establish the requested quiet window; this proposed route
does not qualify moving contact or imply any hardware resistance.

### Predeclared fixed-increment trial

Use a new preparation with `--direct-quiescent`: catalogue-clearance geometry
only, `*DYNAMIC,DIRECT,ALPHA=0`, fixed increment 1e−7 s and total time 2e−6 s
(20 nominal increments). Geometry, contact penalty, zero initial velocities,
reference-scale definitions and all quiet gates remain unchanged. This is
not a time-convergence demonstration; it tests whether the stationary state
can persist through the original requested window without adaptive-step collapse.

Freeze this new trial with `--solver-timeout-seconds 180` before launching.
The preceding run needed roughly 120 seconds for 19 accepted increments;
180 seconds allows bounded overhead for the planned 20-state output, with
200 seconds for the outer process observation. Memory, CPU, network isolation,
single-launch protection and owned-container cleanup are unchanged. Previous
bundles keep their original 120/140-second bounds; no in-flight extension or
automatic retry is permitted. Solver completion still requires a separate
complete-output audit and does not release a moving or full-joint analysis.

### Fixed-increment execution

Preparation `control-r3gnwd2c` and frozen solve `quiescent-ffkg77qe` completed
with native exit 0 and owned-container cleanup exit 0. The native log records
131.788192 seconds, within the predeclared 180-second cap. STA records exactly
20 accepted increments of 1e−7 s, reaching 2e−6 s; there are no rejected
attempts. Previous geometry and adaptive-run evidence are unchanged.

This establishes completion of the requested stationary time window with the
fixed-step procedure. Complete numerical output auditing is separate; no
moving-contact, thread, plywood-joint or whole-board strength conclusion
follows merely from this successful solve.

The separate [complete-output audit and retained report](../fea/results/moving_hardware_control/README.md#complete-fixed-step-quiet-output-audit)
pass the frozen quiet gates across all 20 states. Reported motion, native
energies, penetration and sampled pair-force integrals are zero. This closes
the initial stationary-output gate for this exact geometry, mesh, procedure
and window—not a general contact-law or strength validation.

Next, design and freeze a separate nonpenetrating moving fixture that actually
engages both interfaces; verify its initial pose and preserve this centred
quiet case. Moving transfer needs per-body momentum/angular-momentum and
energy balance, native mass/energy comparison, and timestep sensitivity before
the eleven-body stitch comparison can proceed. The later stitch experiment
can compare transfer between plies, but its fixed-upper-bore diagnostic fixture
cannot validate the real upper joint or imply construction readiness.

## Proposed two-interface moving fixture — not launched

Translate only the catalog washer by local `(0.001, 0.7356, 0)` mm, keeping
the bolt/nut core fixed in its original initial pose (but **not restrained**).
The ideal head gap and nearest bore gap are both 0.001 mm. At an initial
washer velocity of `(-100, 100, 0)` mm/s and zero core velocity, both would
close at 10 µs under free flight. That timing is a geometric prediction,
not a prescribed impact or proof both interfaces transfer force.

Before using this pose, verify separate CAD solids and the entire curved
quadratic mesh surfaces remain nonpenetrating after actual decimal
serialization. Corner-node distances or sampled minima alone cannot prove
that. Retain the centred control and create a separate posed quiet case;
the earlier stationary pass does not qualify a different near-contact pose.
Do not resize parts, merge nodes, introduce preload, or add constraints to
make this fixture work.

The candidate moving window is 20 µs with maximum increment 0.1 µs, requiring
at least 200 increments. Procedure and wall-time bounds still need explicit
prelaunch selection; the 20-increment stationary runtime is not a bound on
an impact calculation. No moving deck or launch is authorized by completion
of a preparation artifact alone.

Cache full per-element 10×10 mass blocks for **both** bodies, separately for
the source-reconstructed native four-point rule and physical Gauss8 rule,
using the posed serialized coordinates. Preserve the helper's returned Gmsh
connectivity order. No row lumping or assumed equal body/ply sharing is
permitted. Compare native mass and kinetic energy with native output before
using moving balance results; the core mass is not covered by the earlier
washer-only comparison.

Use the fixed initial posed washer centre `c=(1.001,0.7356,0)` mm as the
angular reference. Transform both reconstructed momentum and reported CF
moments consistently: `Hc=H0−c×P` and `Mc=M0−c×F`. Integrate each pair's
force and moment through every accepted state, including a verified initial
zero-force state. The expected washer reactions are +X from the head and −Y
from the bore. Opposite core resultants must be checked against independent
core momentum, not assumed to prove assembly conservation.

Retain the predeclared transfer/balance/energy gates above and report native
and physical integration separately. Before running a timestep refinement,
freeze comparisons for angular momentum/impulse and energy as well as linear
momentum and pair impulse. A case that does not transfer nontrivial impulse
at **both** interfaces remains inconclusive, even if its residuals are small.

The [published preparation evidence](../fea/results/moving_fixture_preparation/README.md)
now proves positive selected-surface clearance for the proposed pose and
compares both centred native reference masses with all 20 recorded states.
Full native and Gauss8 matrices are retained separately. No posed deck, posed
mass cache, posed quiet result or moving solver result is included yet.

### Separate posed quiet preparation

Create a new quiet-only input from the verified centred DIRECT preparation
and the frozen pose evidence. Use the exact translated-and-serialized washer
nodes from that proof; keep the core nodes and all connectivity unchanged.
Update posed bounds and the fixed angular reference to `(1.001,0.7356,0)` mm,
while retaining original CAD bounds explicitly as reference geometry.
Recompute the washer reference mass from those exact coordinates rather than
reuse the centred value by assumption.

Retain zero initial velocity, no loads/restraints/preload/friction, the same
contact pairs and penalties, all existing quiet gates, 20 DIRECT increments
of 1e−7 s and total duration 2e−6 s. A future explicit launch uses the existing
180-second inner/200-second outer cap. Preparation itself does not launch a
solver or create a moving case. Complete output, including genuine inactive
contact behavior, must be established before this pose can be used for impact.

For CalculiX 2.21, zero created contact elements do not authorize missing DAT
blocks. `resultsprint.f` calls the print routines without a contact-count
guard; `printout.f` writes the CDIS/CSTR/CELS headers and explicit CELS/CNUM
totals even with empty element loops. `printoutcontact.f` still prints each
requested pair's statistics. Zero-area ancillary NaNs are distinct from
missing primary forces or missing blocks. A synthetic parser regression
checks explicit empty tables, zero totals and both complete inactive CF
blocks, and rejects each missing required block. This is a source/output
contract check, not a recorded posed solver result. The source is retained
in the [native control evidence](../fea/results/native_dynamic_control/README.md).

The subsequent [posed stationary evidence](../fea/results/posed_hardware_control/README.md)
now establishes all 20 quiet states for `posed-control-p8c_gk9h`, including
explicit CNUM=0 and both complete inactive pair outputs. The solver finished
within its frozen cap, with successful owned-container cleanup. Both posed
mass operators are archived; native reference masses agree with both bodies'
printed masses throughout the window. This releases preparation of the moving
comparison, not moving contact or joint/board capacity qualification.

## Moving comparison protocol — selected, not launched

The next preparation must bind the passed posed quiet evidence and retain its
exact serialized nodes, connectivity, material/contact parameters and surface
ownership. It changes only the initial washer velocity to `(-100,100,0)` mm/s
and the diagnostic time window; the core remains initially stationary and free.
There is no velocity ramp, external load, restraint, preload or added damping.
The fixed angular reference is `c=(1.001,0.7356,0)` mm, not the earlier centred
reference. Each moving deck needs its own context-bound mass cache, even though
the coordinates and thus its mass operators should match the posed quiet case.

| Case | Fixed increment | Duration | Increments | Inner / outer runtime cap |
| --- | --- | --- | --- | --- |
| First moving comparison | 1e−7 s | 2e−5 s | 200 | 1800 / 1820 s |
| Conditional refinement | 5e−8 s | 2e−5 s | 400 | 3600 / 3620 s |

Use NLGEOM, implicit `DYNAMIC,DIRECT,ALPHA=0`, with EXPLICIT omitted. These are
selected preparation requirements, **not yet a launchable frozen experiment**:
the existing launcher still accepts stationary cases only. Each eventual
launch must be explicitly selected, single-use and bounded, retaining its own
command, binary/build identity, raw output, exit and owned-container cleanup.
No timeout extension, automatic retry or automatic refinement is permitted.

DIRECT provides nested grids for comparison, not proof of stability. It still
calls native impact logic and can terminate on nonconvergence. The quiet
runtime extrapolates to approximately 930 / 1860 seconds before nonlinear
contact overhead; caps are limits, not completion predictions. Nominal contact
engagement is around 10 microseconds, but mesh geometry can change the actual
engagement times. Neither simultaneous engagement nor a particular contact
time is an acceptance condition. Failure requires diagnosis; adaptive stepping
would be a separately frozen experiment, not an implicit fallback.

Before launch, implement and test an offline replay with these definitions:

- Retain all full nodal U/V tables, exact body ownership and every accepted
  contact sample. Actual STA times must match the requested complete grid.
- Reconstruct each body's native four-point and physical Gauss8 mass, P, H and
  KE separately from its full element matrices. No row lumping, shared-body
  nodes or substitution of static RF for dynamic balance. The formal balance
  gates below use the native operator; Gauss8 remains a separate diagnostic.
- Native EMAS relative error remains ≤5e−6 for each body at every state.
  Native KE error is bounded by
  `5e−6 max(abs(KE_native), abs(KE_reconstructed), 1e−8 E*)`.
  Report when the small reference floor controls a comparison; that is an
  absolute-normalized check, not relative kinetic-energy qualification.
- Use current positions `X+U`. Transform `Hc=H0−c×P` and each pair's
  `Mc=M0−c×F`. Trapezoidally integrate signed vectors over every accepted
  interval. The initial zero-force sample must be justified from the separated
  initial geometry, passed quiet evidence and absence of a velocity-dependent
  contact law; do not infer it from a missing first output interval.
- Compare washer `ΔP−ΣJ` and `ΔHc−ΣK`; independently reconstruct the core and
  compare `ΔP+ΣJ` and `ΔHc+ΣK`. Equal-and-opposite contact resultants alone are
  not proof that the core balances. Preserve the per-body limits of 1e−3 P*
  and 1e−3 H*, and assembly drift limits of 1e−4 P* and 1e−4 H*, throughout
  the accepted window.
- Preserve the total energy residual limit of 1% E* throughout the window:
  `sum(ELKE+ELSE)+CELS−initial_energy`, with no external work in this fixture.
  Keep the native energy audit and physical Gauss8 comparison distinct.
- Require each pair's **endpoint net impulse-vector magnitude** ≥1e−3 P*
  and endpoint core KE ≥1e−4 E*. Also retain cumulative force-norm integrals
  and peak core KE to expose cancellation or transient transfer. Insufficient
  endpoint transfer is inconclusive, not qualification.
- Only a complete coarse pass permits the separately selected half-step run.
  Both runs must independently pass the same balance/energy/transfer gates.
  At every matching coarse-grid time, including the endpoint, require each
  body's P and each pair's accumulated J to differ by ≤1% P*, each body's Hc
  and each pair's accumulated K by ≤1% H*, and total energy by ≤1% E*.

These are numerical qualification gates, not structural allowables. Moving
contact qualification would enable the subsequent stitched-versus-independent
leg comparison; it would not establish plywood resistance or approve a build.

The initial-force assumption is supported for this particular unchanged law:
CalculiX 2.21 `gencontelem_f2f.f:551–560` excludes positive-clearance contact
points in dynamic, non-tied contact. `springforc_f2f.f:186–200` computes the
linear spring response from displacement-derived clearance, area and penalty,
without a velocity term. Its linear formula itself is not a positive-part
clamp; inactive-contact suppression happens during contact generation. Together
with the exact separated pose and recorded quiet CNUM=0, this supports the
initial zero-force sample when only initial velocity changes. It does **not**
establish zero force over the first finite interval or cover another contact law.
