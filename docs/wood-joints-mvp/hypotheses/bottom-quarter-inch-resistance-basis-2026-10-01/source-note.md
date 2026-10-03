# Quarter-inch material source and method boundary

Checked October 1, 2026. The [prior source disposition](../fyb-specification-basis-2026-10-01/README.md)
already separates the NDS test-derived route from a conditional estimate.
This note checks its application to the four bottom-left bolts, corrects an
overly absolute reading of the Appendix's diameter wording, and binds the
arithmetic to the existing source actions. No hardware is selected.

## Inspected sources

Raw PDFs and the supplier page remain local. The AWC PDFs were authenticated
in the upper packet's existing `source-cache/`; the supplier snapshots are in
`/tmp/mini-moonboard-bottom-quarter-inch-resistance-sources-2026-10-01/`.

| Source | Inspected location / SHA-256 |
| --- | --- |
| [NDS 2024 Chapter 12](https://awc.org/wp-content/uploads/2026/09/AWC_NDS2024_withCommentary_20260911_Website_Chapter-12-Dowel-Type-Fasteners.pdf) | §§12.3.6.2/.7.2, p.95; §12.3.9.1, p.96; §12.5.1, pp.97–99; Table 12A, p.101. `53f6ec05dfd1ceabeccd4d6e88c342111678d3da4631ee7b482b706f77c1780f` |
| [NDS 2024 Chapter 11](https://awc.org/wp-content/uploads/2026/09/AWC_NDS2024_withCommentary_20260911_Website_Chapter-11-Mechanical-Connections.pdf) | §§11.2.2/.3, 11.3.2–.6; Tables 11.3.1/.3/.4, pp.71–75. `45a3d78de1a4fba573589be0fc776e37bd581e4cedec24e38d63856161092d33` |
| [NDS 2024 nonmandatory Appendix](https://awc.org/wp-content/uploads/2026/09/AWC_NDS2024_withCommentary_20260911_Website-Appendix.pdf) | I.4, p.185 / PDF p.20; Table I1, p.186 / PDF p.21. `1fa2bcf52803b1bbed8ea30cf13551dd5f76c90bf110ac475b401f81d116ec31` |
| [Value Fastener Grade 5/8 cap-screw technical sheet](https://www.valuefastener.com/documents/products/capscrewgr5-8.pdf) | PDF p.2 Grade 5 size band and footnote. `76dee55df98a5e0336c256812bc3424a85173b40cc12610a5f28f5a60edb67cd` |
| [Lawson/FalconGrip FA21103](https://www.lawsonproducts.com/products/hex-cap-screw-grade-5-1-4-20-x-8-fa21103) | Product description and technical specifications. HTML snapshot `40d9039e9f8daec86c1c84a44ecab8b9963c345e575c318dd2942c1da623e7df` |

Chapter 12 §12.3.6.2 names F1575 bending yield or
“tensile yield strength derived using the procedures of ASTM F 606.”
Appendix I.4 supplies an approximate relation for bolts, `Fyb ≈ (Fy+Fu)/2`.
Using declared Grade 5 minima gives `(92+120)/2 = 106 ksi`. The supplier's
quarter-inch through one-inch size band supports conditional direct-steel
`Fy=92 ksi`, `Fu=120 ksi`, and proof stress `85 ksi`; its footnote identifies
machined-specimen testing when full-part testing is unavailable. This sheet
does not supply an exact-part bending test or an inspected J429-to-F606 test
clause. The estimate is neither a guaranteed minimum nor an adopted input.
Setting `Fyb=Fy=92 ksi` is not justified by this source chain.

The [ASTM F1575 publisher scope](https://store.astm.org/f1575_f1575m-24.html)
describes static bending-yield measurement. The
[SAE J429-2014 publisher record](https://saemobilus.sae.org/standards/j429_201405-mechanical-material-requirements-externally-threaded-fasteners)
supplies edition metadata; its full test clauses were not inspected. No new
delivered-specimen test is imposed: a suitable product/specification/data
basis and reviewed evaluation could support the recognized route.

## Diameter wording and the 45 ksi hypothesis

Appendix I.4 says 45 ksi is reasonable for many commonly available bolts
without an express diameter qualifier. Its next sentence limits the cited
lag-screw samples to `D≥3/8 in`. Table I1's row says
“Bolt, lag screw (with D ≥ 3/8"), drift pin.” The parenthetical naturally
attaches to lag screws; the wording does not unambiguously exclude all
quarter-inch bolts. The earlier note's blanket interpretation is therefore
too absolute. The row's Grade 1 example also does not establish the exact
quarter-inch Grade 5 product's bending yield or a guaranteed lower bound.

The official [TR-12 2026 URL](https://awc.org/wp-content/uploads/2026/06/TR-12_2026_formatted.V3.pdf)
returned HTTP 404 during this check. Its search-index excerpt was located,
but the full PDF was not inspected or hashed and supplies no adopted basis
here. Table 12A's inspected tabulated bolt diameters start at 1/2 inch.
Neither this table nor the preceding approximate discussion establishes the
specific quarter-inch input needed for adopted resistance. The existing
45 ksi case remains a declared arithmetic hypothesis. This is a source-gap
disposition, not proof that a physical bolt is weak or that this geometry
fails an adopted criterion.

## Exact catalog binding and threads

Lawson identifies FA21103 as 1/4-20 × 8 in, Grade 5, partial-thread UNR,
minimum thread length 1 in, minimum tensile strength 120 ksi and ANSI
B18.2.1 dimensions. Its description states
“Conforms to SAE J429 material and mechanical properties.” That is a
source-backed catalog lead for the flagged `side_1` length family, not a
chosen/received part, numeric `Fyb`, or confirmation of a delivered thread
transition. The 6 in rail family's exact-item material binding is weaker;
an 8 in part's statement does not qualify a different SKU.

The existing pinned [hardware requirements](../hardware-material-specification-2026-09-30/requirements.md)
give `side_1` two 88.9 mm bearing intervals, a sufficient last-thread-scratch
coordinate `LB≥157.607 mm`, and an 8 in conditional B18.2.1 class minimum
`LB=171.450 mm`, margin 13.843 mm. This screens the quarter-thread bearing
condition separately in each receiver if that class and full-body diameter
apply. It does not locate usable full-form threads or prove nut travel.
The lateral calculations retain the inherited ideal smooth `D=0.25 in`
scenario and do not silently change it to a tolerance-bound diameter.
Diameter/thread location, nut fit, washer metal/contact and actual
conformance remain separate inputs. No receipt or physical observation is
claimed.
