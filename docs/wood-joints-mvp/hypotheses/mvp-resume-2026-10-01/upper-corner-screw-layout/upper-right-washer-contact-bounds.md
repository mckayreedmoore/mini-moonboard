# Upper-right washer: footprint and reaction bounds

**2026-10-02 — finite analytical sensitivity in the retained radial-strip
model. Complete-joint and release HOLD remain unchanged.** This note owns no
existing producer, geometry, material selection or criterion. It extends
[the washer transfer worksheet](upper-right-washer-transfer.md) using its
frozen upper-right loads. It does not calculate a compatible physical contact
solution.

## Decision

The previous **206.683 MPa** uniform-pressure strip demand is not robust to
reaction redistribution within the same simplified model. At the governing
rail tension, an explicitly capped axisymmetric wood reaction gives up to
**244.609 MPa**. Allowing circumferential redistribution under that same
chosen pressure cap raises the independent-strip bound to **251.231 MPa**.
The latter narrowly exceeds the hypothetical **250 MPa** washer yield.
These are conditional mathematical comparisons, not an observed failure or
an applicable washer design resistance.

The 10 mm flat head/nut circle is also not guaranteed to overlap the washer
bore all around when the catalog washer opening floats against the nominal
bolt shank. This does not establish failed seating, but it removes the
concentric root condition from a general hardware claim.

Practical consequence: the useful missing input is now **a declared bearing
profile and centering condition, coupled to a wood-reaction/compliance
scenario**. The current yield assumption alone cannot close that transfer.
The results also identify conditional variants with more margin without
changing bolt axes; none is adopted here.

## Frozen load and geometry

Use the completed `corner-attempt01/component-results.json` and
`frame-250-attempt02`, preserving their six nominal states. The governing
upper-right rail state is K12 right, `rail_1`:

- Axial tension **757.336006 N**; concurrent lateral action **535.264744 N**.
- Rail washer: exact catalog option **Bolt Depot 2994**, nominal 1/4 USS.
  OD **18.4658–19.0246 mm**, ID **7.7978–8.3058 mm**, thickness
  **1.2954–2.0320 mm**. The catalog lists low-carbon steel with no numeric
  minimum yield. [Exact supplier item](https://boltdepot.com/Product-Details?product=2994).
- Retained strip root: hypothetical flat circle **10 mm diameter**,
  `a=5 mm`; `t=1.2954 mm`; `ri=4.1529 mm` from maximum washer ID.
- Wood bearing reference **4.309223308 MPa**, retained normal-duration dry
  DF-L No. 2 input. This is not a wood constitutive law or a predicted local
  pressure limit.

Head and nut washers each carry the full axial force. This calculation uses
only that axial force; bolt bending, lateral head/washer action and prying
are not supplied by the frozen strip model. The eight upper-right nominal
washer seats retain their saved geometric support result; loaded support is
not inferred from it. No paired hand/foot or other new frame state is used.

## Prescriptive NDS detailing route

The pinned current [2024 NDS Chapter 12](https://awc.org/wp-content/uploads/2026/09/AWC_NDS2024_withCommentary_20260911_Website_Chapter-12-Dowel-Type-Fasteners.pdf),
printed page 81/PDF page 3, §12.1.3.3 requires a standard cut washer, or an
equal-or-larger metal plate/strap, between wood and each bolt head/nut.
Its reference is **Appendix Table L8**. The older chapter version discussed
in the historical hardware note had an inconsistent L6 reference; that
reference is not used here. Parent directly inspected the pinned current
clause and supplied its scope for this worksheet.

The authenticated [2024 Appendix](https://awc.org/wp-content/uploads/2026/09/AWC_NDS2024_withCommentary_20260911_Website-Appendix.pdf),
printed page 195/PDF page 30, Table L8 starts at 3/8-inch washer size, with
basic ID/OD/thickness **0.438/1.000/0.083 in**. It has no 1/4- or 5/16-inch
row. Its footnote refers tolerances and other standard cut washers to
**ANSI/ASME B18.22.1**. The table was inspected in the preserved rendered
primary page, and parent independently confirmed it.

The absence of smaller rows does not reject the current rail/side sizes or
require a 3/8-inch washer minimum. **The standard-identity crosswalk is
resolved:** [ASME's official B18.21.1 record](https://www.asme.org/codes-standards/find-codes-standards/b18-21-1-washers-helical-spring-lock-tooth-lock-plain-washers)
states that B18.22.1-1965 plain washers were incorporated into
B18.21.1-2009. Its [official preview](https://www.asme.org/getmedia/9a1bbfb1-e1e5-4b02-b96a-c96f90194dca/22284.pdf)
identifies the consolidation and lists the Type A and Type B plain-washer
tables. Parent located this primary crosswalk; this worker independently
read the official page and preview on 2026-10-02.

Thus the exact 2994/2995 catalog's B18.21.1 citation is not a conflicting
standard label merely because NDS retains B18.22.1. It is usable in a
conditional plain-washer detailing route. The supplier's stated USS
dimensions remain the working input, with exact size/type conformance a
catalog condition rather than an observation of delivered parts. The free
two-page preview does not contain the full dimensional rows; independent
inspection of those rows is not claimed here. This source limit is not a
washer failure or a new blanket qualification prerequisite.

This route can settle its **installation-detail claim** when conformity is
established. It does not supply an axial washer capacity or convert the
strip calculations into one. Conversely, a new washer yield measurement or
native stress analysis is not imposed as a blanket prerequisite for this
prescriptive detailing route. The numerical transfer sensitivities below
remain separate from it.

## Footprint and washer play

The [existing head/nut source disposition](../../washer-bearing-footprint-inputs-2026-10-01/parent-review.md)
distinguishes the head's offset gauge-circle measurement from its actual
bearing plane and leaves the bearing profile as an explicit input. It also
records nut true-position/runout limits, without turning them into a
guaranteed installed contact area. The 9/10/11 mm circles below remain
hypothetical flat-face branches.

For a nominal smooth bolt shank `d` inside a washer bore `ID`, the washer-only
center offset can reach `e=(ID-d)/2` in this geometric scenario. A flat circle
of diameter `DH`, centered on the bolt, encloses the complete washer bore
only if `DH >= ID + 2e`. This is a sufficient all-around overlap condition,
not a strength or retention criterion.

| Family | Nominal shank (mm) | Maximum washer ID (mm) | Washer-only play (mm) | Circle needed for bore enclosure at that offset (mm) | Frozen circle (mm) |
| --- | ---: | ---: | ---: | ---: | ---: |
| Rail, 2994 | 6.3500 | 8.3058 | 0.97790 | 10.2616 | 10 |
| Side, [2995](https://boltdepot.com/Product-Details?product=2995) | 7.9375 | 9.9060 | 0.98425 | 11.8745 | 12 |

Thus the declared rail circle can lose full bore enclosure at permitted
washer-only offset; the declared side circle satisfies this particular
geometric condition. Neither result predicts the installed washer position.
This comparison excludes actual shank undersize, nut/body eccentricity,
bearing-face runout, tilt and wood-bore motion. It does not establish a
delivered-hardware bound. Bolt motion inside the wood bore is separate from
washer play relative to the head/nut; the offsets are not added to this
head-facing calculation.

When the washer is offset, the projected metal overlap is a circular
intersection problem, not a concentric annulus. Its total area need not
decrease: its angular distribution and resultant location can change even
if area increases. It therefore cannot be reduced to a lost-area factor or
used unchanged as the axisymmetric strip root. No access or assembly claim
is reopened by this purely loaded-contact distinction.

## Reaction envelope in the retained strip model

Let `p(r)` be nonnegative, axisymmetric wood reaction pressure over the
washer annulus. The chosen model requires axial equilibrium:

```text
T = 2*pi * integral_ri^ro p(r)*r dr
m = (1/a) * integral_max(a,ri)^ro p(r)*r*(r-a) dr
sigma_strip = 6*m/t^2
```

`m` is radial root moment per circumferential width, N·mm/mm. The strip root
and absence of hoop action remain assumptions from the previous worksheet.
Axisymmetry cancels global overturning moments, but these equations do not
enforce washer/wood deformation compatibility or construct head contact.

### Explicit pressure cap

For this envelope only, impose **`0 <= p <= P`, P=4.309223308 MPa**. Choosing
the retained mean wood-bearing reference as a pointwise cap is an additional
analyst constraint. It is **not** a consequence of NDS bearing acceptance,
a measured pressure field, a plastic wood law or a stiffness assignment.
The cap must remain explicit wherever these bounds are used.

Because the strip moment kernel increases with radius, its minimum places
reaction nearest the bore and its maximum places reaction nearest the outer
rim. Each field equals `P` on a filled radial interval and zero elsewhere:

```text
inner-fill outer radius B = sqrt(ri^2 + T/(pi*P))
outer-fill inner radius C = sqrt(ro^2 - T/(pi*P))
F(r,a) = r^3/3 - a*r^2/2
m_min = P/a * [F(B,a) - F(a,a)]  if B>a; otherwise zero
m_max = P/a * [F(ro,a) - F(max(a,C),a)]
```

The governing inner-fill radius is **8.555045 mm**. The full annulus can
carry 920.570 N at minimum OD and 991.473 N at maximum OD under this selected
cap, both above the 757.336 N demand.

| Matched OD branch | Outer radius (mm) | Outer-fill inner radius (mm) | Capped minimum strip stress (MPa) | Capped maximum strip stress (MPa) |
| --- | ---: | ---: | ---: | ---: |
| Minimum catalog OD | 9.2329 | 5.413337 | 143.517 | 214.551 |
| Maximum catalog OD | 9.5123 | 5.877212 | 143.517 | 244.609 |

These branches use maximum ID and minimum thickness with each stated OD.
They preserve axial force exactly, unlike treating every possible reaction
shape as the same uniform pressure. They are force-admissible fields within
the strip model, not predicted physical contact patches.

### Circumferential redistribution

Axisymmetry is another restriction. With `p(r,theta)<=P`, the moment of any
individual independent strip is bounded by filling its whole outer span at
`P`:

```text
m_local_max = P/a * [F(ro,a)-F(a,a)]
```

At maximum OD and the 10 mm circle, this gives **251.231 MPa**. It is possible
to meet the same total axial force and zero global overturning moment while
reaching this local strip load: fill the complete radial annulus in two
equal, opposite angular sectors. Their combined circumference fraction is
`T/(P*pi*(ro^2-ri^2)) = 0.763849`; each sector spans **137.493 degrees**.
The construction proves a force/moment-admissible demand in this idealization,
not an elastic contact solution. Hoop transfer and actual washer stress
remain outside the model.

### Removing the pressure cap

Without a pressure cap, axisymmetric reaction can concentrate in an outer
ring. Its strip-stress supremum is
`6*T*(ro-a)/(2*pi*a*t^2)`: **364.855 MPa** at minimum OD and **388.938 MPa** at
maximum OD. Without axisymmetry as well, force alone supplies no finite
pointwise independent-strip bound: reaction can concentrate into narrower
opposite angular sectors. None of these limiting distributions is asserted
to occur. They show why resultant force and projected area alone cannot
qualify loaded pressure or washer stress.

## Same-state worksheet and practical sensitivity

The six `rail_1` states retain their own axial forces. For each, the table
uses the same 10 mm circle, maximum OD, maximum ID, minimum thickness and
explicit pressure cap. These are independent six-case calculations, not a
sum of peaks:

| Nominal case | Tension (N) | Saved uniform-pressure strip demand (MPa) | Capped axisymmetric minimum (MPa) | Capped axisymmetric maximum (MPa) |
| --- | ---: | ---: | ---: | ---: |
| A12 rear | 100.355 | 27.388 | 0 | 49.282 |
| A12 forward | 51.033 | 13.927 | 0 | 25.629 |
| A12 left | 60.566 | 16.529 | 0 | 30.287 |
| K12 right | 757.336 | 206.683 | 143.517 | 244.609 |
| K12 rear | 744.099 | 203.071 | 138.204 | 243.226 |
| A1 rear | 12.998 | 3.547 | 0 | 6.638 |

Zero minimum means a force-admissible reaction can fit beneath the declared
head circle without loading the outer strip. It is not zero actual washer
stress. The pressure-cap local bound is 251.231 MPa for a filled sector;
it remains attainable in this mathematical class at every nonzero table
force by varying sector coverage.

At governing force, changing only the hypothetical circle gives:

| Flat circle diameter (mm) | Capped axisymmetric maximum (MPa) | Capped local strip bound allowing angular redistribution (MPa) |
| --- | ---: | ---: |
| 9 | 319.674 | 337.268 |
| 10 | 244.609 | 251.231 |
| 11 | 183.193 | 184.339 |

At the 10 mm circle, increasing hypothetical washer thickness to **1.5 mm**
reduces the local strip bound to **187.369 MPa**, or **0.7495** of hypothetical
250 MPa yield. This thickness lies within the current item's dimensional
range but is not its published minimum. Conversely, retaining minimum
thickness and choosing a 1.25 elastic stress margin would require hypothetical
yield **314.039 MPa** for the local strip bound. These are unadopted study
variants, not procurement or fabrication instructions, code resistance
factors or assigned product properties.

## What this completes and what remains

This completes a finite footprint/play check and reaction-distribution
envelope for the existing simplified screen. It shows that the previous
250 MPa first-yield hypothesis has little or no margin against permitted
model branches, while larger supported bearing profiles or greater specified
thickness could improve its conditional comparison.

The standard-identity crosswalk above is resolved. Retain the catalog
size/type conformance as an explicit condition of the NDS detailing route.
For the remaining axial transfer question, the next useful finite calculation is a
**compatible one-stack normal response** at the governing rail seat:
explicit head/nut bearing profile and
centering, actual or declared washer thickness/material, compression-only
wood reaction with a stated normal-compliance range, and matched receiver
support. It should return contact extent, resultant location, washer stress
and indentation, retaining the simultaneous bolt action as its scope limit.
It need not become a full-frame or native mechanics program. A supported
reduced method can be used if its applicability to this thickness/contact
geometry is established.

The primary [Teranishi et al. washer-embedment
study](https://link.springer.com/article/10.1186/s10086-021-01973-9)
models metal/wood contact and finds sensitivity to wood transverse stiffness
and strength. Its square washers, cedar and steel inputs do not rate this
round DF-L stack or validate its local stresses. The existing
[method-source note](../../washer-metal-method-preflight-2026-10-01/source-method-review.md)
explains that distinction. The completed
[finite-sector fixture](../../washer-finite-sector-contact-native-2026-10-01-attempt02/README.md)
validates solver contact resultants on another diagnostic assembly, not this
washer's stress or contact patch; it is reused as method context, not rerun.

Full combined bolt bending/group/splitting behavior remains separate.
Assembly/access is treated as the owner's working assessment; this note
does not claim new assembly evidence or change its authority disposition.

## Reproduction and source pins

Only this new Markdown file was written. One read-only arithmetic helper
derived the radial pressure extrema. Calculations use standard-library
arithmetic and saved JSON; no tests, CAD, native or frame solve, review loop,
staging or commit was performed. Previous raw evidence remains preserved.

The [preceding worksheet](upper-right-washer-transfer.md#source-pins-and-reproduction)
pins the full frozen source set. Key receipts for this extension:

| Source | SHA-256 |
| --- | --- |
| `upper-right-washer-transfer.md` | `d3f486e01583ea1b7382e6826a769cb0500cbafa849352eea2eb3c3095a1ddaf` |
| `bolted-replay-results/corner-attempt01/component-results.json` | `401b8876dc3a96b553c847f1029a5a9200ba3f45af5493f64edd61fdc6bc42b6` |
| `frame-250-attempt02/response.npz` | `0625196497b0dbc7b297724d7b9947f7c7c61bb282cd4d9681705629302c76c7` |
| `upper-block-strength-2026-10-01/source-cache/chapter12-2024-awc-20260911.pdf`, relative to `hypotheses/` | `53f6ec05dfd1ceabeccd4d6e88c342111678d3da4631ee7b482b706f77c1780f` |
| Same cache, `appendix-2024-awc-20260911.pdf` | `1fa2bcf52803b1bbed8ea30cf13551dd5f76c90bf110ac475b401f81d116ec31` |
| `washer-bearing-footprint-inputs-2026-10-01/parent-review.md`, relative to `hypotheses/` | `952b5753823048135822985659e8c0150602dd534f005564233fe957e2b291be` |
| `washer-metal-method-preflight-2026-10-01/source-method-review.md`, relative to `hypotheses/` | `20e85755030d56d14779bca0598aa3c057a58e8a188aa77693b8b3219bc85bf0` |
| `washer-finite-sector-contact-native-2026-10-01-attempt02/README.md`, relative to `hypotheses/` | `00e4cc5f45e3f4b29e2ef1f59f68a2fead36ccc0314b7c5ac52f881d3bef2488` |

From the repository root, the following reproduces the six axial reaction
envelopes and governing circle sensitivities without creating output files:

```sh
python3 - <<'PY'
import hashlib
import json
import math
from pathlib import Path

path = Path('docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/bolted-replay-results/corner-attempt01/component-results.json')
if hashlib.sha256(path.read_bytes()).hexdigest() != '401b8876dc3a96b553c847f1029a5a9200ba3f45af5493f64edd61fdc6bc42b6':
    raise SystemExit('Frozen component source changed')
data = json.loads(path.read_text())
P = data['component_references_mpa']['Fc_perpendicular']  # Chosen cap, not a law.
ri, ro, thickness = 8.3058 / 2, 19.0246 / 2, 1.2954
F = lambda r, a: r**3 / 3 - a * r**2 / 2
def bounds(T, a):
    B = math.sqrt(ri**2 + T / (math.pi * P))
    C = math.sqrt(ro**2 - T / (math.pi * P))
    minimum = 6 * P / a * (F(B, a) - F(a, a)) / thickness**2 if B > a else 0
    maximum = 6 * P / a * (F(ro, a) - F(max(a, C), a)) / thickness**2
    local = 6 * P / a * (F(ro, a) - F(a, a)) / thickness**2
    return minimum, maximum, local
states = [s for s in data['states'] if s['block'] == 'top_outer_right_cleat'
          and s['axis_id'].endswith('/rail_1')]
for state in states:
    print(state['case_id'], state['tension_n'], bounds(state['tension_n'], 5))
T = max(s['tension_n'] for s in states)
for diameter in (9, 10, 11):
    print('hypothetical circle', diameter, bounds(T, diameter / 2))
print('hypothetical t1.5 local stress', bounds(T, 5)[2] * (thickness / 1.5)**2)
PY
```
