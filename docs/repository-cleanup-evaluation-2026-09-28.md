# Repository cleanup evaluation

## Post-cleanup evaluation

Reviewed the working tree after navigation compaction, on `master` at
`845e2e0c`. The navigation changes remain uncommitted pending the geometry
owner's integration. This evaluates repository organization and operation;
it does not assess structural adequacy or alter the current model.

**Assessment:** the main reading-path problem is substantially resolved.
The maintained entry is 110 lines, down from 1,270, and distinguishes current
extended-cleat geometry, nominal shop coverage and older numerical evidence.
Recovery is now demonstrated for its recorded scope. Automation, portable
execution and publication boundaries remain the main weaknesses. Another
large source-directory rearrangement would offer little immediate benefit.

### Ratings after cleanup

These use the earlier 1–5 organization rubric; they are qualitative judgments.

| Criterion | Earlier | Now | Reason |
| --- | ---: | ---: | --- |
| Modularity | 3 | 3 | Source boundaries and inherited producer chains are unchanged. |
| Cohesion | 2 | 3 | The development entry is focused; packet code, evidence and chronology still share long-lived trees. |
| Separation of concerns | 3 | 4 | Geometry, shop, response, selected baseline and historical options now have explicit reading paths. |
| Abstraction | 3 | 3 | Existing archive and mesh helpers are reused; no additional general framework is needed. |
| Loose coupling | 2 | 2 | Current work still consumes predecessor paths, frozen sources and absolute external identities. |
| Testability | 3 | 3 | Scoped checks and historical opt-in remain useful; current scene/browser checks still lack a complete portable workflow. |
| Deployability | 2 | 2 | Pages publication remains separate from CI and includes an implicit documentation tree. |
| Reproducibility | 2 | 3 | Exact scoped recovery was tested; a fresh-machine geometry/mechanics replay has not been demonstrated. |
| Recoverable history | 4 | 4 | Original bytes, viewers and recovery bundles survive, but the copied summary needs a better browsing route. |

### Ranked remaining findings

1. **Current-development checks do not gate publication.**
   [CI](../.github/workflows/ci.yml) tests shared/Eoere Python helpers, the
   selected baseline and earlier reviewed wood-joint packet, but does not run
   a named extended-cleat scene or browser gate. The documented source-only
   replay command covers preserved v3 inputs. [Pages](../.github/workflows/static.yml)
   starts independently on a `master` push rather than consuming CI's result.
   The [current overlay](../site/eoere-cleat-extension-overlay.mjs) already
   authenticates scene/parent identities and rejects acceptance transfers at
   runtime; that protection is valuable but does not connect CI to deployment.
   **Next change:** reuse its validator for a cheap Git-supplied receipt/scene
   identity check, clearly name the revision checked, and make publication
   consume the validated commit. Keep baseline, current development and
   historical checks separately named. Full geometry/native replay is not
   required to establish this first automation boundary.

