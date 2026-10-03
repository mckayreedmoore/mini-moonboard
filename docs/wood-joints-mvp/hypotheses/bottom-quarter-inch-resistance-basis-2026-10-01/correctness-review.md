# Independent correctness and source review

Reviewed October 1, 2026 against the six packet files listed in the hash
receipt below, the pinned AWC PDFs, supplier snapshots, and all three frozen
upstream JSON reports. Scope was the quarter-inch bolt material/Fyb basis,
NDS adjustment and geometry disposition, A1 `side_1` comparison, preservation
of signed actions and ties, and the stated claim boundary. No native solve,
CAD operation, geometry or hardware edit was made.

## Result

No substantive implementation, source-basis, action-preservation, or
claim-boundary finding. The 45 ksi case remains an unadopted arithmetic
hypothesis, and the 106 ksi Grade 5 estimate remains an unadopted sensitivity.
The favorable 106 ksi quotient does not become a capacity or criterion pass.

The primary-source reading is consistent with the packet:

- NDS 2024 Chapter 12 §12.3.6.2 (printed p. 95) requires the `Fyb` used in
  `Z` to be based on yield derived by ASTM F1575 methods or tensile yield
  derived using ASTM F606 procedures. Nonmandatory Appendix I.4 (printed
  p. 185) gives `Fyb ≈ (Fy+Fu)/2` as an empirical bolt estimate. The inspected
  text calls 45 ksi reasonable for many commonly available bolts without a
  diameter qualifier, but it does not establish that value as a guaranteed
  minimum for this quarter-inch Grade 5 product. Table I1's parenthetical is
  ambiguous in isolation; its lag-screw sample sentence explicitly says
  `D ≥ 3/8 in`. The packet correctly leaves both 45 ksi and 106 ksi
  unadopted and does not claim that SAE J429 conformance alone proves the
  relevant F606 yield datum.
- The Value Fastener sheet (printed p. 115 / PDF p. 2) supports the stated conditional
  1/4–1 in Grade 5 minima of `Fy=92 ksi`, `Fu=120 ksi`, and proof stress
  `85 ksi`, plus its machined-specimen footnote. Lawson's saved FA21103 page
  identifies a 1/4-20 × 8 in Grade 5 partial-thread product and claims SAE
  J429 material/mechanical conformance. Neither source reports a tested
  bending-yield value for the delivered item. The packet correctly presents
  106 ksi only as the Appendix estimate from those declared minima.
- The pinned NDS Chapter 12 has the expected six yield modes and
  `Kθ=1+0.25(θ/90)`; Table 12.3.1B uses the 4, 3.6, and 3.2 reduction
  terms at `D=1/4 in`. The independent test oracle reconstructs all 2,016
  mode values from receiver force vectors, grain directions, lengths,
  bearing strengths, and both receiver-role assignments. The assumed
  `G=0.50` yields `Fe∥=5,600 psi`; NDS's rounded perpendicular equation at
  `D=0.25 in` yields `Fe⊥=4,450 psi`. These are explicitly conditional
  bearing inputs, not observed wood properties.
- Exact quarter inch is not sub-quarter inch: NDS Chapter 11 §11.3.6.1 and
  Chapter 12 §§12.5.1.1–.3 make the automatic `Cg=1` and `CΔ=1` exceptions
  strict `D<1/4 in` cases, while edge/row geometry provisions apply at
  `D≥1/4 in`. The packet's boundary flags are correct. Chapter 11 defines
  qualifying `Cg` rows by load alignment and requires row/member inputs; the
  pinned interface actions are oblique to their pair lines and do not support
  assigning one favorable two-bolt group or distributing demand. Leaving
  `Cg`, `CΔ`, and adjusted references null is appropriate. The note retains
  the angled-load shear-area requirement and the separate axial bearing,
  bolt/washer, splitting, and local-action dependencies.
- The service-factor values and exception are consistent with the rendered
  NDS Chapter 11 page: Table 11.3.3 gives `CM=0.4` for the wet-fabrication,
  dry-service dowel case, with footnote 2 setting `CM=0.7` below 1/4 in and
  `CM=1.0` for the listed single-fastener/parallel-row exceptions. The
  machine-readable text extractor concatenates the superscript footnote mark
  with `0.4`; visual inspection confirms this is not `0.42`.
