# Flush-frame contact penalty sensitivity

The A12-left case was rerun with timber-face normal penalties of 10 and
1,000 N/mm³ around the original 100 N/mm³ assumption. All three responses
are numerically accepted under the solver's contact and force-rounding checks.
Loads, timber mesh, 72 face-contact points, floor law and other connector
properties were held fixed. Source snapshots were checked against each
report's recorded hashes.

| Penalty, N/mm³ | Bolt lateral ratio | Sampled net-member ratio | Face-bearing ratio | Maximum timber displacement, mm |
| ---: | ---: | ---: | ---: | ---: |
| 10 | 0.881224 | 0.746151 | 0.112048 | 5.718632 |
| 100 | 0.879201 | 0.748768 | 0.119627 | 5.670328 |
| 1,000 | 0.878979 | 0.761916 | 0.120439 | 5.665199 |

The governing bolt comparison changes little over this penalty range. The
largest sampled net-member comparison increases by about 1.76% at the high
penalty. None of these changes closes the rim cut, leg taper, commercial-angle
or fabrication gates. All three still fail the implemented rim end-cut screen.

This is a **penalty sensitivity**, not contact-point or timber-mesh convergence.
It does not establish unsampled pressure peaks, full interface clearance,
physical contact stiffness, friction properties or other load cases. Results
belong to the preserved flush geometry, not the uncut-leg investigation.

The [machine-readable record](floor-flush-contact-sensitivity.json) lists exact
report paths, report/geometry hashes, source-snapshot counts, metrics and
relative changes. Each native directory retains its input decks, outputs and
source snapshots. The initial `penalty-10` directory records a Docker access
failure; only `penalty-10-native` is used as the accepted low-penalty evidence.

Portable report, geometry and source archives are preserved under
[floor-flush-contact-sensitivity](../fea/results/floor-flush-contact-sensitivity/README.md).
Their bundled checker output covers first-stage screens only; it is not a
complete release decision and does not override the remaining gates above.

## Reproduction

Run from the repository root with the source revision recorded in the native
snapshots, using a new output directory:

```sh
.venv/bin/python -m scripts.floor_flush_case a12-left \
  --output fea/generated/your-penalty-10-case \
  --seed fea/generated/floor-flush-first/a12-left/block-01/report.json \
  --contact-stiffness-per-area 10 --max-cycles 100
```

Repeat with penalty 1,000 and a distinct directory. The seed is an iteration
initialization, not transferred acceptance. Use `scripts.floor_flush_checks`
with the matching geometry to recompute each resistance diagnostic. The new
`--frame-size` option permits a separate mesh study; these two runs used the
unchanged 150 mm target and do not constitute that study.
