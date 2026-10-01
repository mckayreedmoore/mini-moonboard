# Parent disposition of the reference and qualification gates

The independent rigid-reference review establishes the discrete constrained
rigid limit. It does not establish the response of the free elastic bolt
body. The native fixture therefore has two separate questions:

1. Does this declared small rotational forcing produce the required nearly
   rigid displacement, velocity and energy response under the frozen numerical
   qualification limits?
2. Do the original free-coordinate mapping and added rigid carrier preserve
   the physical response while producing the intended controls and carrier
   kinematics?

The first question uses pre-run qualification limits. The finite rigid
calculation quantifies one contribution to departure from the linearized
reference; it does not prove that all elastic or numerical departures lie
inside those limits. The second question uses direct/mapped comparisons,
all six intended controls, original equation residuals, and source-defined
carrier kinematics. Physical parity alone is insufficient because a wrong
invertible map can leave the free body response unchanged.

A failed reference comparison will remain a failed fixture qualification.
It will not by itself establish a solver defect or a failed joint. Resolving
such a result requires separating elastic response, numerical behavior and
reference applicability. Thresholds will not be widened after observing the
native result. Conversely, passing the comparisons qualifies only this map,
forcing, amplitude, timestep and method combination; it does not establish
a general elastic error bound or the behavior of all four current maps.

The independent source review found two negligible representation differences
in the parent mass reference: exact 1/24 versus the source's printed quadrature
weight, and full coordinate tokens versus the solver's first 20 characters.
The fixture producer now uses the source weight and parser-visible coordinates.
The independent reference retains its separately bounded arithmetic, so their
agreement is an independent comparison rather than identical implementation.

The per-case output comparisons and the cross-case comparisons use different
printing allowances. Cross-case parity must account for both independently
rounded records. Original equation residuals use each actual printed token's
half-unit rounding allowance weighted by its original coefficient. Missing,
duplicate or nonfinite output cannot be replaced by zero.

The element totals use the same four-point tetrahedron rule. In the pinned
source, `resultsmech.f` selects four points for C3D10 (303), uses `gauss3d5`
and `weight3d5` (558–561), and forms kinetic-energy density from interpolated
nodal velocities (1096–1110). `printoutelem.f` takes reference coordinates
from `co` (255–256), selects the same points and weights (363–366), and
integrates energy, volume and mass (427 onward). Thus the expected ELKE and
EVOL use the discrete reference quadrature; they do not silently substitute
an exact continuum inertia or deformed volume. The source member hashes are
`15fccc9fb553f259af5d33bc78e8d3808f1f9f338ee266ce92192bae33026fa6`
for `resultsmech.f` and
`e5da47dd83dd8e796fcbf8ec81e220b5139211b8f411c03adb17a782436e2544`
for `printoutelem.f`, both in the already pinned source archive.

Parent readiness, a complete verifier and independent input review remain
required before freeze and execution. This disposition selects no current-joint
run and changes no structural-criterion disposition.
