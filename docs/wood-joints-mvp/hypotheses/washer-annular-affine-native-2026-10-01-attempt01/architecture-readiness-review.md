# Architecture/readiness review: affine annulus

**Disposition:** Conditional pass for one parent-owned affine method run. This
review is not the parent readiness receipt or execution authorization.

**Scope:** `annular-affine` only, under freeze SHA-256
`093ab967c805858b33e3d0530cadab25625cc3b8c69f696d3c39885302fa6817`. The
finite-sector contact job remains a separate, unapproved run. No native output
or acceptance is present in this attempt directory.

## Frozen closure and boundaries

I recomputed the freeze manifest: all seven listed attempt artifacts match,
and all nine copied source snapshots match both their recorded hashes and the
live source files. Key inputs are `model.inp`
(`36333a78ef54299cefc1fbb4ca0449ec889ce8a174b3dfc0c5ce8d3b17e93e95`), the
oracle in `model.json`
(`85a02498a9a73901cc6fd27910803fe33f4abc26939fba31ca660f0d8d6707f6`), the
coordinate map (`e04f3b7ef6816042c89d6ea8d15efd2eeb139659f06dd967ed3a2dcca35418dc`),
and `verify.py`
(`164abdea936bb0443d66096ee89cb7059c3db2d27da945c1fb35f555042c8086`). The
pinned CalculiX profile, manual, binary, and image identifiers agree with
`source-pins.json`; the archived source and manual hashes also match the
available `/tmp` archives. The frozen run itself therefore has its deck,
oracle, coordinates, parser, supporting source copies, and solver identity
bound to this freeze.

The generator is less portable than the frozen run: rebuilding its source-pin
receipt reads the source and manual archives from `/tmp` plus repository
artifacts (`prepare.py:20-31, 660-705`). Their hashes are pinned and match in
this environment, so this does not block the frozen affine attempt; retaining
or reacquiring those exact artifacts would be necessary to regenerate the
packet elsewhere.

The affine contract is internally scoped to a software known answer. It uses
the polygonal FE area and volume, affine exterior displacement, free interior
nodes, and fixed stress, reaction-wrench, and energy gates. The model declares
that it is not candidate geometry and keeps mechanical acceptance false
(`freeze.json:12-23`). The copied verifier reports a method-fixture pass, not
mechanical acceptance (`verify.py:262-354`). Preparation, frozen inputs,
future solver outputs, parent readiness, and design acceptance remain
separate records. The support packet reports that its five offline tests,
preparation receipt, Ruff, and hash checks passed; I independently checked
the freeze and source-copy hashes but did not rerun those checks.

## Finding

**Medium — The runner does not enforce the freeze's resource and total-launch
bounds.** The freeze records 60 seconds, 1 GiB, one CPU, and one launch
(`freeze.json:16-20`). The parent runner fixes CPU at one, but accepts any
positive timeout and caller-provided memory, with defaults of 240 seconds and
4 GiB (`fea/wood_joint_reduced_native.py:104-132`). Its ledger serializes
concurrent runs and rejects a reused run ID or an execution record in the same
directory (`fea/wood_joint_reduced_native.py:133-165`), but it does not reject
a second directory carrying the same freeze digest. Thus the documented caps
are caller-enforced, and the one-launch limit is per attempt directory rather
than per freeze.

For this first affine attempt in the owner-authorized development lane, the
parent readiness record should require an empty prior-run lookup for this
exact freeze digest, reserve one fresh run ID, and call the unchanged runner
with `timeout_seconds=60` and `memory="1g"`.
The resulting authorization/execution record should retain that exact
command. Stop after that launch regardless of outcome; do not retry this
freeze. This closes the current operational gate without changing the shared
runner protocol.
