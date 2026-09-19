# V4 small center evidence bundle

This review archive captures one numerically accepted, provisional A1-rear
diagnostic with an assumed 10,000 N/mm joint spring. It supports inspection and
re-extraction of same-case left-center actions. It establishes no bolt rating,
resistance acceptance, six-case envelope, or drilling release.

The [published archive](center-a1-rear-10k-evidence.zip) is the review copy.
Verify it from a checkout without the local diagnostic directories:

```sh
uv run --group dev python -m scripts.bolted_center_evidence_bundle verify \
  docs/bolted-candidate-prototypes/center-a1-rear-10k-evidence.zip
```

With the local full diagnostic available, regenerate it with `build` and the
same archive path, then verify. The archive is not a fresh native solve.

The archive holds the byte-for-byte original `report.json` as
`original-report.json`. That report retains all contact cycles, numerical
equilibrium records, the complete source digest list, and the complete original
artifact digest list. `report.json` is a derived replay copy with its artifact
and source lists restricted to the packaged files. Both reports retain the
same diagnostic scope and final-cycle selection. The archive also holds the
full final `cycle-09/input.json`, `diagnostic-scope.json`, six required producer
source snapshots, `actions.json`, and `bundle-manifest.json`. The manifest
hashes every other archive member. The selected source and input hashes must
also match the original report.

Verification reconstructs the small replay directory, runs the existing
source-bound candidate extractor, and compares the extracted same-case actions
with `actions.json`. Its report digest identifies the derived replay report;
the original report's separate digest is in `bundle-manifest.json`. No raw
solver cycle directory, solver output, model pickle, or earlier-cycle input is
packaged. The original artifact manifest still names those local files so the
full run remains traceable; the archive does not re-run the numerical solve.

The published archive is 1,189,991 bytes (about 1.14 MiB), SHA-256
`c597fd21cf3f985662702da56e91df7e503ade2742565fa30e4e780d65fb08c5`.
