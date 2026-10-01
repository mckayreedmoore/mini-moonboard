# Balanced-force result

Both frozen native jobs completed 100 increments normally in 0.89 seconds
each. Both pass the predeclared method comparison. No axial restraint,
prescribed actuator motion, damping or mass scaling was used.

| Quantity | Direct nodal loads | Homogeneous free-controller load |
|---|---:|---:|
| Maximum displacement difference from independent Newmark solution | 4.99e-10 mm | 4.99e-10 mm |
| Maximum mass-center displacement | 0 mm | 0 mm |
| Final relative displacement | .008509312 mm | .008509312 mm |
| Final elastic energy | 3.620420e-5 N·mm | 3.620420e-5 N·mm |
| Final kinetic energy | 1.124913e-5 N·mm | 1.124913e-5 N·mm |
| Applied-work minus elastic and kinetic energy, from native motion | 1.47e-12 N·mm | 1.47e-12 N·mm |

Native printed work and energies also agree at their printed precision.
An independent agent checked the force patterns, relative-mode mass,
Newmark recurrence and result interpretation and agreed with this bounded
method pass.
`independent-force-audit.json` contains the comparisons and source hashes;
the two `*-execution.json` records bind the exact pinned binary, input hashes,
output hashes and stopped containers. Saved producer/auditor files reproduce
the fixtures and calculations.

## Applicability

This verifies the tested balanced-force loading and output interpretation,
including a homogeneous generic equation. It does not qualify nonlinear
contact, C3D10 integration, the actual bolt/nut coupling, or a joint response.
The result is intentionally dynamic; its kinetic energy is substantial and
is not a quasi-static joint criterion.

The full patch should apply the audited dual nodal loads directly to the two
external member caps, omit artificial support and prescribed port-motion
equations, and extract motion from the same projection. Generalized applied
work then equals applied nodal work by the dual-map identity, even if caps
warp. Section tractions remain separate observations; their resultant alone
need not account for work of cap deformation. Preserve all body motion and
contact outputs and include inertia in force and moment balance.

The static force-sweep mechanism gate remains in effect. This alternative
is a bounded physical-inertia transient, not a static solution from the open
clearance state. Current joint sensitivities and family evaluation remain open.
