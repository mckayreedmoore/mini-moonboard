# Right four-duty rail integration

Status: source-bound installed-geometry diagnostic, 2026-09-24. This combines
the WJ-04 G7 inner pair and WJ-06 outer pair on the same four finished source
hosts. It is not a complete joint, assembly sequence, accepted replacement,
or fabrication release. The active WJ-04 configuration and viewer are unchanged.

The [report](right-rail-integration.json) records four cleats, sixteen complete
modeled stacks (80 components), and 24 removed legacy SDS axes. It retains
120 other SDS axes, twenty other angle bodies, all 66 fixed panel/kicker
screw axes, twelve starting frame-bolt arrangements, and six panels.

All four source hosts reconstruct with zero reported symmetric-difference
volume before candidate cuts. Native source machining follows each host's
actual transform: trimmed rails retain the native hole datum, whereas the
translated right side carries translated cutters. Purchased-length panel
screw cuts are applied separately as candidate work. The report audits all
24 replaced axes and records each host's native and candidate cuts.

The implemented static screens report no unintended candidate-body,
installed-hardware, or cross-bore intersections. Every declared bore layer
is present and all head/nut washer seats have full modeled support. The
side-shaft maximum-envelope comparison remains a geometric sensitivity.
These results do not establish signed load transfer, capacity, tolerance
feasibility, tool fit, or forward/reverse assembly. The proposed insertion path for each rail with its two
cleats has not been run here, and complete-layout clearance
remains untested.

Parent verified every recorded input hash against the working tree. Report
SHA-256 is `5be5efe219d0a6b9d82444e1be87580ac09a7d8209749164eb8aec315fdab99e`.
The corrected serialized run completed in 75.73 seconds. It uses the shared
six-inch bolt minimum length of 149.86 mm; the previous 150.876 mm bound
was too high by 1.016 mm. Nominal solids are unchanged. The earlier report
is preserved in the [pre-correction archive](wj12-before-receiver-completion/right-rail-integration.json). The focused adapter suite
passed eleven tests; Ruff and whitespace checks passed. No native solve or
physical observation was performed. All release and acceptance flags remain
false. This local checkpoint is uncommitted during quiet hours.

Reproduce from the repository root, with the report's matching source hashes:

```bash
uv run --no-sync python - <<'PY' > /tmp/right-rail-integration.json
import json
from scripts import wood_joint_right_rail_integration as integration
from mini_moonboard.wood_joint_frame import validate_source_binding

geometry = integration.materialize_right_rail_geometry()
assert validate_source_binding(geometry.source) == geometry.source_binding
print(json.dumps(integration.diagnostic_report(geometry), indent=2))
PY
```

The earlier missing-loader, purchased-cut/native-replay mismatch, and
candidate-cleat report-key failures were implementation diagnostics. They do
not change the reconstruction tolerance or supply any acceptance evidence.
