# Timber consumption of physical shaft actions

The [frozen method receipt](timber-common-shaft-method-v4.json) issues a new
consumer for one independently admitted 132-body physical-shaft state. Its
fourteen known-answer fixtures and Ruff checks pass; independent review found
no remaining concrete contract issue. No candidate state has been consumed.
The failed first 132-body attempt has no recovered actions and cannot be used.
All eighteen completion gates and all physical releases remain open.

The producer is
[`scripts/thin_bolted_timber_common_shaft_checks.py`](../../../../../scripts/thin_bolted_timber_common_shaft_checks.py),
SHA256 `c27d8d0209f2b0a032c490314fe05cee8fbc949f608dabbf813676c044b90cc7`.
It uses the corrected export gate, SHA256
`26feb3bb369490729c6f8e48365d816cbda458b2fdeea89a97b8286842d1be58`,
and reuses the issued steel port and shaft-cut reduction APIs. The receipt
pins these dependencies and its fixtures. Preserve their frozen bytes.

The consumer requires seventy shafts, 308 actual radial bearing points and
140 own head/nut capture ports. It independently reproduces eighty-two wood
bearing wrenches, including every actual force arm and free couple. Each wood
capture uses its own host support datum; the shaft pressure datum remains
separate. The seventy-two flange aliases and seventy physical shaft cut
tables are independently checked through the reused steel methods. Every
aggregate and consumed cut binds one case, accessory placement and complete
parameter state. The released input is read as one byte payload and rehashed
before return.

Finished bearing intervals, signed boundary probes and the existing 1,050
section areas/stations are reused. New member meshes must preserve the twenty
authenticated centerlines, bases and complete nonoverlapping extents; interior
refinement is allowed. Only these unchanged geometry fields are selected
from the preserved corrected-floor state. Its forces, displacement and
acceptance are not selected. No CAD query, reconstruction or solve occurs.

The output preserves each radial point's signed grain angle, a body/root
diameter sensitivity for the NDS dowel-bearing material parameter, and each
own direct-wood capture beside its ideal Fc-perpendicular annulus reference.
Foundation patch average pressure divided by NDS `Fe` is a material diagnostic,
not an allowable local bearing utilization. Actual `Dr`, `Fyb`, product
conformity and delivered thread transitions remain unverified. Unequal
distributed shaft forces and couples are retained; equal/opposite six-mode
or symmetric four-mode capacities are not inferred from them.

Simultaneous signed force and moment vectors are recovered at the saved member
stations using the current point/capture/contact actions and mass-preserving
affine selfweight. Separate component selectors retain each selected cut's
complete vector. Average axial `Ft`/`Fc` references use CD1, with conditional
CD1.6 arithmetic only for an authenticated live-load case and CD0.9 arithmetic
for a permanent-only case. No duration increase is applied to washer bearing.
Exact centroid/inertia and linear normal stress can subsequently use the
[targeted section method](timber-section-method-v4.md) at parent-selected
saved stations. Shear, torsion, local fracture, stability and complete adjusted
member resistance remain separate.

The reproduction API is
`consume(field_path, released_sha256)`. After the parent releases a converged
field that passes the corrected independent support/load/equilibrium gate,
run:

```sh
UV_CACHE_DIR=/tmp/thin-timber-uv-cache uv run python -m scripts.thin_bolted_timber_common_shaft_checks \
  --field PATH --field-sha256 RELEASED_SHA256 --out DISTINCT_RESULT_PATH
```

The result path must be new. Exact missing inputs include formal oblique
end/edge classification and actual connected fracture surfaces; distributed
wood-bearing and shaft yielding; actual washer pressure and metal spreading;
head/nut/thread/prying resistance; first-order finite-motion applicability;
and complete case coverage. This receipt issues the consumer method, with
complete joint acceptance and fabrication/climbing release false.
