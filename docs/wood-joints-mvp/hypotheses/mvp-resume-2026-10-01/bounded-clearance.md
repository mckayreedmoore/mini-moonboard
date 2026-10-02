# Finite clearance certificate for the terminal A12 rear state

The completed `two-receiver-frame-attempt02` packet has **bounded, nonunique
seating motion at fixed force**. It does not exhibit an unbounded mechanism
within that fixed-force set. Its four unconstrained linear directions are
global-Y translations of the two center post cleats and two center principal
cleats. The actual circular holes and inactive contact inequalities bound those
translations. The force-bearing rank remains **296/300**, including when the
actual circular-law tangent stiffness is used. The original rank gate remains
unsatisfied.

This is one calculation on the saved, unaccepted `a12-rear`, `gap_scale=1`
iterate. It neither recalculates frame forces nor replaces the retained
six-joint baseline. Complete-joint, formal, native, frame-state and physical
acceptance flags remain false. The selected candidate and its evidence are
unaffected.

## Consumed state and unchanged laws

The parent packet was complete and its run had ended before this calculation.
Its `producer.py.snapshot` matches the producer hash in `stop.json`. The saved
`f`, `q`, and `a` were consumed directly. Reconstructing the lumped operators
with the existing `simple_frame.lump_floor` gives exactly the saved `q` through
`q = D a + e - H f`; the maximum reconstruction difference is **0 mm**.
Only the files needed for this calculation are pinned; their hashes are also
stored in `bounded-clearance-attempt01/result.json`.

The 88 independent candidate bolts retain their saved circular gaps: 68 at
1.15 mm, 16 at 0.95 mm, and four corrected top-side bolts at 1.0625 mm. The four
continuous candidate bolts and twelve retained frame bolts keep their original
zero-gap laws. All 66 Hillman axes retain 132 lateral and 66 axial components
at the frozen **2689.678816784642 N/mm**, conventionally displayed as
2689.679 N/mm. No hardware capacity is inferred from that conditional stiffness.

The consumed parent audit and independently reconstructed state quantities are:

| Quantity | Value |
| --- | ---: |
| Maximum body force imbalance | 5.2581e-12 N |
| Maximum body moment imbalance | 1.1715e-8 N mm |
| Maximum finite-law error | 3.0718e-7 N |
| Maximum circular-law error, parent audit | 6.8507e-10 N |
| Held floor motion, parent audit | 1.7369e-13 mm |
| Released floor tangent force | 0 N |
| Maximum positive normal motion | 0.6829382 mm |
| Force-bearing row rank | 296 |
| Actual active tangent rank | 296 |

There are 470 active and 778 inactive unilateral rows, six bearing floor
footprints with twelve held tangents, 26 force-bearing circular pairs and 62
free circular pairs. The largest force in a free pair is 1.7441e-12 N, numerical
zero under the existing 1e-4 N force tolerance. All free pairs lie strictly
inside their actual disks; the smallest radial margin is 0.00102579 mm.

## Equations and finite bound

Holding `f` and `e` fixed also holds elastic deformation fixed. For a rigid
coordinate increment `delta_a`, compatibility therefore gives

```text
delta_q = D delta_a.
```

Let `E` contain the rows of `D` for ordinary bilateral finite laws, positive
unilateral laws, force-bearing circular pairs, and held floor tangents.
Free circular pairs are excluded. Positive-force circular laws have an
invertible force-to-motion relation, so both motions are fixed when their
force vector is fixed. The 706 fixed rows give

```text
E delta_a = 0,
delta_a = N z,       N has 300 rows and four orthonormal columns.
```

The maximum fixed-row residual `abs(E N)` is 2.7951e-16. Row normalization is
used for this SVD only. The relative rank cutoff is 1e-11: the smallest retained
singular value is 0.00778505, while the largest discarded value is 6.3032e-16.
The rank separation is substantial.

For each inactive unilateral row and each free circular pair, respectively,
the required geometry is

```text
q_i + (D N z)_i <= 0,
||q_pair + D_pair N z||_2 <= g_pair.
```

The LP uses the circumscribed component box

```text
-g_pair <= q_pair + D_pair N z <= g_pair
```

