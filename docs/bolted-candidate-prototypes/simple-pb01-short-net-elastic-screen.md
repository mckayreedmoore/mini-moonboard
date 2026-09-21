# PB-01 six-inch corner block: bore-center elastic normal-stress sensitivity

Status: **far-field elastic algebra on diagnostic bore cuts, not a wood
net-section resistance check, joint utilization, or drilling release.**
This study concerns the bolted solid-wood corner block (`cleat` in retained
machine records), not a selected construction detail.

The [reproduction script](../../scripts/simple_pb01_short_net_elastic_screen.py)
pairs source-verified A12-left and K12-right *tension-only* hybrid section
actions with the [bored-section geometry](simple-pb01-short-bored-section-probe.md)
of the same 152.4-mm block. The four bores use a 7.5-mm **diagnostic CAD
envelope**, not a drill size. It evaluates both reported load cut sides at
each of N=265 mm (`u1`), 290 mm (`r1+r2`) and 310 mm (`u2`), for six values
per case. The native section moments are about the modeled gross centerline;
the code shifts them to each net centroid before superposing axial and
biaxial bending. In the right-handed local X/T/N basis, the field at a net
section point is
`σ_N = N/A + M_X(T−T_c)/I_X − M_T(X−X_c)/I_T`.
The source check reconstructs the block centerline start from the maintained
`u1` bore and face geometry, then matches the native report's start, end,
grain axis and both section axes before using its moments. This is a
coordinate-provenance check, not validation of the physical joint model.
The section product moment is zero for these specific retained strip shapes.
The four exterior corners remain wood at all three cuts, so the extremes of
this *linear* field occur at those corners. This follows standard
[combined-loading centroidal-section mechanics](https://mechref.engr.illinois.edu/sol/combined.html)
and the [composite-section/parallel-axis derivation](https://ocw.mit.edu/courses/1-050-solid-mechanics-fall-2004/8f0200f4ca3236383a2ef048c7ec4c40_emech9_04.pdf).

| Maximum over six bore-center cut sides | A12-left | K12-right |
| --- | ---: | ---: |
| Positive elastic normal stress, MPa | 0.009471 | 0.015991 |
| Negative elastic normal stress magnitude, MPa | 0.008731 | 0.014843 |

Both positive maxima occur on the **before-load** side of the rail-pair
cut. The results are neither local peak stresses nor adjusted wood design
values. A beam-like linear field can miss the real stress concentration,
load introduction and splitting around a dowel bore; it says nothing about
the remaining wall, group distribution, axial washer path, shear, torsion,
moisture, grade, or repeated assembly. The two runs also retain **23 legacy
ML24Z/SDS proxy stations** and are not full V4 demands. Consequently even a
small number here cannot be divided by a material property to claim a
complete or safe joint.

Reproduce with `.venv/bin/python -m
scripts.simple_pb01_short_net_elastic_screen` and
`.venv/bin/python -m pytest -q
tests/test_simple_pb01_short_net_elastic_screen.py`.
