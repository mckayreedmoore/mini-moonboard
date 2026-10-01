# BG003 nominal smooth-section action conversion

The [reviewed compatible diagnostic](../../support-corner-review-2026-09-30/README.md)
already supplies signed middle-cut shear and bending for both continuous
BG003 bolts in three authenticated rear cases. This packet combines those
actions with each case's actual outer-seat axial tie, without substituting
one case's forces for another. It converts all 18 diagnostic scenarios to
nominal quantities for a **hypothetical smooth 6.35 mm circular section**.

At A12-rear bolt 1, beta=100, the signed middle-cut bending has magnitude
5,933.768 Nmm and the source tie is 95.96739 N. With gross area
`πd²/4` and elastic section modulus `πd³/32`, the corresponding extreme normal
stress range is −233.023 to +239.083 MPa. The separately sampled peak bending
conversion is 266.565 MPa. The latter is at a different bolt station and is
not combined with a shear stress from the middle cut.

These figures describe the declared zero-gap, isotropic elastic diagnostic.
They are not actual bolt stress predictions or strength ratios. The axial
conversion assumes the source outer-seat tie remains constant through the
middle cut, with no introduced preload or distributed axial bearing. Signed
`V/A` values are mean transverse tractions, not maximum shear stresses; no
equivalent-stress formula mixes stresses from different locations. No material
yield or NDS reference is treated as a qualified product strength.

A delivered bolt must identify which sections actually have smooth shank,
thread root or runout. The smooth section cannot be transferred to a threaded
section. Actual clearance, grain-dependent bearing, shared two-bolt timber
compatibility, axial/washer/thread interaction, splitting and complete group
resistance remain unresolved. This packet supplies a conditional calculation
input for those checks, not a complete-corner pass.

The producer authenticates the reviewed diagnostic, its producer and all
recorded source hashes, then takes the tie from the matching usable full-load
export. No native solve or reviewed geometry change occurs.

```sh
OPENBLAS_NUM_THREADS=1 .venv/bin/python \
  docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-bg003-smooth-section-action-conversion-attempt01/convert.py --verify
```
