# Continuous knee bolts: recovered static bearing and bending

## Result and decision

The four continuous quarter-inch knee bolts now have an explicit static
bearing distribution through their three receivers for all six current
nominal-gap load states. This adds **24 bolt states, 72 receiver fields and
96 normalized endpoint fields** to the existing asymmetric lateral screen.
It uses saved forces and geometry; no frame, CAD or native solve is performed.

At the governing A12-left state, `knee_outer_left_side_1` has:

| Quantity | Conditional result |
| --- | ---: |
| Maximum recovered bolt shear | 667.304 N |
| Maximum recovered bending moment | 9.25061 N·m |
| Simultaneous exterior tie | 96.6713 N |
| Smooth-shank elastic bending stress | 368.001 MPa |
| Thread tensile-area axial stress | 4.71197 MPa |
| Conservative spatial axial/bending/shear stress envelope | 375.876 MPa |
| Envelope / declared Grade 5 yield, 634.318 MPa | **0.592568** |
| Maximum constructed wood bearing pressure | 11.0328 MPa |
| Pressure / minimum nominal dowel-bearing strength, 30.6817 MPa | **0.359589** |

The bending maximum lies 31.2545 mm into the middle `base_side_left`
receiver. The pressure maximum occurs at the exterior spine's side-member
interface. Those maxima are distinct positions in the same bolt/load state.
The stress envelope deliberately combines spatial maxima to bound every
section; it does not claim their exact simultaneous occurrence at one fiber.

This construction finds no additional nominal bearing or smooth-shank steel
exception in the saved force states. Retain the current bolt arrangement for
the conditional model. It supplies **no adjusted NDS capacity, complete-joint
pass, actual contact pattern or common-bolt clearance result**. The existing
92 ksi endpoint-sum reference remains 0.919158 and its 45 ksi sensitivity
1.312488; these results do not replace those design-reference comparisons.

## The finite model

Each modeled stack is exterior spine → side member → inner frame block,
with bearing lengths 38.1 / 88.9 / 88.9 mm. There is one continuous 6.35 mm
shaft and no lateral head/nut reaction, hidden applied end moment or added
receiver. Its axial direction is +X on the left and −X on the right.

Let `P1` and `P2` be the source plane vectors on each plane's first body.
The three receiver forces are `F0=P1`, `F1=−P1+P2`, `F2=−P2`.
Within a receiver of length `L`, local coordinate `x` starts at its headward
wood face. Choose bearing on the wood `q(x)=a+b x`, in N/mm, satisfying:

```text
integral q dx = F
integral x q dx = J
b = 12 (J − L F/2) / L³
a = F/L − b L/2
```

The required first moments are `J0=L0 F0`, `J1=−L1 F2`, and `J2=0`.
They preserve the source actions at the two actual interfaces, including
each receiver's lateral transfer moment. The equal and opposite bearing on
the bolt is integrated through the full ordered stack to recover quadratic
shear and cubic bending functions. Their vector-norm maxima are evaluated
at endpoints and real stationary polynomial roots. Both free-end shear and
bending close to arithmetic tolerance.

The parent also compared the integrated fields with all 72 original receiver
wrenches about their saved global datums: force differences are zero and
the largest moment difference is 1.621×10⁻¹⁰ N·mm. The producer's maximum
receiver first-moment integration residual, including endpoint fields, is
4.370×10⁻¹¹ N·mm. These are equilibrium arithmetic checks, not evidence of
physical contact or inspected hardware.

The affine distributions reverse bearing direction within a receiver.
Their negative portions represent compression against the opposite bore
wall, not timber tension or face friction. Actual clearance, bolt rotation
and member displacement must permit those contacts for this field to occur.
That displacement/contact compatibility is not solved here. In the source
frame, all four continuous bolts still have zero modeled lateral gap.

## Material and endpoint comparisons

[AWC TR12](https://web-media.awc.org/wp-content/uploads/2021/12/17210714/AWC-TR12-1510.pdf),
§§1.3 and 1.7, distinguishes nominal bearing/bending inputs from the
reduced lateral design reference. It defines bearing resistance per unit
length `Fe D` and circular dowel moment resistance `Fyb D³/6`. Those nominal
quantities are used only for the static field comparison here.

All receiver pressure checks use the conservative minimum of the existing
DF-L dowel-bearing hypotheses: **4450 psi**, including the middle member's
changing bearing direction. This avoids adopting an oblique interaction
surface from a favorable local direction. It is not the 625 psi perpendicular
compression allowance used for washer faces and is not an adjusted connection
design value. Splitting, brittle fracture and existing cuts remain separate.

The steel envelope assumes the conditional J429 Grade 5 **92 ksi** yield
basis already recorded in the [fastener material packet](../hardware-material-specification-2026-09-30/fasteners.md).
For diameter `D`, area `A=πD²/4`, elastic section modulus `S=πD³/32`, and
quarter-inch thread tensile area `At=0.0318 in²`, the declared envelope is:

```text
sqrt[(T/At + Mmax/S)² + 3 (4 Vmax/(3 A))²]
```

The parabolic solid-round shear maximum, smooth bending section and spatial
envelope are explicit mechanics assumptions. Delivered thread/runout/root
dimensions, bearing-zone stresses, head/nut and washer transfer are not
qualified by this arithmetic. Use the separate [hardware profile requirements](assembly-package/hardware-engagement.md).

Each endpoint field scales one source plane's signed vector to its saved
single-shear `Z`, sets the other plane to zero, and recovers the same complete
three-receiver force/moment distribution. No middle interval receives a
second simultaneous capacity allowance. All 96 fields fit the declared
nominal bearing and plastic bending bounds:

| Endpoint scenario | Maximum nominal bearing ratio | Maximum nominal plastic bending ratio |
| --- | ---: | ---: |
| 45 ksi Fyb sensitivity | 0.368837 | 0.733052 |
| 92 ksi Fyb hypothesis | 0.522823 | 0.512681 |

These fields establish static endpoint embedding within the stated nominal
bearing/bending construction. They do not establish kinematic embedding or
the complete physical convex admissible set assumed by the earlier
[endpoint-sum screen](three-member-checks.md). That screen remains conditional;
neither endpoint field nor nominal stress margin supplies a normative
asymmetric three-member capacity.

## Sources and reproduction

The saved source is
`three-member-screen-attempt01/all-two-receiver/screen.json`, SHA-256
`306aa4a8e4c6113d4a0258d09564292d07095131ef2b4621370d7284e75e0377`.
Its geometry, 24 signed plane/tie states and force scope are reused unchanged.
The underlying current frame is `two-receiver-frame-attempt03/`; its nominal
seating is bounded and nonunique, not a motion envelope or strict stability
result. All **158 source and output bindings** matched before and after the
calculation, including the original receiver geometry and material references.

[knee_bearing_checks.py](knee_bearing_checks.py) produced ignored/local
`knee-bearing-attempt01/checks.json`, SHA-256
`a3761a18818e31b790a14480195d3110d71d08702bea9cc8e7617250d84d41ad`.
The directory preserves its exact producer snapshot. Complete replay requires
the retained local source artifacts; this published source is not a backup
of all frozen arrays or geometry.

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/knee_bearing_checks.py --output docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/knee-bearing-attempt02
```

Use a fresh output directory. Ruff passes. No software tests, review agents,
native execution, geometry/hardware change or physical work were performed.
All 47 criteria remain pending, all eight release flags remain false and
Actual/Disposition cells remain blank. The panel attachment deficit and
top-rail proxy exception are unchanged.
