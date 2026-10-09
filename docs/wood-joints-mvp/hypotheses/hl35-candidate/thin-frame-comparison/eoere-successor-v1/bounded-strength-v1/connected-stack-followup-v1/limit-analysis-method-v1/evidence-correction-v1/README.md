# Corrected synthetic evidence entrypoint

This corrects two confirmed evidence-handling defects in the frozen
[synthetic benchmark](../README.md). It reuses its numerical calculation and
dimensional field checker. **All six original files, issued attempts and
independent reviews remain unchanged.** No candidate action, material or
geometry is introduced, and complete candidate joint resistance remains null.

The original numerical equations, 45 fields, LP certificates and byte replay
passed independent review. Review also demonstrated that the original producer
could label an old-input calculation with a later input hash, and that the
original verifier could accept forged capacity/scope claims, invented analytic
answers and a NaN compact moment peak. Use this entrypoint for future synthetic
production and verification; the original CLIs remain historical evidence.

## Source binding and validation

[correction.py](correction.py) reads and authenticates the exact original input,
analyzer and checker bytes before importing or computing. It executes the
captured, authenticated Python source and parses the captured input bytes.
The original six-file manifest is embedded in [inputs.json](inputs.json) and
bound to its issued digest; no copied numerical implementation is introduced.
The source closure also includes the correction, its regression checker,
correction inputs, five external references and three original review receipts.
All **17 source files** are checked through final serialization before a
successful production marker or verification receipt is written.

Production requires a new directory and creates files exclusively. A source
change during calculation or serialization rejects the attempt. The
`run-provenance.json` success marker binds the result/detail hashes, captured
input hash, complete source snapshot, validated claims and dimensional checks.
The corrected verifier requires this marker, reads a stable snapshot of both
run and replay, and checks their bytes and source/output bindings.

Before calling the retained dimensional checker, it rejects nonfinite JSON
numbers, duplicate JSON keys, unrecognized fields or schemas, altered method
limits and any candidate/capacity claim. Case and grid coverage must exactly
match the frozen inputs. All six analytical raw-mode answers are independently
recomputed with 48-digit Decimal arithmetic; governing modes, published rounded
references, loads, scaling, refinement, summaries and reported end actions are
checked against the inputs and fields. LP residuals must be finite and within
the frozen tolerance. The corrected verifier does not reconstruct LP KKT
matrices; the preserved numerical correctness review supplies that separate
check. Successful receipts record the claims actually validated from the
input artifact.

## Regression evidence

The retained [check.py](check.py) exercises the actual command-line entrypoint.
Its [compact verification](verification.json) binds commands and detailed
results retained in ignored output.

- **23 corrupt-result controls reject without issuing a receipt:** separate
  candidate-input/capacity flags, non-null capacity, wrong schema/disposition,
  invented raw modes/loads/equations/published comparisons, NaN peak, infinite
  summary, duplicate or missing cases/grids, invented summary counts/modes,
  altered source closure/limits/scaling, invalid residual, extra claim and
  duplicate JSON key. Forged run and replay bytes match each other, and their
  provenance hashes are updated, so rejection does not rely on a trivial
  replay or output-hash mismatch.
- **Five isolated source-change controls reject before writing any output:**
  original input, analyzer, checker and correction change during the real
  calculation; original input also changes during final serialization. Each
  fixture has its own copied source tree. Shared and original files stay intact.
- A consumed evidence file changed after receipt serialization is rejected.
- Existing directory, file, dangling symlink, directory symlink and verifier
  output are refused. Receiving fixtures and issued bytes remain intact.
- Two fresh production invocations and corrected verification pass. Their
  result and detail files match the original issued bytes; all three fresh
  production files match the second run byte-for-byte.

The maximum independent member-force residual remains `9.10e-13 lbf` and the
end-moment residual remains `3.39e-12 lbf·in`. The original maximum 128-cell
raw analytical shortfall remains **0.005209%**. These are scalar synthetic
method results, not ASD or complete joint capacities.

## Reproduction and retention

Run from the repository root. Choose new output names; existing files and
directories are intentionally refused.

```bash
correction_dir=docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/bounded-strength-v1/connected-stack-followup-v1/limit-analysis-method-v1/evidence-correction-v1
correction_raw=fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/bounded-strength-v1/connected-stack-followup-v1/limit-analysis-method-v1/evidence-correction-v1
uv run python -B "$correction_dir/correction.py" produce --out "$correction_raw/reproduce-01"
uv run python -B "$correction_dir/correction.py" produce --out "$correction_raw/reproduce-02"
uv run python -B "$correction_dir/correction.py" verify --run "$correction_raw/reproduce-01" --replay "$correction_raw/reproduce-02" --out "$correction_raw/reproduce-verification.json"
uv run python -B "$correction_dir/check.py" regress --out "$correction_raw/reproduce-controls"
```

Issued correction evidence is in `attempt01`, including both fresh runs,
the full regression receipt, rejected evidence and copied source-change
fixtures. Its source map is `attempt01/frozen-packet.json`. The original
`limit-analysis-method-v1/independent-review-v1` receipts remain pinned and
recoverable. The original six files and this correction remain active method
evidence. All raw attempts and controls are retained; no archive or pruning
operation is proposed. The small permanent supplement contains source, input
pins and compact verification; it reuses the original result rather than
duplicating the 45 detailed numerical fields. Shared summary integration,
publication and fresh independent review belong to the main session.
