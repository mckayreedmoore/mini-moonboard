# Corrected finite-sector contact packet, attempt02

This preparation-only packet carries a corrected contact deck in its own
folder. The prior contact deck generator built the required restraint text but
did not emit it into the input. The corrected deck now includes one model
definition `*BOUNDARY` card before `*STEP`: every node in the lower `GROUND`
set is fixed in DOFs 1–3; upper gauge node 33 is fixed in DOFs 1–2; and upper
gauge node 45 is fixed in DOF 2. It applies no constraint to a loaded pressure
node or to an upper-body z DOF. The generated deck parser test independently
reads the emitted node sets, upper element connectivity, and boundary rows;
synthetic missing, duplicate, wrong-DOF, pressure-node, and upper-z changes
must be rejected.

The contact result audit follows the pinned CalculiX 2.23 pressure assembly
rule. `e_c3d_rhs.f` selects `gauss2d5` for C3D10 triangular faces; `gauss.f`
defines three points with weight 1/6. The audit uses that discrete three-point
wrench as the load and equilibrium oracle and also reports an independent
six-point degree-four TRI6 wrench. It gates their force difference at the
existing 0.02 N force limit and their moment difference at the existing
0.05 N·mm moment limit. The contact-resultant moment gate remains 0.05 N·mm
absolute plus its existing relative allowance. A curved TRI6 synthetic
known-answer test distinguishes the rules: for the paraboloid face, continuous
`My` is `4/15`, solver-rule `My` is `29/108`, and their signed difference
(solver minus continuous) is `1/540` N·mm.

This folder is separate from the earlier preparation and parent-owned freezes.
It does not edit or replace them. The deck retains the numerical geometry,
material values, pressure, and contact law from the previous contact fixture;
the emitted boundary card is the only input-deck change. Contact-resultant
reference values and existing contact-resultant gates are preserved. The
expected JSON adds the source-bound pressure quadrature method and separately
checks quadrature error using those existing force and moment limits. This
fixture checks solver method and integrated contact resultants only. It does
not qualify washer material, local metal stress, plastic recovery, product
behavior, or resistance.

`prepare.py` emits only `prepared/finite-sector-contact/` plus pinned source
and receipt files. It refuses to overwrite a nonempty destination, never runs
CalculiX or Docker, and records no freeze or native readiness. `source-pins.json`
records the pinned CalculiX 2.23 `*BOUNDARY` manual section and hashes for this
packet's code paths. `preparation.json` binds all generated files and support
code hashes. `verify.py` remains the offline result audit; it is not an input
freeze or launch tool.

Run the offline checks with:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s docs/wood-joints-mvp/hypotheses/washer-contact-known-answer-preflight-2026-10-01-attempt02/tests -v
PYTHONDONTWRITEBYTECODE=1 python3 docs/wood-joints-mvp/hypotheses/washer-contact-known-answer-preflight-2026-10-01-attempt02/verify_preparation_receipt.py
.venv/bin/ruff check --no-cache docs/wood-joints-mvp/hypotheses/washer-contact-known-answer-preflight-2026-10-01-attempt02
```

No freeze, native run, candidate acceptance, or hardware claim is created by
this packet. Any later run requires the parent-owned review, separate freeze,
readiness receipt, and serialized runner protocol.
