# Guarded reproduction and verification provenance

This supplement closes the two evidence-handling findings for the frozen
[revised-base audit](../README.md) and
[connected-stack followup](../../connected-stack-followup-v1/README.md).
The ten original packet files and all issued attempts remain unchanged.
Numerical results, conditional comparisons and unresolved strength questions
are unchanged. No full analysis, CAD query/rebuild, native solve, new response
or physical test ran to produce this supplement.

The original analysis CLIs accept an existing output folder and can overwrite
its JSON. Preserve those files as issued source history. **Use
[run_fresh.py](run_fresh.py) for future reproduction.** It reserves a new output
directory before source authentication, analysis imports or calculation;
an existing file, directory or final-component symlink is rejected. Each output
file is created exclusively. Failed attempts keep their reserved directory;
select a new directory for another attempt.

## Future analysis commands

From the repository root, choose an unused output directory for every call.
These commands invoke the frozen analyses' `run()` methods through the new
guard; they do not execute either original overwrite-capable CLI:

```bash
uv run python docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/bounded-strength-v1/revised-base-audit-v1/reproduction-guard-v1/run_fresh.py --packet audit --out fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/bounded-strength-v1/revised-base-audit-v1/reproduction-guard-v1/future-audit01

uv run python docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/bounded-strength-v1/revised-base-audit-v1/reproduction-guard-v1/run_fresh.py --packet connected --out fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/bounded-strength-v1/revised-base-audit-v1/reproduction-guard-v1/future-connected01 --compare fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/bounded-strength-v1/connected-stack-followup-v1/attempt02
```

The entrypoint uses only the standard library until an authenticated analysis
is imported. It checks the selected issued closure before and after calculation,
checks all ten original packet files, and uses the original source hashes:

| Packet | Frozen analysis SHA256 | Issued source pins |
| --- | --- | ---: |
| Audit | `9ec29f1ba0dba1dbbec193366284abfd1604e09099822714335c28e226bd84ca` | 1,120 |
| Connected stacks | `56c84c7fbe06da68ddfe27fe147fff52344cf0cdd0ef72cda489d9163926e82b` | 1,126 |

`--compare` reads a prior result/details pair and checks exact serialized
agreement before writing the fresh pair. It writes no comparison input.
Successful future runs add `run-provenance.json`, binding the entrypoint,
guard inputs, issued details, source closures and output hashes. The guard
does not change the original mathematical methods or issue a new joint rating.

## Retained verification source and historical recovery

The audit's original extra checker ran as interactive Python stdin, rather than
an originally retained script. The exact **2,720-byte** source was recovered
verbatim from the recorded October 9, 2026 03:23:09.816 UTC tool call
`call_62ba25e2c4c14f40bb41c0ddf0c67707`. Its SHA256 is
`221c8c19ce55435c9210248cce4c539e39bddda39b803863df6e966fb86ac579`.
The source-recovery record, original command and captured tool records remain
in their existing ignored evidence folder, bound by [inputs.json](inputs.json).
No duplicate copy is introduced here. They are active provenance dependencies.

[check_evidence.py](check_evidence.py) authenticates the recovered source against
the historical command and recorded call, matches the call/output identities,
and verifies exit-zero stdout against the original `independent-checks.json`.
It **never executes the historical command**, whose fixed output path would
overwrite that frozen file. Recovery establishes the source of the historical
observation; it is not a new saved-BREP execution or an independent engineering
review.

The retained new checker reproduces a narrower, explicit supplement:

| Fact | Reproduced or reused evidence |
| --- | --- |
| Twelve canonical intervals | Reuses the source-authenticated v3 direct-solid proof and its principal/kicker subset; checks saved-bound arithmetic without importing BREP |
| Thirty-six changed-host washer seats | Independently checks ring volume and recorded full-support tolerance; reuses the authenticated issued CAD intersections |
| Four member restraint station gaps | Independently computes station/end gaps from frozen screw coordinates and source member datums using standard-library arithmetic |
| Full/gap/clipped coupon values | Historical checker copied producer known answers; it did not independently query these coupons |

The interval reuse is explicitly bound to the prior closed v3 proof,
SHA256 `1b33f3861673c0dc179f95b5ea57be7a76c17cf64859b6c22d487356d4dcdffd`.
Its exact base SHA matches the audit. The twelve reused rows have maximum
saved-bound error **1.0001953e-7 mm**. The 36 recorded washer intersections
remain full within **0.0001 mm³**, with maximum recorded volume deficit
**1.405e-11 mm³**. Independent station gaps are **400.000, 870.150, 358.383
and 358.383 mm**. This does not qualify restraint stiffness, effective length,
Cp, delivered hardware or complete joint resistance.

## Checks and receipts

All **14 guard controls** pass. They cover fresh stub output, rejection of
existing populated/empty directories, files and symlinks, exclusive-write
collisions, changed sources before/during calculation, failed-attempt retention,
and matching/mismatching comparisons. Both real future CLIs reject their issued
attempt directories under `python -S`, before third-party imports or analysis.
Successful calculation fixtures use standard-library stubs through the common
guarded runner. They do not claim a new full-analysis reproduction.

The evidence supplement rejects four corrupted fixtures: altered interval
bounds, a partial intersection, altered ring volume and a shifted header screw
station. Both original source closures verify before and after the controls;
the supplement verifies its 1,147-source extended closure. Ruff passes for
the three new scripts. [result.json](result.json) contains the compact receipts,
and [verification.json](verification.json) binds files, commands and raw outputs.

Run these cheap checks into unused directories:

```bash
uv run python docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/bounded-strength-v1/revised-base-audit-v1/reproduction-guard-v1/check_guard.py --out fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/bounded-strength-v1/revised-base-audit-v1/reproduction-guard-v1/future-controls01

uv run python docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/bounded-strength-v1/revised-base-audit-v1/reproduction-guard-v1/check_evidence.py --out fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/bounded-strength-v1/revised-base-audit-v1/reproduction-guard-v1/future-evidence01
```

The original packets stay active for their frozen old-action/base-v3 scope.
This supplement is the active future-entrypoint and verification reading path.
Historical commands, recovery records, original attempts and the existing v3
proof remain recoverable; none were pruned. The parent owns shared summary,
ledger, staging, review and publication. No strength acceptance or physical
release is added.
