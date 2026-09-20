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
not a delivered mass or selected hardware schedule. Its temporary kerf-right
mesh hooks are serialized within this adapter, reject an already-patched
builder, and restore the shared functions after a preparation failure;
run it in an isolated process because older diagnostic adapters do not
share that lock. The model
uses the current grain-N **four-bolt diagnostic pose**, which still has
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