as a **conservative outer set**. Inequality right-hand sides are enlarged by
1e-8 mm to accommodate the recorded numerical motion tolerance. Every exact
disk-feasible increment is in this outer set. Finite bounds on the larger set
therefore bound the disk set. Box vertices are never admitted as circular-law
states.

Minimizing and maximizing each of the four `z` coordinates gives:

| SVD coordinate | Minimum, mm | Maximum, mm |
| --- | ---: | ---: |
| 0 | -1.347612 | 1.457205 |
| 1 | -1.408863 | 1.501227 |
| 2 | -0.780042 | 1.567466 |
| 3 | -0.341926 | 1.172065 |

These displayed endpoints are rounded outward. The basis is arbitrary; the
physical movement bounds below are easier to use. Every coordinate has finite
extrema. For each maximum, the retained LP dual supplies `y >= 0` with
`A.T y = c`, establishing `c.T z <= b.T y`; minima use `-c`. All eight dual
vectors and the outer-set extremizers are retained in `certificate.npz`.
Their maximum dual residual is 3.0532e-16 and maximum primal inequality
violation is 8.8818e-16 mm. This is a floating-point certificate at stated
tolerances, with formal acceptance false.

A physical recession direction would require `E d = 0`, nonincreasing inactive
unilateral motions, and `D_pair d = 0` for every finite disk. The finite
coordinate bounds exclude such a nonzero direction in this fixed-force set.
For a single mode the same hole geometry is the elementary quadratic

```text
||u + t v||_2^2 <= g^2,
(v.T v) t^2 + 2(u.T v)t + (u.T u - g^2) <= 0.
```

Any pair with `v != 0` limits travel to a finite interval. No infinite travel
is assigned to the interior of a finite hole.

## Physical seating increments

All significant null motion belongs to four global-Y translations. Other body
translations are below 1.7e-15 mm and all rotation bounds below 2.3e-17 rad,
numerical zero in this calculation. Bounds below are **increments about the
saved iterate**, not absolute positions or total frame deflections.

| Cleat | Global-Y increment, mm | Conservative maximum translation increment, mm |
| --- | ---: | ---: |
| `center_post_cleat_left` | [-0.563762, 1.133107] | 1.133107 |
| `center_post_cleat_right` | [-0.694021, 0.958548] | 0.958548 |
| `center_principal_cleat_left` | [-1.058218, 0.466348] | 1.058218 |
| `center_principal_cleat_right` | [-0.086724, 0.851756] | 0.851756 |

The common-datum translation differences between each cleat and its header
and post/principal receiver have the same bounds to rounding. Datums and all
body/interface component bounds are retained in `result.json`. A common-datum
map uses each body's physical-node centroid and
`delta_u(p) = delta_t + delta_theta cross (p - centroid)`;
the last three saved rigid coordinates equal `1000 * theta`.
Because forces remain fixed, the elastic contribution does not change.

The external-work projection `W.T N` gives an outer-set work-increment range
of **[-5.1942e-13, 5.7246e-13] N mm**, numerical zero. Gravity and the other
saved loads therefore do not drive these four seating directions at this state.

Nonuniqueness is demonstrated by shortening an outer LP extremizer until its
segment obeys the actual disk equations, then taking half that travel. The
retained witness changes the four cleat Y coordinates by approximately
`(+0.0743862, +0.0629267, -0.0694698, -0.0056933) mm`, in the table order.
Its rigid-coordinate increment norm is 0.119798 mm, fixed-law motion change is
2.8325e-17 mm, and every free pair remains inside its disk. The smallest disk
margin is still 0.00102579 mm; the maximum inactive unilateral motion is zero.
`disk_witness_delta_a` and `disk_witness_q` retain the witness. It is explicitly
marked as an unaccepted frame state.

## Tangent stiffness, uniqueness and acceptance

For each force-bearing circular pair with equal component stiffness `k`,
radius `r > g`, and unit vector `u = q/r`, the actual tangent is

```text
K_pair = k * ((1 - g/r) I + (g/r) u u.T).
radial stiffness = k,
transverse stiffness = k * (1 - g/r).
```

Counting both component rows as equally stiff would overstate transverse
support. The smallest actual transverse stiffness here is only
**0.13604484 N/mm**. The certificate uses the square roots of the actual
radial/transverse stiffnesses in a separate 300-column SVD, together with
ordinary active finite laws and held floor constraints. Its rank is still 296;
its smallest retained singular value is 0.410807 and largest discarded value
2.8925e-13, against a cutoff of 3.8207e-8. Neither SVD conceals an additional
lost direction in this state.

