# Parent-path boundary for the frozen synthetic entrypoint

This is a narrow correction to [v2](../README.md). Review confirmed that
`abspath` removed `link/..` before checking components, while the operating
system could follow the original symlink to a different run. Retargeting that
hidden component during serialization could produce a receipt for evidence
no longer reachable through the supplied argument.

[run.py](run.py) rejects every `..` path component in public run, replay and
output arguments **before normalization or engine loading**. The same check
guards the public functions and the reused engine methods. Ordinary relative
paths, `./` prefixes and absolute paths remain supported. Paths requiring
parent traversal must be supplied directly without parent components.

The wrapper executes the frozen v2 launcher bytes authenticated by its
six-file map and retains the existing mechanics, finite compact/schema/claim
validation, raw repair bounds, captured-source checks and lexical identity
checks. It adds this supplement and the three v2 reviews to the source closure
through final serialization. No numerical implementation or candidate input
changes. All **17 preceding method/correction files** and all issued attempts
and reviews remain frozen.

[check.py](check.py) retains seven actual-CLI negative controls and four API
controls. They reject parent components on production output, verification
run/replay/output, the reported `symlink/../run` bypass and its installed
serialization-retarget callback. The latter is rejected before engine loading;
neither the engine nor its serialization hook executes. A separate ordinary
path reaches its retarget hook and is still rejected by the retained v2 path
guard, with no receipt. Public and backend APIs also reject parent components.

Two fresh production invocations and corrected verification pass, including a
normal `./` relative run argument. All three production files replay exactly.
The compact numerical result and all 45 bearing fields still match the
original issued bytes. The [verification](verification.json) binds the complete
**34-file source closure**, commands, checked synthetic/null-capacity claims
and original dimensional residuals. It adds no candidate force result, joint
capacity, fabrication instruction or release.

Run from the repository root with new output names:

```bash
path_guard=docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/bounded-strength-v1/connected-stack-followup-v1/limit-analysis-method-v1/evidence-correction-v1/review-fix-v2/path-boundary-v3
path_raw=fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/bounded-strength-v1/connected-stack-followup-v1/limit-analysis-method-v1/evidence-correction-v1/review-fix-v2/path-boundary-v3
uv run python -B "$path_guard/run.py" produce --out "$path_raw/reproduce-01"
uv run python -B "$path_guard/run.py" produce --out "$path_raw/reproduce-02"
uv run python -B "$path_guard/run.py" verify --run "$path_raw/reproduce-01" --replay "$path_raw/reproduce-02" --out "$path_raw/reproduce-verification.json"
uv run python -B "$path_guard/check.py" regress --out "$path_raw/reproduce-controls"
```

[Inputs](inputs.json) embed the frozen v2 map and pin the three review receipts.
Issued evidence and all controlled fixtures are retained in ignored
`attempt02`, with its source map at `attempt02/frozen-packet.json`. The unissued
`attempt01` retains its successful controls and all five packet files in
`source-at-run` before a lint-comment correction. This boundary
is the active proposed synthetic entrypoint, subject to the main session's
final independent review. Earlier packets remain recoverable history. No raw
files were archived or pruned; no CAD, frame calculation, candidate action,
shared-document edit or staging occurred. Shared integration/publication and
the separate current-frame calculations remain with the main session.
