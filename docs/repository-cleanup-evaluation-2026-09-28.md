# Repository cleanup evaluation

## October 3 navigation and retention update

The owner authorized addressing the repository-state audit: one obvious
development reading path, with older material retained for reference and a
writeup. The active path is now [wood-joint development](wood-joints-mvp/README.md).
The selected screw-and-bracket baseline keeps its machine authority and is
presented as a separate reference packet. No candidate, geometry, load,
mechanics source or acceptance criterion changes in this cleanup.

- **Current entry:** the root README leads with wood-joint work. The development
  landing page is 89 lines, linking the current disposition, corrected force
  register, assembly packet and unadopted knee proposal. It distinguishes
  reviewed 104/208 bolt/washer inventory from proposed 108/216, completed
  conditional packet from ongoing numerical assessment, and all 47 pending
  formal criteria/eight false release flags.
- **Preserved text:** the [historical landing-page snapshot](history/wood-joint-development-summary-before-navigation-cleanup.md)
  retains all 284 original lines, including the unpublished panel-comparison
  addition. Its original payload SHA-256 is
  `c03de6d8542f6b4082e01df4fca7f20f9331c45a632a168824c46bcdf756c5a3`.
  Formal coverage and completion-ledger headers now direct readers to current
  results while preserving their earlier method mappings and chronology.
- **History:** the [design-history catalog](history/design-history.md) adds the
  conditional packet milestone and groups superseded work orders, earlier
  layouts and closed method investigations. Its original seventy-model
  collection remains byte-identical. Historical paths, failed results,
  reusable fixtures and live inherited dependencies remain available.
- **Viewer navigation:** the menu labels the selected baseline as preserved
  and V4/corner/barrel layouts as previous bolted concepts. A current wood-joint
  status link precedes the reviewed-scene link. Model values, ordering and
  asset references are unchanged. A separate owner-authorized worker now owns
  native proposal integration into the viewer; that work is not this cleanup's
  geometry or acceptance result.

Validation checked 548 local link targets, resolving preserved snapshot links
against their original directory, and checked exact historical payload bytes,
unchanged original menu construction and JavaScript syntax. The existing
mesh URL gate verified 13,618 shared URLs. The selected-candidate identity
check still reports the previously documented `compact_floor_flush_frame.py`
geometry-source snapshot mismatch. Its source and authority were not edited.
No native solve, CAD rebuild, broad historical test run, source relocation or
pruning was performed.

### Current evidence recovery bundle

The finite direct-consumer snapshot is stored outside the checkout:

```text
/home/mckay-linux/repos/mini-moonboard-cleanup-backups-2026-10-03/
  current-evidence.tar.gz
  current-evidence.tar.gz.manifest.json
```

It contains **2,146 files / 2,010,788,027 uncompressed bytes**, including
2,139 repository files, two externally pinned inputs, two historical Git
versions and three preservation records. The archive is **528,179,840 bytes**.
The selection plan retains expected hashes separately from current bytes.
It covers the direct reviewed-force/operator/register, assembly and fit
inputs, all 390 proposed-knee source pins and all 498 all-joint source pins,
their recorded outputs, and the older artifact manifest's live files.
It does not recursively collect every closed native/build experiment.

| Recovery artifact | SHA-256 |
| --- | --- |
| `current-evidence.tar.gz` | `e3bae4b51370ed415af7a0c4c95c06146a7590b6468e7dfe5ceac6acb7dc5ead` |
| Companion manifest | `be557e2946fbecb021ee8c2c1e09f9f698544314285d26f1ee69388a24132163` |

Existing `scripts/evidence_archive.py` inventory, archive writer and verifier
APIs produced a namespaced explicit-file snapshot, avoiding broad dirty source
directories. Every archive member and a complete fresh restored tree were
verified. All 2,141 live repository/external source files were hash-checked
again after archival and remained unchanged. Originals stay in place.

To recover, transfer both files together and restore into a fresh external
directory. This command uses the existing standard-library CLI:

```sh
python3 scripts/evidence_archive.py restore \
  --manifest /home/mckay-linux/repos/mini-moonboard-cleanup-backups-2026-10-03/current-evidence.tar.gz.manifest.json \
  --destination /tmp/mini-moonboard-current-evidence-restored
```

