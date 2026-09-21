# PB01 short-block tension-only diagnostic evidence

Two NEW `quarter_short` old-proxy hybrid sensitivities were numerically accepted with
both contact and axial active sets converged at cycle 13. A12-left and K12-right use
the same 260 source hashes, solver image, and trial stiffnesses. They are diagnostic
results only: no V4 same-case joint demand, capacity, structural qualification,
bolt schedule, or drilling release follows from them. The preserved bilateral
archive is separate and unchanged.

## Retained evidence outputs

- [A12-left evidence](../bolted-candidate-evidence/pb01-short-tension-a12-165adbf-evidence.zip)
  SHA-256 `4a3a700222fb8335fa8365339be5b1f3b0a72df0e803c91ee894729546c3dfa8`
- [K12-right evidence](../bolted-candidate-evidence/pb01-short-tension-k12-165adbf-evidence.zip)
  SHA-256 `e5fafb5fd56bf73901d7438e38304a378344808b57840a8632b16c937cfedd7c`
- [Signed comparison](../bolted-candidate-evidence/pb01-short-tension-a12-k12-165adbf-comparison.json)
  SHA-256 `09df8d9f7e59f1518c41c65942d6aebf02a2ccaf5b7b5373fb41d63f4038d194`

These self-contained evidence files have been copied byte-for-byte from
temporary storage and verified in the repository. The original `/tmp` run
directories are not the retained source of record.

Each ZIP contains the unchanged top report and diagnostic scope, matching final
cycle input/report/deck (`frame.inp`)/data (`frame.dat`)/log/STA, all source
snapshots named in `source_sha256`, replay metadata, signed PB01 results, and a
member-hash manifest. The packager checks selected artifact digests against the
top report and source snapshots against both hash maps; archive verification
repeats those checks without the original run directory. The comparison checks
both archives and requires matching source hashes, solver image, and stiffnesses.
The raw earlier cycles and large FRD displacement field are omitted.

## Signed comparison

Positive bolt extension is tension; negative extension is shortening with zero
bolt tension. Positive face opening is a gap; negative opening is compression.
Contact and bolt forces are nonnegative unilateral spring magnitudes. The JSON
comparison gives every bolt and face point, with deltas defined as K12 minus A12.

| PB01 observation | A12-left | K12-right |
| --- | ---: | ---: |
| Rail r1 extension / bolt tension | +0.020495 mm / 20.495 N | +0.019668 mm / 19.668 N |
| Rail r2 extension / bolt tension | -0.043134 mm / 0 N | -0.072336 mm / 0 N |
| Upright u1 extension / bolt tension | -0.001703 mm / 0 N | -0.059757 mm / 0 N |
| Upright u2 extension / bolt tension | -0.008806 mm / 0 N | -0.070543 mm / 0 N |
| Upright closed face points / summed compression | 2 / 14.565 N | 4 / 62.831 N |
| Rail closed face points / summed compression | 2 / 19.808 N | 2 / 31.196 N |

The summed face forces are model spring outputs, not allowable joint capacities.

## Rebuild and verify

From the repository root, use fresh output paths. `build` and `compare` refuse
to overwrite existing outputs.

```sh
uv run python -m scripts.simple_pb01_short_tension_evidence build \
  /tmp/pb01-short-tension-a12-165adbf /tmp/pb01-short-tension-a12-165adbf-evidence.zip
uv run python -m scripts.simple_pb01_short_tension_evidence build \
  /tmp/pb01-short-tension-k12-165adbf /tmp/pb01-short-tension-k12-165adbf-evidence.zip
uv run python -m scripts.simple_pb01_short_tension_evidence verify \
  /tmp/pb01-short-tension-a12-165adbf-evidence.zip
uv run python -m scripts.simple_pb01_short_tension_evidence verify \
  /tmp/pb01-short-tension-k12-165adbf-evidence.zip
uv run python -m scripts.simple_pb01_short_tension_evidence compare \
  /tmp/pb01-short-tension-a12-165adbf-evidence.zip \
  /tmp/pb01-short-tension-k12-165adbf-evidence.zip \
  /tmp/pb01-short-tension-a12-k12-165adbf-comparison.json
```

The archived `replay.json` records the source directory, original report digest,
solver image, final cycle, trial stiffnesses, and producer command. A fresh
native replay still requires the solver and recorded source environment; archive
verification checks evidence integrity and does not rerun the solve.
