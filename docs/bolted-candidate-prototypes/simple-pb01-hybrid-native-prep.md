# PB-01 preparation-only native bridge

[`prepare_case`](../../scripts/simple_pb01_hybrid_native.py) builds an
**unsolved** kerf-right hybrid for any of the six unchanged load-case IDs.
It adds the existing diagnostic 4×6 grain-N cleat as an independent timber
body, two named trial bolts on each serial rail/cleat and principal/cleat
interface, and four compression-only contact samples per seated face. It removes the
old ML24Z body and six SDS springs at `clip_horizontal_lower_right_1`.
The other **23 stations remain the old angle/SDS topology**, explicitly
identified as proxies. All 66 fixed panel/kicker screw axes are retained.

The adapter supplies independent, provisional bolt axial and lateral stiffness
(1,000 N/mm per bolt each by default), plus total face-normal stiffness
(1,000 N/mm per interface by default). Four interior samples divide the face
total equally. They use the actual timber-face overlap in a 2×2 grid; each
carries one quarter of the rectangular area less two nominal bore areas.
Both timber solids are checked at every sample. This permits an off-row
compression couple while closed, without friction or a rotational spring.
It is not a measured pressure field or seating stiffness. It does not establish
delivered bolt stiffness,
contact pressure, clearances, group action, or 2024 NDS resistance. It
includes an explicit **diagnostic** gravity estimate for four trial steel
stacks using 8-in/5-in shafts and simplified washer/head/nut envelopes;
half of each is applied to each connected body at its interface. This is
not a delivered mass or selected hardware schedule.
The eight half-stack nodal weights are also listed as explicit per-member
loads at their application points for free-body and section recovery; the
member-balance postprocessor otherwise counted only member-center gravity.
This bookkeeping change does not establish a connector resistance.
Its temporary kerf-right mesh hooks are serialized within this adapter,
reject an already-patched
builder, and restore the shared functions after a preparation failure;
run it in an isolated process because older diagnostic adapters do not
share that lock. The default model uses the grain-N **3/8-in four-bolt
diagnostic pose**. `prepare_case(case, variant="quarter")` selects the
same four bolt centerlines with a distinct candidate identity and an
explicit 6.35-mm trial-shaft mass. The nominal bore diameter is recorded
but does not change this mesh. Both variants retain the same default trial
spring inputs; a native-response difference at fixed inputs isolates
the **trial stack mass**, not a geometric, diameter-dependent stiffness or
strength effect. The separate CAD comparison checks 1/4-in bore fit.
The head/nut and 25.4-mm washer envelopes in the
mass estimate remain provisional, not selected retail stacks. The 3/8-in
pose retains conditional placement conflicts; the 1/4-in CAD screen clears
those particular margins, but real access, load directions and strength
remain unqualified. The unilateral contacts use four points per face, not a
verified pressure distribution. The code
returns a structure and ownership metadata only; it invokes **no native
solve** and creates no accepted force result, case archive, candidate
input manifest, or drilling instruction. No old-proxy response may be
reported as the V4 same-case joint demand.

The focused test prepares `a12-forward`, verifies the 23/1 station split,
independent cleat body, 66 preserved panel axes, serial bolt identities,
positive trial stack gravity, contact normals pointing into the actual host
wood, off-row moment and opening-contact release, face stiffness/tributary
totals, and equal/opposite synthetic force recovery
about the PB-01 datum. Its synthetic 1/2/3-N vectors are a software
identity check, **not applied loads or joint demands**. This is a bridge
toward a later connected V4 model; all original connection duties must be
replaced and checked before six new same-configuration cases can support
a candidate verdict.

For a reproducible **hybrid sensitivity** solve, run
`uv run python -m scripts.simple_pb01_hybrid_diagnostic_run a12-left --output DIR`.
Add `--variant quarter` for the separate nominal 1/4-in geometry sensitivity.
The runner also accepts `--bolt-axial-n-per-mm`, `--bolt-lateral-n-per-mm`,
and `--face-normal-total-n-per-mm` as separate trial inputs; its scope
sidecar records them. Changing them defines a sensitivity, not a bound.
This wrapper fingerprints the adapter, pose generator, their repository
Python import closure, and trial-pose JSON in addition to the native
solver's regular source closure. It rejects changed producer files after import,
retains a diagnostic-scope sidecar, and does not promote a converged old-proxy
result into V4 same-case demand. The older exploratory runs without this
additional source inventory remain unauthenticated and must not be cited as
candidate evidence.