`repository/` preserves original repository-relative file names. Copy only
needed frozen files into a clone after comparing its existing versions; do
not overwrite newer work. `external-inputs/tmp/` preserves the exact NDS PDF
and retained-frame-bolt resistance JSON at their recorded temporary-path
identities. `preservation-record/` describes source selection and limitations.
`historical-artifact-pins/` contains the older completion-ledger version from
commit `33d0e129742f5683ee06c3087694c811309b1fd1` and earlier outer-viewer version
from `40b97ecffe30d06b0167b15219063e011defc0d5`, matching their old manifest pins.

The old `luna-max-completion-handoff.md` manifest pin
`b40650e35ce0b012d0879b8997a6a6d60b656943f9fca5f4c6a3943b76a01d9d`
differs from its preserved current version; its exact earlier bytes were not
recovered. This historical-document mismatch is explicit, and no frozen pin
was replaced. All current knee/all-joint source and output pins match.

This is a restore-only snapshot, not a source-tree pruning manifest. It is a
local transferable backup, not a hosted download supplied by a fresh clone.
Later assessment or viewer inputs need their own recorded snapshot; this
bundle does not claim to cover future changes. The earlier closed-run archive
below remains the recovery source for its separate historical raw data.

## October 1 implementation

The owner authorized mesh sharing, a short current development summary,
restorable closed-run archives and verified scratch removal. The cleanup does
not change candidate geometry, loads, engineering criteria or acceptance.

- **Viewer:** 13,618 duplicate STL files (2,172,457,012 bytes) were removed.
  `site/mesh-aliases.json` maps original paths to byte-identical retained assets.
  All 20,441 original mesh paths were checked against their original Git blob
  hashes. Both selected plywood-width packets stay intact; all 70 design menu
  choices and all three viewers remain available. Frozen part manifests, scenes,
  reports and pinned exporter sources were not rewritten.
- **Current summary:** [wood-joint development](wood-joints-mvp/README.md) now
  states usable results, genuine remaining work and next actions. Detailed
  chronologies remain linked. Unpublished evidence is explicitly local-only.
- **Existing archived scratch:** both expanded panel-screw trees were restored
  and checked against `fea/results/panel-screw-sensitivity-v1.tar.xz` before
  removal: 552 files, 865,019,186 bytes. The canonical archive remains tracked.
- **Closed raw runs:** 249 inactive ignored trees contain 71,001 files and
  69,123,446,520 bytes. The 15,170,925,806-byte external archive passed complete
  member and fresh-restored-tree verification. The originals were removed after
  repeating archive and complete unchanged-source checks.
- **Reconstructible caches:** 1,297 ignored interpreter, test and linter cache
  files (27,871,516 bytes) were removed after checking that none were tracked,
  nonignored or symlinks. The Python environment remains available.

These operations removed about 72.2 GB of logical file data from the checkout.
The five recovery files total about 15.4 GB, so the net saving after backups and
seven small new maintained files is about 56.8 GB. The 13,618 removed meshes are
42.9% of the original 31,717 tracked paths. These are working-tree savings;
existing Git history was preserved.

Recovery files live outside this checkout in the local sibling directory
`/home/mckay-linux/repos/mini-moonboard-cleanup-backups-2026-10-01/`:

| File | Purpose |
| --- | --- |
| `viewer-duplicate-meshes.zip` | Verified original mesh bytes, removed paths and alias map |
| `closed-generated-runs.tar.gz` and `.manifest.json` | Verified closed raw-run archive and original path/size/mode/SHA-256 manifest |
| `cleanup-dispositions.json` | File-count, size, age, reference and keep/archive/delete classification |
| `panel-screw-existing-archive-coverage.json` | All 276 canonical members and both original prefixes, restoration and removal receipt |

The closed-run archive SHA-256 is
`8f9a9039f0871711866a45f9ab938ff4868df8bc26aca91f57fda625b147b258`.

The classification retains all fifteen current tool/manual/wood-joint and
selected floor-runner case directories plus every immediate file in
`fea/generated/`. Current wood-joint experiment trees, Git history, historical
CAD/viewers and other owners' tracked/untracked work remain in place. Ignored
does not mean disposable; this archive set was checked for current consumers,
links, write dates and running-process use.

`python3 scripts/evidence_archive.py restore --manifest PATH --destination NEW_DIRECTORY`
restores and verifies the complete original relative tree into a fresh external
directory. Copy a required historical tree back only when its repository path is
absent. For the panel-screw trees, the retained canonical archive has relative
members for either original prefix; the coverage receipt records both mappings.
Use the [contributor commands](../CONTRIBUTING.md) to materialize legacy mesh
paths temporarily for unchanged tests, generators and replays.

