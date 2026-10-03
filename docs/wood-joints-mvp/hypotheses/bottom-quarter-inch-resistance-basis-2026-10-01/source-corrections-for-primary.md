# Source wording reconciliation for the primary

These are precise follow-up locations, recorded October 1, 2026. This packet
does not edit another owner's files or rewrite pinned historical receipts.
The [source note](source-note.md) supplies the actual inspected PDF hashes,
printed pages, catalog snapshots and limits.

| Existing location | Correction or clarification |
| --- | --- |
| [`bolt-resistance-basis.md:36`](../../bolt-resistance-basis.md#dowel-bending-yield-strength-fyb), and its 106 ksi wording at line 39 | Attribute `(Fy+Fu)/2` to nonmandatory NDS Appendix I.4 rather than the separately published Commentary; retain estimate/no-guaranteed-minimum status. |
| `bolt-resistance-basis.md:50` | Separate ambiguous Appendix I1 diameter wording from the TR-12 example; do not assert an unambiguous universal bolt diameter exclusion from I.4/I1. Preserve the quarter-inch product-specific source gap. |
| [`hardware-material-specification-2026-09-30/fasteners.md:77`](../hardware-material-specification-2026-09-30/fasteners.md#grade-5-bolt-and-nut-material-references) | Correct Appendix attribution. At line 79 distinguish the table parenthetical from any separately authenticated TR-12 provision. The present TR-12 URL was unavailable; its search excerpt is not inspected PDF evidence. |
| [`fyb-specification-basis-2026-10-01/README.md:33`](../fyb-specification-basis-2026-10-01/README.md#what-the-specification-permits) | Qualify the statement that the Appendix lists bolts and lag screws only at ≥3/8 in. I.4's unrestricted bolt sentence and its separate restricted lag-screw sentence do not support that absolute reading. No quarter-inch Grade 5 guarantee follows. |
| `fyb-specification-basis-2026-10-01/independent-source-review.md:48` | Preserve the reviewed historical receipt; append/link a correction rather than silently rewriting the review's source conclusion. |
| [`upper-block-strength-2026-10-01/hardware.md:70`](../upper-block-strength-2026-10-01/hardware.md#material-and-transfer-boundaries) | Correct Appendix attribution at line 71. At line 73 identify the actual inspected bolt table: Chapter 12 Table 12A's diameter rows start at 1/2 in; the 3/8 in statement is not the observed Table 12A lower diameter. |
| [`remaining-single-shear-reference-2026-10-01/README.md:60`](../remaining-single-shear-reference-2026-10-01/README.md#method-and-applicability) | Clarify Appendix ambiguity separately from the TR-12 example; retain the correct Table 12A 1/2-in lower diameter and all original unadopted 45 ksi results. Its existing explicit full-TR-12 uninspected boundary remains valid. |

Line numbers describe the bytes observed at this handoff, and the primary
should recheck them before reconciliation. These corrections affect source
attribution and scope, not the frozen 45 ksi equations, input values, source
actions, authenticated response gates or selected geometry.

The runnable report separates governing modes at every state. At A1 full
load, `side_1` remains Mode IV under both 45 and 106 ksi. The latter's
928.221778 N unadjusted reference and 0.713136407 quotient leave a required
`Cg×CΔ` budget, not a demonstrated factor. Both rail bolts instead switch
from Mode IV at 45 ksi to Mode IIIs with receiver 0 as main at 106 ksi
(the role-swapped name is IIIm). Their 106 ksi references are 851.817614 N
and 963.319448 N. These switches prevent a universal square-root scaling
of the six-mode reference; source material and timber/group conditions
remain independent unresolved inputs.
