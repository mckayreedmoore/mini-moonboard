# Attempt 01: nominal Class 2A/2B axial flank travel

**Prepared:** 2026-09-25. **Status:** conditional geometric comparator only.
This calculation bounds the ideal axial lost-motion band for a hypothetical
matched 1/4-20 Unified pair when relative rotation is fixed. It is not an
installed clearance, purchased part, strength calculation, or physical
WJ24 acceptance.

## Primary dimensional source and values

The [NBS Handbook H28 (1969), Part I](https://nvlpubs.nist.gov/nistpubs/Legacy/hb/nbshandbook28-1969p1.pdf)
is the source for the values used here. Its standard-series limits table
lists the nominal `.250-20 UNC` external 2A pitch diameter as
`0.2127–0.2164 in` and the internal 2B pitch diameter as `0.2175–0.2224 in`.
H28 §9 explains that the maximum-material pitch-diameter limit is an
envelope/virtual-diameter constraint that accounts for lead, helix, and flank
angle deviations, while the minimum-material pitch-diameter limit applies
to pitch diameter as a single element. Its geometry relation for Unified
threads is `δE = 1.7321 δp`, where `δp` is an axial pitch/lead deviation and
`δE` is its functional-diameter equivalent.

ASME's current [B1.1-2024 record](https://www.asme.org/codes-standards/find-codes-standards/b1-1-unified-inch-screw-threads-un-unr-thread-form)
identifies the current standard and states that it covers Unified thread
form, series, class, allowance, tolerance, and designation. Its public
preview does not expose the numerical 1/4-20 class tables. Consequently, the
numbers below are faithfully bound to the H28 reference edition; rebind them
to the current purchased B1.1 table before treating them as current
acceptance dimensions. The hypothetical class pair is a calculation input,
not a WJ24 hardware selection.

## Calculation

The matched pair's diametral pitch-diameter clearance at the tight limit is:

```text
C_d,min = D2_internal,min − d2_external,max
        = 0.2175 − 0.2164 = 0.0011 in
```

At the loose limit:

```text
C_d,max = D2_internal,max − d2_external,min
        = 0.2224 − 0.2127 = 0.0097 in
```

For an ideal 60° flank cross-section, an axial phase offset has a functional
pitch-diameter equivalent 1.7321 times the axial offset (H28 §9). Inverting
that relation gives the full axial reversal travel between opposing loaded
flanks:

```text
b_axial = C_d / 1.7321

b_min = 0.0011 / 1.7321 = 0.0006351 in = 0.0161307 mm
b_max = 0.0097 / 1.7321 = 0.0056001 in = 0.1422435 mm
```

This is total movement from one flank contact to the opposite flank contact
at fixed relative rotation. If an idealized starting point is centered, the
one-sided clearance is `b_axial/2`; the standard does not set the no-load
phase or centered position. Starting from any arbitrary no-preload phase,
the one-direction free travel to contact may range from zero to `b_axial`.

The derivation assumes zero pitch/lead and flank-angle deviations from the
nominal single-start helix and 60° profile. H28's maximum-material
envelope rules require those errors to consume effective-size tolerance, so
the perfect-form geometry is an idealized fit comparator, not a field
measurement or a complete production-variability model. The conditions are
deliberately stated so this calculation is not mistaken for every possible
as-built thread profile.

## Relative rotation and helix

For a single-start 20 TPI thread, `p = 1/20 in = 0.050 in = 1.27 mm`. Once
thread flanks engage, axial travel is coupled to relative angular motion:

```text
Δz = p Δθ / (2π)
360° relative rotation → 1.27 mm axial advance
1 mm axial advance → 283.4646° relative rotation
```

The geometric helix angle at basic pitch diameter
`d2 = 0.250 − 0.649519/20 = 0.217524 in` is
`atan(p/(π d2)) = 4.1847°`. It is not a self-locking result. The thread class
does not specify friction at thread flanks or nut/washer seating faces, and
there is no initial preload in the current analysis scenario. Therefore this
note assumes neither a fixed nut rotation nor self-locking. With rotation
unrestrained, total axial motion is limited by actual thread ends and
hardware stops, not by the class flank-clearance band; those coordinates are
not available in the current WJ24 geometry/hardware record.

## Nut entry and exit boundary

The WJ24 [ordinary hardware basis](../../current-ordinary-hardware-basis.md)
has a finished-hex nut thickness envelope of 5.3848–5.7404 mm, equal to
4.24–4.52 nominal pitches. That envelope does not locate the first and last
full-form female flanks. Product entry/exit chamfers, incomplete thread turns,
and the bolt's first full-form thread/runout can reduce the mutual active
length. The fixed-rotation clearance formula applies if at least one complete
full-form turn overlaps and the class limits apply to that actual engagement
span. No engagement-strength inference follows from the pitch count.

Accordingly, the fit geometry supplies a useful *conditional numerical
interval*, while current physical WJ24 axial seating remains unbounded by
available project evidence until these exact fields are established:

1. Current-edition numeric 2A/2B limits and the selected/delivered thread
   class, final effective pitch diameters, and coatings.
2. Axial coordinates of first/last complete internal and external thread
   forms, including entry/exit chamfers and runout.
3. As-assembled angular phase and which flank is initially seated.
4. Whether the nut is rotationally restrained, and actual thread-end/seat
   stops limiting multi-turn travel.

## Machine-readable values

See [`calculation.json`](calculation.json) for the input limits, computed
clearance/travel values, and the assumptions/non-claims in a compact record.