Independent review corrected unpublished evidence links, backup-corruption and
newly-staged-evidence refusal coverage, and durable JavaScript URL gates in CI
and deployment. The final three-agent pass found no substantial findings.
Nine focused Python tests, Ruff,
URL resolution, original mesh byte checks and five real browser scenes pass.
The affected integration run passed 49 tests and failed one unchanged
weight-catalog test: the original published catalog omits
`compact-floor-flush-kerf-right` and `compact-spliced-flush-top-development`.
Its catalog and part-manifest inputs match pre-cleanup Git bytes exactly.
The selected-candidate identity check has the same pre-existing stale
`compact_floor_flush_frame.py` geometry snapshot error recorded before cleanup;
the wood-joint identity/release-boundary check passes. No native solve ran.

## Earlier cleanup record

**September 29 follow-up:** the navigation pass is implemented locally. The
root and builder entries distinguish baseline/development/history; the new
[development entry](wood-joints-mvp/README.md) points to the existing coordinator
checkpoint; the [history catalog](history/design-history.md) preserves links
to all 70 main-viewer choices and both wood-joint viewer pages. The main viewer
links to the reviewed WJ24 scene and keeps its earlier-trials link. Existing
viewer scripts, candidate authorities, model assets and evidence were left
unchanged. No files were relocated or pruned.

Validation: 28 focused existing tests passed; the initial link audit checked
86 local document links, and 27,424 existing mesh-path references were present.
Four early hybrid variants are generated by the unchanged Pages workflow and
were not rebuilt locally. The selected-candidate configuration check reports
the same pre-existing geometry/source mismatch before and after the edits;
this cleanup does not repair or qualify that evidence. Direct guidance to the
running task could not be delivered because the messaging tool required
unavailable approval; the development entry records the guidance instead.

September 28, 2026. This is a proposed organization and retention plan, based on
the current working tree. It changes no candidate, geometry, mechanics method,
acceptance criterion, or evidence disposition. No existing files were moved or
deleted, and no native solver was run.

## Earlier recommendation

Keep two clearly labeled working lanes: the selected screw-and-bracket baseline
and the reviewed wood-joint development candidate. Put older designs and closed
experiments behind an archive index while retaining the working historical viewer.
Keep reusable calculations and inherited
geometry code available even when their names describe an older design.

The owner specifically wants to explore previous options and retain enough
material for a presentation or writeup about successes and failures. Historical
viewer functionality, visual assets and the underlying story are retention
requirements, not optional storage savings.

Start with navigation and a curated history catalog. Then bundle inactive
evidence and prune proven scratch files. Defer source-module relocation:
it has much less storage benefit and substantially more dependency risk.

The biggest opportunity is separating ongoing design work from accumulated
experiment records. Deleting old prose alone will barely affect disk usage.

## Measured inventory

Sizes are rounded filesystem allocation from `du`, not compressed download sizes.
The [directory inventory](repository-cleanup-inventory-2026-09-28.csv) records
166 directories, including the largest generated-run directories. Parent and
child rows overlap and must not be added together. Indexed counts include staged
additions; byte counts use working-tree files, not Git blob sizes. The inventory
is a snapshot, not a deletion allowlist or a complete dependency graph.

| Area | Local size | Finding |
| --- | ---: | --- |
| Entire checkout | 89 GB | Includes Git, environment, ignored runs and untracked work |
| `fea/generated/` | 72 GB | Largest reclamation opportunity, but mixes scratch and referenced evidence |
| `fea/results/` | 3.0 GB | Saved analyses, source snapshots and diagnostic evidence |
| `site/` | 3.5 GB | 62 subdirectories under `site/hybrid/`; selected width variants are about 137 MB each |
| `docs/` | 4.8 GB | Almost all size is in wood-joint experiment packets |
| `docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/` | 4.3 GB | 472 immediate experiment directories |
| `exports/` | 463 MB | Historical CAD and supporting exports alongside reference assets |
| `.git/` | 3.3 GB | Moving files within the repository does not remove historical objects |
| `.venv/` | 1.9 GB | Reconstructible environment, useful during active work |

At the inventory checkpoint, `docs/` contained approximately 4,543 MiB in 2,812
untracked, nonignored files. The index had 1,084 added files across the repository.
These are ongoing work, not disposable clutter. Git history alone cannot recover
untracked files. Do not use a blanket `git clean`, stash-and-drop, or recursive
delete as the cleanup implementation.

## Ranked findings

