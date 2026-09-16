# Rim end and support resolution study

## Decision

Do not release the flush rim cut by renaming its existing projected-seat-depth
comparison as an NDS notch check. That calculation has not established the
required geometric mapping. Investigate removing the vertical heel and keeping
the full horizontal bevel first, retaining the compact 2×6 header and its
existing bearing footprint. This avoids adding a wedge and its restraints.
The cut-face classification still needs current-case verification as described
below. A square-ended rim with a fitted timber bearing wedge is a fallback
geometry, not a qualified or selected replacement.

The fallback removes the rim's compound heel/seat cut from the resistance
question. It introduces explicit wedge material, bearing, restraint and joint
checks. Those checks cannot be replaced by the old assembly's passing ratios.

## Method basis

The primary [NDS 2024 Chapter 4, §4.4.3 and Figures 4A–4B](https://web-media.awc.org/wp-content/uploads/2021/12/17210008/AWC_NDS2024_20241011_AWCWebsite_Chapter4.pdf)
limits end notches and tapers; the compression-face figure places its remaining
depth dimension at the inner support edge. [Chapter 3, §3.4.3.1 and Figure 3D](https://web-media.awc.org/wp-content/uploads/2021/12/17210019/AWC_NDS2024_withCommentary_20240718_AWCWebsite_Chapter-3-Design-Provisions-and-Equations.pdf)
routes tension-face tapers through end-notch shear treatment. Both figures
were visually inspected. The downloaded chapter 4 source also confirms that
merely having a convex outline does not establish an exemption.

The existing calculation projects the entire horizontal seat onto the rim's
depth direction. That is neither an intersection at the inner support edge
nor a demonstrated tension-notch equivalent. The adjacent full-section stress
diagnostic includes tension on the removed heel face, so a compression-only
interpretation is unsupported. No alternate stress-concentration factor or
capacity is introduced here.

## Preferred first investigation: full horizontal bevel

Remove the vertical heel cut. The horizontal termination at Z277 then extends
from Y−223.862729528 to Y−41.497331208. Keep the header unchanged. Actual
bearing remains Y−175.7 to Y−41.497331208, length **134.202669 mm**;
the free exterior tail is **48.162730 mm**. The sources reviewed do not
establish a requirement to support the entire 182.365398 mm bevel footprint.
Check required bearing area, local forces and the free tail directly.

This change removes a cut on the CAD **q−** face. The surviving horizontal
bevel reduces the opposite **q+** face as grain-normal stations approach the
end. Therefore, the earlier tensile diagnostic on q− does not itself classify
the surviving bevel as a tension-face cut. The NDS compression-taper route,
if supported by the actual q+ stresses, has full remaining depth **139.7 mm**
at the inner support edge and zero inward taper extension there. It does not
use the old 102.805 mm terminal-seat projection.

The saved A12-left gross-section q+ corner stresses are −0.199079/−0.185325 MPa
without coincident loads and −0.025550/−0.160535 MPa with them. The right rim
has −0.003703/+0.014949 MPa despite zero rim/header contact force in that case.
Thus the existing response does not support a blanket compression-only claim
for both rims. These are adjacent full-section stresses, not a local partial
section solution; fresh geometry, contacts and each relevant case must establish
the actual face classification and connection-induced local demands.

The [AWC 2018 Manual, printed page 36](https://web-media.awc.org/wp-content/uploads/2022/01/17210413/AWC-2018-Manual-1810.pdf)
contrasts engineered I-joists with conventional lumber and reports a historical
45-degree bevel shear convention. The proposed end is 40 degrees from a
grain-normal cut, or 50 degrees from grain. This is useful evidence that an
ordinary end bevel need not be equated to every notch. However, that discussion
concerns fire-cut-style geometry and does not provide a stand-alone 2024
exemption for this inclined, combined-load joint. Do not use it to skip the
current cut-method mapping or local connection checks.

## Exact geometry for a square-ended rim

All coordinates are millimetres in the existing assembly datum. Preserve the
rim's grain, transverse position, full 88.9 × 139.7 section and upper geometry.
At the current first full section, use one grain-normal end plane:

- Local grain station: **−1183.619990337**.
- High end-face point `(Y,Z)`: **(−148.513739912, 366.797429073)**.
- Low end-face point `(Y,Z)`: **(−41.497331208, 277.000000000)**.

Each independent wedge has the two points above and a third point
`(−148.513739912, 277)` in its side profile. Its X extent matches its rim.
Its horizontal base is **107.016409 mm** long and its rise **89.797429 mm**.
Its base fits the unchanged header footprint `Y=[−175.7, −36]`, with **27.186260**
and **5.497331 mm** nominal margins. A single nominal 6×6 blank can contain
this geometry with grain along Y; an 88.9-mm-thick 4×6 blank cannot contain
the required rise. This is a separate bearing block, not doubled vertical
stock or an assumed composite member.

Run `python3 scripts/floor_runner_rim_support_options.py` to reproduce these
coordinates directly from the preserved geometry JSON. No CAD file changed.

## Required engineering work for this option

1. Establish fitted contact between the rim end and wedge and between the wedge
   and header, including real contact area rather than nominal point pressure.
2. Provide a positive connection for the horizontal thrust and uplift. Do not
   rely on unmeasured interface friction to keep the wedge in place. Existing
   angle actions and screw positions must be recalculated after the cut.
3. Check rim end bearing, wedge compression at its actual grain angle, wedge
   shear/splitting, header bearing and each restraint's fastener geometry.
   The wedge's pointed tip is not an assumed effective load-carrying section.
4. Model the changed contacts, restraints and member ends in all current cases.
   The rim no longer carries load through the removed tail; old equivalent
   beam offsets and gravity must not silently persist.

## Other bounded options

Restoring a 10 mm heel reserve to `Y=−185.7` gives **2.690653 mm** positive
margin in the historical projected-depth comparison, including its existing
3 mm allowance. It leaves timber beyond the header edge and does not establish
the missing NDS mapping. Restoring 7 mm leaves only **0.392520 mm** after that
allowance. Neither is adopted as a resistance resolution here.

Removing the vertical heel entirely produces a horizontal rim end from
`Y=−223.862729528` to `−41.497331208`, length **182.365398 mm**. This exceeds
the current 139.7 mm header footprint by **42.665398 mm**. A nominal 2×8
header could nearly contain that end only after shifting its position, with
less than 1.8 mm total nominal excess width. A wider header alone neither
establishes a cut-method exemption nor resolves the angle's unlisted actions.
The fitted-block option therefore deserves investigation before enlarging
the compact base solely to satisfy the old scalar.
