# Six header cleats: reduced-depth component readiness

## Decision

**STOP_NOT_READY: the existing saved evidence does not establish an applicable
NDS §3.4.4.1 comparison for any of these six complete cleats.** This is a
bounded applicability decision, not a calculated strength failure, a proof
that the provision can never apply, or a complete-joint qualification.
No new numerical producer or demand-only worksheet is prepared.

The scope is the two center-post cleats, two center-principal cleats and two
inner knee frame blocks, under all six saved cases. The reviewed 104-axis
geometry remains authoritative. The fresh source uses the `ce69ba58…` gravity,
`c3a8ff02…` frame comparison and `62bd4116…` response identified in
[the fresh adapter](header-fresh-force-adapter.md). Planning gravity includes
the unadopted 108-axis proposal's mass, but the four proposed internal-v ties
have no global connector rows. No 108-axis response or tie resistance is
inferred.

## Applicable source requirement

[NDS 2024 Chapter 3](https://web-media.awc.org/wp-content/uploads/2021/12/17210019/AWC_NDS2024_withCommentary_20240718_AWCWebsite_Chapter-3-Design-Provisions-and-Equations.pdf),
§3.4.4.1, printed p.21 / PDF p.7, supplies a reduced-depth shear comparison
for a matching rectangular bending-member connection component. Its induced
section shear must follow engineering mechanics, with the actual loaded and
unloaded edges and fastener-center geometry. It does not impose a minimum
member length or require that all other actions vanish. Separate axial,
washer and combined-action duties do not erase an otherwise applicable
transverse-component comparison; see
[the completed receiver interpretation](../beam-connection-shear-completion.md).

Consequently, the short grain lengths below are not themselves an exclusion.
The unresolved items are the actual connection direction, section and
simultaneous transfer path. A supported local mechanics proof could address
these; a complete three-dimensional reconstruction is not added as a blanket
prerequisite.

## Existing grain-section evidence

All six material frames use grain `g = +Z`, `u = +X`, `v = +Y`. The fresh
finished geometry records two header-bolt passages extending through each
cleat's entire grain length. These are longitudinal passages, distinct from
the ordinary cross-grain holes in the receiver reduced-depth comparisons.

| Cleat family | Bodies | Grain length, mm | Saved grain-normal traces, both bodies |
| --- | ---: | ---: | ---: |
| Center-post | 2 | 128.9 | 624 |
| Center-principal | 2 | 134.7 | 672 |
| Inner knee frame | 2 | 139.0 | 672 |

The fresh `same-cut-states.jsonl` contains **1,968** selected traces across
**36** body/case states. Every selected trace has
`section_status = NON_APPLICABLE_BORE_OR_PASSAGE`; both its `cd1` and `cd1_25`
shear references are null. Thus this archive supplies no adopted finished
rectangular section comparison for these bodies.

The status alone is not a universal prohibition on holes. The receiver beam
worksheet separately establishes reduced-depth components despite ordinary
cross-grain bore exclusions in an earlier plain-section screen. Here the
full-grain passages and actual loading require a demonstrated retained
component and transfer path; substituting the gross envelope would not
establish that demonstration.

## Actual group directions and contact paths

Read-only inspection of the saved point actions uses the inherited
`1e-4 N` direction-resolution threshold solely to classify direction. All
actual force components, point positions and free couples remain retained;
no section force or capacity is recomputed.

For the other-host cross-grain bolt groups, **24** body/case states have no
resolved lateral `v` direction. The remaining **12**, covering both inner
knee blocks in all six cases, have opposing `v` directions. None provides a
single common loaded edge for its complete physical pair.

For example, left inner knee / `a12-rear` retains:

| Source action | Global point, mm | Saved `Fy`, N |
| --- | --- | ---: |
| `knee_outer_left_side_1/plane-38`, row 75 | (-1130.3000000000002, -106.22808665153461, 331.31555301851245) | +52.15381799252375 |
| `knee_outer_left_side_2/plane-40`, row 79 | (-1130.3, -77.30264421564029, 365.7875529588667) | -52.15381799252349 |

The points differ in both `g` and `v`. The corresponding other-host contact
patches have `u`-normal reactions, so their frictionless contact does not
supply a `v` reaction. Neither net-force cancellation nor splitting the
physical pair into favorable independent loaded-edge checks establishes
the pair's simultaneous transfer. A matching treatment of the opposing
actions remains absent.

There are exactly two resolved header-interface `u` lateral action states:

| Body / case | Source action | Saved `Fx`, N |
| --- | --- | ---: |
| `center_principal_cleat_left` / `a12-left` | `center_principal_header_left_2/plane-26`, row 50 | +26.3249000591298 |
| `center_principal_cleat_right` / `k12-right` | `center_principal_header_right_2/plane-28`, row 54 | -29.817566410513738 |

The principal contacts do have `u` normals, making these genuine candidate
components to consider. However, the header shafts run parallel to the
cleat grain, and the saved section and field evidence does not establish a
matching retained rectangular component with induced `Vu` from all
simultaneous actions. A header bolt's lateral force is not itself that
section shear. No resistance or utilization is assigned to either state.

Static contact-patch identities are 26/28 for the posts, 39/50 for the
principals and 89/98 for the inner knees. Their stored normals are along
global X. These static geometry records do not supply old forces to the
fresh comparison.

## Preserved evidence and remaining qualification

The fresh adapter retains every source point action and its complete body
wrench. Its mapped header interfaces pass integrated action, interface and
body accounting, while other interfaces remain source point actions. Those
accounting passes establish neither a complete physical boundary nor the
missing applicable component above. Existing opposing-direction, contact,
finished-section and source-orientation guards remain in force.

This finite review ends here under the parent's bounded instruction. It
does not add another native run, frame solve, hardware change or diagnostic
producer. All splitting resistances and complete-joint acceptance remain
unassigned for this six-cleat scope; adoption and physical release remain
false. Other duties retain their existing results and unresolved checks.

## Independently authenticated inputs

| Saved artifact, relative to this document | SHA-256 |
| --- | --- |
| `../../member-screen-attempt02/knee-bridge-gravity01/geometry.json` | `c61139087fac34e8094f2336f15dd6de5c0112d26d37b9535526f47332f453af` |
| `../rawlocal/knee-bridge-members/attempt01/same-cut-states.jsonl` | `b516e2f7e69699d5767d90563e697ca6b91f6fce1b32ecd13e0b447b1a80d7e7` |
| `../rawlocal/knee-bridge-members/attempt01/checks.json` | `0d623eb62605ddac9aa5111e2469a1c63f4857e356fe607741fc425d5ea59e65` |
| `../rawlocal/knee-bridge-members/attempt01/receipt.json` | `fa4d5f5568d53c0e4e62a74d31a814738b39a78951a4c27ae6e4c141ef5be794` |
| `rawlocal/header-fresh-force-adapter/attempt02/fresh-header-actions.jsonl.gz` | `09293d656b0a3b49c2fe770a1b5962371c01f5ca793552edda4beed7d4d1c59b` |
| `rawlocal/header-fresh-force-adapter/attempt02/checks.json` | `94e8f4c698772530ac25df0bc5f91715db64078bba1c27fc26b42545d86680b6` |
| `rawlocal/header-fresh-force-adapter/attempt02/receipt.json` | `5294be28ae9854dc5b90641c8223a64d7fca817d1494d90965f2c6d3173be738` |
| `../rawlocal/header-local-transfer/attempt01/model.json` | `eae4fc005cdd079f90f527be611e45a137aa275b129e16eebf964c422d69ae52` |
| `../rawlocal/profile-method-completion/sources/nds2024-chapter3.pdf` | `205df74e16f632dfe78211e99bfa5dfa8b9f8dd316e9c5fa1316493f795ec644` |

Only saved-field inspection, source authentication and this documentation
were performed for this decision. No engineering producer was executed.