### 1. Historical names do not identify unused code

The selected frame imports `compact_floor_taper_frame`, which imports
`compact_floor_recess_frame`, which imports `compact_base_finish` and
`compact_rail_frame`. The selected module also uses `compact_spliced_trimmed`.
The reviewed wood-joint producer similarly builds on preceding revision scripts.

The selected viewer [manifest](../site/hybrid/compact-floor-flush-development/manifest.json)
binds 172 source/reference files, including many historical-sounding modules and
the `clear-space-floorflush` result bundle. These are provenance bindings; not
every binding is necessarily a runtime import, but none should be removed
without checking its role. The authority also points directly at that bundle's
geometry snapshot.

**Action:** retain these paths initially. Classify them as inherited/shared
implementation, rather than as active design alternatives. Before any later
module move, trace imports, dynamic access, file reads, tests and manifest
bindings. Do not flatten the selected geometry's wrapper chain merely to tidy
the repository; the existing working-set agreement explicitly preserves it.

### 2. Ignored generated files include evidence dependencies

The ignore rules exclude `fea/generated/`, but 96 wood-joint Markdown, JSON and
Python files mention that path. Examples include the pinned
`fea/generated/ccx_2.23.pdf`, the earlier manual under `connection/`, and solver
build records. Earlier selected-case search records also point to rejected runs
in ignored directories.

**Action:** inventory each proposed deletion against manifests, result records,
source snapshots and live work. Preserve required inputs, raw outputs, solver
identity, manuals, scripts and hashes in a verified bundle before removing local
duplicates. A failed run can still be the only evidence explaining a rejected
method. No measured amount of the 72 GB is yet certified disposable.

### 3. The public website is also the historical design collection

[The Pages workflow](../.github/workflows/static.yml) rebuilds historical V1 and
hybrid meshes, calculates prototype weights and uploads the entire `site/` tree.
The main viewer includes historical and barrel-nut modes. Its wood-joint link
opens the earlier WJ-03/WJ-04/WJ-05 viewer, while the reviewed revision is identified
by the WJ24 scene in `wood-joints-candidate.json`.

**Action:** keep all currently available historical model choices working,
including their geometry, metadata, controls and shareable URLs. Improve the
archive grouping and add a link to the reviewed development viewer. Do not
shrink the published asset set to the current candidates. An explicit deployment
asset list can still clarify ownership, but it must include the full historical
viewer dependency closure. Any later separate archive deployment must retain
convenient access and tested URL compatibility before changing the existing
site. Keep historical meshes in place for the first cleanup. The roughly 3.1 GB
outside the two selected hybrid folders is therefore retained history, not a
proposed removal allowance.

### 4. Current navigation omits the active development lane

[The selected working set](selected-working-set.md) says everything outside the
floor-runner lane is preserved evidence. That no longer describes the reviewed
wood-joint work. The root README and builder documentation are useful baseline
entry points, but there is no equally clear repository-level route to the active
development candidate. The history README acknowledges broken old internal links.

**Action:** add a short repository map with three entries: selected baseline,
active wood-joint development, and history. Retain the existing builder entry
point. Each development entry should point at the authority, reviewed scene,
current status, next calculation and open criteria. Repair archive navigation
with indexes and path maps without editing frozen evidence bytes.

### 5. Experiment chronology dominates operational documentation

The wood-joint completion ledger and next-MVP plan contain extensive chronological
run detail. Numerous dated status files, attempt reports and independent reviews
are mixed with current decisions. This makes finding the next relevant action
harder and encourages closed numerical experiments to look like ongoing work.

**Action:** introduce one short maintained status page that points to existing
evidence. It should distinguish current design questions, selected methods,
pending work and archived alternatives. Keep accepted numerical fixtures as
reusable method evidence with their applicability limits. Group closed solver
instrumentation work as historical method research once its owner confirms it
is no longer active. Do not interpret this filing proposal as changing the
mechanics plan or declaring a method validated.

## What stays, what moves, what goes

