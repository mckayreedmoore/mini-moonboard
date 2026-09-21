# Astra RV-3: PB-01 four-contact quarter diagnostic evidence

This directory preserves the latest relevant `a12-left` quarter-labelled
four-contact run found in `/tmp`: `mini_pb01_quarter_contact4_a12left_4c60e46`.
The top-level report SHA-256 is
`c10b2b2d1b979fe82ffc5bca31c60e374650610e4c44245e8e56431c7b0c4918`.
The copied archive SHA-256 is
`fc298a3a481437a5dc9f24c02bc9a234458074c2ffcba6753fe33875f4805546`.
It is a byte-for-byte copy of the existing frozen archive in
`docs/bolted-candidate-prototypes/`; no native solve was run for RV-3.

The [archive](pb01-quarter-contact4-a12left-evidence.tar.gz) contains the
original report and its 260-entry source SHA-256 manifest, all 260 source
snapshots, diagnostic scope, and matching `cycle-13` input and report. It also
contains that cycle's native solver deck (`frame.inp`), data (`frame.dat`),
run log (`frame.log`) and status (`frame.sta`). The report records the full
14-cycle contact history and original artifact hashes; earlier raw cycles are
not packaged. The empty or nonessential native outputs and model pickle are
not needed for the local-force extraction.

[Local forces](local-forces.json) are the signed bolt/contact actions and
interface resultants from the existing source-authenticated extractor.
[Replay seed](replay-seed.json) records the source commit, case, variant,
contact update strategy, initial contacts, solver image, trial stiffnesses,
scope and runner arguments. The native source snapshots are the preserved
source-of-record for this run; the current checkout may have changed.

To verify or regenerate the two small JSON sidecars from the frozen archive,
run `python3 docs/bolted-candidate-evidence/archive.py` from the repository
root. This checks the archive identity, source snapshots, final-cycle hashes,
and local extraction. It never invokes the solver. The source archive is only
needed if the copied archive is absent. The original extractor can also run
against this copy with `python3 -m scripts.simple_pb01_hybrid_local_actions
--archive docs/bolted-candidate-evidence/pb01-quarter-contact4-a12left-evidence.tar.gz`.

This run uses one trial 1/4-in four-bolt cleat at PB-01 with four
compression-only contact samples on each face; 23 other ML24Z/SDS stations
remain old-topology proxies. Bolt axial, bolt lateral and total face normal
stiffness were each assumed 1,000 N/mm. The quarter variant changes trial
stack mass only in this native model; bore diameter does not change its mesh.
Convergence and equilibrium apply to this numerical diagnostic only. It is
not a V4 same-case demand, joint rating, design acceptance or drilling release.

## Later six-inch, tension-only diagnostic (different model)

The separate [A12-left ZIP](pb01-short-tension-a12-165adbf-evidence.zip),
[K12-right ZIP](pb01-short-tension-k12-165adbf-evidence.zip), and
[signed comparison](pb01-short-tension-a12-k12-165adbf-comparison.json)
record the 152.4-mm corner-block variant with no-preload tension-only bolt
axial springs and compression-only face contacts. Both cases converged at
cycle 13 with numerical equilibrium. Each ZIP contains the final-cycle
input/report/native files and 260 authenticated source snapshots. Run
`uv run --no-sync python -m scripts.simple_pb01_short_tension_evidence verify`
followed by the ZIP path to verify it without the temporary run directory.
See [the case note](../bolted-candidate-prototypes/simple-pb01-short-tension-evidence.md)
for hashes and scope. These newer runs still retain 23 legacy connector
stations and do not qualify a complete V4 frame, joint or drilling plan.
