# PB-01 preparation-only native bridge

[`prepare_case`](../../scripts/simple_pb01_hybrid_native.py) builds an
**unsolved** kerf-right hybrid for any of the six unchanged load-case IDs.
It adds the existing diagnostic 4×6 grain-N cleat as an independent timber
body, two named trial bolts on each serial rail/cleat and principal/cleat
interface, and one compression-only contact sample per face. It removes the
old ML24Z body and six SDS springs at `clip_horizontal_lower_right_1`.
The other **23 stations remain the old angle/SDS topology**, explicitly
identified as proxies. All 66 fixed panel/kicker screw axes are retained.

The adapter supplies a named, arbitrary trial spring stiffness of
1,000 N/mm by default. It does not establish delivered bolt stiffness,
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
same maintained 1/4-in four-bolt geometry with a distinct candidate identity
and an explicit 6.35-mm trial-shaft mass. The two variants deliberately retain
the same arbitrary 1,000-N/mm trial spring stiffness; a response difference
would be a sensitivity to geometry/mass, **not a diameter-dependent stiffness
or strength prediction**. The head/nut and 25.4-mm washer envelopes in the
mass estimate remain provisional, not selected retail stacks. Both poses still have
conditional placement and installed-access conflicts. The unilateral
contacts use one point per face, not a pressure distribution. The code
returns a structure and ownership metadata only; it invokes **no native
solve** and creates no accepted force result, case archive, candidate
input manifest, or drilling instruction. No old-proxy response may be
reported as the V4 same-case joint demand.

The focused test prepares `a12-forward`, verifies the 23/1 station split,
independent cleat body, 66 preserved panel axes, serial bolt identities,
positive trial stack gravity, contact normals pointing into the actual host
wood, opening-contact release, and equal/opposite synthetic force recovery
about the PB-01 datum. Its synthetic 1/2/3-N vectors are a software
identity check, **not applied loads or joint demands**. This is a bridge
toward a later connected V4 model; all original connection duties must be
replaced and checked before six new same-configuration cases can support
a candidate verdict.

For a reproducible **hybrid sensitivity** solve, run
`uv run python -m scripts.simple_pb01_hybrid_diagnostic_run a12-left --output DIR`.
Add `--variant quarter` for the separate nominal 1/4-in geometry sensitivity.
This wrapper fingerprints the adapter, pose generator, their repository
Python import closure, and trial-pose JSON in addition to the native
solver's regular source closure. It rejects changed producer files after import,
retains a diagnostic-scope sidecar, and does not promote a converged old-proxy
result into V4 same-case demand. The older exploratory runs without this
additional source inventory remain unauthenticated and must not be cited as
candidate evidence.