| Content | Proposed disposition | Reason / condition |
| --- | --- | --- |
| `current-candidate.json`, `wood-joints-candidate.json`, `AGENTS.md` | Keep at root | Distinguish selected baseline from active development; preserve authority |
| `barrel-nut-candidate.json` | Retain at its current path initially; label historical in navigation | Referenced by preservation contracts; not an active replacement authority |
| Both `floor-flush-construction*` packets, assembly guide, checklist, selected criteria and six-case evidence | Keep readily accessible | Useful baseline and comparison; conditional scope remains intact |
| `fea/results/floor-runner-mvp/` (about 26 MB) and bound `clear-space-floorflush` bundle | Keep intact | Small, valuable authenticated baseline and geometry dependency |
| Reviewed WJ24 scene/report, 66 screw axes, 92 candidate axes, 12 retained frame-bolt arrangements, current criteria and demand preparation | Keep active | Current development identity and necessary analysis inputs |
| Hardware/material references, loads, panel datums, resistance calculations, shared CAD and analysis utilities | Keep active where used | Reusable knowledge; old filenames do not make methods obsolete |
| `docs/history/`, earlier bolted/barrel/V4 studies, old construction and drilling packets | Archive as coherent studies | Keep decisions, geometry, results and limitations together; migrate only after reference checks |
| Historical `site/hybrid/*`, legacy viewer modes and their supporting assets | Keep browsable and deployed | Preserve every currently available model option and its dependencies; organize menus without removing options |
| Historical `exports/*` CAD and schedules | Retain in the design-history collection | Preserve exact candidate geometry for future illustrations and comparisons; bundle by revision after checking consumers |
| Closed `hypotheses/*attempt*/` records, obsolete handoffs and dated statuses | Retain as immutable experiment history, remove from primary navigation | Preserve failed as well as passing results; do not merge away different input states |
| Validated solver fixtures and pinned solver source/build documentation | Keep reusable; separate from experimental solver patches | Enables future method checks without repeating research |
| Rejected solver patches and their native results | Archive together when inactive | A useful diagnostic record, not a permanent default prerequisite |
| `.pytest_cache`, `.ruff_cache`, `__pycache__` | Disposable when not in use | Low-risk cleanup, negligible overall savings |
| Unreferenced intermediate meshes, duplicate logs and scratch outputs in `fea/generated/` | Remove after inventory and preservation checks | Biggest likely savings; not approved by directory name alone |
| Active `.venv`, `scans/`, `design_inputs.toml`, `.agents/`, staged/untracked work | Preserve | Environment, private inputs or ongoing work; not evaluated as disposable |
| Git history | Keep | No history rewrite needed for organizational cleanup |

Exact duplicate bytes can be stored once in an archive, but retain a mapping for
every original path and hash. Similar filenames, meshes or solver logs are not
proof of duplication. Git history is useful for committed source; large evidence
bundles also need a documented retrieval method and a verified restoration check.

## Proposed organization

Use logical organization first; do not mass-move existing evidence:

```text
README.md                         short repository map
current-candidate.json            selected bracket baseline authority
wood-joints-candidate.json        reviewed development authority
docs/README.md                    baseline builder entry, retained
docs/selected-working-set.md      selected baseline map, corrected scope
docs/wood-joints-mvp/README.md     proposed active development entry
docs/history/README.md            candidate and experiment archive index
mini_moonboard/                   active and inherited CAD/library modules
fea/                             reusable mechanics and solver tooling
fea/results/                     preserved result bundles at existing paths
fea/generated/                   scratch plus explicitly recorded retained files
scripts/                         maintained entry points; classify before moving
tests/                           shared/current tests plus historical opt-in
site/                            current and historical viewers and required assets
```

For new work, keep small explanatory documents under `docs/` and place bulky
native outputs in a named evidence bundle rather than another prose directory.
Each bundle should identify candidate/revision, method, input hashes, results,
limitations, original paths and consumers. A later cold archive can contain the
original repository-relative tree so restoration does not require rewriting old
scripts. Storage location remains an implementation choice; this evaluation
does not upload, publish or remove anything.

## Preserve a presentation and writeup trail

Add a human-readable design-history catalog under `docs/history/`, with a row
for each distinct design milestone and links to the detailed experiments. This
catalog should complement the chronological decision log. It should not require
reading hundreds of native-run reports to understand why the design changed.

For each milestone, retain or prepare:

- Candidate/revision identity, date or commit, predecessor, and its interactive
  viewer link. Distinguish the selected design at that time from an unselected trial.
- The problem it addressed, constraints, proposed change and reason for moving on.
- Original CAD/export files and part metadata; retain existing screenshots and
  diagrams. Later capture comparable front, rear and joint-detail images from
  the real models, including camera settings and explanatory captions.
- What worked, what failed, and what was left unknown. Link each numerical claim
  to its inputs, method, load case and result. Distinguish a geometry conflict,
  failed strength criterion, numerical failure and deliberate design preference.
