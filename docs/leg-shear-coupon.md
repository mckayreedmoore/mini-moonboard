# Actual inclined-leg formulation comparison

The original left leg's 968 C3D10 elements and 16 quadratic floor faces were
tested with both penalty and MORTAR contact. This is a conditional, actuated
coupon, **not a free-standing frame solution or local-contact validation**.
It follows the [sliding cube comparison](contact-shear-coupon.md).

The upper 60 mm node band receives 1,200 N total downward nodal preload,
without gravity. X/Y are held during seating; X then moves 1 mm while Y stays
held and Z stays free. This load is ten times the cube's preload: compare
formulations within the leg pair, not absolute residuals across unlike coupons.
The historical gravity-plus-1,200 N actual-leg study remains untouched.

Ground is the existing 100 mm deep C3D8 brick extending 100 mm past the actual
foot's bounding box on every side. It has E=7,000 MPa and ν=0.3, identical in
both formulations. Only its four bottom nodes are fixed; its master surface
can deform. The complete node coordinates and ground displacements are in the
raw evidence. Contact slopes remain 10,000/100 N/mm³ and μ=0.3. Common maximum
increments are 0.25 and 0.125, with automatic cutbacks.

| Formulation | Increment | Maximum absolute seating moment residual, Nmm | Maximum absolute final moment residual, Nmm | Endpoint global result |
| --- | ---: | ---: | ---: | --- |
| Penalty | 0.25 | 1.315 | 0.240 | Rejected at seating |
| Penalty | 0.125 | 0.476 | 0.429 | Pass |
| MORTAR | 0.25 | 0.230 | 0.141 | Pass |
| MORTAR | 0.125 | 0.689 | 0.314 | Pass |

All four solves completed normally in approximately 5–9 seconds. The unchanged
moment limit is 1 Nmm; force residual and necessary aggregate friction checks
also run at both full-step endpoints. Noncontact bottom SPC reactions and
upper actuator X/Y forces are the external support forces. Applied Z load is
counted once, and every moment uses its deformed location. Free contact-node
RF is never counted as another support.

The foot's mean X displacement is only about -0.006 mm for MORTAR and
-0.008 mm for penalty, despite 1 mm upper travel. This test predominantly
exercises the inclined leg's deformation; it does **not** demonstrate gross
sliding as the cube did. Its passing external balance cannot qualify every
contact law, gap, stress or member-capacity prediction. In particular, wood
Z displacement is not the actual gap against a deforming ground surface.

MORTAR is therefore promising for further qualification, not selected for
the full frame yet. Required next evidence includes active/open local contact
semantics, appropriate weak-law checks, actual gap reconstruction, and further
geometry/mesh/history tests with the same external balance gates.

[Report and endpoint values](../fea/results/leg_shear_coupon/report.json).
[Raw decks, contexts, outputs and launch sources](../fea/results/leg_shear_coupon/solver_evidence.tar.gz).

```sh
docker run --rm --user "$(id -u):$(id -g)" -e OMP_NUM_THREADS=2 \
  -v "$PWD:/work" mini-moonboard-fea:box-v1 \
  python3 -m fea.leg_shear_coupon --max-seconds 60
uv run pytest -q tests/test_contact_shear_coupon.py tests/test_leg_shear_coupon.py
```
