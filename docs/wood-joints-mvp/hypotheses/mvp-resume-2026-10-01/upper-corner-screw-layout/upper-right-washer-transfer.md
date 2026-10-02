# Upper-right washer transfer: finite radial-strip screen

**2026-10-02 — conditional calculation only. Complete joint and physical
release remain HOLD.** Geometry, hardware selection and the 47-criterion
authority are unchanged. This note reuses the completed
[corner replay](bolted-replay.md#completed-top-corner-replay); it does not
solve a new frame or contact model.

## Decision

The current upper-right rail washer requires **206.683 MPa radial-strip
bending stress** in the existing declared model. The upper-right side washer
requires at most **95.600 MPa**. A hypothetical washer yield of **250 MPa**
passes the model's uniaxial first-yield comparison, with rail demand/yield
**0.8267**. This is a mathematical result under stated assumptions, not a
published property of the current washers or an applicable design allowance.

The exact product fact missing from both current washer listings is a
**numeric minimum yield strength, or an applicable washer resistance**.
Their low-carbon-steel description and dimensional standard supply neither.
Even assigning a hypothetical yield does not establish that the strip model
bounds actual head/nut/washer/wood transfer: the loaded bearing footprints
and pressure distribution are still assumed.

The useful next transfer calculation is therefore to establish, or bound,
the **rail washer's effective wood reaction and head/nut bearing footprint**
at the governing state. A product yield value alone would settle the narrow
material comparison, but would leave that mechanics question open.

## Frozen scope and same-state demand

Input is the four-moved-screw, 250 lb dynamic scenario at
`frame-250-attempt02`, using only its six nominal-gap states. The completed
`corner-attempt01/component-results.json` binds these forces to the corrected
top-corner geometry. Earlier corner packets and the parent's separate paired
vertical-load sensitivity are not substituted.

Upper right has four bolt axes, eight outer washer seats and 24 simultaneous
bolt states. Each head washer and each nut washer carries the **full axial
bolt tension**, not half: they are in series. The saved model assigns the
same idealized washer demand to both ends; actual head and nut footprints
may differ. All eight nominal maximum washer envelopes have full modeled
wood support in the saved replay. That is a geometric result, not a loaded
contact solution.

The governing radial-strip state is `k12-right`,
`top_outer/clip_single_top_right_2/rail_1`, joining `base_rail_top` to
`top_outer_right_cleat`. Its simultaneous lateral force is **535.265 N** and
axial tension **757.336 N**. The lateral force is retained here for state
identity; it is not included in this axial-only washer strip calculation.

Every case below is governed by `rail_1`. Values in each row occur together:

| Nominal case | Tension (N) | Lateral force (N) | Ideal wood pressure (MPa) | Strip bending stress (MPa) |
| --- | ---: | ---: | ---: | ---: |
| A12 rear | 100.355 | 13.842 | 0.469764 | 27.388 |
| A12 forward | 51.033 | 6.315 | 0.238886 | 13.927 |
| A12 left | 60.566 | 15.060 | 0.283513 | 16.529 |
| K12 right | 757.336 | 535.265 | 3.545118 | 206.683 |
| K12 rear | 744.099 | 536.126 | 3.483157 | 203.071 |
| A1 rear | 12.998 | approximately 0 | 0.060845 | 3.547 |

For completeness, the four axis envelopes are distinct:

| Axis | Governing case for strip stress | Tension (N) | Strip stress (MPa) |
| --- | --- | ---: | ---: |
| `rail_1` | K12 right | 757.336 | 206.683 |
| `rail_2` | K12 right | 235.258 | 64.204 |
| `side_1` | K12 right | 491.381 | 88.976 |
| `side_2` | K12 rear | 527.959 | 95.600 |

## Exact washer identity and dimensions

The retained hardware input uses **Bolt Depot 2994** at the quarter-inch rail
bolts and **2995** at the 5/16-inch side bolts. These are the catalog options
bound by the calculation, not observations of delivered parts.

| Catalog washer | OD range (mm) | ID range (mm) | Thickness range (mm) | Declared flat head/nut circle |
| --- | ---: | ---: | ---: | ---: |
| [2994, 1/4 USS](https://boltdepot.com/Product-Details?product=2994) | 18.4658–19.0246 | 7.7978–8.3058 | 1.2954–2.0320 | 10.0 mm diameter |
| [2995, 5/16 USS](https://boltdepot.com/Product-Details?product=2995) | 22.0472–22.9870 | 9.3980–9.9060 | 1.6256–2.6416 | 12.0 mm diameter |

Both primary catalog pages were checked on 2026-10-02. They identify
low-carbon steel, zinc plating and dimensional standard ASME B18.21.1 as
listed, without edition. Neither gives numeric yield, hardness, a material
grade or installed contact-area bounds. The [supplier strength
chart](https://boltdepot.com/fastener-information/Materials-and-Grades/Bolt-Grade-Chart)
is explicitly a bolt chart; Grade 5 bolt strength is not washer strength.
Other fitting-family material minima do not qualify these two items.

The 10/12 mm circles are **explicit flat, concentric bearing-face scenarios**,
not catalog guarantees. Head across-flats dimensions do not define the flat
contact circle. The existing
[bearing-footprint source note](../../washer-bearing-footprint-inputs-2026-10-01/source-review.md)
also distinguishes a head's offset gauge plane from its actual bearing
plane; its quarter-inch examples do not qualify the current side stack.

## Recovered model and limits

The frozen producer computes the following for each family, in N and mm:

```text
Amin = pi/4 * (ODmin^2 - IDmax^2)
p = T/Amin
b = ODmax/2
a = 5.0 mm for rails; 6.0 mm for sides
m = (p/a) * [(b^3-a^3)/3 - a*(b^2-a^2)/2]
sigma_strip = 6*m/tmin^2
```

Here `m` is root bending moment per unit circumferential width, in N·mm/mm.
The formula integrates prescribed uniform upward wood pressure over an
independent radial cantilever strip outside the assumed head/nut circle.
The strip root is at `a`; circumferential plate action is omitted. The
rectangular strip stress assumes linear elastic bending through thickness.

| Quantity | Rail, governing K12 right | Side, governing K12 rear |
| --- | ---: | ---: |
| Minimum projected annulus area (mm²) | 213.627873 | 304.695368 |
| Maximum lever radius `b` (mm) | 9.5123 | 11.4935 |
| Assumed root radius `a` (mm) | 5.0 | 6.0 |
| Minimum thickness `t` (mm) | 1.2954 | 1.6256 |
| Uniform pressure `p` (MPa) | 3.545118 | 1.732742 |
| Root moment per width `m` (N·mm/mm) | 57.804484 | 42.104940 |
| Required strip bending stress (MPa) | 206.683114 | 95.599785 |

Combining minimum annulus area with maximum OD is a tolerance envelope, not
one matched physical washer. It increases demand within this prescribed
uniform-pressure strip idealization: actual area is no smaller, lever radius
no larger and thickness no smaller than the chosen bounds. It does **not**
bound pressure redistribution or actual three-dimensional washer stress.

No pressure field is solved. There is no wood-seat stiffness, head/nut tilt,
washer eccentricity, bolt bending or prying, initial clamp load, friction,
contact opening, contact-edge radius or hoop stress in this formula. The
geometric support result uses a 0.05 mm inward probe at nominal seats;
it does not prove the entire annulus remains loaded. Previous eccentric
support packets for other axes/geometry are not transferred as acceptance.

The [MIT annulus
example](https://ocw.mit.edu/courses/2-080j-structural-mechanics-fall-2013/de27f1d8f647ff995771d4b8d48d34bc_MIT2_080JF13_Recitation5.pdf)
uses uniform pressure with both annular edges clamped. That supports its own
benchmark, not this washer contact condition. The existing
[washer-method note](../../corner-washer-method-investigation-2026-10-01/source-note.md)
records why a physical contact/stress model needs an applicability argument.
This finite screen does not create one or prescribe a native run.

## What a material hypothesis can close

For the declared uniaxial elastic strip comparison, the threshold is
`Fy >= 206.683114 MPa` at the rail and `Fy >= 95.599785 MPa` at the side.
The following values are **hypothetical material inputs**, not properties
assigned to 2994 or 2995:

| Hypothetical yield (MPa) | Rail stress/yield | Side stress/yield | First-yield strip comparison |
| --- | ---: | ---: | --- |
| 200 | 1.0334 | 0.4780 | Rail exceeds hypothesis |
| 250 | 0.8267 | 0.3824 | Both below hypothesis |
| 300 | 0.6889 | 0.3187 | Both below hypothesis |

At 250 MPa, the rail's yield/demand ratio is only **1.210** within this
model. It is not a complete-joint safety factor. If the study instead
declares a 1.25 or 1.50 elastic stress margin, required rail yield becomes
**258.354 or 310.025 MPa**, respectively. These margin choices are study
specifications, not sourced code resistance factors. No duration adjustment
or bolt-grade property is transferred to washer steel.

Thus an explicit material hypothesis can close **this narrow conditional
strip first-yield screen**. Product applicability and complete washer
transfer remain open. The exact strength fact needed for a product-based
comparison is a minimum yield or applicable resistance bound to these exact
washer items; actual bearing-face geometry and a bounded loaded pressure
field are separate mechanics inputs.

## Useful sensitivity, without a new solve

At the same governing rail tension, minimum thickness and prescribed uniform
wood pressure, changing only the hypothetical flat bearing-circle diameter
gives:

| Hypothetical flat circle diameter (mm) | Rail strip stress (MPa) |
| --- | ---: |
| 9 | 277.464 |
| 10, frozen scenario | 206.683 |
| 11 | 151.652 |

The 9 mm scenario exceeds the 250 MPa material hypothesis. Bearing-face
uncertainty therefore can change this conditional decision. These are
concentric profile sensitivities, not measured diameters or an installation
instruction. At the same 10 mm circle, increasing hypothetical thickness
within the catalog range gives **125.303 MPa at 1.6637 mm** and
**83.997 MPa at 2.032 mm**. A midrange or maximum thickness cannot replace
the published minimum without an explicit requirement; no washer is changed.

For wood, the frozen normal-duration DF-L No. 2 perpendicular-to-grain
reference is **4.309223 MPa**. Uniform mean-pressure bookkeeping requires at
least **175.747682 mm²**, or **82.268%** of the minimum rail annulus, at
757.336 N. Holding that force fixed:

| Hypothetical effective fraction of minimum annulus | Mean-pressure/reference |
| --- | ---: |
| 100% | 0.8227 |
| 90% | 0.9141 |
| 85% | 0.9679 |
| 80% | 1.0284 |

This is area sensitivity only. It does not establish peak pressure, local
wood damage or the equilibrium contact patch, and it does not alter the
saved strip pressure. A smaller loaded area can ease some washer spans while
raising wood pressure; a contact model must resolve both together.

## Source pins and reproduction

Paths below are relative to `mvp-resume-2026-10-01/` unless noted. The
calculation reads the frozen component JSON, re-evaluates its formula using
standard-library arithmetic and checks the listed input hashes. It does not
import CAD or run software tests, a native solve or a frame solve. One
read-only source helper checked the exact supplier items; it changed no
files. No existing producer or maintained note was edited.

| Source | SHA-256 |
| --- | --- |
| `upper-corner-screw-layout/bolted-replay-results/corner-attempt01/component-results.json` | `401b8876dc3a96b553c847f1029a5a9200ba3f45af5493f64edd61fdc6bc42b6` |
| Same directory, `producer.py.snapshot`; identical current `corner_checks.py` | `177e13712575b735dfb2cd4d1314d006e3f8fc77d3cbc9b3e117609fbe561bb0` |
| `upper-corner-screw-layout/frame-250-attempt02/comparison.json` | `bea6cbc330af3cdb20499d774a8f6bb24481d687c3150adb01ede18e4c1d50ca` |
| Same directory, `response.npz` | `0625196497b0dbc7b297724d7b9947f7c7c61bb282cd4d9681705629302c76c7` |
| `top-corner-hardware/hardware-inputs.json` | `a2110d7580621dee92017403345f21c458729612547ac1f7b2eb8068d0c723c7` |
| `top-corner-contact-geometry.json` | `987af6908d6677165b6a712537ecca0c02827d558ca386ced96f4c1f6436008f` |
| `top-corner-correction/top_outer_right_cleat.step`, saved support only | `fe199dcce78d43140ef5299d82d0b888631905bd8686537d98a0997163e45b79` |
| `top-corner-correction/base_side_right.step`, saved support only | `6b79617b36f44fc6750b334556779a01191802f8b67b2a3e46c69a6c42bc9601` |
| `evaluation-resume-2026-09-24/current-full-frame-member-solids-attempt01/bundle/members/base_rail_top.step`, relative to `hypotheses/`, saved support only | `79b4f7f66f35928ed383d0e396ce221d9a4302136b088a7bcd41749c52a10a60` |
| `washer-bearing-footprint-inputs-2026-10-01/source-review.md`, relative to `hypotheses/` | `1a7a236ddf92f5fb1487619ebe8493de5f6ddfa97e924bc48cf5ebb5fe83f975` |
| `corner-washer-method-investigation-2026-10-01/source-note.md`, relative to `hypotheses/` | `4785ed0784c430efded876e5bab178516c619e88adb7b159c32f58e9bd31f3de` |

Run from the repository root to reproduce the six governing rows and the
rail/side formula envelopes without writing any output:

```sh
python3 - <<'PY'
import hashlib
import json
import math
from pathlib import Path

root = Path('docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01')
path = root / 'upper-corner-screw-layout/bolted-replay-results/corner-attempt01/component-results.json'
digest = hashlib.sha256(path.read_bytes()).hexdigest()
if digest != '401b8876dc3a96b553c847f1029a5a9200ba3f45af5493f64edd61fdc6bc42b6':
    raise SystemExit('Frozen component source changed')
report = json.loads(path.read_text())
states = [s for s in report['states'] if s['block'] == 'top_outer_right_cleat']
for case in dict.fromkeys(s['case_id'] for s in states):
    state = max((s for s in states if s['case_id'] == case),
                key=lambda s: s['declared_washer_radial_strip_bending_stress_mpa'])
    print(case, state['axis_id'], state['tension_n'], state['lateral_n'],
          state['declared_washer_radial_strip_bending_stress_mpa'])
for family, od_min, od_max, id_max, t_min, a in [
    ('rail', .727, .749, .327, .051, 5.0),
    ('side', .868, .905, .390, .064, 6.0),
]:
    subset = [s for s in states if '/' + family + '_' in s['axis_id']]
    state = max(subset, key=lambda s: s['tension_n'])
    area = math.pi / 4 * 25.4**2 * (od_min**2 - id_max**2)
    p, b, t = state['tension_n'] / area, od_max * 25.4 / 2, t_min * 25.4
    m = p / a * ((b**3 - a**3) / 3 - a * (b**2 - a**2) / 2)
    stress = 6 * m / t**2
    print(family, state['case_id'], area, p, m, stress,
          'hypothetical Fy250 ratio', stress / 250)
PY
```

No actual washer failed a physical test in this work. The strip comparison,
wood mean-pressure reference and geometric seat support remain distinct
from combined bolt behavior and complete-joint acceptance.
