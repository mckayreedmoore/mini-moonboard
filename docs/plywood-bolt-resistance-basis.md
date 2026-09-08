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

Next obtain a supported larger-dowel plywood resistance method and the selected
leg/gusset plywood properties, then evaluate the intended shear planes and
member-specific thread exposure. Neither the purchased face sheet nor an
unspecified 19.05 mm leg ply supplies those properties automatically. Preserve
independent-ply behavior: two adjacent leg plies on the same side of a rim are
not a symmetric timber-between-two-side-members double-shear joint.

These are input requirements for the pending calculation, not findings of
physical failure. No bolt resistance, equal load sharing, glue contribution or
clamping-friction capacity is assigned by this source check.
