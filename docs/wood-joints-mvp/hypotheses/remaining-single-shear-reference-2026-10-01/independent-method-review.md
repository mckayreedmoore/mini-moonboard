# Independent method review

**Disposition:** No unresolved material method finding in the bounded reference
census. The output is an unadjusted, conditional single-fastener lateral-yield
comparison for two-receiver axes. It is not an adopted resistance, complete
joint check, or acceptance result.

This review is bound to the final README SHA-256
`f17fe0e85bf25bfd34d7cc379442f656f23db0ef4c888bba8666a7c4484e6e34`, producer
`5f2a7fdca2ef0c56c661fa10e4122189f8a7a1ae0725062cb8c56d95dd911edf`, focused
tests `4f5431999333fa1904ac1296416ac36cce210c54cd11fa893def00e2cb03d4a0`,
closed-form verifier `848e65019ad87dfb7ad07916f845511e1fe78931df070b5242161a79af133e54`,
and replay JSON
`6551861db1112c91b87c5705bbceb3bb26f55f0d7e70029a74d828519425145e`.
The reviewed NDS PDF is
`docs/wood-joints-mvp/hypotheses/hardware-material-specification-2026-09-30/materials-source/AWC_NDS2024_withCommentary_20250328_WebsiteChapter-12-Dowel-type-fasteners.pdf`, SHA-256
`5fc837523ff10acc097a162718700a9b4ba64e627d2b0023439146d42fe4ee2a`.

## Source and method

I rendered and inspected the pinned 2024 NDS Chapter 12 pages. Printed p.91
(Table 12.3.1A and §12.3.1) gives the six single-shear yield equations and
requires contacting member faces, load perpendicular to the dowel axis, and
minimum spacing/end/edge distances. Printed p.92 (Table 12.3.1B) gives the
diameter-dependent reductions and `Kθ = 1 + 0.25(θ/90)`, with `θ` the largest
load-to-grain angle among members. Printed pp.93–94 give the solid-wood `Fe`
equations, 50-psi rounding, and the DF-L assigned `G = 0.50`. Printed p.95
(§§12.3.4–12.3.7) covers load-angle interpolation, dowel bearing length,
the ASTM F1575/F606 basis for `Fyb`, and full-body/root diameter rules. Table
12A, printed p.101, supplies the full-body bolt `Fyb = 45,000 psi` scenario.
Those source provisions support the equations and stated assumptions; they do
not establish that a delivered bolt or timber has those properties or that all
connection conditions are met.

The producer pins and reuses `fea/dowel_yield.py`,
`mini_moonboard/bolted_timber_checks.py`, and the existing NDS scenario wrapper
in `mvp-acceleration-2026-09-28/nds-screen/`. Their reviewed SHA-256 values are
respectively `d6c318e75c1a720d0b91f810a892e8309ef89735f66f48820ee853b753f8fe45`,
`a1414547d9eaa3d60e81482b4a2cac2d49e88f31aafa341dca5be9ec8ef4aa13`, and
`21d3b2b254b1ceb9a6cf777b98eb492b52f989cc019afa2209b92be3e4a3cdb0`; the
scenario JSON is pinned at
`130041246af11fc8e3568a7091f585d0d75581b2e1fbb3a3f4b97b750d68a7ea`.
I also compared direction and reduction handling with
`docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-corner-resultant-direction-single-shear-attempt01/produce.py`
(SHA-256 `d14ece8fd0d32e790e4f3de67aa8d860e6881231d6421b650e5b47f699aab57f`):
both compute each receiver's acute angle from its actual lateral resultant to
the proposed grain axis and use the greatest member angle in the same pinned
wrapper.
The resulting calculation is algebraically consistent with NDS Table 12.3.1A:
it uses the conditional quarter-inch full-body diameter and zero-gap scenario,
`q = Fe·D`, `M = Fyb·D³/6`, the six single-shear modes, and the Table 12.3.1B
reductions. The independent comparison recalculates NDS equations without
importing either production helper.

For each lateral plane, the source join checks the force pair and receiver
order, uses the signed resultant direction separately against each proposed
grain axis, and applies the larger grain angle in `Kθ`. The two main/side role
assignments are checked under the appropriate mode permutation (`Im↔Is`,
`IIIm↔IIIs`, with `II` and `IV` unchanged); their governing references must
agree. Source-derived current-shaft intervals are checked against the long
probe and their shared interface datum. These are modeled lengths and proposed
grain directions, not inspected stock or purchased bolt-length instructions.
The same-state outer tie is recorded separately and is not added to lateral
demand.

## Census, checks, and limits

The 52 two-receiver axes produce 1,092 rows across three cases and seven states
per case. Forty-two transverse-to-grain axes have references in 882 rows. Ten
axes with a fastener parallel to one receiver grain retain explicit null
references and ratios for 210 rows. This is the reused helper's applicability
limit, not an absence of an NDS method: §12.3.3.4 (printed p.92) specifies
`Fe⊥` for a qualifying main-member end-grain connection, and §12.5.2.2
(printed p.100) specifies `Ceg = 0.67`. Neither route is calculated or applied
here. The continuous three-receiver side bolts also remain excluded from this
two-member method. Section 12.3.8 (printed p.96) gives separate multi-member
procedures; none is adopted in this packet.

I reran `parent_verify.py` against the pinned replay JSON. It passed all 1,092
state identities, the 882/210 applicability partition, source-file hashes,
and 10,584 direct mode comparisons; the largest relative difference was
`9.695710447204099e-16`. The one ratio above one is the explicitly
unadopted scenario at `bottom_outer/clip_horizontal_bottom_left_1/side_1`,
A1 full load: 661.948743 N / 604.790663 N = 1.094508867, Mode IV. It is not an
adopted failure or a pass. No service, geometry, group, end-grain, or complete
joint adjustment is established by this census.

The six focused unit tests and Ruff check pass on the pinned files. During
review, a test initially applied the half-inch TR-12 example to the packet's
quarter-inch helper; the test was corrected to exercise the actual half-inch
benchmark. A test fixture was also updated for the producer's explicit bolt
axis argument. My first independent transcription of the NDS `k1` exponent
was wrong; the rendered p.91 equation is
`sqrt(Re + 2Re²(1 + Rt + Rt²) + Rt²Re³)`, and the parent verifier was corrected
before the final passing replay. These were resolved test/oracle issues, not
remaining producer findings.

The official 2026 TR-12 binary remains uninspected; the existing
[attempt06 packet](../evaluation-resume-2026-09-24/current-steel-direct-screen-attempt06-tr12-2026/README.md)
records direct-access failure and partial official search-index excerpts
only. This review does not claim a new-edition TR-12 method review.
The existing three-case producer replay was performed by the parent; I
independently reran its equation/source cross-check and focused tests. No native
solve or candidate acceptance review was performed.
