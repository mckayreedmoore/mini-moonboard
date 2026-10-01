# Upper packet verification

Status: extraction and calculation review completed September 30, 2026.
This verifies the packet's bookkeeping and stated conditional calculations;
it is not professional engineering review, joint acceptance or a native
response-model qualification.

The parent ran `produce.py --verify` after the final producer changes.
Frozen source hashes, accepted case/revision identities, all response gates,
92/12/66 inventories, sixteen unique upper axes, 336 bolt action records,
672 signed member directions and 84 complete block balances passed.
The JSON and CSV reproduced byte-identically. All block residuals reproduced
their source audits and passed both the original numerical tolerances and
propagated RF-rounding interval checks.

The separate [checker](check.py) reads the native DAT files directly, rather
than copying force numbers from the response JSON. It recovers all seven
ALLN force-output blocks in each case, identifies the two lateral scalar
carriers per upper bolt from the frozen source model, reverses endpoint RF
to physical source-body action and reconstructs the signed global vector.
All 336 lateral vectors match the report to 1.01 × 10⁻²⁸ N maximum component
difference. The checker independently projects those forces into each
member's conditional grain and determines the loaded grain end from the
source endpoint geometry. All 672 comparisons match to 7.11 × 10⁻¹⁵ N
for the grain component and 1.71 × 10⁻¹³ mm for loaded-end distance.

[verification.json](verification.json) binds that result to the checker,
report and freeze hashes. The direct-token check uses the existing source
carrier mapping; it does not prove the physical stiffness law, hole contact,
axial tie behavior or resistance. Axial actions and finite contact rows are
checked in the complete block sums and source audit gates, not independently
reparsed by this lateral-only checker.

A separate Luna agent at maximum reasoning effort,
`/root/corner_blocker_review`, performed a read-only review under the
repository's agent authorization. It independently reproduced all four
lateral/tension maxima, both unadopted lateral-reference conventions and
the center principal terminal-end directions. It checked force ownership,
equal-and-opposite signs, distinct endpoint locations, self-weight inclusion,
right-handed geometry/grain frames, grip dimensions and the distinction
between component references and complete strength. It reported no concrete
blocking error. Its remaining concerns are retained in the README: signed
oblique detailing applicability, nearer cuts/bores, splitting and complete
shared-member/bolt-group behavior.

Ruff passes for both scripts. Packet documentation links resolve locally.
No native solver, model alteration, stock inspection or hardware receiving
claim is part of this verification.

Read-only replay from repository root:

```sh
OPENBLAS_NUM_THREADS=1 .venv/bin/python docs/wood-joints-mvp/hypotheses/upper-frame-joint-review-2026-09-30/produce.py --verify
OPENBLAS_NUM_THREADS=1 .venv/bin/python docs/wood-joints-mvp/hypotheses/upper-frame-joint-review-2026-09-30/check.py --verify
```
