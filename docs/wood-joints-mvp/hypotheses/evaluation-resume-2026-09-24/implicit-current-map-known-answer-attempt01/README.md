# Current bolt-map method fixture

This packet records three bounded implicit-dynamic checks using the actual
first bolt body and its current shaft-fit equations. All three frozen native
cases now [pass the predeclared numerical checks](RESULTS.md), with ten accepted
increments and complete outputs each. The [independent postrun review](independent-postrun.md)
confirms the result and all frozen/captured hashes.
The [verifier and runner preflight](verifier-preflight.md) and 24 synthetic
controls passed before the parent-owned freeze and serialized execution. The
[Luna/max completion handoff](../../../luna-max-completion-handoff.md)
records the exact remaining execution sequence.

The cases isolate the positive-mass bolt body, add its six free REF/ROT
coordinates through the original equations, and then add its zero-density rigid
nut carrier. They retain the reviewed geometry and apply a small, declared
rotational body-force history. All physical displacement and velocity fields,
all six mapped controls, carrier motion, mass, volume and energies must be
checked at every accepted state. Physical direct/mapped agreement alone cannot
validate the intended mapping when the control coordinates are free.

The [independent mass reference](parent-mass-reference.json) uses the pinned
four-point C3D10 mass quadrature. The [finite rigid reference](parent-rigid-reference.json)
solves the corresponding discrete constrained-rigid Newmark problem at high
arithmetic precision; it is not the elastic finite-element solution. The
[field comparison](parent-rigid-deviation.json) quantifies finite-rotation
departures from the linearized reference over all bolt nodes and fitted
controls. The [proposed acceptance limits](acceptance-proposal.json) are
pre-run qualification criteria, not a proof that the elastic response must
meet them.

Preflight found that the draft exponential CLOAD values exceeded the pinned
solver's 20-character numeric field. The corrected values now fit that field;
the [independent input audit](parent-input-audit.json) checks all 22,696 load
components against an independent mass calculation, with maximum difference
1.40e-21 N. It also verifies source coordinates, connectivity, the original
equations and separate body/carrier totals requests. Original
source files remain unchanged. The pinned source's printed quadrature weight
also differs from exact 1/24 by approximately 8e-15 relative; that representation
difference is separately bounded in review. The producer now uses the native
source weight; the independent parent reference retains exact 1/24.

Parent owns readiness, the immutable freeze and serialized execution. The
runner limits each case to one CPU, 1 GiB, 120 seconds and 64 MiB of native
output. This method fixture covers one current map and one small rotational
forcing. It does not qualify the other maps, general rotation histories,
physical thread compliance, current-joint contact or joint capacity. It does
not alter any full structural-criterion disposition or authorize physical work.
