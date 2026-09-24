# WJ-04 upper G7 crosscut probe

Status: revised, unaccepted paired-geometry hypothesis. It does not change the
active configuration or manifest and grants no purchase, drilling,
fabrication, structural, or physical-replacement acceptance.

## Reproduction and provenance

Run from the repository root with the revision that contains the archived
producer and report:

```sh
uv run python -m scripts.wood_joint_wj04_upper_g7_crosscut_probe --materialize > /tmp/wj04-upper-g7-crosscut.json
```

The archived JSON is byte-identical to the preserved report, SHA-256
`1d103d1ebf711ed1ae8237b67fdbbd0e4e410d79a10e4b1c0b160495b8debdf3`. Producer
SHA-256 is
`94d2b301450c942f1c7a95f89e3e7ee1ed643ce4db43576c78c1bce04f9302b9`; focused
test SHA-256 is
`a83de0e8b2781638e9d06899a759829cc38a07ff296d3c1a2467a764cfbbb3dd`.

The report identifies candidate `compact-floor-flush-development`, variant
`kerf-right`, canonical WJ-04 config SHA-256
`d1c63e1fa5617999e8af68d683cc0f3074fb84f518b048a087ec5ed276206c0e`, and
source-inventory SHA-256
`07af4c3eb642cf3887595fe4415eb65404cdcf74d66c5c7bb182847ef21c2d78`. It also
records fixed screw-axis SHA-256
`22224a0afc78500cb0f832f3b6c6ea4e0d1dd934813c8570d637c16cb052a4f1`, frame
bolt-axis SHA-256
`524792bb6fe1f966a7725aad7a7ed4290c355bebafcc27d84f9a5e2690ad3e27`, runtime
module and shape hashes, and path/hash entries for 33 declared inputs. The
full recorded provenance is in the JSON; these entries describe the report's
declared inputs. The predecessor `full_x88p9_lower_upper_pair_hypothesis` remains
preserved separately as `wj04-upper-pair-probe.json` (SHA-256
`2df952ff8b01a9b56b1c445d54d5aea8ea7b94b75b818bcc002a1719168b9d9f`).

## Geometry and remaining blockers

- The pair keeps the lower full-stock cleat and uses an upper 88.9 × 88.9 mm
  cleat with an 86.9 mm N-depth crosscut; their nominal clear gap is 55.15 mm.
  The upper cleat has a nominal 2.0 mm clearance from the provisional 50.8 mm
  `hold_tnut_main_G7` projection; delivery and placement tolerances are not
  included. The crosscut reduces the upper
  two-face contact-area screen from 10,641.33 to 7,725.41 mm² (27.4%). This is
  geometry only; no load transfer is inferred.
- The cleat bodies have no reported host, other-wood, panel, protected-volume,
  or pairwise intersection. All eight bores cover their two intended wood
  layers, with no unintended wood, panel, or protected hits. Installed stack
  components have no reported intersections, and all 16 head/nut washer seats
  are fully supported.
- The rail-row end distance is 26.95 mm at each bolt, or 0.6063 of 7D. This
  factor is conditional on signed demand and member-specific resistance
  checks; neither is assessed here.
- The eight stacks use a provisional `25C600HCS5Z` 6-inch partially threaded
  cap-screw envelope at 127.0 mm grip. Catalog fit, delivered thread
  transition, functional nut engagement, and capacity remain unverified.
- With all source service members in place, rail-bolt insertion paths are
  blocked and the assembly screen finds no clear installed order. Reversing
  the upper rail stack removes its installed axial overlap, but the probe says
  the upper bolt/cleat subassembly must be installed before the lower cleat
  occupies its insertion path, or another erection path must be proven. Actual
  tool access is unresolved; envelope results prove neither physical access
  nor impossibility.

The report is a local two-duty geometry hypothesis, not a complete WJ-06
layout or load path. Its claim boundary records zero accepted replacements and
keeps structural acceptance, capacity, purchase, drilling, and fabrication
release false.
