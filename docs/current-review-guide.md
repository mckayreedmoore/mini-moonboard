# Current design review guide

Current MVP development: [single-2×6 square-cut baseline](square-2x6-mvp.md),
retained with explicit failed fit checks for selective revision.

The review package below is the preserved **`wide-principal-development`**
candidate. This is an auditable development package, not approved construction or climbing plans. Historical
variants remain for comparison; their geometry and analysis must not be mixed
into this candidate's schedules.

## Open these first

The [latest local package audit](current-package-audit.md) records 57 passing
geometry/hardware/machining tests and the current candidate's browser check,
with their coverage limits. Passing these checks does not close the gates below.

1. [Interactive model](https://mckayreedmoore.github.io/mini-moonboard/?model=wide-principal-development&view=rear)
   and [candidate overview with STEP and export links](wide-principal-development.md).
2. [Assembly and disassembly sequence](wide-principal-assembly.md).
3. [Metric/imperial machining and profile references](wide-machining.md) and
   [structural hardware BOM](wide-purchase-bom.md).
4. [Current leg-bolt comparison](leg-bolt-resistance.md),
   [coupled joint FEA](coupled-leg-release.md) and
   [unanchored floor-equilibrium screen](wide-floor-screen.md).
5. [Plywood versus 2×6–2×12 leg study](leg-stock-comparison.md): separate
   selectable straight-leg CAD variants, rigid-floor comparison and
   [native coupled results](lumber-leg-response.md) for all four stock sizes
   plus a longer 2×8 and a finer-leg mesh check. The present compact joint is
   not qualified; joint revision and combined strength checks remain open.

The viewer shows candidate geometry, not a live FE solution or a stress plot.
Its 291 selectable entries comprise 103 bodies and 188 connection assemblies.
It does not visualize the ideal bonds, fixed floor or assumed springs used in
individual analysis trials. The analysis report, not the render, defines those
conditions. No 3D holds or pad are included as structural FE components.

## Decisions required before releasing build plans

| Item | What exists | What remains unresolved |
| --- | --- | --- |
| Leg/rim and stitch joints | Eight rim-bolt stacks, six stitch axes, separate-ply mesh ownership and conditional force/reference calculations | Individual-ply bolt/stitch transfer without glue credit; applicable material and bolt properties, slip, group/splitting and axial/washer checks. See [ply load path](leg-ply-load-path.md). |
| Kicker/backing and base | Continuous backing, principal housings, retained through-bolts and released-gusset diagnostics | Complete bearing/retention and base-joint resistance. The [ML23Z end-angle trial](end-angle-installation-gate.md) is **not selected** and needs application confirmation; do not add it to the current BOM. |
| Removable panel attachments | 56 machine screws and insert receivers in CAD and schedules | [Insert recess, usable thread engagement and anchorage](panel-insert-selection.md). Occupied CAD envelopes and pilot reservations are not final installation instructions. |
| Unanchored stability | Current rigid floor-equilibrium screen and conditional fixed-floor FE results | Actual friction and compliant contact/uplift behavior. Fixed XYZ restraints are analysis assumptions, not permitted anchors. |
| Materials and installed hardware | Purchased face-sheet identification, nominal stock and product families | [Delivered stock and remaining hardware details](remaining-material-hardware-closure.md), including actual ply thickness, hold-bolt fit, T-nut screws and wiring provisions. The user's offcut-test waiver remains unchanged. |
| Final release | CAD, plans and numerical checks available for review | Close the above evidence gaps, synchronize any resulting changes, obtain appropriate structural review and establish a safe physical verification/inspection plan. No climbing approval is implied. |

One climber, **250 lb maximum**, is the owner's design request; 150/200 lb
comparisons and 300 lb sensitivity remain in the analysis. At the stiffest
assumed connector setting, peak leg-bolt lateral force is 770.90 N at 250 lb
and 903.13 N at 300 lb. The 797.62 N bonded-laminate reference is conditional,
not an adjusted allowable. Neither comparison proves adequacy or physical
failure. Lower assumed stiffness produces different forces and displacements;
the sweep is not a physical bound.

## Most useful human input now

- Give the prepared [end-angle application question](end-angle-installation-gate.md#prepared-supplierreviewer-question--not-sent)
  to Simpson or the structural reviewer. No inquiry has been sent on the owner's
  behalf. This asks whether a proposed detail is supported, not permission to
  improvise an installation.
- Confirm the insert's installed recess and usable internal thread dimensions
  with the manufacturer, and obtain an applicable anchorage basis; the
  [prepared insert application question](panel-insert-selection.md#prepared-manufacturerreviewer-question--not-sent)
  can be forwarded as written. It has not been sent.
- Provide grade stamps, actual thicknesses and bolt identification/certificates
  when available. These resolve inputs; they are not substitutes for connection
  and whole-frame evaluation.

The [active work ledger](connection-design-goal.md) retains the detailed
engineering history and next analysis steps. Keep this guide as the entry point;
do not use a historical “next step” elsewhere as the current design decision.
