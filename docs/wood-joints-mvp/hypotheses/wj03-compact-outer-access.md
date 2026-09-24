# WJ-03 compact outer access screen

Status: `diagnostic_only_not_acceptance`. Archive preserves one sampled access
hypothesis; it changes no active configuration, pins, or manifest.

## Reproduction and binding

Producer has no CLI. From repository root:

```sh
uv run python - <<'PY' > /tmp/wj03-compact-outer-access.json
import json
from scripts.wood_joint_wj03_compact_outer_access import build_access_report, materialize_geometry

print(json.dumps(build_access_report(materialize_geometry()), indent=2, sort_keys=True))
PY
```

Archived report SHA-256: `cd4e8350254e7ff24f0ebb1a7dcf756f9b182e5b7274320f3bccfb402a3a1cf1`.
Producer SHA-256: `d1a909da2bfa660d00731551972e6b256da70c9e124f4057b04a47c5404592bc`.
JSON `source_binding` lists direct input hashes, including source inventory
`07af4c3eb642cf3887595fe4415eb65404cdcf74d66c5c7bb182847ef21c2d78`; pins are
partial, not a complete transitive closure. Inventory
identifies selected source authority `df7f5eca86ae831b35a8bcf9e6dcd7ae8af852bb`.

## Results and limits

- Six outer-body removal translations pass sampled screens: both sides'
  bridge, under-header link, and spine. Removal order is bridge → link → spine;
  assembly is recorded as reverse. Screens do not establish continuous motion.
- All 20 provisional bolt stations pass straight shaft and head envelopes
  (40 checks). Each axis retains 778 obstacles: intended bored wood, frame and
  legacy hardware, services, T-nuts, panel screws, WJ-05 components, other
  WJ-03 hardware, and staged panels. Own stack is excluded. No tool fit or
  nut-removal screen is included.
- All 42 lower-panel/kicker screw axes remain fixed; nominal 50 × 25.4 mm tool
  proxies and 114.3 mm shaft-withdrawal envelopes pass. Lower-panel outward
  translation and sampled return pass. Kicker hits lower panel if left in
  place (1–18 mm; max overlap 33.544427 mm³); with lower panel staged, kicker
  translation and reverse pass. Thus lower panel stages first. Hold/hold-bolt
  removal remains an unverified precondition.
- Global z=0 is analytical. Body paths stay ≥56.1 mm above plane; body-plus-
  bolt stroke minimum is 126.251 mm. Report-wide installed hardware and
  body/hardware/detached-path minima are +0.1928 mm, inherited from WJ-05
  diagnostic installed geometry; this is not outer-bolt ground penetration.
  −54.8072 mm `body_hardware_and_tool` is from WJ-05 diagnostic tool proxies,
  not WJ-03 outer hardware or a verified floor.

No continuous motion, support/capture, hand access, tolerances, physical tool
fit, capacities, or complete-joint acceptance is established. WJ-05 receiver
and bore shapes are collision geometry only.
