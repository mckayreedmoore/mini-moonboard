# Independent source review: conditional bolt `Fyb` basis

Reviewed October 1, 2026. I reviewed the adjacent `README.md` against the
two pinned AWC source PDFs and the official ASTM/SAE publisher pages linked
there. I found no material source-interpretation error. The draft preserves
the distinction between an exploratory estimate from a grade specification
and an adopted, product-specific NDS input.

## Source check

The PDF bytes in the upper-block packet's local source cache match the
recorded hashes:

| Source | Reviewed provision | SHA-256 |
| --- | --- | --- |
| [NDS 2024 Chapter 12](https://awc.org/wp-content/uploads/2026/09/AWC_NDS2024_withCommentary_20260911_Website_Chapter-12-Dowel-Type-Fasteners.pdf) | §12.3.6.2, printed p. 95 / PDF p. 17 | `53f6ec05dfd1ceabeccd4d6e88c342111678d3da4631ee7b482b706f77c1780f` |
| [NDS 2024 Appendix](https://awc.org/wp-content/uploads/2026/09/AWC_NDS2024_withCommentary_20260911_Website-Appendix.pdf) | Nonmandatory I.4, printed p. 185 / PDF p. 20; Table I.1, printed p. 186 / PDF p. 21 | `1fa2bcf52803b1bbed8ea30cf13551dd5f76c90bf110ac475b401f81d116ec31` |

The reviewed draft was [README.md](README.md), SHA-256
`515f037339e69901b56ead2731855c3a7da81784d01d268121bcee3ee9ed9ebe`.
The source attribution is correct: I.4 is part of the NDS's expressly
nonmandatory Appendix, not the separately published Commentary.

## Interpretation

NDS §12.3.6.2 says the `Fyb` used to determine reference lateral value `Z`
must be based on yield derived using ASTM F1575 methods or tensile yield
derived using ASTM F606 procedures. The clause gives these as alternatives;
it does not require a new bending test on each delivered bolt for a
conditional analytical sensitivity. ASTM's public descriptions of
[F1575/F1575M-24](https://store.astm.org/f1575_f1575m-24.html) and
[F606](https://store.astm.org/standards/f606) confirm that F1575 measures
bending-yield moment/strength, while F606 supplies mechanical test
procedures and defers property requirements and applicable tests to
individual product standards. Neither public scope page establishes that a
specific J429 Grade 5 product has an F606 tensile-yield result suitable for
this connection.

Nonmandatory Appendix I.4 describes using tensile-test data to estimate
`Fyb` when direct bending tests are impractical for short, large-diameter
fasteners. Its research-based relation is an approximation, not a guaranteed
minimum or specified product property. Applying it to the stated hypothetical
Grade 5 minima gives `(92 + 120)/2 = 106 ksi`; that is a conditional estimate
for sensitivity work, not an F606-derived result or adopted NDS resistance
input. The README labels this limitation accurately. It also correctly
declines to infer `Fyb = Fy`.

Table I.1's 45 ksi row covers bolts/lag screws with `D ≥ 3/8 in` and drift
pins, with a Grade 1 example. It cannot establish a quarter-inch value or
lower bound. Its Grade 1 example is consistent with caution about treating
the research approximation as a guaranteed result.

The README also correctly leaves the J429-to-F606 link unresolved: the
[public SAE J429-2014 record](https://saemobilus.sae.org/standards/j429_201405-mechanical-material-requirements-externally-threaded-fasteners)
supplies edition metadata, while the full J429-2014 test clauses were not
inspected. The 92/120 ksi inputs remain assumptions from
the existing hardware screen, not an independently verified J429 table or
an assertion of exact SKU conformance. A separate delivered-specimen test is
not established as the only possible route; the missing item for a
product-specific adopted input is a reviewed basis showing how that chosen
fastener supplies and evaluates the NDS-recognized yield data.

This source review adopts no strength, verifies no delivered hardware, and
establishes no joint pass. The steel first-yield check and the wood-connection
lateral-yield `Fyb` input remain distinct questions.