- The producer binds all 84 A1/A12/K12 states for the four axes to exact
  upstream report hashes. The seven tests compare every copied source bolt
  row, tie, interface wrench, cleat state, and contact-cell state to its
  pinned source and assert `joint_accepted` and `adopted_capacity` are false.
  Separately, the generated output marks each `Fyb` scenario unadopted and
  the service assumptions unobserved. A1 full-load `side_1` remains
  661.948743 N lateral plus its distinct 197.1248 N tie; the unadjusted
  45 ksi ratio remains 1.094508867 and the 106 ksi reference is 928.221778 N
  with ratio 0.713136407. Both remain comparisons only. No 45/106 favorable
  result reduces a signed action, allocates a group resultant, or accepts the
  complete joint.
- `source-corrections-for-primary.md` accurately separates source attribution
  and scope corrections from frozen 45 ksi arithmetic, upstream actions, and
  selected geometry. Its corrections do not silently rewrite other owners'
  evidence.

## Findings

No substantive correctness or source-interpretation findings remain within
this bounded review.

## Checks

The packet producer replay completed successfully using the three frozen raw
reports. All seven unit tests passed, including the 2,016-value independent
mode oracle and full action-preservation comparison. Ruff reported
`All checks passed!`. These checks establish reproducibility and arithmetic
consistency only; they do not qualify the modeled joint.

## Hash receipt

All six reviewed packet files and the frozen inputs below matched the values
observed during this review. The raw PDFs and supplier snapshots remain in
their existing source-cache/local-cache locations.

| Reviewed file | SHA-256 |
| --- | --- |
| `produce.py` | `d6ff5c94264af433f0da482970119e1cecb6fffd2e92158c18efaad9cccc8666` |
| `test_basis.py` | `6c07face307dbe30690a54c6ef4f67cec96f69cb4c3e444cc101c4fec023e7b6` |
| `README.md` | `67fafbd3ed618130a7c93f393ac0732e5045676f409d0aadf7dc6e367b77f202` |
| `source-note.md` | `8f450e6603d56206b99a33f1adbbff5fba195d3b70d4be448c652376e1fea577` |
| `applicability.md` | `a899a41289da46105def694d266ec3121c51a56fd9e0a20677dd127e8b518301` |
| `source-corrections-for-primary.md` | `461f6a597e29341e837f61765d79a28de1734c8a3fe49ee5269d2292e0edd599` |
| NDS 2024 Chapter 11 source PDF | `45a3d78de1a4fba573589be0fc776e37bd581e4cedec24e38d63856161092d33` |
| NDS 2024 Chapter 12 source PDF | `53f6ec05dfd1ceabeccd4d6e88c342111678d3da4631ee7b482b706f77c1780f` |
| NDS 2024 Appendix source PDF | `1fa2bcf52803b1bbed8ea30cf13551dd5f76c90bf110ac475b401f81d116ec31` |
| Value Fastener Grade 5/8 cap-screw sheet | `76dee55df98a5e0336c256812bc3424a85173b40cc12610a5f28f5a60edb67cd` |
| Lawson/FalconGrip FA21103 HTML snapshot | `40d9039e9f8daec86c1c84a44ecab8b9963c345e575c318dd2942c1da623e7df` |
| Hardware requirements JSON | `15ec799c4ad02e1f8900537fad56eef2000afec4c9474d0e6c5591017f6ed100` |
| Pinned `fea/dowel_yield.py` | `d6c318e75c1a720d0b91f810a892e8309ef89735f66f48820ee853b753f8fe45` |
| Remaining single-shear reference report | `6551861db1112c91b87c5705bbceb3bb26f55f0d7e70029a74d828519425145e` |
| Bottom-outer placement report | `21c2eba56b80efa174cdb5ecdb206468a6b15882732c6edd548d2027063f58c3` |
| Bottom-outer joint report | `fcf393be26c433daf760a6afcf9fd6260d88f04f43a6234def960bbba4789029` |
