# Plywood bolt resistance: verified scope boundary

Checked September 8, 2026 against the
[2024 NDS, Chapter 12](https://awc.org/wp-content/uploads/2026/08/AWC_NDS2024_withCommentary_20250328_WebsiteChapter-12-%E2%80%93-Dowel-type-fasteners.pdf).
The locally inspected PDF has SHA256
`5fc837523ff10acc097a162718700a9b4ba64e627d2b0023439146d42fe4ee2a`.
No vendor PDF is redistributed.

Section 12.3.3.2 and Table 12.3.3B (printed pages 92 and 95) limit the tabulated
wood-structural-panel dowel-bearing values to fasteners of diameter at most
1/4 inch. They do not directly qualify this candidate's 3/8-inch bolts.
Section 12.3.3.1 separately excludes wood structural panels from its ordinary
wood-member table route. Do not silently treat plywood as solid Douglas-fir.

Section 12.3.7 distinguishes full-body and reduced/threaded diameters. Its
nominal-diameter exception for threaded full-body fasteners requires threaded
bearing length no greater than one quarter of bearing length in the member
containing those threads; otherwise use the applicable reduced-diameter or
permitted detailed-analysis route. Section 12.3.6 requires a supported bolt
bending-yield basis. Catalog tensile strength alone is not an assembled wood
joint rating.

## Application to this candidate

The leg-to-rim, leg-ply stitch and base-gusset groups therefore remain open.
The [hardware record](selected-bolt-hardware.md) already identifies threads
inside the nut-side grip, but its historical total-stack lengths must not be
substituted for each current member's individual bearing length. Map the thread
boundary through each actual member before selecting a yield-equation diameter.

The follow-up TR12 source below supplies a larger-dowel plywood bearing input.
Use it to evaluate the intended shear planes and
member-specific thread exposure. Neither the purchased face sheet nor an
unspecified 19.05 mm leg ply supplies those properties automatically. Preserve
independent-ply behavior: two adjacent leg plies on the same side of a rim are
not a symmetric timber-between-two-side-members double-shear joint.

These are input requirements for the pending calculation, not findings of
physical failure. No bolt resistance, equal load sharing, glue contribution or
clamping-friction capacity is assigned by this source check.

## Resolved larger-dowel bearing route: AWC TR12

[AWC Technical Report 12, Appendix A.3 and Table A1, printed pages 25 and 27](https://web-media.awc.org/wp-content/uploads/2021/12/17210714/AWC-TR12-1510.pdf)
explicitly supplies **Fe = 5,600 psi (38.6106 N/mm²)** for plywood with bolts
larger than 1/4 inch, regardless of species and face-grain direction. This is a
reference dowel-bearing input to the connection equations, not an allowable
bolt force or a plywood bending/splitting property. Its equivalent G=0.50 must
not be used as a measured density or to infer other plywood strengths.

The retrieved TR12 is the October 2015 edition; local SHA256 is
`95abb7d382aadf6984121f8731a5b91c2b633516e7f134991ad0a34a1b916be2`.
Retain the distinction from the 2024 NDS small-dowel table above. This resolves
the previously missing larger-dowel bearing source, not all joint inputs.

Proceed with conditional yield-mode calculations using the actual member stack,
supported bolt bending properties and the applicable diameter. Keep geometry,
group effects, splitting, net section, independent-ply transfer and combined
axial/lateral loading as separate checks. Do not multiply 5,600 psi by projected
bearing area and report that number as the joint's allowable resistance.
