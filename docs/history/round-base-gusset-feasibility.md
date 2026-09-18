# Bounded feasibility: restore a designed bolted base gusset

A bolted plywood gusset offers a standard calculation path that avoids assuming
an unlisted commercial-angle rating. **The historical gusset cannot be restored
unchanged on the current single 2x6 rim.** This is a feasibility study, not a
hardware change or construction detail. Current replacement demands are pending.

## Historical dimensions and actual load path

[`timber_frame.py`](../mini_moonboard/timber_frame.py) defines one outside
plywood plate per side, 460 mm high, 285.75 mm front-to-back and an assumed
19.05 mm thick, face grain vertical. Its world envelope is `z=20..480 mm`,
`y=-321.75..-36 mm`; the inner plate face is at `x=±1219.2 mm`.
Four 3/8-16 × 3-inch bolts per plate connect two distinct timber members:

| Bolt group | Historical Y, Z axes (mm) | Timber receiver |
| --- | --- | --- |
| Upper pair | (-80, 300), (-80, 380) | Outer rim |
| Lower pair | (-100, 100), (-240, 100) | Outer post |

This joins **rim to post**, bypassing the header, rather than replacing the
rim/header angle with an equivalent two-member connector. Header compression
bearing and the other header connections remain. Uplift must continue through
the revised whole assembly; a gusset does not anchor the post to the floor.

All four nominal 9.525 mm shafts fit the current raw timber. However, projection
onto the current rim's depth axis puts the upper historical bolt only
**10.573 mm from its rear edge**, versus 61.996 mm for the lower bolt. The old
upper axis was inherited from a deeper rim. The rear post bolt is only 30.95 mm
from the present post's rear edge. Shaft containment is not a spacing pass.

One bounded starting arrangement for a later fit/design pass is rim axes
`(-80,295), (-80,335)` and post axes `(-100,100), (-220,100) mm`, mirrored in X.
It gives a 40 mm upper bolt separation, about 39.50 mm minimum rim depth-edge
distance and 50.95 mm rear-post edge distance. These are nominal geometric
distances, not an NDS layout acceptance or completed collision check. Keep the
original plate envelope initially and use the owned plywood's actual thickness
instead of assuming 19.05 mm. Do not drill these provisional coordinates.

## Standard equations make the lateral check finite

[AWC TR12](https://web-media.awc.org/wp-content/uploads/2021/12/17210714/AWC-TR12-1510.pdf),
Table A1, provides plywood dowel bearing `Fe=5600 psi` for bolts over 1/4 inch,
without requiring Structural I or all-Douglas-fir veneers. This is a useful
published basis for the owned AC plywood's **bolt bearing**, not its panel
shear or washer pull-through. TR12 Table 1-1 supplies the single-shear yield
equations; reference resistance is the smallest yield value divided by its
applicable reduction term. Actual geometry, service adjustments, group effects
and member limit states remain separate.

The existing [`single_shear`](../fea/dowel_yield.py) implements those equations.
An illustrative input uses 1.5-inch timber, 23/32-inch plywood, timber
`Fe=3650 psi`, plywood `Fe=5600 psi`, 0.298-inch bolt root throughout and assumed
`Fyb=45000 psi`, with zero gap. Its conditional reference is **136.878 lbf per
bolt**, governed by mode II using the existing conservative reduction terms.
This number is not adjusted group resistance: steel identity, delivered section,
load angle, end-use factors and the final bolt layout must be resolved.

For an equal-stiffness in-plane group with centroid-relative positions
`r_i=(y_i,z_i)`, distribute its own interface force and moment as
`f_i=F/n + Mx*(-z_i,y_i)/sum(y_j²+z_j²)`. Check the vector load angle for each
bolt; assess upper and lower groups separately. This is a mechanics assumption
to validate, not permission to divide load equally despite eccentricity.

## What this fixes, and what still needs calculation

Through-bolts supply a defined in-plane uplift path through dowel bearing and
plywood, while separated axes can resist the in-plane couple `Mx`. Their
resistance need not come from an ML24Z moment table. The new geometry must still
carry the **entire simultaneous wrench**. Out-of-plane force `Fx` and moments
`My/Mz` require bolt axial forces, washer bearing/pull-through, plywood bending
and contact; an in-plane shear-only gusset calculation cannot carry them by
assertion. One outside plate is a single-shear connection with eccentricity.

Adding an inside plate is not an automatic double-shear solution. A matching
full inside rectangle intersects the continuous header at `z=186.9..225 mm`.
Cutting a full-width header notch would disconnect that plate's upper and lower
portions unless a separately sized bridge remains outside the header envelope.
Both plates' fit and actual sharing would need design; do not double the
single-shear value or introduce an unmodeled built-up vertical member.

Finite remaining work for this alternative:

1. Solve the revised rim-to-post load path with compression-only header bearing
   and explicit installation/floor assumptions; recover forces at both groups.
2. Check NDS bolt edge/end/spacing, group action, grain-angle bearing, timber
   splitting and net sections using the final axes. Plywood does not eliminate
   cross-grain forces in the timber.
3. Check gusset net-section tension, in-plane shear, compression/buckling and
   out-of-plane bending with the applicable sanded-AC panel properties; check
   bolt axial/combined loads and adequately designed washers or bearing plates.
4. Verify bolt grade, thread/shear-plane geometry, grip/length and full hardware
   access against existing screws, bores, header and panels; release one exact
   drawing only after those checks pass.

The [owned-material record](round-material-led-verification.md) establishes the
AC-fir product direction. [APA's plywood guidance](https://www.apawood.org/engineered-wood-products/plywood-osb/plywood/)
identifies separate directional panel strength properties; a roof/floor span
rating is not a gusset calculation. This alternative is calculable using
conventional connection and panel design, but it does not yet close the base
construction-release gate and does not inherit the removed angle's demands.
