# Source and calculation audit

## Source identity and locator

The official [MIT OpenCourseWare resource page](https://ocw.mit.edu/courses/2-080j-structural-mechanics-fall-2013/resources/mit2_080jf13_recitation5/)
identifies “2.080J Structural Mechanics Recitation 5: Summary of Plate
Bending,” lists Prof. Tomasz Wierzbicki, and exposes the 656 kB problem-solving
note. The producer's pinned [direct MIT-hosted PDF](https://ocw.mit.edu/courses/2-080j-structural-mechanics-fall-2013/de27f1d8f647ff995771d4b8d48d34bc_MIT2_080JF13_Recitation5.pdf)
opens as a nine-page `application/pdf`. This confirms the stated first-party
source and the page locator. As the producer says, remote PDF bytes were not
stored or hashed in the repository.

I checked the PDF's extracted source text at all three cited pages:

- PDF page 1 / printed `5-1` gives the plate governing equation and flexural
  rigidity `D = E h^3/[12(1 - nu^2)]`.
- PDF page 2 / printed `5-2` defines an annular plate with uniform pressure
  `P`, says both inner and outer edges are clamped, gives the axisymmetric
  solution, and applies zero displacement and zero slope at `r=a` and `r=b`.
- PDF page 3 / printed `5-3` sets `a=1`, `b=10` and prints the illustrative
  coefficients rounded to one decimal place.

The producer's equation transcription is correct, including the power on the
second term:

```text
w(r) = C1 ln(r) + C2 r^2 + C3 r^2 ln(r) + C4 + P r^4/(64D)
```

The source derivative is consistent with this expression:

```text
dw/dr = C1/r + 2 C2 r + C3(2 r ln(r) + r) + P r^3/(16D)
```

Thus the source boundary conditions are `w(a)=w'(a)=w(b)=w'(b)=0`. With
`a=1`, `b=10`, and `xi=r/a`, the producer's normalized expression
`W(xi)=A ln(xi)+B xi^2+C xi^2 ln(xi)+F+xi^4/64` and its four boundary
conditions follow directly. No equation, sign, source-page, or locator
discrepancy was found.

## Independent numerical recomputation

I formed an independent boundary system in logarithmic radius `t=ln(xi)`.
Because `dW/dt = xi dW/dxi`, zero slope in `xi` is equivalent to zero slope
in `t` at either nonzero edge. Let `L=ln(10)` and order unknowns as
`[A,B,C,F]`. The system is:

```text
W(t)  = A t + B exp(2t) + C t exp(2t) + F + exp(4t)/64
W_t   = A + 2B exp(2t) + C exp(2t)(2t+1) + exp(4t)/16

at t=0: [ 0,   1,       0,       1 ] [A B C F]^T = [ -1/64 ]
        [ 1,   2,       1,       0 ]                  [ -1/16 ]

at t=L: [ L, 100,   100 L,       1 ] [A B C F]^T = [ -156.25 ]
        [ 1, 200, 100(2L+1),     0 ]                  [ -625   ]
```

A separate 60-digit `Decimal` implementation with pivoted Gaussian elimination
produced:

```text
A = -10.7602000748211578315807848566902662628677087014965066752351
B =   7.17724045448044369389870558663887938254196724968625419510194
C =  -3.65678083413972955621662631658749250221622579787600171496914
F =  -7.19286545448044369389870558663887938254196724968625419510195
W(5) = 17.5518541635653691580554382466930582382098360620729901386720
```

These agree with the producer's unrounded coefficients and `W(5)` to the
reported precision. A second double-precision solve using the same log-radius
system gave endpoint residual magnitudes below `1.5e-13`. Substituting the
source's displayed one-decimal coefficients directly gives `W(5) ~= 16.31069`;
that loss of interior precision is consistent with the producer's warning not
to use the rounded source vector as an exact oracle. The exact boundary system,
not the rounded illustration, defines this reproducible answer.

## Scope distinction and limits

The immediately preceding washer-source attempt used J. C. Heap's ANL-6905
annular-plate report. Its identified example is a uniform load applied on a
concentric circle, with the case described as outer simply supported and inner
free. That is a ring-load problem with a different support family. The MIT
example reviewed here is instead a uniformly pressured annular domain with
both boundaries clamped. They are distinct load and boundary-value problems;
this review does not transfer the MIT answer to Heap's case.

The MIT result validates only one idealized classical-plate response case:
linear, isotropic thin-plate theory, constant thickness, axisymmetry, uniform
pressure over the annulus, and perfect clamping at both annular edges. It does
not test a finite washer/head/nut bearing footprint, line or ring loading,
partial or unilateral support, timber-seat compliance or crushing, local
washer shear, plasticity, or strength. It does not establish how to map WJ24
geometry or actions into this model. A helper using this vector should label
and implement the stated idealized boundary-value problem explicitly; the
actual `washer_bending` criterion remains open pending a supported candidate-
specific model and inputs.

## Local integrity and boundaries

The producer's verifier passed when run from the repository root:

```text
OK: packet checksums and predecessor pins match
```

The packet's own `sha256sum -c SHA256SUMS` passed when run from the producer
packet directory. The verifier checks packet file checksums, JSON record
identity, and four pinned files in attempt01; it does not fetch or hash mutable
MIT web content. No producer file, maintained helper/test, CAD, solver input,
queue, or candidate model was changed by this review.
