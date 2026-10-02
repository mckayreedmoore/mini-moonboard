# Upper-right corner: local combined bolt and contact response

**2026-10-02 — conditional working model. Complete-joint and physical-release
HOLD remain unchanged.** The calculation preserves the reviewed geometry,
frozen frame forces, existing hardware policy and 47-criterion authority.
It supplies a finite local response under explicit assumptions, not an
adopted joint resistance.

## Decision

All **72 local states balanced**. The largest nominal smooth-shank combined
stress proxy is **267.858 MPa**, or **0.4223** of the retained hypothetical
92 ksi steel comparison. No steel branch exceeds that hypothesis. Derived
head/wood contact moments fit within the declared circular footprints.
This supports the local bolt-transfer scenario under the stated assumptions.

The contact calculation also changes the seat picture: the governing rail
seat's peak pressure is **7.45–8.31 MPa**, versus its unchanged **3.545 MPa**
full-annulus mean. The prior uniform-pressure washer stress cannot be taken
as the stress for this tilted contact state. The modeled washer is rigid and
its actual stress and resistance remain unassigned.

The next useful joint calculation is **a common-host contact response for
the upper-right rail pair**, using the saved rail-interface wrench and
existing cleat-face contact together with these local bolt laws. It should
derive force shares and end moments under one rail pose, while preserving
the present frozen demands as a comparison. This is a finite next check,
not a new requirement for a native program, assembly redesign or external
sign-off.

## Finite scope

The calculation uses all four upper-right axes in each of the six nominal
states of `frame-250-attempt02`. Each bolt is a local beam with wood-bore
contact and two head/nut–washer–wood contact stacks. Its saved lateral vector
and axial tension act together. Three explicitly hypothetical stiffness
branches give **72 local bolt states and 144 end-contact states**.

Local beam/contact compatibility is solved within each bolt stack. The four
host motions are independent responses to preserved individual bolt forces:
they are not constrained to a shared rigid-host pose and do not redistribute
those forces. Thus simultaneous evaluation of both groups is not complete
compatibility of the orthogonal groups or the whole frame. The baseline
frame response remains unchanged.

The existing [uniform-pressure strip worksheet](upper-right-washer-transfer.md)
and [reaction bounds](upper-right-washer-contact-bounds.md) remain separate.
Their prescribed pressures and strip stresses are not copied onto the
loaded contact fields calculated here. Washers in this finite extension are
rigid; **washer bending stress and actual washer resistance remain null**.

## Inputs and reasonable study assumptions

The reviewed cleat is 88.9 × 139.7 × 119.7 mm in its X, T and grain
directions. The two rail axes retain 33 mm pitch; the two side axes retain
67.85 mm pitch. Current geometry comes from
`operators-attempt02/model.json: proposed_corner_axes`, the current raw
interface rows and the fresh corner component packet. Historical inherited
metadata containing a 127 mm rail grip or a quarter-inch side bolt is not
the geometry basis.

| Input | Rail pair | Side pair |
| --- | ---: | ---: |
| Nominal smooth-shank diameter, mm | 6.3500 | 7.9375 |
| Bore envelope diameter, mm | 7.5 | 9.0 |
| Radial clearance at each receiver, mm | 0.5750 | 0.53125 |
| Host / cleat grip, mm | 38.1 / 139.7 | 88.9 / 88.9 |
| Total wood grip, mm | 177.8 | 177.8 |
| Catalog washer scenario | Bolt Depot 2994 | Bolt Depot 2995 |
| Minimum OD / maximum ID, mm | 18.4658 / 8.3058 | 22.0472 / 9.9060 |
| Minimum catalog thickness, mm | 1.2954 | 1.6256 |
| Hypothetical concentric flat head/nut circle, mm | 10 | 12 |

