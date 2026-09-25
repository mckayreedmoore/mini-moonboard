# Sixteen-duty integrated static diagnostic

Status: nominal development geometry, 2026-09-24. All eighteen implemented
static/provenance checks pass. No joint, assembly path, capacity, or release
is accepted.

The [composition](composition.json) merges the corrected
[twelve-duty layout](../wj12-integrated-static/README.md) with the
[four left service duties](../left-service-integration/README.md). It contains
twenty candidate connector pieces, 72 proposed bolt stations, and 360 installed
hardware shape roles. Heads and shafts are separate CAD roles, so that last
count is not a purchased-piece count. Ninety-six former SDS axes are removed;
eight top/bottom duties with 48 SDS axes remain. All 66 fixed Hillman axes and
twelve starting frame-bolt arrangements remain accounted for.

The compositor rebuilds thirteen shared hosts from raw shapes, source-native
machining, candidate purchase-length cuts, and all existing/new candidate
bores. It removes the source cuts belonging to all sixteen replaced duties.
It does not merely drill left-family holes into the old finished side and
principal members. The two prior left-service receiver overlays become
rebuilt hosts; three other source overlays retain eight purchase-length cuts.
The four redirected backer axes remain separately accounted for.

The [combined diagnostic](diagnostic.json) took 170.17 seconds; composition
took 2.12 seconds using the retained family geometry. It checks full-scene
body/hardware/bore interactions, protected services, receiver material and
machining at all 66 axes, retained frame bolts, source reconstruction, and
input hashes. Its additional fixed layout contract requires exact duty, host,
part, axis, retained-hardware, and overlay identities and counts independently
of the object being tested. Raw receiver material and nominal clearance do
not establish embedment, wood resistance, or supported assembly.

Integration repairs distinguish the complete six-panel family scene from its
three right-panel replacements and named frame-component aliases from indexed
installed components. The three left panels match their canonical source;
the right panels match the WJ12 replacement shapes. Per-bolt shape fingerprints
reconcile the sixty installed frame-hardware components. Thirty-seven focused
tests for the shared diagnostic and WJ16 contract pass; Ruff checks pass.
The new default WJ12 identity contract also passes against the retained actual
twelve-duty object; its historical reports and snapshots remain unchanged.

The [manifest](sha256.json) binds both reports and all three current diagnostic
producer snapshots. The diagnostic binds the composition JSON hash and family
input fingerprints. No native solve has run. Native analysis is now authorized
after model and method readiness; see the
[adapter plan](../../native-adapter-readiness.md).

The [WJ12 upper-right motion report](../wj12-right-rail-motion/README.md) found
wire intersections during removal and does not accept a transport sequence.
Those operations still require a supported staging solution and rechecking
against the completed layout. The next geometry slice is the top outer pair,
followed by the top-center and bottom duties. Complete mechanics, tools,
tolerances, stock/hardware costs, and coordinated shop instructions remain
open. Selected authority, historical evidence, active narrow WJ04 configuration,
and public viewer are not promoted by this static diagnostic.