Static balance and the finite laws are satisfied, but displacement is not
unique and strict active tangent stability is not established. The four modes
are neutral seating motion while their bolt pairs remain inside the holes;
their finite travel bounds do not establish complete-joint resistance, behavior
after seating, dynamic stability, or stability under a different load or floor
branch. No result for another case is inherited.

The parent can attach this certificate to a proposed conditional state while
preserving false acceptance flags and reporting bounded free play explicitly.
It must not silently waive rank 300, label the iterate unique, or replace the
retained baseline. The certificate remains active for parent reuse; the
upstream terminal and baseline packets remain retained. No raw packet is
archived or pruned here.

## Reusable calculation and evidence

[`bounded_clearance.py`](bounded_clearance.py) exposes:

```python
report, arrays = finite_clearance_certificate(
    D, q, f, k, unilateral, floor_normals, floor_tangents,
    clearance_targets, clearance_gaps, W,
    movement_maps=maps,  # Optional matrices mapping delta_a to observables.
)
```

The callable requires the caller's state to satisfy the original balance,
finite-law, floor and positive-domain gates. It calculates fixed-motion and
actual-tangent ranks, all null-coordinate extrema, dual bounds, observable
movement bounds, and external work. For an unbounded LP it recovers an explicit
recession vector, checks that it fixes active motions and disk coordinates,
and returns that vector rather than a bounded certificate. No frame solver,
force update, native execution or CAD operation is called.

The completed calculation used Python 3.12, NumPy 2.2.6 and SciPy 1.15.3 from
the existing cached environment. OSQP 1.0.4 is needed only to import the
existing `simple_frame` module; its solver is not called. The command is:

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 \
  uv run --offline --no-project --python 3.12 \
  --with numpy==2.2.6 --with scipy==1.15.3 --with osqp==1.0.4 \
  python docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/bounded_clearance.py
```

The default output is the owned, ignored `bounded-clearance-attempt01/`.
Existing output is preserved; replay requires an empty output location at that
same path. The completed run made 2,012 small LP calls on four variables, plus
the two SVDs with 300 columns. No tests, native/frame solve, CAD rebuild,
staging, commit or subagent work occurred.

| Artifact | SHA-256 |
| --- | --- |
| Parent `stop.json` | `d9b56a73f18599e4776c9a46e8c606ea0b5e37697589edd4093fb00f1d1bf9b8` |
| Parent `unaccepted-iterate.npz` | `81a2fc6abcb777cded9fb673e0bd5f150d551f9459c08f62b4b48de78f3e6c23` |
| Parent producer snapshot | `c13c67d70621cd3294618f83bb065158f59e588cc1ba3d71e92adc5551cecd55` |
| Frozen `operators.npz` | `f40bf53412afb400df23ff108e90bac66db3c493da26a19af5c05de329c165ad` |
| Frozen `row-identities.json` | `bec1feb75be61b321220a047a652cc42f09c4c11d1d3c66377c4035bde4826d5` |
| Frozen `model.json` | `d17dadd7c999e4a1634f53226cf63e131f547cd9cf5d46d87d75c935f2dc807e` |
| Retained six-joint `comparison.json` | `ec69b49c821a56fdde76d94148405f9f743e4f72add17c89d35af512be76f6a3` |
| Retained six-joint `response.npz` | `aa70480aa18c33bb1cbd7d3a53ff582a0c7a90c93487f92721619474ec251901` |
| Certificate producer snapshot | `35c0ceb7609c7ff77118ddf0a8e9f0da681ae41ad3396e4a95a71792724a9c7b` |
| `certificate.npz` | `b8741ef67c37b202beee005734f1d37270c2ee94f0f8a3dac06835e6e50440aa` |
| `result.json` | `10c6105f34656efa5f72d30951a3018ae4d3bf5f23c28c337d713317f5f1c521` |

The ignored certificate, report and producer snapshot total 360,384 bytes.
They contain reproducible numeric evidence rather than additional mesh or
solver exports. Initial dependency/rounding stops happened before either SVD
or any LP; their details are retained in `startup-stops.json` beside this
completed calculation.
