# Provisional 106-bolt hardware and marking packet

This packet binds the [106-bolt geometry](../geometry-receipt.json) to its [matched six-case bank](../response-bank.json): four original cold fields and two same-input precision refinements, each with two independent replays. [Current engineering findings](../README.md) govern the remaining criteria. All physical-use holds remain.

The tables contain **106 bolts, 106 nuts, 212 washers, zero spacers and 148 physical receiver rows**. Outer top corners use four bolts each; each plywood cleat retains eight and each center-top connection retains four. Twenty sawn members, four physical cleat leaves and six panels retain thirty exterior profiles.

Use the [per-axis hardware crosswalk](hardware-axis-crosswalk.csv), [grouped hardware](grouped-hardware.csv) and [receiver table](receiver-planning.csv). Exact product/profile qualifications remain conditional, and four Grade 5 types still lack qualified supplier SKUs. Actual/Disposition cells are blank. The new 148 receiver rows govern proposed holes; older 112/114 hole and hardware quantities do not transfer. Unchanged exterior cut/stock and screw information may be read in the [preserved build package](../../shorter-bolts/build-package/README.md) within those categories only. Model bores, axis lengths and entry projections are analysis geometry rather than drill-bit or purchased-length instructions.

The [source index](source-index.json), [force binding](force-binding.json) and [validation](validation.json) retain exact six-case and twelve-replay links. The numerical precision update changes no hardware, geometry, jig or mask bytes.

Five existing marking prototypes are reused within the [checked registration scopes](jig-reuse.json):

- [Left upper-rear template](../../relocated-rear-pair/planning/left-upper-rear-marking-template.stl) and [right upper-rear template](../../relocated-rear-pair/planning/right-upper-rear-marking-template.stl).
- [Left rear-foot/leg jig](../../shorter-bolts/build-package/runner-leg-jigs/prototype-v3-verified/left-rear-foot-leg-marking-jig.stl) and [right rear-foot/leg jig](../../shorter-bolts/build-package/runner-leg-jigs/prototype-v3-verified/right-rear-foot-leg-marking-jig.stl).
- [Horizontal-rail marking jig](../../shorter-bolts/build-package/bracket-jig/horizontal_rail_marking_jig.stl), for its twelve checked horizontal-rail registrations only. It has no outer-top or post-flange registration claim.

At the **two outer top angles**, only the existing FAR pair on each flange is active. All eight NEAR holes there are inactive. The [hole-ID table](outer-top-hole-mask.csv), [mask policy](outer-top-mask-policy.json) and [unscaled reference graphic](outer-top-mask-reference.svg) identify this distinction. The graphic is not a fitted mask or a printable drilling guide. Cleat eight-bolt patterns remain unchanged.

The far top-beam distance is 65.0875 mm versus the separate full 7D marker of 66.675 mm, a 1.5875 mm screening shortfall. The current signed geometry and connection interpretation determine applicable reductions; this packet does not clear them. Existing near-cleat-post end-distance, tool/sequence, hardware, bond, splitting and support limits remain separate.

**HOLD: purchase, marking, cutting, drilling, fabrication and climbing.** These are conditional development tables and reusable marking prototypes, with no inspected build or physical-use release.