- A short lesson learned and the subsequent design change it motivated.
- Recorded part counts, weight or cost where available, including their basis;
  leave unavailable comparisons blank instead of reconstructing unsupported numbers.

Keep complete primary evidence for the selected baseline and for every result
used in that narrative, including negative results. Intermediate logs may move
to a restorable evidence bundle; they need not dominate the reading path.
Preserve all existing viewer options even if several are summarized in one
presentation milestone. Do not keep only the winners or recast untested ideas
as structural failures.

The existing sources already support a useful initial outline:

| Story milestone | Starting evidence | Narrative boundary |
| --- | --- | --- |
| Early leg and bolt-pattern limits | [Leg decision](history/leg-completion-decision.md), [bolt-pattern investigation](history/leg-bolt-pattern-decision.md) | Separate member checks from connection checks; preserve failed alternatives |
| Compact, knee/splice and floor-runner iterations | [Chronological decisions](history/decision-log.md), historical model viewers and associated study packets | Explain geometry and transport tradeoffs; do not transfer one revision's passes |
| Screw-and-bracket baseline reaches its bounded target | [Six-case record](floor-runner-mvp-case-log.md), [completion ledger](floor-runner-mvp-completion-ledger.md) | Six cases pass 36 adopted checks; preserve unlisted bracket-action limitations |
| A difficult numerical case eventually resolves | [A12-forward search history](floor-runner-mvp-case-log.md#numerical-search-history) | Three rejected searches, then 69-cycle convergence; a numerical-method story |
| Removable bolted, barrel-nut and wood-block alternatives | [Bolted plan](bolted-candidate-plan.md), [wood-joint authority](../wood-joints-candidate.json), existing concept viewers | Geometry/access progress is distinct from complete-joint acceptance |
| Detailed contact analysis becomes a bottleneck | [Solver reuse assessment](wood-joints-mvp/solver-reuse-assessment-2026-09-27.md), [acceleration reassessment](wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/README.md) | Preserve useful method discoveries and failures; the revised analysis route is ongoing work |

This is a proposed narrative outline, not a finished historical article or a
new verdict on any candidate. A future presentation can use the catalog's
figures and claims without losing access to the underlying models and evidence.

## Implementation order and verification

1. **Navigation and history catalog.** Add the repository/development maps,
   identify active versus historical lanes, and correct the main
   development-viewer link. Inventory all existing viewer choices and their
   links before editing navigation. Keep authoritative and frozen paths unchanged.
2. **Preserve the working checkpoint.** Inventory staged, unstaged and untracked
   ownership. Save required untracked evidence before any relocation. Do not
   commit another worker's changes as part of cleanup.
3. **Verify viewer preservation.** Retain the full viewer collection. Check every
   pre-cleanup model URL, its manifest and mesh dependencies, plus selected and
   WJ24 geometry, part metadata and documents. Keep the existing deployment unless
   a replacement serves the same collection. Capture real milestone views for
   the history catalog in a later documentation pass.
4. **Archive inactive studies in small batches.** Start with organizing study
   indexes and construction packets whose consumers have been checked. Keep
   historical CAD accessible for future illustrations. Keep immutable
   snapshots byte-identical. For moved maintained documents, update links; for
   frozen bundles, preserve their original internal layout and add a locator.
   Restore and verify hashes before removing the original local copy.
5. **Prune scratch runs.** Produce a file-level keep/archive/delete manifest,
   account for generated-path evidence references and live processes, and retain
   anything unresolved. Report actual reclaimed bytes after execution.
6. **Classify tests and tools.** Reuse the existing `--include-historical` mechanism
   rather than inventing a second system. Retain tests for inherited active code
   and reusable methods. Mark closed experiment tests historical only after
   checking current coverage; do not reclassify tests merely to hide failures.
   Source relocation is a later, optional task with no promised speed benefit.

For changes affecting model paths, run the existing selected-candidate identity
check, selected export rebuild check, and wood-joint development candidate check
as applicable, plus affected tests. Archive verification does not require a new
native strength solve. Keep failed historical checks visible as historical
results rather than regenerating evidence to make cleanup pass.

## Evaluation limits

This review inspected authorities, manifests, documentation, import examples,
test selection, workflows and directory/file inventories. It did not compute
every transitive runtime dependency, hash all large files for deduplication,
certify individual files for deletion, benchmark CI, or rerun engineering checks.
The September 28 evaluation created only this report and its inventory. The
September 29 navigation follow-up is recorded at the top of this document.
