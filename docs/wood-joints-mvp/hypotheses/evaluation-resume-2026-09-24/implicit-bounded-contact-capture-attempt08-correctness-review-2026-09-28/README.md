# Independent correctness review — attempt08

Reviewed 2026-09-28. This report is bound to attempt08 `source-pins.json`
SHA-256 `998b35f0e8c885e76ea8c93435751871a07a97151ffde62f41a37479b33e00bb`,
archive `9c88385c10fb04f5dc6c4e98027a51bebdd8aee3920e05190d6c1dd08357d6e7`,
patch `abaaa6d65d709edb53043619e4a974184b2ec278ef0a3e1cba9dde7c92a84e5e`,
contract `fc0f1d5c112c698ab78b23109b836888ab3a804139ff4fbc658f8e4979f6e4a3`,
sink `0715f915f4500f5cab1810e4274ad9c18a1e3b785dccd32e4c943237765fdb28`,
and reader `8692a22286150cb88afc55e857e9791de81d208ab68af0e4360cc16e1f7638f9`.
The full packet inventory and verification results are in [verification.json](verification.json).

**Result:** no confirmed correctness findings in the reviewed offline source
delta, sink, reader, and harness. Blocker: 0; high: 0; medium: 0; low: 0.
This does not qualify a production build or solver run.

The attempt08 packet inventory hashes all match `source-pins.json`. The pinned
archive has 1,197 source files and the same SHA-256 as attempts05–07. The
attempt07 source-pins and both review-basis documents match their attempt08
pins. Replaying `capture.patch` from the archive with
`patch --batch -p1 --fuzz=0` succeeds. It changes only the three declared
members; the replayed hashes match the pins, and a line diff against the
archived originals contains insertions only.

The pinned CalculiX 2.23 `checkconvergence.c` source is SHA-256
`776ecbeec10de037dc1a18171b81ede973fca52d587a2c4d4342f0d14f362b11`.
It sets `icntrl=1` and `icutb=0` on successful convergence (lines 348–349),
sets `icntrl=1` and increments `icutb` on cutback (lines 701–702 and
820–821), and increments `iit` on the ordinary no-convergence path (line
874). The attempt08 `nonlingeo.c` hunk places `ccxcap_iteration_link_` after
`checkconvergence`; the sink validates the live `iit`, step, increment, and
attempt transition before writing the link. The reader independently accepts
nonconverged links only when the attempt is unchanged, and converged links
only when the attempt resets to one or advances by one. It derives acceptance
only from convergence plus the reset to one. The offline controls cover the
cutback, accepted retry-reset, invalid-transition closure, and mutated
nonconverged attempt cases.

The state-join writer now accounts for empty old and new candidate sets and
emits per-tie counts. The reader rejects negative join counts and checks both
old-side and new-side conservation, plus status-transition bounds. The
`MAP_SUMMARY` checks bind each summary identity to `GEN_BEGIN`, candidate
totals to the live face-span census, and candidate/reason/law partitions to
their declared totals. Trial capture requires each generated point to join
once; force aggregates require one finite row per expected point, and when
`nener==1`, energy likewise requires one enabled finite row per expected
point and a finite aggregate. Reader checks enforce these requirements even
when the caller requests permissive force or energy handling.

Temporary output is opened exclusively and unlink ownership is set only after
that open succeeds. The writer checks flush and close, then publishes by a
no-overwrite hard link; the offline controls cover pre-existing temporary and
destination paths and injected flush/close failures. Writer and reader enforce
the 128 MiB stream ceiling; the writer also bounds sweeps, face rows,
candidate rows, ties, and state storage. The reader checks byte and line
limits before splitting and validating the input.

Two boundaries remain explicit rather than findings:

- `ITERATION_LINK` stores the captured iteration, not post-hook live `iit`.
  The writer validates live `iit` at the hook; the reader cannot independently
  repeat that check from this schema. This limitation is stated in the pinned
  README and contract.
- A mutation probe changed `map_complete` or `trial_complete` to zero on a
  rejected cutback link. The reader still returned `PASS_CAPTURE_STRUCTURE`;
  the frozen contract requires these flags before treating an increment as
  accepted, and the probe kept `accepted=0`. The corresponding mutation on an
  accepted link is rejected. I therefore do not count the rejected-link probe
  as a finding. The reader API takes an already materialized `bytes` or `str`
  value, so its byte ceiling is not a streaming file-reader or strict
  peak-memory guarantee.

The exact offline command from the packet was run from the attempt08 directory:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s tests -v
```

Result: 37 tests passed. No Docker, patched production build, solver, coupon,
or native run was performed. The review does not establish production
compilation/runtime behavior, native field semantics beyond the pinned source
inspection, MPI or concurrent-process behavior, or mechanics acceptance.
