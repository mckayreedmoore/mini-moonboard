# Finite saved-state panel diagnostics

The new [consumer](../../../../../scripts/thin_bolted_finite_panel_consumer.py)
extracts panel diagnostics from one admitted finite field. It reuses the frozen
finite plate, projected-ring port and generic screw-reference helpers. It does
not rebuild CAD, prepare an energy quadrature, assemble stiffness, or solve a
response. The [method receipt](finite-panel-consumer-method-v1.json) binds the
source bytes and 24 focused fixtures. No candidate field or resistance pass is
issued by this method packet.

## Admission and identities

`evaluate(field_path, samples=41, *, admission_sha256=...)` requires the exact
`thin_bolted_finite_frame_response/v1` schema and a caller-supplied 64-character
SHA256 for `scripts/thin_bolted_finite_state_audit.py`. Only that module's
`audit_finite_state` entry point and its
`independent_finite_current_support_load_and_equilibrium_checks_pass` key can
admit a field. Missing, malformed or changed gate hashes fail. An old reference
field fails before any gate import.

The file is read once into immutable bytes. Both JSON decoding and the gate
use those same bytes; the receipt must return the exact payload hash, state,
case, accessory placement and gate-source hash. The consumer checks source
pins before and after evaluation and rejects a changed field path at the end.
It retains all 66 screw identities, all six panel maps, their disjoint saved
coefficient indices, and both generalized load corrections per panel. The
output keeps the original identities and includes the chosen audit hash.

The map reader uses the saved midsurface origin, axes, cubic knots, dimensions,
CAT23/32 thickness and twist scale. `MappedFinitePanel` can replay the frozen
current point/director and rigid-generator methods, but its internal response
and load-preparation methods reject calls. An optional
`reconstruct_load_corrections` utility prepares only the retained mass measure
for an independent admission check; it does not assemble K or query CAD.

## Simultaneous current screw actions

Each screw is checked at its admitted projected-ring panel port. Its outward
unit director and current point must agree with the exported coefficient
field, and the two body forces must be opposed. Withdrawal/head demand is the
signed receiver force projected on that current director, with only numerical
roundoff clamped at zero. The projection must agree with the same action's
axial spring scalar. Lateral demand is the norm of the simultaneous force in
the current tangent plane. The output also retains its two current material
tangent components, world force, current points, and the spatial couple on the
panel. A director couple is not assigned a screw or head moment capacity.

The frozen generic references remain unchanged: the retained nominal #10
withdrawal scenario uses ESG 0.50 and gross geometric embedment; the APA Group 1
head reference uses the owner-reported 9 mm head and CAT23/32 sheet. Effective
thread embedment, delivered head/body geometry and Hillman 42605 resistance
remain unmeasured or unsupported. The mean projected ring pressure does not
establish conical indentation, punching or edge capacity. These distinctions
follow the recorded [APA panel references](https://www.apawood.org/guides-tools-training/technical-document-library/technical-guides/panel-design-specification/)
and [AWC NDS material](https://awc.org/resources/2024-nds/), rather than a
manufacturer qualification for the purchased screw.

## Finite panel measures

For the deformed midsurface `r(x,y)` in the original material coordinates, the
consumer reuses the exact Green metric strains and covariant curvatures from
the frozen [finite plate method](finite-plate-method-v4.md):

`epsilon = [(.5*(r_x*r_x-1)), (.5*(r_y*r_y-1)), r_x*r_y]`

`kappa = [-n*r_xx, -n*r_yy, -2*n*r_xy]`.

The energy and six conjugate section resultants are per reference area/width,
with the original horizontal grain direction. Principal Green strains and
principal current curvatures are reported as applicability markers without a
new limit. The conditional APA zero-Poisson section energy remains a proxy,
not an authenticated finite plywood laminate law.

If `G` is the energy gradient with respect to
`[r_x,r_y,r_xx,r_xy,r_yy]`, the reported variational forces per reference width
are

`T_x = G_x - d_x(G_xx) - .5*d_y(G_xy)`

`T_y = G_y - d_y(G_yy) - .5*d_x(G_xy)`.

The spatial derivatives use the analytic local Hessian and exact cubic third
derivatives. This symmetric mixed-derivative split recovers the retained
linear Q at small strain. Its normal component is a variational transverse
force diagnostic; it is not an established through-thickness rolling stress.
Energetic conjugacy and covariant measures are consistent with the primary
[Kirchhoff–Love formulation](https://arxiv.org/html/2008.05254v2), while that
paper's full through-thickness constitutive formulation is not implemented by
the present APA proxy.

At intact full-thickness sample points, the consumer compares the saved proxy
resultants with the retained linear APA Group 1 CAT23/32 section targets. The
result is explicitly a `conditional_reference_constitutive_index`, not a
finite capacity utilization. Bores, conditional 9 mm seats and the kicker
bevel are excluded from these full-section comparisons. Samples do not resolve
local free hole boundaries, hold footprints, net-section stress, contact
pressure or edge reactions. The default 41-by-41 sample field is not a
convergence study. CD1 is the base comparison; conditional CD1.6 remains the
wind/earthquake scenario only, with permanent duration and creep separate.

Both `retained_rigid_RHS` and `reference_port_alignment` corrections retain
their exact local generalized vectors. Their potentials are `-f*q`, and the
current rigid-generator dual recomputes each equivalent force/moment wrench.
They are reported separately as generalized terms without invented physical
tractions. Finite assembly equilibrium must include both terms through the
new admission gate.

## Focused checks and use

Twenty-four fixtures pass. Analytic coupons cover exact uniaxial Green strain,
20-degree common rigid motion, the known linear transverse-force limit,
independent spatial gradient differences, nonzero-warp objectivity, and
simultaneous current-direction screw projection. The remaining checks cover
the two correction potentials/current wrenches, saved mass/alignment vectors,
forbidden stiffness/load assembly, all malformed admissions and old fields,
and immutable payload selection under a changed path. Ruff passes on the two
new Python files. The receipt records observed numeric coupon differences.

```sh
UV_CACHE_DIR=/tmp/mini-moonboard-uv-cache OPENBLAS_NUM_THREADS=1 uv run --offline python -m pytest tests/test_thin_bolted_finite_panel_consumer.py -q
UV_CACHE_DIR=/tmp/mini-moonboard-uv-cache uv run --offline ruff check scripts/thin_bolted_finite_panel_consumer.py tests/test_thin_bolted_finite_panel_consumer.py
```

After the parent independently freezes the new gate and admits a finite field:

```sh
UV_CACHE_DIR=/tmp/mini-moonboard-uv-cache OPENBLAS_NUM_THREADS=1 uv run --offline python -m scripts.thin_bolted_finite_panel_consumer --field FIELD.json --out NEW-OUTPUT.json --admission-sha256 FROZEN-GATE-SHA256
```

The output file must be new. Every release flag remains false; full panel
resistance, Hillman capacity, finite response/contact convergence and local
aperture/seat/hold behavior remain separate evidence.
