# Straight annular compression column

**Conditional local static witness only.** The proposed four knee-spine `v`
ties admit an exact equilibrium field through their washer annuli, provided
the two end faces use the same bounded normal-pressure profile. This does not
close splitting resistance for all 30 duties or establish a complete-joint
pass. The producer is prepared but has not been executed here; parent owns
engineering runs and integration.

## Exact field

Use local coordinates `(g,u,v)`, with `g` along grain and `v` along the
through-bolt. Let `p(g,u) ≥ 0` be the washer's normal pressure on either end
face. Extend that same pressure unchanged through the sound annulus along
`v`:

```text
sigma = -p(g,u) e_v ⊗ e_v in the annular column; sigma = 0 outside it
```

Because `p` is independent of `v`, `div(sigma)=0`. Annular side normals have
no `v` component, so the inner and outer cylindrical walls carry zero
traction, including at the pressure-profile boundaries. The two end faces
carry exactly the inward washer tractions `+p e_v` and `-p e_v`. Equal,
concentric pressure maps give equal and opposite resultants, zero pair moment,
and section resultant `N_v=-T` at every interior `v` cut. The field carries no
shear, torque, or moment about the bolt axis. This is an exact statically
admissible continuum field for the stated end tractions; it is not an elastic
compatibility solution.

About the spine-local `(g,u)=(0,0)` reference, its signed six-component cut
wrench in order `[N_v,V_g,V_u,M_v,M_g,M_u]` is
`[-T,0,0,0,-uT,+gT]`; the last two entries retain the axis offset and are
not bolt-axis bending moments.

This construction avoids assigning an invented plug-shear or splitting
capacity to the column. Its only local material screen is the maximum
perpendicular-to-grain compressive pressure against the already-recorded
`Fc_perp=4.309223308230226 MPa`. A washer-area mean is not a peak-pressure
bound.

## Geometry certificate basis

The receipt-bound proposal uses spine stock `276.3 × 38.1 × 139.7 mm` and
four proposed axes at `(g,u)=(100,0)` and `(250,0) mm` on each spine. Washer
hypothesis is `25.4/8.3058/2.5 mm OD/ID/thickness`; proposed bore radius is
`3.75 mm`. The annular area is `452.52575506508134 mm²`.

The producer recomputes finite axis-segment distances from the saved six-bore
geometry, checks the full proposed through-bore interval, both washer centers
and signs at each spine, plus annulus containment on the rectangular stock
faces. Frozen geometry gives these limiting clearances:

| Check | Minimum clearance |
| --- | ---: |
| Annular column to an original perpendicular `u` bore | 7.462447 mm |
| Annular column around its own 7.5 mm `v` bore | 0.402900 mm radial gap to washer ID |
| Column outer disk to `u` stock faces | 6.350000 mm |
| Column outer disk to nearest `g` stock face | 13.600000 mm |
| One annular column to the other | 124.600000 mm |
| One annular column to the other proposed bore | 133.550000 mm |

The four original bore centers are `g=31.75, 73.8, 191.61555301851,
226.08755295886 mm`; all four finite cylinders are checked against each
column's complete swept outer envelope. Both `v` end faces are intended
washer lands and match the saved supported-annulus area. These are model
clearances, not inspection of wood, holes, or washers.

## Pressure profile and numerical demand

The fresh knee replay has 12 body/case states and 24 tie tensions at the
already-included `1.25` force margin. Its maximum is `1038.9839065627812 N`
on the left spine in `a12-forward`, bridge 2. The saved washer-contact
envelope is `1060.6566047532085 N`, concentric with `M=0`, and already includes
the same margin. Its finite contact model has full-annulus wood contact and
positive homogeneity over the lower replay tensions.

The uniform mean at the fresh replay peak is `2.2959663509392003 MPa`
(`0.532803` of `Fc_perp`); that mean alone does **not** establish the local
screen. The saved washer state reports a quadrature pressure peak of
`2.610038 MPa` at its envelope tension and an inner-edge sample of
`2.610453 MPa`. Both are below the reference, but sampled values alone do not
prove a continuous maximum.

[`anchorage-column.py`](anchorage-column.py) authenticates the replay,
original normal allocation, washer result, and receipts. It reconstructs the
stored M=0 radial washer-contact polynomial without rerunning its solve,
finds each polynomial's stationary points, checks its continuous finite-model
pressure maximum, and scales that **same** profile to each of the 24 replay
tensions. It also checks full-annulus force and zero first moments. A generated
profile is usable only within the saved washer/contact assumptions; no actual
installed pressure or physical wood capacity follows.

API: `build(output)`. Use a fresh child of
`all-joint-splitting/rawlocal/anchorage-column/`:

```sh
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
  .venv/bin/python docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/all-joint-splitting/anchorage-column.py \
  --output docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/all-joint-splitting/rawlocal/anchorage-column/attempt01
```

The built-in 100 N uniform-annulus coupon checks area, end-force balance, and
the zero net end-pair wrench. Its signed end wrenches are
`[+100,0,0,0,0,0]` and `[-100,0,0,0,0,0]` about the centered reference; its
section stress resultant is `[0,0,-100]` in local `(g,u,v)` coordinates. It
is arithmetic only. The producer reports a local conditional field; it never
sets `complete_joint_acceptance` or `physical_release` true.

## Use with fresh complete demand

Count each load-induced steel tension once. The `1.25` factor is already in
the replay forces; no preload, friction, or extra capacity is available. For
a fresh complete stress map, use this field as its normal washer-transfer
component only when both washer lands carry this same bounded `p(g,u)` map.
Combine it with complementary stresses that exclude that transfer. If the
complete model already includes those washer tractions, partition or replace
that component; do not superpose it again.

At every shared cut, recover the signed full
`[N_v,V_g,V_u,M_v,M_g,M_u]` wrench once, using the local spine origin stated
above. The column contributes `[-T,0,0,0,-uT,+gT]`; thus its force is only
`-T` in `N_v`, while its eccentric moments are retained explicitly. All
other member, contact, gravity, shear, torque, and residual moment demands
remain in the complete calculation. Existing replay `wood_wrench(q,T)=q-T`
is already residual after tie allocation. Do not subtract or add that `T`
again. The resulting pointwise combined stress field still needs every
applicable complete-joint criterion.

For an existing bolt-host stack, use this method only after certifying a
retained-material annulus through that host, no intersecting voids or side
faces, and matching supported pressure distributions at both ends. A
washer-to-wood interface on one side and an unverified host contact on the
other do not satisfy this condition from bolt alignment alone. No current
existing stack is accepted by this packet. The four proposed knee ties do
not transfer a result to the other 26 joint duties or any frame receiver.

## Limits

- The pressure maximum is exact for the saved finite washer polynomial, under
  its `M=0`, zero-gap, no-preload contact assumptions. It is not actual
  washer pressure or a material test.
- The field proves equilibrium for its prescribed end tractions. It does not
  prove elastic compatibility, changed-hole stiffness, washer/nut/bolt
  resistance, adjacent-member load exit, or interaction with the other five
  wrench components.
- Pressure comparisons do not qualify cracks outside the swept annulus or
  splitting in another timber.
- The 108-axis proposal remains separate and unadopted. No geometry change,
  fabrication, drilling, native/frame/CAD run, or physical release occurs.
