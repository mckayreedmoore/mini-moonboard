# Current center-kicker source audit review

This review covers only the source-only packet for
`compact-floor-flush-wood-joints-development`, revision
`led-clearance-2x6-runner-seated-blocks-v1`. The primary authorized the bounded
audit; this secondary changed only its assigned folder. No CAD import,
native solve, model/source geometry change, shared-document edit, staging,
commit or push was performed.

## Findings and disposition

The first independent Luna/max pass used three disjoint reviewers, with no
peer notes or review record shared:

- Correctness, `/root/center_backing_correctness`: no substantive findings.
- Testing, `/root/center_backing_testing`: preserve per-pair broadphase
  status so exact separation and upstream AABB separation remain distinct.
  Fixed by the complete 97-row pair census and an identity test that swaps
  flags while preserving aggregate counts.
- Architecture, `/root/center_backing_architecture`: current authority must
  identify the reviewed candidate/revision and all three unique required
  obligations. Fixed by explicit identity, scene/report/snapshot binding,
  unique-complete ID and pending-status guards, with refusal mutations.

Pre-review exact-byte verification also exposed unordered stock-list
emission. Sorted member identity order and its regression test resolve that
reproducibility defect. No geometry or action value changed.

The second fresh pass found no substantive correctness or architecture
findings. Testing identified an authority geometry-label substitution:
another already-pinned path and its matching hash could be accepted under
the wrong geometry label. Fixed by requiring the exact separately reviewed
path and hash for each label, with a matching-path-and-hash substitution
refusal test. The observed current source was correct throughout.

The third fresh pass closed on the final frozen bytes:

- Correctness, `/root/center_backing_closing_correctness`: no substantive
  findings; source identities, pair census, actions and claim boundaries match.
- Testing, `/root/center_backing_closing_testing`: proposed semantic handling
  for a future edit to the edge-obligation prose. The primary accepted an
  explicit bounded deferral: today's text was manually audited and is
  hash-frozen in this report; changed text refuses the saved `--verify`.
  Regeneration under revised authority requires a new source review. This
  packet includes no generalized authority updater or automatic acceptance.
- Architecture, `/root/center_backing_closing_architecture`: withdrew its
  registry/coverage drift finding after confirming the immutable atlas pins
  enforce both files before the authority loop. The current registry path/hash
  and all three pending statuses match. It also withdrew its runtime finding
  because observed-runtime byte binding is intentional. No substantive
  architecture findings remain.

No confirmed in-scope defect remains. The future authority updater is
explicitly deferred, not presented as implemented. Runtime portability is
also limited: the canonical report records the observed Python version and
refuses changed bytes under another version. Cross-patch byte reproduction is
not promised. The synthetic tests need the documented repository-shaped
layout and project Python, without the saved CAD/native artifacts.


## Validation and independent comparisons

The focused suite passes 42 tests with no repository conftest. Ruff checking
and formatting pass. The same 42 tests pass with only the six Python files
copied into an otherwise empty temporary repository-shaped directory tree,
without source JSON, STEP or native artifacts. The producer assumes its
documented repository-relative directory depth; arbitrary flat relocation
is not the supported clean-checkout layout.

Pure metadata `produce.py --write` followed by exact-byte `--verify` passes.
Verification under separate Python hash seeds reproduces the saved bytes.
All 302 current pin hashes and sizes match. The four upstream panel, surface,
axis and stock closures match; the atlas retains 216 matching pins and its
one exact disclosed `STALE_PROSE_INPUT`. Its broad historical closure remains
`REFUSED`. The original expected binding is preserved alongside current
bytes; current authority and reviewed geometry bindings are independently
checked. No public historical geometry replay is claimed.

The independent raw geometry comparison imports no packet helpers. It uses
saved edge endpoints for seam incidence, corner shoelace area and circle
circumference for removed areas. All six direct rear timber patches match;
the maximum area difference is 4.3655745685100555e-9 mm². It matches all 97
per-pair states/flags, including four exact-separated and 78 AABB-separated
pairs, both covered intervals [238.9, 277] mm and lower gaps [0, 238.9] mm,
the 141.0725/142.8875 mm lower support offsets and all 302 current pins.

