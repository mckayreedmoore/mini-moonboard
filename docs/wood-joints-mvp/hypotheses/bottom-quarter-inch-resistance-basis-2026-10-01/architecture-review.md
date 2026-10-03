# Architecture and integration review

Reviewed October 1, 2026. **Disposition: clean scoped receipt; no packet-code
or integration defect found.** This review covers `produce.py`, `test_basis.py`,
`README.md`, `source-note.md`, `applicability.md`, and the owner handoff
`source-corrections-for-primary.md`. It does not modify the frozen model,
inputs, source notes, or upstream packets.

## Findings

The producer has a narrow dependency surface: it imports the existing
`fea.dowel_yield.single_shear` helper, whose exact bytes are pinned, and uses
Python's standard library for validation and serialization. It pins all three
raw report hashes, the hardware requirements JSON, and the three AWC PDFs.
The source reports also have to agree on candidate and geometry revision, and
the expected report-to-report links are checked. The README's producer command
replayed successfully from the repository root with `.venv/bin/python`.
Every embedded file and report pin checked out in this workspace.

The source-action boundary is preserved. The producer selects exactly 84
states for the four named bottom-left axes across A1/A12/K12, validates the
signed receiver vectors and their resultant, and emits each source row intact,
including its separate same-state signed outer tie. It carries through 168
member/bolt states, 84 interface-wrench states, 21 complete-joint states, 252
contact-cell states, eight placement records, and the four matching hardware
requirement rows. Nothing in this data flow allocates a favorable resultant
back to bolts or substitutes a lateral scalar for the complete action.

The calculation remains conditional and lane-specific. The raw inputs bind it
to `compact-floor-flush-wood-joints-development` and
`led-clearance-2x6-runner-seated-blocks-v1`; the packet describes only the
three rear cases and says the selected baseline is unchanged. Neither the
45 ksi hypothesis nor the 106 ksi Appendix estimate is adopted. The exact
quarter-inch trigger is implemented and tested at the boundary: automatic
sub-quarter-inch `Cg` and `CΔ` exceptions are false at 0.25 in. The output
leaves `Cg`, `CΔ`, and adjusted resistance null. The side and rail receiver
groups stay distinct, with group, row, geometry, and signed-action questions
open. No case pass, material qualification, physical observation, or complete
joint acceptance is claimed.

The source note supports the 45 ksi case as an arithmetic hypothesis and
corrects the prior blanket reading of the Appendix diameter parenthetical.
It derives 106 ksi only as the nonmandatory Appendix I.4 estimate from
conditional Grade 5 `Fy`/`Fu` minima, and explicitly leaves product-specific
`Fyb`, delivered-part conformance, and the test/evaluation path unresolved.
The adjustment note likewise declares dry/normal/temperature assumptions as
unobserved analysis inputs, keeps alternate moisture cases unapplied, and
separates wood adjustment factors from direct-steel resistance. These
boundaries agree with the producer's null acceptance fields and the retained
complete-action records.

`test_basis.py` contains a separate closed-form oracle driven from the signed
source vectors and pinned receiver grains. It checks the 2,016 mode values,
exact source-row retention, mode changes, the diameter boundary, and rejection
of altered or incomplete inputs. I inspected the tests but did not run the
test suite. The README's documented producer replay was run.

The AWC PDFs and supplier snapshots are present at the paths named in the
source note, and their SHA-256 values match its entries. The AWC files are
enforced by the producer. The Value Fastener PDF and Lawson HTML capture are
manual source-review evidence and are not consumed or pin-checked by the
producer; both currently reside under `/tmp`. This does not prevent calculation
replay in this workspace, but repeating the supplier-source review in a fresh
environment depends on retaining or reacquiring those captures. The note
discloses that locality.

The separately supplied `source-corrections-for-primary.md` lists precise
upstream wording locations and asks that historical receipts be preserved.
It is a primary-owned reconciliation handoff; this review makes no upstream
edits and does not rewrite that handoff or any existing review receipt.

## Reviewed hashes

| File | SHA-256 |
| --- | --- |
| [`produce.py`](produce.py) | `d6ff5c94264af433f0da482970119e1cecb6fffd2e92158c18efaad9cccc8666` |
| [`test_basis.py`](test_basis.py) | `6c07face307dbe30690a54c6ef4f67cec96f69cb4c3e444cc101c4fec023e7b6` |
| [`README.md`](README.md) | `67fafbd3ed618130a7c93f393ac0732e5045676f409d0aadf7dc6e367b77f202` |
| [`source-note.md`](source-note.md) | `8f450e6603d56206b99a33f1adbbff5fba195d3b70d4be448c652376e1fea577` |
| [`applicability.md`](applicability.md) | `a899a41289da46105def694d266ec3121c51a56fd9e0a20677dd127e8b518301` |
| [`source-corrections-for-primary.md`](source-corrections-for-primary.md) | `461f6a597e29341e837f61765d79a28de1734c8a3fe49ee5269d2292e0edd599` |

The three raw-report pins, existing helper pin, hardware-requirements pin, and
AWC PDF pins were also checked against their bytes. The supplier captures
match the hashes documented in `source-note.md`.
