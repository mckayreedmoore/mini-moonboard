# Complete left corner: carrier and force-recovery inventory

This packet binds the five corner members and six new BG001/BG003/BG045
bolt axes to the frozen C11 **input** carrier geometry. It does not read
response forces or active states. C11's rejected contact-sign branch remains
rejected. The selected angle-frame baseline and twelve original leg/runner
resistance arrangements remain separate.

The extraction in [interface-map.json](interface-map.json) contains seven
internal contact pairs / 28 cells, eight lateral bolt planes and six outer-seat
ties. BG003's two bolts each have two lateral planes and one outer-seat tie.
The internal contact pairs are header/post, header/side, header/spine,
header/inner block, post/spine, side/spine and side/inner block. Direct bearing
can share or bypass the nominal new-bolt chain. Whether it actually does so
depends on signed contact and compatibility, not on contact area alone.

Across the complete five-member inventory there are 36 contact pairs / 236
cells. The other 29 pairs / 208 cells are boundary carriers. These include
runner/spine and runner/post bearing, contacts with neighboring frame members
and panel receivers, and four modeled post/floor normal cells. The four paired
post/floor tangent ownership rows are also retained; they represent the old
finite-spring diagnostic, not a verified ideal no-slip floor law. There are
four original leg/runner lateral ownership rows and their outer-seat ties;
identifying them here does not reopen their unchanged resistance checks.

Each ownership row preserves its body identities, physical point or outer
seat points, axis and force basis as available. Contact cells preserve their
normal, area, source-patch index and physical point. Descriptor midpoints are
provided as convenient moment datums only: they are not support stations,
actual cut locations or mass centroids. Future recovery must use each force
on the correct body at its physical application point. Translate moments
with `(point - datum) × force` and retain explicit couples. An aggregate
corner cut cancels internal forces and cannot prove individual joint demand;
each member and the complete assembly need separate closure.

The map includes 20 panel-screw axial ownership rows, explicitly labeled
non-qualifying parametric withdrawal. Their presence identifies potential
load accounting, not product stiffness or capacity. No new panel study or
catalog search follows from this inventory.

## Minimum next demand inputs and stop

To calculate complete corner actions, supply simultaneous six-component
boundary/member-cut actions and source-bound external loads at stated datums,
then an applicable compatibility/contact scenario for the internal carriers.
A prescribed local cut-load scenario can produce conditional corner actions;
it must not be called the six-case frame result. A current six-case frame
result additionally needs the supported global floor rule, receiver load
sharing, member response and complete input/output mapping already identified
in the readiness record. This map supplies none of those missing forces.

The exact stop is therefore **input carrier coverage complete, signed demand
not supplied**. Do not recover C11 forces as design demand, substitute aggregate
panel resultants for these cuts, or omit direct bearing to obtain a bolt-only
answer. No native run, mesh, geometry change or fabrication is authorized by
this packet. Parent retains frozen inputs, readiness, serialized execution and
final validation.

Reproduce from the repository root:

```sh
python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-corner-interface-recovery-map-attempt01/produce.py
python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-corner-interface-recovery-map-attempt01/produce.py --verify
```

The standard-library producer verifies input SHA-256
`d3417111926c982a07ced393aa1c12f815aa87b5b8eb851b45bc63a1ea10fac0`
before extraction. Parent separately counted the seven internal pairs and
areas, checked the eight corner planes / six ties, and inspected the paired
floor ownership. Reproduction is an input-coverage check, not mechanical
validation or a criterion pass.
