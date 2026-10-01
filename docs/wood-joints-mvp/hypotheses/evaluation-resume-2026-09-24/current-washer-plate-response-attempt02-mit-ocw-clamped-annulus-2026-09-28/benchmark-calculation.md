# Provisional benchmark: uniformly pressured, clamped annular plate

## Source-stated problem

The MIT OCW Recitation 5 PDF gives the linear classical-plate equation, flexural rigidity, axisymmetric general solution for constant uniform pressure, and the four boundary equations for a uniform-pressure annulus with both inner and outer edges clamped. The worked illustration sets inner radius `a = 1`, outer radius `b = 10`; pressure intensity is denoted `P` in the handout. The handout's constants and plotted deflection expression are rounded to one decimal place.

This is a small-deflection, isotropic, constant-thickness, linear-elastic thin-plate example. It has no contact nonlinearity or material-strength calculation.

## Normalized equations

Let `xi = r/a` and `W(xi) = D w(r)/(P a^4)`, with `D = E h^3/[12(1 - nu^2)]`. For `a = 1` and `b/a = 10`, write the solution as

```text
W(xi) = A ln(xi) + B xi^2 + C xi^2 ln(xi) + F + xi^4/64
```

The source's clamped conditions are

```text
W(1) = 0,     W'(1) = 0,
W(10) = 0,    W'(10) = 0.
```

They give this dimensionless linear system:

```text
[ 0          1          0                   1 ] [A]   [-1/64]
[ 1          2          1                   0 ] [B] = [-1/16]
[ ln(10)   100       100 ln(10)             1 ] [C]   [-156.25]
[ 0.1       20        20 ln(10) + 10        0 ] [F]   [-62.5]
```

The solution, in `[A, B, C, F]` order, is

```text
A = -10.7602000748
B =   7.17724045448
C =  -3.65678083414
F =  -7.19286545448
```

The response at the fixed interior station `xi = 5` is

```text
W(5) = D w(5a)/(P a^4) = 17.5518541636.
```

As a secondary check on the response profile, the interior stationary point is at approximately `xi = 5.09068681454`, where `W = 17.5652289510`; the clamped endpoint values and slopes are zero. The interior sample at `xi = 5` is the simpler proposed known-answer comparison.

## Reproduction and limits

The numeric values above follow from solving the displayed four-equation boundary system and substituting its unrounded solution into the displayed analytic expression. They are not copied from a published numerical table. The source's coefficient vector is rounded, so direct evaluation of that rounded vector at interior radii has significant cancellation error; it must not be treated as a precision oracle.

This benchmark exercises only the axisymmetric response of a uniformly pressured annulus with both boundaries fully clamped. It does not exercise concentrated ring loading, a finite bolt-head/nut pressure footprint, partial timber support, unilateral contact, timber-seat compliance/crushing, local washer shear, nonlinear response, or yield/capacity. It can at most verify one generic elastic plate-response pathway pending independent review. A separate primary-source benchmark matched to the eventual implemented load/support family may still be needed.
