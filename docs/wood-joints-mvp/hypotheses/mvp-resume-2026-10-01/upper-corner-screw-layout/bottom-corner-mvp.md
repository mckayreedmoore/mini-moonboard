# Bottom outer corner MVP comparison

## Historical draft

This draft predates the completed component replay and the later decision to
retain the original 100 mm load lever. Its pending-result and 50 mm statements
below preserve that earlier scope, not the current task or load contract. Use
[the completed component record](bottom-corner-components.md) and
[the fresh proposal references](knee-bridge-corner-references.md) for subsequent
results. The original draft follows unchanged.

## Scope and finite decision

This worksheet reuses the completed [bottom corner transfer](bottom-corner-transfer.md)
and its prepared [same-state component replay](bottom-corner-components.md).
It covers two bottom outer cleats, six cases, 24 host/interface states and
48 bolt states. Geometry and hardware remain unchanged. Each comparison
uses one bolt's simultaneous lateral force, axial tie and saved bending
stress; independent force maxima are not combined.

The transfer is complete under its stated first-order, rigid-timber,
concentric-washer and reference-geometry assumptions. The component replay
is awaiting the coordinator's numeric receipt. No new component result or
acceptance is claimed before that receipt is consumed.

This packet retains the original 100 mm source load lever. The owner's
subsequent 50 mm MVP assumption is a separate force-basis decision owned by
the coordinator; the present results must not be relabeled as a 50 mm run
or scaled into another load state.

## Comparisons to report

The table will retain separate left/right governing witnesses. A value below
one is a comparison within its declared component hypothesis; it supplies
neither a whole-joint capacity nor a permitted scaling of the applied load.

| Comparison | Existing reference and interaction scope |
| --- | --- |
| Lateral, 45 ksi scenario | Bottom-only single-shear yield equations with actual receiver lengths and load/grain angles, 4450/5600 psi bearing inputs and existing Cg/Cdelta component modifiers. |
| Lateral, 92 ksi scenario | Same calculation with the separate 92 ksi steel hypothesis. No steel property is transferred from the bolt label or from the top geometry. |
| Same-state 92 ksi steel reserve | Concurrent axial stress on the retained 0.0318 in² area and direct shear reduce the hypothetical steel yield input before repeating the lateral equations. This is the existing sensitivity, not an adopted interaction rule. |
| Finished cleat path | Signed force parallel to cleat grain divided by the existing Fv reference and its own finished bore-tangent path area. No group or splitting resistance is assigned. |
| Washer mean pressure | Concurrent axial tie divided by the smaller supported area at that bolt's two seats, using the existing worst combined-offset areas, then compared with the stated Fc-perpendicular reference. |
| Smooth-bolt stress | Saved same-state, same-position combined axial/bending/shear stress proxy divided by the 92 ksi hypothesis. Delivered shank, thread/runout and material remain conditional. |

Saved K20 wood-seat pressure peaks, face-contact pressures and the washer
radial-strip stress are separate diagnostics. A supported-area mean does
not bound local pressure. The strip calculation supplies no actual washer
metal resistance. Both groups' independent host and whole-cleat force/moment
balances remain attached to the comparison.

## Reused source receipt

Paths are relative to this folder.

| Artifact | SHA-256 |
| --- | --- |
| `rawlocal/bottom-corner-transfer/first-order-attempt01/checks.json` | `4d255ba5ebd8f1f93fb41ef90511eb3da49906f4729f33f5f63766e0a0bd78ed` |
| Same packet, `source-pins.json` | `5fdeb9927a759644f5c25d462b532fcd2bb9d2f389f69b462b716f33857fcb51` |
| `bottom-corner-components.py` | `5239f1b4897e17ade2c4c4e73b8f9a42e9433f76357fbe0f355308c84fcbd3a7` |
| `bolted-replay-results/bottom-attempt01/component-results.json` | `ec421ee35b9477842660faa6d2528bd957f8a06620f7d84c46d9654e40ce146a` |

The component producer authenticates the existing transfer's complete source
closure and its reused arithmetic/material inputs. The worksheet adds no
producer, frame solve, CAD, native calculation, test, review loop, catalog
search, staging or commit. Root owns this leaf and its result annotation;
the coordinator owns execution and publication. Existing producers and their
notes stay with their current owner.

## Result receipt and disposition

Coordinator component result pending. Final completion will record its exact
hashes, the governing comparisons and their same-state witnesses, then return
this leaf to the coordinator for the joint MVP disposition.

Actual hardware/washer capacities, Ft-perpendicular and full group/splitting
resistance remain unassigned. These explicit scope limits do not commission
additional FEA, product searches or an automatic qualification program.
The 47-criterion authority, complete-joint HOLD and all fabrication/physical
release boundaries remain unchanged.
