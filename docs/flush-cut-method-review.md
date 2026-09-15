# Flush cut method review

## Disposition

The existing negative quarter-depth screen is a real result of its implemented
geometry calculation, but it is not yet a demonstrated NDS rejection of the
actual inclined support detail. Do not delete the result or declare the detail
accepted. The prescribed measurement station and loaded face must first be
mapped to the actual support and current forces.

## Primary provisions checked

[NDS 2024 Chapter 4](https://web-media.awc.org/wp-content/uploads/2021/12/17210008/AWC_NDS2024_20241011_AWCWebsite_Chapter4.pdf),
§4.4.3 and Figures 4A–4B, applies its sawn-lumber end-cut restrictions to both
notches and taper cuts. A convex profile is therefore not a general exemption.
The end-bearing limit is one quarter of member depth; Figure 4B locates the
compression-taper remaining-depth dimension at the inner support edge.

[NDS 2024 Chapter 3](https://web-media.awc.org/wp-content/uploads/2021/12/17210019/AWC_NDS2024_withCommentary_20240718_AWCWebsite_Chapter-3-Design-Provisions-and-Equations.pdf),
§3.4.3.1(c), (e) and Figure 3D, distinguishes tension-face taper cuts from
compression-face end tapers. The compression-taper calculation explicitly
measures remaining depth perpendicular to grain at the inner support edge.
Its extension parameter is also measured from that edge. The tension-face
taper route instead invokes the end-notch treatment; an alternate method is
not automatic permission to discard that treatment.

The chapter 4 PDF was downloaded from AWC and its printed pages 33–34 were
read and visually checked. Chapter 3 printed pages 20–21 were read and visually
checked in the previously downloaded AWC PDF. No third-party transcription is
the evidence basis. The old 2018 chapter URLs used elsewhere in this repository
should not be substituted for this same-edition review.

## Actual rim geometry and existing calculation

`floor-flush-geometry.json` describes each solid 4×6 side rim with 139.7 mm
depth and 88.9 mm width. In the side elevation its lower bearing seat extends
from `(Y,Z)=(-175.7,277)` to `(-41.497331,277)` mm. Its vertical flush heel
extends up to `(-175.7,334.398106)` mm. These coordinates are reconstructed
from the stored local profile, grain vector and centre, without a new CAD solve.

`floor_flush_geometry.end_cut_screen` multiplies the horizontal seat length
by the vertical grain component. That gives 102.805209 mm, subtracts it from
139.7 mm, and applies the existing 3 mm allowance. Its margin is consequently
−4.969791 mm. Even without the allowance this particular measurement exceeds
the quarter-depth removal limit by 1.969791 mm.

This is the normal projection of the complete terminal bearing-seat length.
The function does not locate the inner edge of the support, establish the
tension/compression face, or intersect the timber at the NDS compression-taper
measurement station. Those omitted operations matter: the stored timber
profile already has its full 139.7 mm depth at and inward of local grain
station `s = -1183.619990` mm, the inner end of the actual seat. A support edge
farther inward cannot be represented by the reduced terminal-seat projection.
This observation identifies a possible conservative screen mismatch; it does
not establish that an inclined, combined-load detail satisfies the horizontal
beam diagram without the mapping below.

## Concrete next calculation

1. Extract the actual header support boundary and bearing patch in the same
   local grain/depth coordinates as the rim. Record the inner support edge,
   available contact, remaining depth and taper extension explicitly.
2. Use each new, contact-enabled case's local axial force and both bending
   moments to determine stress on the removed heel face throughout the
   cut/support region. Do not infer its compression status from the visual
   slope, the applied load direction, or the preceding candidate's forces.
3. If the compression-taper route applies, implement its prescribed station
   and shear expression with tests that distinguish terminal tip depth from
   inner-support depth. Preserve the previous scalar comparison as history.
4. If any required case puts the relevant face in tension, retain the
   tension-face end-cut restriction for that case. Resolve the detail with an
   applicable supported method or change the cut/support geometry; neither
   moving an angle bracket alone nor a passing bolt check restores timber.
5. Independently retain bearing, net-section, connection-induced shear and
   actual angle force checks. Correcting one applicability comparison cannot
   qualify the entire joint.

## Rear-leg thickness taper

The rear-leg taper removes 38.1 mm from the transverse 88.9 mm thickness;
the other 139.7 mm section dimension stays constant. In bending about the
affected axis, its removal is 42.86% of that thickness. Merely reorienting a
sawn-beam quarter-depth limit does not provide a passing answer, and the
actual floor support/runner contact must be mapped before borrowing a support
notch equation.

The present EC5 notch factor of 1.0 is not an established correction for all
axial, biaxial and torsional taper stresses. Continue the bounded work in
[taper-method-applicability-review.md](taper-method-applicability-review.md):
establish the actual tapered-face shear and transverse normal stress and use
a supported resistance/interaction basis. A longer taper reduces slope but
does not by itself prove that those omitted stresses are acceptable. An
unnotched leg with an independently supported outboard runner connection is
a possible design alternative if that method cannot be justified; it would
require fresh geometry, connections and force assessment, not a documentation
change or a transfer of the old passing result.

No design or acceptance threshold was changed in this review.
