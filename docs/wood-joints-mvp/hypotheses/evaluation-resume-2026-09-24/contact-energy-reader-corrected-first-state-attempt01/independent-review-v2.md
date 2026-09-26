# Independent review: corrected-reader adapter v2 compatibility

This review is limited to the old-run-only adapter and its terminal
attempt02 record. It does not inspect the live attempt03 run or invoke CAD,
CCX, or a build.

Reviewed adapter pins:

- Producer `audit_corrected_reader.py`:
  `9fa150182a8d6e779433f51233e6bc3394a362e221b5c744e7b28009ef8a0a03`
- Focused tests `test_audit_corrected_reader.py`:
  `a5f3ed65ec47e89f788aa6411bbeeb37ec3ce11e9061e0d0ded020d7526d33ec`
- Regenerated `analysis.json`:
  `950d41f268878031f7d31cea5be612fddf07bd110420b20ae1bc9eeb29d244a4`
- `README.md`:
  `92e24badba9d7565fd34e278a781e8689c0027f3ec01d711487522c2eeaca858`

The run evidence binds the attempt02 source index
`c97455660320627d00803d1f2c9bd32a086f58b29dbdf0957b38babe138f761b`,
binary `4e794cae6d0495a5a543e5bd962f5dde2a3539f0cb850432e230ee23494654e9`,
and runtime image `sha256:5adec98a0bb4f4cffbcc3fa15f5014db08621f1204b65cf1f130ff46d9cd32b0`.
The execution record's actual attempt02 trajectory-source hash is
`28934ff37b9c2235c9832abc1a337ef1e3a4d78cd4aba51758238d91a6dc25fe`;
the common terminal-inspection helper is
`da85913fa670d9a2729faf02a428f296dd8f97a0c220641f37f93114cba58159`.
The later attempt03 source index (`b55323…`) is rejected by the producer's
exact index pin, so it cannot silently enter this old-build report.

The final validator checks the v2 execution schema, closed non-OOM terminal
state, return-code coherence, status-specific timeout/output/parent-stop
evidence, unchanged-input/preparation/source-index flags, and the pinned
source index, executable, and runtime image. Required outputs must match the
terminal SHA inventory; an absent point-map CSV is accepted only when its
name is listed missing and no output hash claims it. The final revision also
rejects any name appearing in a missing-output list and any of the three
output-hash inventories. It rejects disagreement between hash-map aliases
and between comparison hashes and the complete output hash map. Focused
negative tests cover the missing/hash contradiction and a terminal image
that is self-consistent but differs from the pinned source index.

I ran all 18 focused tests; they pass. I also ran the adapter against the
frozen attempt02 files with output redirected to `/tmp`. The generated JSON
is byte-identical to the pinned `analysis.json` above. The v2 run status is
`completed_outputs_incomplete`, terminal `exited`, return code 1, no timeout
or OOM. Its accepted first state is step 1 / increment 1 at 0.0005 s after
23 iterations. The terminal inventory lists the point-map CSV and all-physical
acceleration output as missing; the adapter authenticates the map's absence
and DAT is 42 bytes with no CELS table. The accepted-increment LOG energy
`3.478602e-11 N mm` is retained,
while writer/DAT comparisons are explicitly incomplete and unavailable. The
ACC-map guard error, unverified requested horizon, and false mechanical
acceptance are preserved in the report. No missing energy is substituted
with zero.

The adapter compares only the old attempt02 reader lineage. Its source-index
pin rejects attempt03 rather than implying that the old result validates the
new binary. Reader cross-check status does not imply native completion,
mechanics, or joint acceptance.

The README wording issue from the initial review is closed. It now describes
`wood_joint_dependent_native_check.py` as the shared terminal-inspection and
evidence helper called by the attempt02/03 v2 trajectory-record producers.
The actual attempt02 trajectory-source hash remains identified separately.
