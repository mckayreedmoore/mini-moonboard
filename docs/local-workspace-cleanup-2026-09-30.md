# Local workspace cleanup, September 30, 2026

The initial inventory contained 7,334 changed or untracked paths: eight
tracked edits and 7,326 untracked files, about 10.72 GB in total. Most of
the backlog is generated analysis evidence and copied source/CAD bundles,
rather than additional maintained code. The cleanup keeps those files at
their existing paths and makes their local-only status explicit.

The [publication checkpoint](wood-joints-mvp/code-summary-checkpoint-2026-09-30.md)
publishes maintained implementation and Markdown result summaries. It leaves
native inputs/outputs, detailed JSON/CSV evidence, generated geometry, raw
logs and copied source archives local. Existing tracked history remains
tracked. The new scoped ignore files apply that policy to future generated
files without hiding maintained Python, Code_Aster command templates or
Markdown summaries.

| Classification | Disposition |
| --- | --- |
| Generated models, native decks/results, matrices, meshes, CAD, histories and detailed evidence tables in wood-joint hypotheses | Ignore in Git; retain original local bytes and paths for frozen consumers |
| Copied `sources`, `bundle`, source snapshots and group-action `base` trees | Ignore local copies; retain maintained producers, tests and existing tracked history |
| Generated node-by-node Code_Aster mapping command files and runtime deck copies | Ignore the generated files; retain their generators and other command source |
| Native run ledger/lock, working task queue, generated solver build profile and filesystem inventory | Keep as local orchestration/provenance; do not commit live state |
| Completed upper-action/method reports, source-backed contact screen, BG003 necessary bound and native coupon reports | Commit code and Markdown in separate reviewed chunks; detailed packets remain local |
| Coordinator checkpoint, gate matrix and artifact manifest still being updated by the working agent | Leave active edits local; do not capture a moving status ledger in the cleanup commits |
| Stale untracked repository-root `SHA256SUMS` | Move its original bytes to `.git/local-artifacts/cleanup-2026-09-30/root-SHA256SUMS`; retain a local restoration record |

The ignore classification covers 7,312 of the original untracked files,
10,717,407,479 bytes. It changes Git visibility, not storage usage. No native
evidence, failed experiment, selected-baseline file or historical viewer
asset was deleted. The stale root checksum was the only relocation: its
declared root README hash did not match the current README. Its original
76 bytes remain recoverable in the common Git directory. No disk-space
reclamation is claimed.

The running agent was told that this thread owns staging and commits. It
identified completed result packets and retained ownership of the live
coordinator/checkpoint records. Completed method code is committed without
reformatting hash-frozen historical sources. Native runs remain under that
agent's serialized execution; cleanup launches none.

Validation checks the ignore rules against the original inventory and verifies
that maintained code, Markdown, selected authorities and public viewer paths
stay visible. The original inventory and file-level classification remain
local under `/tmp/mini-moonboard-*cleanup*`. Relevant saved-output replays
and Python syntax checks cover the published result chunks. Remaining
engineering and historical lint/replay limitations retain their original
status; cleanup establishes no strength acceptance.

Cleanup commits use the actual current time outside the Monday–Thursday
07:30–18:00 Denver window and run the normal hooks. No timestamps or
published history are rewritten.