The independent raw duty comparison authenticates the six input reports
against their frozen hashes and imports no helpers. It matches four screw
identity/receiver/bore records, all 84 signed screw-state records and 252
source scalar components, 84 recursive summaries, 84 physical endpoint
summaries and 42 panel-contact summaries. Eight structural bolt records,
two separate direct-seat/cleat routes and five stock records match the raw
graph/inventory. This is saved-record equality, not an independent native
solution or downstream joint force allocation.

The separate raw authority comparison verifies the criteria source path/hash
join and matching pending statuses for `actual_kicker_cutouts`,
`center_kicker_receiver_paths` and `complete_load_path_coverage`. Both registry
and coverage bytes have immutable expected hashes in the atlas closure.
Observed replay Python: 3.12.3.

## Frozen artifacts

| File | SHA-256 |
| --- | --- |
| README.md | `abb632a9a9b47322c9784fc1977df1808754c107684565dcc54ade6d87517862` |
| backing-duty.json | `79f7058b9067d4c0a34206d04f6c6580c005a603a42388dd00bb54ac070979ad` |
| backing.py | `398bd2c5ec609cd56a8bde57af0ce436c553766de0d55841fdfcc7685547e53f` |
| duties.py | `a7078fba5a4bb305b37d7bb33f3e434de3b62fa3ba686964276fa91e0f9c33a1` |
| plan.md | `ff2b9d10f7221980bd9588ef06830e8a372dc495c92c7ad6381d78b8ab40bd7f` |
| produce.py | `29852d7ea5a35ce443f2ec199a41d32a8d0ff90393c3fef927f9e208dcf2e669` |
| source-dependency-note.md | `97c40cd86aa2d96efc5e540adffc5fbfffac8cddc34acf40725967a0200e58e4` |
| source-pins.json | `6bac530fd7374ddc40e3948f885befcbb5c2ebead61a4c6e17df4e46b5198d6d` |
| test_backing.py | `97761b428923516df38c42003209478eb8c736ac0ab15106c234b181884d7186` |
| test_duties.py | `a4963c727167eb5c3f5642368238a807a8b1512a019d34d4d331bba5f9a0f038` |
| test_produce.py | `cae9320bdaff99274c5ec528bce87bb8e78ac2a9b3ffe998243f4d16f2fc1996` |

The report and source manifest are ignored local evidence. This review is
kept outside the producer's source closure to avoid output-hash cycles.

Independent receipts and scripts are retained locally:

| Local artifact under /tmp | SHA-256 |
| --- | --- |
| mini-center-backing-raw-oracle.py | `e769b3e8da77606b852ee74eb6878de86198dc92b7031c959a2d24d03b4e866d` |
| mini-center-backing-raw-oracle.json | `0a3951480a537e06b7fb4935e76df5266120c2de90d2195d16915557e0f1f3ab` |
| mini-center-duty-raw-oracle.py | `1f0eeb4abf8239be17372cacb6f661e1d5ab9d7ebc372175a0ca0ecceb021f26` |
| mini-center-duty-raw-oracle.json | `c481e098dac387fa0466a0d8039a76ce47c5a02e40af0280a572d3e76df12226` |
| mini-center-authority-raw-oracle.json | `3721018014c50802adf508cc4749f797e0c4ff7649144349a55c2275c1fc65a8` |
| mini-center-clean-test-receipt.json | `c83253cde788fae2268620e3abeb66b9a3f6e68752e1aab390bdeb72023ed61d` |

## Claim boundary

The geometry gap is not an adopted failure and does not mandate a member
change or continuous backing. The 18 kicker screws are total, nine per
kicker, within the 66-axis policy; the shared note's per-kicker count typo
remains unchanged for primary additive reconciliation. The four center
receivers, eight candidate bolt duties, 92 total candidate axes and twelve
starting frame bolts remain the reviewed geometry.

The direct post/header seat and post/cleat/header route have no resolved
force split, active contact law, stiffness or candidate bolt demands here.
Three-case screw records remain diagnostic; the refused recursive reduced-DOF
transfer does not become a support reaction through the separate physical
endpoint reconstruction. Six-case support/load-transfer behavior, plywood
edge/bending/bearing resistance, exact Hillman resistance and complete
receiver-to-frame qualification remain open. No adopted criterion pass,
joint capacity, physical inspection or fabrication/climbing release follows.