2. **Recovery is proven locally, but distribution and execution remain local.**
   The [recovery record](#navigation-implementation-and-active-input-recovery)
   verifies 777 non-Git inputs plus 420 Git-supplied files. Its runner and plan
   are outside Git, with fourteen provider bundles across four sibling backup
   directories. Those bundles total **653,287,919 compressed bytes**; the new
   gap bundle alone is not a complete recovery kit. Current producer/gate code
   retains absolute identities, and browser checks require Bun plus Playwright
   and the runner in the neighboring `gwen` checkout. New mechanics preparation
   is explicitly outside the completed recovery scope, rather than silently
   covered by it.
   **Next change:** give the existing kit a durable shared retrieval location
   and explicit environment setup, then demonstrate recovery from a clean
   checkout. Test any path mapping separately before claiming portable replay;
   preserve frozen labels and hashes. Extend coverage only after the mechanics
   owner freezes the relevant new input set.

3. **The archived summary preserves bytes but breaks normal relative browsing.**
   In the [new historical copy](history/eoere-development-summary-before-compaction.md),
   **113 of 135 local path-link occurrences** fail from `docs/history/`;
   all 135 resolve from the recorded original directory. This is a defect in
   the navigation cleanup. The earlier link check used the declared original
   base for frozen content, so it established source-path validity rather than
   clickability in the copy's actual location.
   **Next change:** add a prominent wrapper link to the
   [original summary at its exact commit](https://github.com/mckayreedmoore/mini-moonboard/blob/845e2e0cf2bf1514398e115c382865579fd77141/docs/wood-joints-mvp/README.md)
   for browsing in the original path context. Preserve the 96,499-byte payload
   and its hash. A separately generated view could rebase links later; another
   rewritten evidence copy is unnecessary.

4. **The website's publication boundary includes the whole documentation tree.**
   Tracked `site/docs` is a symlink to `../docs`. The Pages upload action follows
   symlinks through its `--dereference` archive option, so uploading `site/`
   also packages that target. [Official action source](https://github.com/actions/upload-pages-artifact/blob/v3/action.yml)
   confirms this behavior. Index-listed documentation currently accounts for
   about **294 MB**; this is a working-tree measurement, not a measured CI
   artifact or a claim that ignored local runs exist on a clean runner.
   Some documentation URLs are required: the WJ24 viewer fetches
   `docs/wood-joints-mvp/source-inventory.json`, and historical designs link
   drilling and evidence files.
   **Next change:** inventory those consumers and build an explicit publication
   directory containing the required documents and all preserved viewer assets.
   Check URL compatibility before narrowing it. Keep analytical source paths
   intact; moving or deleting the source documentation is not the remedy.

5. **Some maintained labels still describe the old development lane.**
   The [viewer header](../site/index.html) calls the main summary “Current
   wood-joint work,” and the [baseline working-set guide](selected-working-set.md)
   uses the older lane label. Their links reach the correct compact entry, so
   this is smaller than the original conflicting-geometry problem.
   **Next change:** align maintained labels when those files are next touched.
   Keep source-bound historical labels and reviewed records unchanged. The
   11,311-line completion ledger can remain detailed evidence while the compact
   summary carries the actionable reading order.

### Measurements and review limits

The index now lists **19,750 paths**: 19,749 regular files and the `site/docs`
symlink, all present. Logical regular-file sizes plus the seven symlink-label
bytes total **5,574,256,834 bytes**. This includes intent-to-add paths; it is
neither compressed clone size nor the size of committed `845e2e0c`.
The first navigation implementation adds a net **22,684 bytes** across its
seven owned paths relative to its saved pre-implementation state, including
the 97,125-byte wrapped historical snapshot. That measurement precedes this
evaluation. No raw-run or viewer storage was reclaimed by navigation cleanup.

This review rechecked all **581 direct extended-cleat source hashes**: 105
index-listed inputs, 475 non-indexed inputs and one external manifest, with no
missing or changed bytes. It authenticated the seven retained recovery files
against the prior verification record and reused the completed full recovery
proof rather than repeating unchanged restoration. It inspected current CI,
Pages, scene/browser checks, shop composition and source-gate path behavior.
It also checked archived links from both the actual and original directories.

The next useful batch is small: repair the archive wrapper and maintained
labels, establish the cheap current-revision validation/publication gate, then
address explicit publication contents and shared recovery distribution.
Another general directory shuffle or raw-run prune is not justified by these
findings. Only this existing evaluation record is edited; the geometry owner's
README/ledger, frozen historical payload, source inputs and staging stay under
their existing ownership. Current native mechanics and its pending admission
remain separate ongoing work.

## Navigation implementation and active-input recovery

The owner authorized implementing the structure recommendations below. The
implementation starts from `master` at `845e2e0c`, after the geometry owner
published the extended side cleats and matching shop records. The earlier
review's `6d2f97f3` measurements retain their original checkpoint scope.

- **Main entry:** [Eoere development](wood-joints-mvp/README.md) is reduced from
  1,270 to **110 lines**. Its revision map names the extended-cleat geometry,
  provisional extra-grid layer, current shop packet and separate raised-rail
  six-case response. Four cleat/post stations remain HOLD, actual observations
  remain blank and all 200 access sides remain unverified.
- **Incoming navigation:** the root README and baseline reference entry point
  to that map. Their repeated, outdated aligned-wire/current-model descriptions
  are removed. The selected baseline authority and viewer default stay intact.
- **History:** the [existing catalog](history/design-history.md#eoere-development-sequence)
  adds the Eoere revision sequence and links all preserved predecessor choices.
  The complete original summary is retained in an
  [immutable history snapshot](history/eoere-development-summary-before-compaction.md).
  Its **96,499-byte / 1,270-line payload** is byte-identical, SHA-256
  `179f917091aeb555c5c95e99916c94fa0dbdae1356e88bfd9f5482f1a571052f`.
  The small wrapper records the original link base. Compatibility anchors in
  the maintained entry route old working-model links to preserved discussions.
- **Contributor workflow:** affected documentation/archive checks are
  distinguished from CAD/native work, and the existing source-only replay
  gate has an explicit command and revision limit. CI's baseline/earlier WJ24
  checks remain separately scoped; a full Eoere CI replay still requires a
  transferable input-distribution arrangement.

The snapshot is the only new tracked artifact for this implementation. Its
full historical payload preserves the unique old prose while allowing the
main entry to remain compact. No meshes, fields, manuals, installed dependencies
or numerical packets are added to Git by this cleanup.

### Recovery coverage and verified result

The recovery set covers the current extended-cleat geometry, nominal shop
packet and two guarded bounded followups. It merges the recorded geometry
source maps, shop-input/finished-solid references and existing guarded analysis
closures. Every recorded input is authenticated before and after recovery.
This is **not** the input closure for the geometry owner's new mechanics
descriptor, pending current cases or future work.

The later [extended-cleat numerical completion](wood-joints-mvp/completion-ledger.md#current-extended-cleat-numerical-completion)
now has six fresh fields and twelve component reports. Its ignored raw inputs,
operators and detailed reports remain active and are **not** in this earlier
recovery snapshot. Compact source, process, test, review and summary records
are retained separately; no later output is pruned or declared remotely
recoverable by the 1,197-file restoration below. The original temporary serial
permit has an exact small evidence copy in the numerical parent-authority
folder; recovering that historical permit does not authorize another run.

| Input class | Files | Result |
| --- | ---: | --- |
| Git-supplied inputs | 420 | Exact file bytes match both the recorded hashes and commit `845e2e0c`. |
| Required ignored inputs | 767 | Included in the verified recovery map. |
| Required untracked inputs | 9 | Preserved as inputs, rather than treated as disposable work. |
| External pinned archive manifest | 1 | Recovered at an explicit external-input identity. |
| **Total** | **1,197** | All source hashes match before and after; no original is removed or overwritten. |

Existing archives cover 718 of the 777 non-Git inputs. The new gap bundle
contains only the remaining **59 files / 81,854,828 uncompressed bytes**.
Its compressed size is **37,583,332 bytes**. These include source-bound saved
solids, detail rows and references needed by the scoped current consumers;
age and ignored status do not make them closed scratch.

The full recovery test uses **13 existing bundles plus the new gap bundle**.
The shared `scripts/evidence_archive.py` inventory, archive-writer and verifier
APIs build and completely verify the explicit-file gap snapshot and a fresh
restoration. The retained recovery runner then restores each provider through
the same shared archive helper, checks every selected member and verifies all
777 recovered input files together with the 420 Git-supplied files. Temporary
expanded copies are removed only after complete hash checks; compact proof
receipts remain. All 1,197 original source bytes are checked again and unchanged.

The existing v3 replay-source gate also passes in
`VERIFY_EXISTING_FROZEN_V3_INPUTS_ONLY` mode, including **29 rejected controls**.
It performs no CAD replay and supplies no extended-cleat mechanics pass.

### Recovery location and command

The restore-only additions live outside the checkout:

```text
/home/mckay-linux/repos/mini-moonboard-cleanup-backups-navigation-v1/
  eoere-current-input-gaps-v1.tar.gz
  eoere-current-input-gaps-v1.tar.gz.manifest.json
  recovery-plan.json
  required-inputs.json
  restore_current_inputs.py
  recovery-proof.json
  verification.json
  coverage.json
```

| Record | SHA-256 |
| --- | --- |
| Gap archive | `d067111f7222dbea414dfc558b81a6d6e9cce9bc21a1f2c260eb3c39f64e3bec` |
| Gap manifest | `1698cc4e67df800551e5e8bb595e95167bc314fe09fe9a656cfaedbb0c33b056` |
| Recovery plan | `bcc2e8622fc4be3fe06fb5623e6f18085c657c9509eec027f123b78758a7b0af` |
| Recovery runner | `cb5fe623038963cff51bf401281feb7f1b26940430b494e865850e85041382b0` |
| Full recovery proof | `655365149a8caaef65d68b21713687d4cf01be1960451c7f286d0b4c40c3f966` |

Keep the existing October 3, October 7 and October 8 sibling backup directories
alongside this directory. The plan names the exact thirteen provider manifests,
their hashes and each required member; it does not depend on a broad old
archive being presumed applicable. The runner authenticates that plan, input
map, shared archive helper, every manifest and every recovered file.

From a clone containing the recorded Git input bytes, restore into a fresh
external directory:

```sh
python3 /home/mckay-linux/repos/mini-moonboard-cleanup-backups-navigation-v1/restore_current_inputs.py \
  --repository /home/mckay-linux/repos/mini-moonboard \
  --destination /tmp/mini-moonboard-current-inputs-recovered
```

For another machine, retain the sibling backup layout and adjust the runner,
repository and destination paths. The runner writes only the fresh destination.
`repository/` contains original repository-relative identities;
`external-inputs/` preserves the absolute-label hierarchy of the external
manifest. Compare hashes before copying only missing inputs into a checkout.
The original producer and receipts retain their absolute-path requirements;
this verifies recovery of bytes, not execution at silently substituted paths.
No current geometry/native replay is performed by recovery.

### Navigation validation

The affected checks pass: **179 local link occurrences** across the seven
maintained files, ten incoming fragment references and **78 viewer query identities**
from the original model-selection definitions, including generated lumber
choices. The no-query viewer default remains the selected baseline. The frozen
summary payload, original complete viewer-catalog section, baseline packet body
and entire earlier cleanup record are byte-identical to their saved originals.
Links inside the historical payload retain the original link base recorded in
its wrapper. `git diff --check` passes for the edited maintained files.

Recovery destination controls reject both an existing external directory and
a destination inside the checkout before restoration. Receipts for navigation,
destination controls and the source-only replay gate are kept in ignored
`fea/generated/repository-navigation-v1/`; the full recovery proof and retained
runner are in the external backup directory above. No CAD rebuild, native solve
or complete historical export is part of this validation.

### Retention after this implementation

The full old summary is archived in the history reading path; historical
viewer choices and the original seventy-choice catalog remain intact.
The compact entry, current shop packet, frozen geometry/response receipts,
source maps and recovery plan stay active. The geometry owner confirmed that
fields, operators, cached BReps, source banks, descriptors and review records
are still consumed by current preparation. Their original paths remain live.

No additional raw-run set is certified inactive by this implementation, and no
active or other worker's tree is pruned. The previously noted superseded
resistance attempt/source-survey exports remain candidates for a later checked
batch. Their existence outside the new scoped recovery set is not deletion
authority. This preserves continued development while making the reading path
and recoverable inputs explicit. The geometry owner's shared completion ledger,
all existing numerical/geometry packets and untracked worker changes are kept
outside the navigation edit set.

## Current MVP repository-structure review

Reviewed October 8, 2026, on `master` at `6d2f97f3`, including the unpublished
adjusted-base v3 work present in the shared checkout. This section updates the
recommendations; the earlier cleanup records below retain their original scope.
It is an organization review, not a structural assessment or an implemented
file migration.

**Recommendation:** make the existing development summary a compact current-MVP
entry point with an explicit revision map. Correct its incoming links, then
make the active inputs recoverable before moving older files. The repository
already has useful archive, mesh-sharing and historical-test mechanisms; extend
those rather than introducing a second archive system or rewriting the CAD.

The owner's present development focus is the **Eoere bolted frame**, candidate
`compact-floor-flush-eoere-bolted-development`. Its latest local base is
`eoere-midpoint-ready-frame-v3`, with the unofficial extra grid **off**.
The optional extra-grid revision is a separate geometry layer. Neither is a
fabrication release. The formally selected screw-and-bracket baseline remains
`compact-floor-flush-development` under [current-candidate.json](../current-candidate.json).
Making the development focus obvious does not change that authority or transfer
the earlier geometry's numerical results.

### What a good repository should provide

For this project, clarity and exact evidence identity matter more than having
few directories. A folder can be historical as a design option and still contain
required implementation or evidence inputs.

| Criterion | Practical acceptance target |
| --- | --- |
| One obvious development entry | A reader can find the main development model, its status, current evidence and next actions from the root README in a few minutes. Keep `docs/wood-joints-mvp/README.md` around 100–150 lines; put chronology behind links. |
| Exact revision identity | The entry identifies candidate, geometry revision, viewer query, optional-grid state, applicable mechanics revision and shop-document revision. “Current” and a candidate name alone are insufficient. |
| Clear claim boundaries | Geometry checks, component references, completed conditional reporting, unresolved resistance and physical release stay separate. Shop datums from an earlier revision are labeled as such; actual observations remain blank. |
| Explicit dependencies | Distinguish current design records, inherited/shared code, reusable method fixtures, frozen history and temporary runs. Check imports, file reads, manifests and source pins before classifying a path as inactive. |
| Recoverable execution | A maintainer can retrieve the exact required inputs, verify hashes and follow recorded commands with the pinned environment. Ignored files and external absolute paths have a documented recovery route. |
| Proportional evidence storage | Keep small inputs, formulas, results, source bindings and recovery records readily accessible. Put bulky closed raw runs in verified external bundles; reuse existing manuals, meshes and dependencies. |
| Useful design history | Preserve decisions, failures, geometry and limitations together. Existing model URLs and viewer choices keep working, and the history index explains why each revision was superseded. |
| Checks match the work | Distinguish documentation/source checks, current development checks, preserved-baseline checks and historical opt-in. A green baseline check must not imply that the development frame has been evaluated. |
| Safe shared changes | Work on `master`, identify ownership, stage only owned changes and inspect added byte volume. Archive candidates need consumer and process checks, a verified restore and an unchanged-source check before pruning. |

### Architecture assessment

These are organizational ratings on a 1–5 scale, not engineering grades.

| Criterion | Rating | Evidence and implication |
| --- | ---: | --- |
| Modularity | 3 | CAD, mechanics, scripts, tests and deployment have recognizable top-level homes. Many current producers still depend on earlier revision scripts. |
| Cohesion | 2 | The main development summary mixes current instructions with extensive predecessor detail; frozen experiment code and evidence also live under `docs/`. |
| Separation of concerns | 3 | Receipts distinguish geometry from mechanics and release. The reading paths do not consistently reflect those distinctions or the latest geometry. |
| Abstraction | 3 | Existing archive, alias and evidence helpers avoid duplication. Replacing the preserved geometry wrapper chain would add risk without a demonstrated benefit. |
| Loose coupling | 2 | Runtime imports, fixed packet paths, ignored BREP inputs and external archive-manifest paths cross several historical studies. Filename-based relocation is unsafe. |
| Testability | 3 | Current/shared tests and historical opt-in already exist. Some full replays and browser checks depend on local inputs or a neighboring checkout. |
| Deployability | 2 | Pages has an established deployment, but its workflow and CI do not invoke the latest adjusted-base checks, and the default viewer remains the selected baseline. |
| Reproducibility | 2 | The inspected geometry source hashes match locally. A Git clone alone does not supply their complete inputs or the external manifest. |
| Recoverable history | 4 | Historical viewers, byte-preserving mesh aliases and verified archive records are valuable existing foundations. Later source sets still need their own coverage. |

### Measured working set

The index lists **19,622 paths** with **5,571,950,781 working-tree bytes
(5.189 GiB)**. This includes intent-to-add entries and reads current file sizes;
it is not the committed size of `6d2f97f3`, a compressed download estimate or a
deletion inventory. Untracked work and ignored runs are outside this count.
All index-listed paths were present at the inventory checkpoint.

| Indexed area | Paths | Logical size |
| --- | ---: | ---: |
| `fea/` | 5,460 | 2.991 GiB |
| `site/` | 6,991 | 1.459 GiB |
| `exports/` | 315 | 0.450 GiB |
| `docs/` | 5,078 | 0.273 GiB |
| `scripts/` | 598 | 9.51 MiB |
| `tests/` | 986 | 5.34 MiB |
| `mini_moonboard/` | 176 | 1.20 MiB |

There are 126 files directly under `docs/`, 2,149 indexed Markdown documents
under it, 571 top-level Python scripts, 169 top-level library modules and 983
Python files under `tests/`. The development summary has **1,221 lines** and its
completion ledger **10,877 lines**. These measures explain the navigation
burden; they do not identify disposable files.

Separately, allocated filesystem sizes from `du -x -s -B1` are
3,466,317,824 bytes for `.git/`, 7,463,948,288 for `fea/generated/` and
1,990,283,264 for `.venv/`. These use a different measurement basis from the
index table. Moving a tracked directory elsewhere within this repository
does not reclaim its Git history or reduce the published asset set.

Local `docs/` allocation is **32,363,491,328 bytes (30.14 GiB)**, including
**20,273,594,368 bytes (18.88 GiB)** in the October 1 resume tree and
**4,605,198,336 bytes (4.29 GiB)** in the September 24 evaluation tree.
Parent and child measurements overlap. The nested experiment ignore rules
exclude many native fields, copied source bundles and other generated files,
so the indexed 0.273 GiB does not describe documentation's local footprint.
These large trees warrant a closed-run consumer inventory, not a blanket
archive operation: later studies still use some of their saved fields and
helpers. No part of their measured size is certified reclaimable here.

The two v3 geometry receipts each bind the **same 570-source map**:

| Source location | File identities | Present source bytes |
| --- | ---: | ---: |
| Index-listed repository files | 95 | Part of the 24,129,263-byte total |
| Non-indexed files under ignored `fea/generated/` | 474 | 16,074,951 |
| External archive manifest | 1 | Part of the 24,129,263-byte total |

All 570 hashes match in both receipts. The maps contain an absolute label for
the producer inside this checkout and an absolute external label for
`mini-moonboard-cleanup-backups-2026-10-08/eoere-aligned-wire-cutouts-v1.tar.gz.manifest.json`
in the sibling directory. These are **direct recorded source maps**, not a
complete recursive proof of every replay dependency. Index membership also
does not mean the unpublished working changes have been committed.

The preceding aligned-wire receipt binds 784 sources: 257 index-listed and
527 non-indexed. Its 528 `fea/generated/` entries include one index-listed
file. All 784 hashes also match. The completed numerical packet instead uses
its separate local, ignored curation index at
`fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/fixed-floor-components-v1/curation-index-v1.json`
and recorded publication bindings; it does not use a top-level
`source_sha256` map. Its recorded 691 publication pins were not rehashed as
part of this structure review. Thus neither “ignored” nor “older geometry”
identifies scratch that can be removed.

### Revision map to put in the main entry

This is the proposed navigation map for the inspected checkpoint. Receipt and
viewer identities are existing records, not new candidate selections. The
adjusted-base and extra-grid work is local/unpublished at this checkpoint;
the earlier aligned-wire publication is recorded in the maintained ledger.

| Role | Revision / viewer | Evidence boundary |
| --- | --- | --- |
| Main development geometry, extra grid off | `eoere-midpoint-ready-frame-v3`; [adjusted base](../site/index.html?model=eoere-adjusted-frame-development&view=rear) | [Base receipt](wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/occupied-adjusted-base-v3.json): coordinated principal, member, connection and screw moves; 100 bolt axes and 66 screws. No matching admitted frame response. |
| Optional unofficial extra grid | `eoere-2026-horizontal-midpoint-grid-v3`; [extra-grid view](../site/index.html?model=eoere-new-2026-adjustments&view=rear) | [Extra-layer receipt](wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/occupied-2026-adjustments-v3.json): provisional midpoint assumptions and added service cuts. Keep separate from the base and from confirmed hold positions. |
| Latest builder-support work | [Drilling/fixture guide](wood-joints-mvp/eoere-builder-drilling-guide.md) | Proposed setups and initial nominal layouts; affected station drawings, access, tolerances and the tapered-recess operation remain unresolved. |
| Preserved shop instructions and six-case response | `eoere-bottom-rail-tnut-clearance-v1`; [raised-rail view](../site/index.html?model=eoere-bolted-bottom-rail-development&view=rear) | [Shop guide](wood-joints-mvp/eoere-shop-assembly-guide.md) and [numerical receipt](wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/fixed-floor-numerical-mvp-v1.json) cover that earlier geometry, retaining exceedances and unknown complete joint resistance. |
| Preserved intermediate geometry | `eoere-rear-trimmed-cleats-v1` and `eoere-grid-aligned-wire-cutouts-v1` | [Trim receipt](wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/occupied-cleat-trim-v1.json) and [aligned-wire receipt](wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/occupied-aligned-wire-v1.json): distinct geometry checks; inputs remain live where consumed by later work. |
| Bounded component evidence | [Four studies](wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/bounded-strength-v1/README.md) and [resistance followup](wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/bounded-strength-v1/resistance-followup-v1/README.md) | Preserve their own old-action/local-geometry limits. The local revised-base audit adds geometry/applicability information, not a revised response or complete-joint acceptance. |
| Original Eoere proposal | `eoere-far-pairs-cleat-corners-v1`; [original contract](../eoere-bolted-candidate.json) | Frozen proposal identity, earlier A12 work and original scene; not a selector for the latest Eoere geometry. |
| Selected baseline and earlier designs | [Baseline working set](selected-working-set.md); [design history](history/design-history.md) | Preserve their authorities, evidence and viewer choices. WJ24, HL35 and thin-frame predecessors can remain live dependencies while their design alternatives are historical. |

### Ranked findings and recommendations

#### 1. Entry pages disagree about the latest model

**Observed:** the [root README](../README.md) and [baseline documentation entry](README.md)
call the aligned-wire geometry latest and describe the principal shift as
unadopted or the axes as unchanged. The [development summary](wood-joints-mvp/README.md)
and local [viewer](../site/index.html?model=eoere-adjusted-frame-development&view=rear)
now point to adjusted base v3, with 22 moved bolt stacks and ten moved screws.
The no-query viewer still intentionally opens the selected baseline.

**Impact:** a reader can follow a prominently labeled current link into the
wrong geometry and then pair it with older shop datums or numerical findings.
This is a documentation identity problem, not evidence that any structural
criterion has passed or failed.

**Recommendation:** lead the root entry with one short current-development
link, identify its local/publication status and use explicit model queries.
Reduce repeated geometry prose in other entry pages. Put the revision map
above in the existing development summary and label the numerical/shop
revision there. Make `docs/README.md` a builder entrance with current MVP work
first and the preserved baseline as a separate reference route.
Keep the baseline machine authority intact. The existing default is enforced
by `scripts.current_candidate`, so use an explicit MVP URL for the first pass.
A later change to the bare-site default can follow the development navigation
map, with the corresponding default check updated while retaining baseline
identity/evidence checks. A landing-page choice does not establish engineering
selection or acceptance.

#### 2. Required inputs are mixed with ignored runs and external recovery files

**Observed:** the v3 source maps require 474 ignored files and the sibling
archive manifest. [The producer](../scripts/eoere_2026_adjustments.py) authenticates
that manifest and reads saved geometry through earlier packet paths. The
existing [replay-input gate](../scripts/check_eoere_2026_replay_inputs.py) verifies
frozen source bindings; its default mode does not execute CAD.

**Impact:** a fresh clone cannot reproduce the latest geometry from Git alone.
Pruning a closed-looking predecessor tree can remove live input geometry even
when the current scene remains viewable. The earlier October 1/3 archives
cannot be assumed to cover later source sets.

**Recommendation:** enumerate the active input closure and its known
consumers, including nested manifests, required fields, manuals and tool
identity. Reuse `scripts/evidence_archive.py` for any missing recovery bundle;
record its location, hashes and exact recovery command in the existing ledger
or this record. Check coverage against the newer October 7/8 bundles before
creating another copy. Document absolute-path requirements explicitly and
demonstrate recovery without depending on the original checkout. Any maintained
locator or replay wrapper must preserve frozen labels and source hashes;
silently rewriting old manifests is not a portability fix.

#### 3. A candidate name does not select its current evidence revision

**Observed:** [eoere-bolted-candidate.json](../eoere-bolted-candidate.json) still
binds `eoere-far-pairs-cleat-corners-v1`. Later raised-rail, trimmed-cleat,
aligned-wire and adjusted-base receipts reuse the same candidate identity.
Their viewers, finished geometry, actions and shop coverage differ. The
small numerical receipt explicitly names the raised-rail revision.

**Impact:** a consumer looking only at the root contract can choose an older
scene, while a consumer looking only at the newest scene can overread the
completed six-case packet as current strength evidence.

**Recommendation:** make the revision table the maintained human selector,
with separate geometry, response and shop-document columns. Identify optional
layers explicitly. Preserve the original proposal contract and selected
baseline authority. If an automated consumer later needs a latest-development
pointer, add a small separate selector and check its referenced identities;
do not repin a historical contract merely to make its filename look current.

#### 4. The summary has become a second historical ledger

**Observed:** the 1,221-line summary contains lengthy preserved Eoere, thin-frame
and wood-joint narratives. The 10,877-line completion ledger also contains
earlier sections titled “current” and old next-action instructions. The
existing [history catalog](history/design-history.md) principally explains the
earlier floor-runner and WJ24 work; the Eoere sequence is easier to find in the
development chronology.

**Impact:** routine continuation requires reconstructing chronology, and old
instructions can appear to reopen completed work. Repeated current-model
descriptions create the drift seen in finding 1.

**Recommendation:** keep only the current revision map, usable results, exact
open inputs and next actions in the main summary. Link existing evidence and
ledger anchors for details. Add Eoere milestones to the existing history
catalog, preserving distinct failures and revision limits. Before removing
unique old prose, check its consumers and preserve any frozen bytes in their
existing historical packet. Avoid another dated checkpoint or copied ledger.

#### 5. Validation and deployment do not yet identify the active development lane

**Observed:** [CI](../.github/workflows/ci.yml) runs selected-baseline export
checks and the earlier reviewed wood-joint candidate check. Default Python
tests include Eoere helpers, and historical selection already exists through
[tests/conftest.py](../tests/conftest.py) and `tests/historical.txt` (316 whole
modules and 16 individual cases). Neither workflow invokes the adjusted-base
scene or replay-input gates. [Pages deployment](../.github/workflows/static.yml)
rebuilds historical meshes/weights and uploads `site/`; it is separate from
CI's final validation gate. The local
[adjustments browser check](../scripts/check_eoere_2026_browser.cjs) depends on
Bun and Playwright/the browser runner from the neighboring `gwen` checkout.

**Impact:** baseline or WJ24 validation cannot stand in for adjusted-base
validation. Local browser evidence has an environment contract a fresh clone
does not provide. The workflow arrangement also does not make a Pages deploy
conditional on the CI job's success.

**Recommendation:** document and reuse three check levels: fast identity/source
checks, affected development behavior/scene checks, and deliberately invoked
historical replays. Once exact development inputs are recoverable, add the
applicable existing gates to CI with an explicit input-restoration step.
Record Bun, Playwright and shared-runner versions/setup rather than copying
their installations into a packet. Keep baseline validation separately named
and historical tests opt-in. Treat recorded pre-existing failures explicitly;
do not refresh frozen evidence or exclude live tests just to obtain green CI.
Evaluate deployment gating as a separate workflow change after deciding which
checks can run from a fresh checkout. Documentation cleanup needs no native
solve or complete historical export.

#### 6. Physical source moves offer little immediate benefit

**Observed:** the selected frame imports `compact_floor_taper_frame` and
`compact_spliced_trimmed`; its preserved wrapper chain continues through
earlier modules. The adjusted-base producer imports HL35 service helpers,
thin-frame hardware/routing and WJ24 mesh helpers, including private functions.
The indexed size is dominated by analyses and viewer assets. Mesh sharing
already preserves original paths through `site/mesh-aliases.json`.

**Impact:** moving “old” scripts or library modules can break live imports,
file reads, tests and authenticated source labels. Moving frozen evidence
inside Git adds churn without removing historical bytes. Versioned scenes
must not be treated as duplicate bytes merely because they look similar.

**Recommendation:** classify and index inherited implementation where it is.
Keep historical design options behind the history reading path while retaining
their live dependencies. Reserve physical moves for unbound maintained
documents or new work whose consumers are understood. Archive truly closed
raw runs externally in small verified batches. Continue byte-identical mesh
sharing through the existing workflow; preserve frozen scenes and manifests.
Extract a shared helper only when a concrete ongoing change needs it, with
affected geometry and source contracts checked.

### Recommended retention and archive boundaries

These are proposed dispositions, not a pruning allowlist. A historical design
label and active dependency status can both apply to the same packet.

| Content | Disposition now | Condition for any later move |
| --- | --- | --- |
| Adjusted-base v3 and optional-grid receipts, scenes, producer and verification helpers | Keep at current paths; geometry owner retains unpublished integration work | Freeze and validate the exact source set and publication state before changing locations. |
| Current builder-support guide, its drawings and preserved raised-rail shop guide | Keep readily accessible with revision labels | Move only unbound maintained prose after updating its consumers; do not reuse old station datums as current templates. |
| Raised-rail six-case packet, old fields, bounded studies and component resistance followup | Keep as active evidence for their recorded scopes | Their inputs and admitted actions are still consumed. Archive only verified closed raw surplus after tracing those consumers. |
| Revised-base applicability audit and other untracked/staged work | Preserve under its owner's control | Integration/retention decisions belong to the worker; file age or missing Git history is not deletion authority. |
| HL35, thin-frame, WJ24 and selected-baseline implementation still imported by current tools | Keep paths and bytes; label inherited/shared implementation | A source move needs import/read/test/provenance checks and a demonstrated benefit. |
| Earlier Eoere revisions, WJ alternatives, obsolete handoffs and closed solver investigations | Archive in the reading path first | Preserve exact evidence and existing URLs; determine which parts remain live inputs before relocating any physical bundle. |
| Already noted superseded resistance `attempt01` and temporary source-survey exports | Candidates for a later external archive | The existing ledger calls them candidates; confirm consumers, ownership and process use, then verify archive/restore and unchanged sources before pruning. |
| Historical viewers, export geometry and frozen manifests | Keep browsable; share identical meshes with existing aliases | Any storage change must preserve every existing viewer choice, asset identity and recovery path. |
| Reconstructible caches and demonstrably unconsumed temporary runs | Consider last, after ownership/use checks | Measure actual savings and use the existing archive workflow where historical evidence is involved. |

The October 1 and October 3 recovery entries below remain applicable to their
original sets. Later Eoere recovery records live in the
[development ledger](wood-joints-mvp/completion-ledger.md#build-package-completion)
and the sibling October 7/8 backup directories. This review checked the presence
of those directories and inspected source/manifest bindings; it did not restore
or revalidate all historical archives. No current dependency, failed experiment
or other worker's file is classified for immediate deletion.

### Proposed reading and ownership layout

Use existing locations first. This map states their roles, not a mass rename:

```text
README.md                         short project map; explicit current-development link
current-candidate.json            selected baseline authority, preserved
eoere-bolted-candidate.json        original Eoere proposal contract, preserved
docs/wood-joints-mvp/README.md     compact development summary and revision map
  completion-ledger.md            detailed evidence chronology and task dispositions
  eoere-builder-drilling-guide.md current builder-support work, scoped by revision
  eoere-shop-assembly-guide.md    preserved raised-rail operations
  hypotheses/                    frozen studies and their existing evidence links
docs/README.md                    builder entrance: MVP work and separate baseline reference
docs/history/design-history.md   decisions, failed options and viewer reading path
mini_moonboard/                   CAD/library code, including inherited implementation
scripts/                         maintained producers and checks; indexed by purpose
fea/results/                     preserved analyses at their recorded identities
fea/generated/                   active cached inputs plus runs with recorded retention
tests/                           current/shared checks and historical opt-in
site/                            current and historical viewers; shared mesh aliases
```

For new work with unchanged frozen inputs/scope, continue in its existing
packet and reuse helpers. Keep bulky temporary output ignored; record necessary
permanent artifacts and their byte volume in the maintained ledger. Old packet
paths can stay long when shortening them would invalidate evidence. Readers
should reach them through the compact map, without learning the full path tree.

### Implementation order and completion checks

1. **Repair navigation and shorten the main summary.** Update the root and
   baseline entries to link the current development summary; insert the
   revision map and current actions there. Check all changed links/fragments,
   explicit viewer queries and consistent local/publication labels. Preserve
   existing detailed evidence and unique frozen prose.
2. **Establish recovery coverage for the active MVP.** Inventory ownership and
   the source closure; compare it with existing archives before writing a new
   bundle. Verify a fresh restoration and hashes, document exact paths and
   commands, and run the existing source-only gate. This prerequisite applies
   to moving/pruning inputs, not to continuing the authorized development work.
3. **Align validation with the named revisions.** Reuse current source, scene
   and affected behavior checks, with explicit setup for their inputs and
   shared browser dependencies. Keep selected-baseline and historical results
   separately labeled; add no structural acceptance through CI wording.
4. **Extend the history catalog and archive closed batches.** Add the Eoere
   milestones, then select small closed raw-run sets. Check their consumers,
   ownership and processes; use `scripts/evidence_archive.py` to create and
   restore-verify, recheck unchanged sources, record recovery, then perform its
   separate prune operation. Do not move imported predecessors wholesale.
5. **Measure the result and stop when it is useful.** A new reader should find
   the development model, applicable response, scoped shop guide, open inputs
   and archive route from one short entry. Report recovered bytes and surviving
   URLs after actual cleanup. Further source reorganization needs a concrete
   maintenance benefit; a smaller-looking tree is not sufficient.

### Review validation and limits

This review read the authorities, entry pages, current geometry receipts,
selected import chains, historical-test inventory, CI/Pages workflows, replay
and browser checks, and existing recovery records. It rehashed the two v3
570-source maps and the 784-source aligned-wire map with no missing or changed
inputs. Those checks reuse saved geometry and establish source identity only.

Only this existing cleanup evaluation is edited for the structure review. Its
earlier 31,337 bytes are preserved byte-for-byte. All 29 new local link uses
resolve, including the checked Markdown fragment and explicit viewer keys.
Six tables have consistent columns, and `git diff --check` passes. The added
section is approximately 29 KB of prose; no permanent raw output is added.
The review does not run CAD/native mechanics, replay full numerical packets,
restore all older archives, relocate/prune files, stage another owner's work,
commit or publish. The selected-candidate source mismatch and repository-wide
failures reported in earlier records were not rerun or repaired by this audit.
The recommendations leave both development and historical acceptance boundaries
intact.

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