The washer dimensions reuse the authenticated supplier inputs in the
[earlier source worksheet](upper-right-washer-transfer.md#exact-washer-identity-and-dimensions).
Thickness is recorded but not used as a washer stiffness: the present washer
is rigid. The flat circles are hypothetical bearing profiles, not guaranteed
contact footprints of delivered heads or nuts. Both ends use the same
declared profile within a family. Washer offset, asymmetric actual head/nut
profiles and washer bending are excluded.

Other explicit assumptions are:

- Bolt Young's modulus **200,000 MPa**, smooth circular section over the
  entire grip, small strains and small rotations. Thread location, runout,
  local root bending and head fillet effects are not modeled.
- Timber bore and washer-seat stiffness **5, 20 or 80 MPa/mm**. Each branch
  uses the same hypothetical modulus for those two different local contact
  mechanisms. These are exploratory stiffness specifications, not measured
  DF-L properties or code values.
- Hypothetical head-to-washer normal stiffness **10,000 MPa/mm**. Its role
  is an almost rigid bearing face relative to the declared wood seats, not a
  material test or an actual steel contact law.
- Rigid receiver wood outside the distributed bore and seat springs; a fixed
  cleat and independently translating/rotating host for each bolt.
- No preload, friction or contact adhesion. Bore contact acts normal to the
  selected lateral bending plane. No local external host moment is assigned
  about that bolt's interface datum.
- Saved positive axial tension is force-controlled and acts at **each** outer
  washer stack. Each end carries the full tension, not half. Tension-induced
  beam geometric stiffness is retained.

The conditional 92 ksi bolt material value and the fresh timber reference
values remain diagnostics from the source component packet. They are not a
product qualification, a combined-load NDS resistance or a pointwise wood
constitutive law. An elastic branch exceeding its declared material input
cannot be used as a physically elastic prediction.

## Mechanical model

### Bolt and wood bore

For one bolt, let `x=0` be the host outer face, `x=Lh` its interface with
the cleat, and `x=L` the cleat outer face. The beam has eight cubic Hermite
elements per receiver, giving seventeen nodes. Its variables are beam
deflection `w`, section rotation `beta`, host interface translation `u`
and host rotation `phi` in the selected lateral plane. The source lateral
vector chooses that plane. The external host drive is opposite the saved
connector force on that host; scalar `V` is its magnitude.

The beam strain energy is:

```text
Ubeam = 1/2 * integral_0^L [E*I*(w'')^2 + T*(w')^2] dx
A = pi*d^2/4
I = pi*d^4/64
```

The tensile geometric term is the positive-force version of the small-angle
[beam-column model](https://ocw.mit.edu/courses/16-20-structural-mechanics-fall-2002/9fb9073e6163cd6c908b07c42eccd1c5_unit17.pdf).
The adopted sign follows positive axial tension. Euler–Bernoulli theory
omits transverse shear deformation. The [primary beam-on-foundation
paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC7832909/) distinguishes that
assumption from a Timoshenko model and gives the linear Winkler foundation
equations. Neither source supplies a timber connection stiffness or a
capacity. The unilateral gap extension below is this study's assumption.

At each of three Gauss points per element:

```text
receiver_motion = u + phi*(x-Lh) on host; 0 on cleat
q = w - receiver_motion
penetration = max(abs(q) - radial_gap, 0)
Ubore = 1/2 * sum Kwood*d*quadrature_weight*penetration^2
```

The bore spring gives an opposing reaction on the contacted wall. A sample
cannot contact both walls at once. Opposite walls may be active at different
stations along the same bolt. This is a distributed, unilateral spring
model, not a pressure field in a continuum wood block. Local neighboring
bolt effects and splitting are excluded.

### Head, rigid washer and wood seat

Every end has two annular compression-only contacts in series. The head
annulus extends from the maximum washer-hole radius to the hypothetical
flat-circle radius. The wood annulus extends from that hole to the minimum
washer outer radius. Each annulus uses eight radial Gauss points and
32 azimuthal stations.

For a contact with area weights `Ai`, coordinates `yi`, tilt `theta` and
center closure `delta`, the law and force condition are:

```text
pi = K * max(delta + theta*yi, 0)
sum Ai*pi = T
M = sum Ai*pi*yi
W(theta;T) = min_delta [1/2*K*sum Ai*max(delta+theta*yi,0)^2 - T*delta]
```

The center closure is eliminated at the prescribed tension. The washer tilt
`alpha` balances the same moment through both contacts:

```text
Mhead(relative_bolt_tilt - alpha) = Mwood(alpha)
relative_bolt_tilt = beta(0)-phi at host end; beta(L) at cleat end
Uend = Whead + Wwood
```

This resolves nonnegative pressure, contact opening, closure and relative
tilt within the rigid-washer hypothesis. It includes partial contact rather
than assigning stiffness to a zero-force contact. With zero tension
and no preload the end contact has no normal force or moment. A zero-lateral
state may retain neutral bore placement; a minimum-norm representative
position is not a unique motion envelope.

### Equilibrium and diagnostics

Minimize `Ubeam + Ubore + Uhost_end + Ucleat_end - V*u` with analytic
derivatives. The finite production receipt records convergence and residuals
for every source state. A failed equilibrium is a stopped numerical branch,
not an adopted hardware failure and not permission to relax a law.

Recover beam moment `M=E*I*w''` and bending shear `Q=E*I*w'''` at element
endpoints and sampling stations. At the **same station**, report a nominal
smooth-shank stress proxy:

```text
sigma = abs(T/A) + abs(M)*d/(2*I)
tau = 4*abs(Q)/(3*A)
sigma_vm_proxy = sqrt(sigma^2 + 3*tau^2)
```

This is an elastic nominal-section diagnostic; it is not a code interaction
equation. The source's nominal thread tensile area is a separate axial
screen and does not define thread bending properties. Wood-bore pressure
and washer-seat mean/peak pressure remain demand outputs. Comparing them
with retained timber references does not turn a mean bearing reference into
a pointwise failure law.

The reported axial separation includes the signed center closures of both
series contacts, elastic axial bolt stretch, and small-angle shortening of
the bolt's projected length:

```text
required_separation = head_closure + nut_closure + T*L/(E*A)
                      - 1/2*integral_0^L (w')^2 dx
```

It can be negative when a tilted partial contact closes at an edge while its
center opens. Interpenetration of the host/cleat faces, shared-host axial
compatibility and installed seating are not checked by that bookkeeping.
The end labels `end_head` and `end_nut` denote host and cleat ends in this
symmetric-profile study; they do not observe actual delivered head/nut
orientation.

The head/wood end moment is **derived from contact equilibrium**. It is not
assigned `V*L/4`. Internal bolt bending may exceed end-contact moment because
distributed bore reactions act between the ends. For nonnegative pressure
within a centered circular head radius `a`, `abs(M)/T < a` is a necessary
finite-area contact condition; this is checked against the returned contact
field, not used as a bolt bending resistance.

## Source identity

Only the six nominal-gap states are used: `a12-rear`, `a12-forward`,
`a12-left`, `k12-right`, `k12-rear` and `a1-rear`. Source forces retain their
signed components. No new load case or plywood-orientation result replaces
this frozen force source.

| Frozen source, relative to this directory | SHA256 |
| --- | --- |
| `frame-250-attempt02/comparison.json` | `bea6cbc330af3cdb20499d774a8f6bb24481d687c3150adb01ede18e4c1d50ca` |
| `frame-250-attempt02/response.npz` | `0625196497b0dbc7b297724d7b9947f7c7c61bb282cd4d9681705629302c76c7` |
| `operators-attempt02/model.json` | `b5f9b87b70c4a9920372a3443a55e37dfe34351fb9ac8210b299c1360fb93626` |
| `operators-attempt02/row-identities.json` | `cdf218780bdabdb8774174c79b37d7c9f554abc6be2e1f817999635e56868b27` |
| `bolted-replay-results/corner-attempt01/component-results.json` | `401b8876dc3a96b553c847f1029a5a9200ba3f45af5493f64edd61fdc6bc42b6` |

The frozen [current register](joint-register.md) supplies authenticated
interface points, receiver ownership, signed component rows and tie rows;
its machine input hash is
`79db8c6830dee42e47dcdcd75c331ce22a67cd3d27e38f9a8b616e820c37d3ca`.
The producer directly checks that register and its generated outputs, the
model, comparison, response and fresh component packet. It crosschecks each
register force against the exact response array. The present row-file hash
listed above was also checked during worksheet postprocessing; it is
inherited mapping provenance rather than a live producer input. Older
packets are preserved and supply no numerical acceptance here.

## Finite comparison

These are **separate six-case envelopes**. Different entries in a row can
occur on different axes or cases; they are not one simultaneous combined
state. The raw results keep each signed V/T pair and its witnesses.

| Hypothetical Kwood, MPa/mm | Rail peak steel proxy, MPa | Side peak steel proxy, MPa | Rail peak wood-seat pressure, MPa | Side peak wood-seat pressure, MPa |
| ---: | ---: | ---: | ---: | ---: |
| 5 | 214.839 | 267.858 | 7.452 | 3.335 |
| 20 | 166.178 | 186.022 | 8.307 | 4.417 |
| 80 | 129.251 | 137.497 | 7.540 | 4.746 |

The largest sampled bore pressures are **9.332–21.067 MPa** at the rail
host and **8.158–19.112 MPa** at the side host across the three branches.
At the corresponding witnesses they are **0.302–0.683** and
**0.289–0.677** of the frozen directional Fe references. These ratios are
pressure diagnostics, not a dowel design interaction or a continuum bound.

For the middle stiffness branch, the peak steel witness within each case
has the following simultaneous demands. Every row's T, V and stress occur
together; they do not include washer bending:

| Case | Governing axis | T, N | V, N | Peak nominal steel proxy, MPa |
| --- | --- | ---: | ---: | ---: |
| A12 rear | rail_2 | 72.564 | 68.966 | 17.456 |
| A12 forward | rail_2 | 37.907 | 30.063 | 7.903 |
| A12 left | rail_2 | 44.561 | 27.625 | 7.592 |
| K12 right | side_2 | 506.755 | 1097.576 | 184.875 |
| K12 rear | side_2 | 527.959 | 1098.757 | 186.022 |
| A1 rear | side_2 | 7.968 | 6.772 | 1.026 |

At K12 right, rail_1 retains **T=757.336 N, V=535.265 N**. Its host-end
contact moment is **2.347 / 2.795 / 2.397 N·m** at Kwood 5 / 20 / 80.
The middle value requires eccentricity **3.690 mm**, within the hypothetical
5 mm head radius. These end moments are distinct from internal beam bending.
The largest sampled internal moment anywhere is **12.617 N·m**, at
K12 rear, side_2, Kwood 5; distributed wood-bore reactions supply the
intermediate force path.

An important contact sensitivity occurs in the lighter A12-left side_2
state. At Kwood 20 its host-end resultant reaches **0.9756** of the declared
head radius and only **2.47%** of head-annulus quadrature area is active.
This is a mathematically admissible, near-edge contact within the chosen
discretization. It is not a bound on the real local pressure, proof of
retention at an actual bearing profile or a washer strength result.

## Robust and assumption-dependent conclusions

**Stable across these three branches:** local equilibrium is obtained;
nominal bolt steel proxies remain below the chosen steel hypothesis;
distributed bore contact allows internal bending moments larger than the
outer-seat moments; every outer-seat contact carries full T; the full-area
mean rail pressure remains 3.545 MPa at its governing axial state.

**Dependent on the model:** pressure concentration, contact patch, end
moment and displacement. At governing K12-right rail_1, lateral interface
motion is **3.985 / 2.102 / 1.480 mm** and required axial separation is
**1.409 / 0.359 / 0.107 mm** at Kwood 5 / 20 / 80. Those are independent
local-host responses, not measured frame motion or assembly checks. The
largest projected-shortening correction is **0.1047 mm**.

There are **24 representative states with neutral placement**, corresponding
to eight essentially zero-V source states repeated at three stiffnesses.
Each has two numerical tangent neutral modes. The model does not retain a
zero-force bore contact to remove them. Other local tangents are nonsingular
within the stated numerical threshold; this does not establish whole-frame
stability or remove out-of-plane freedoms omitted by the local model.

The rail peak seat pressure exceeds the retained 4.309 MPa **mean bearing
reference** in every branch. No pointwise pressure cap was imposed. This
identifies a sensitivity to actual seat compliance and redistribution; it
does not constitute a physical test failure or an adopted timber failure
criterion. A nonlinear seat law could change the moments and force shares.
The rigid washer likewise supplies moment transfer without predicting its
own bending. These limits prevent complete-joint acceptance.

## Reproduction and receipts

Maintained producer: [upper-right-combined-transfer.py](upper-right-combined-transfer.py).
Completed output: `rawlocal/upper-right-combined-transfer/attempt02/`.
The ignored folder contains the frozen producer snapshot, full 72-state
JSON, 5,760 beam sampling rows, 3,456 bore sampling rows, state CSV,
source/output pins, and a standalone saved-result worksheet postprocessor.

The first attempt is preserved. The second corrects axial projected-length
bookkeeping; all 72 force, contact, lateral motion and stress outputs are
exactly unchanged. It adds the small-angle shortening to the separation
expression above. Neither attempt changes the frozen frame, source geometry
or contact assumptions.

| Completed artifact | SHA256 |
| --- | --- |
| Maintained producer and attempt02 snapshot | `fba852724b82ee3cd28b0318bfdf156ac1786f85ac26257698d8d103c26c62b0` |
| `attempt02/checks.json` | `7e357df19c24b8d9eeaee4bb1e1935a9d681756f472143871fa29cf52e8a3ceb` |
| `attempt02/source-pins.json` | `535ce752d60a70d24acb7dd761def28deeff7b463cd7b9253f57474e8dd2e2bd` |
| `attempt02/worksheet-summary.json` | `969b32c2a34cf37732f41ccabef75cfcb7a615a0eaab6623e36a7d3af878f6a6` |
| `attempt02/states.csv` | `d9475ac50af07a95e33c117df66c72a9caab2f0941cb481579316540d6a6a114` |
| `attempt02/beam-fields.csv` | `a5aa8860e8022aa775b8588813be80aedce503aa8d949f67d44662e54fc264b5` |
| `attempt02/bore-fields.csv` | `8d7a56324185398a989a5bd537bccd4055580f8ccc01cb1f87858f6d5f9f4e11` |

Run the producer with `--output` naming a **new** ignored directory; it
refuses to overwrite a prior attempt. Environment is Python 3.12.3,
NumPy 2.5.2 and SciPy 1.18.1. The worksheet postprocessor reads saved arrays
and receipts only, without repeating the local solve.

All eleven directly bound source pins and six generated output pins were
rechecked. Maximum nodal residuals are **1.47e-9 N** and
**4.25e-6 N·mm**; maximum contact force and series-moment residuals are
**1.57e-12 N** and **4.20e-10 N·mm**. Declared production tolerances are
1e-6 N and 0.0001778 N·mm. Ruff passed for the maintained producer.
No software tests, frame/CAD/native solves or review loop were run.
No staging, commit, push, physical work or authority/release change was made
by this worker.
