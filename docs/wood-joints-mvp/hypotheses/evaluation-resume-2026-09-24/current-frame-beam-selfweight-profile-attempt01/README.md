# Current frame beam self-weight profile — attempt01

This exploratory artifact bins the 20 exact frame-timber STEP bodies along the
source-bound `axis`, `start`, and `end` descriptors in
[`member-geometry.json`](../../mvp-acceleration-2026-09-28/reduced-static-attempt01/member-geometry.json).
The axis is sign-checked against the conditional grain direction in the pinned
material-frame map. The producer does not extract an OBB or infer a structural
axis from principal inertia.

CadQuery 2.8.0 intersects each exact BRep with 50 mm longitudinal slabs. Each
bin records exact-BRep volume and centroid under a uniform 600 kg/m³ modeled
density scenario. Bin-centroid gravity resultants, average uniform-equivalent
line loads, and discrete couples about the descriptor axis are reported. The
couples preserve each bin's resultant wrench when that finite bin is reduced to
the descriptor axis; they are not an exact continuous eccentric-moment field.
The profile conserves mass and first moment at the reported bin resolution. It
does not claim exact continuous `q(s)`.

The rotated-box known-answer fixture passes for 50 mm bins and a final partial
bin. For all 20 timbers, the 599 bins close combined gravity force to
`4.67e-9 N` and first moment about the global origin to `4.60e-6 N·mm` against
the source mass-centroid rows. Modeled total frame-timber mass and weight are
`127.5321817203 kg` and `1250.663469867 N` at 600 kg/m³. These remain conditional
on modeled geometry, the source density scenario, the selected descriptor
axes, and uniform density within each solid.

## Pinned inputs

| Source | SHA-256 |
|---|---|
| `member-geometry.json` | `121f1940d0180367f953a1f92443964ded901ca775536750a9b028e37d6c8187` |
| Current timber material-frame map | `f867b4926ed23c9f356005c134778e138c8b1230547f0b69be7c3f9bc2a42409` |
| Current mass-centroid inventory | `4c107b76d42d2a6f49b81c4857ba20bb236920932a7c34392c63e70d0882099a` |
| Attempt04 full-frame manifest | `9e682e28c3d4c3c0594863f82c6b74d19dee2700f3856d34e1a26f69082e4f11` |
| Current full-frame STEP bundle index | `8979d678f7b45d3b75fa465e810b0910d72874c5c1c705290d1fcb2bf2b78420` |
| Board-weight density scenario | `7425c8100c9bbf0586d8e1732138eb5ec1e6147f8418b5cf3ea95dc6108e035e` |
| Current load-case gravity contract | `9c7c43c51ce635ebfeaeddabdbbe2a0ac80dfd7819ec357662dd132db648b83a` |
| `pyproject.toml` | `84e007ad5c9cfffa853f21627fecbaec0a85c602560d5d5e0b507326e9b02452` |
| `uv.lock` | `5ea7a77ddb3072bfe1c2ba131e34b293a0103f931eb9b911e9eb248ccb6d84d3` |

The machine-readable source, per-member STEP hashes, descriptor stations,
bin volumes and centroids, equivalent bin wrenches, fixture, and closure checks
are in [`beam-selfweight-profile.json`](beam-selfweight-profile.json). The
record's canonical content digest is
`3d3f11095091609940a3b0525ee4f65cb54bb0afc58772b5084eecbcb928b984`.

## Limits and verification

This is not a structural support model, beam end-condition definition, line-load
section-force recovery, solver result, member or joint demand, capacity, or
design acceptance. Received lumber density, species, grade, moisture, and
transverse orientation remain unresolved. Panels, blocks, hardware, equipment
allowance, climber loads, and support reactions are outside this timber-only
profile.

From the repository root, recompute the geometry slices and compare them to the
append-only record:

```sh
uv run --no-sync python3 \
  docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/\
current-frame-beam-selfweight-profile-attempt01/produce.py --verify
```

The producer pins all source files and each of the 20 STEP files. `--write`
refuses to replace an existing record; input or method changes require a new
attempt directory.
