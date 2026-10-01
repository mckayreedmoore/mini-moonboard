# Current steel elastic role map, attempt 01

## Result

This source-only map binds the existing conditional generic steel elastic
scenario to the 460 candidate hardware component-role records on the 92
candidate bolt axes in full-frame manifest attempt03. Each axis has five
modeled roles: `shaft`, `head`, `head_washer`, `nut_washer`, and `nut`. The
head and shaft role rows share one candidate physical-bolt identity while
remaining separate source mass/component roles; this does not define a fused
finite-element body.

For future diagnostic comparisons, the map carries the reference scenario
(`E = 200,000 MPa`, `ν = 0.30`) and all eight other cases in the existing
3-by-3 numerical sensitivity grid. One scenario is intended to apply
uniformly across the 460 candidate roles in a comparison. These are
conditional model inputs, not observed or delivered hardware properties.

The 60 component-role rows on the 12 retained frame-bolt axes are listed in a
separate inventory with no material assignment. The existing material policy
requires those roles to be separately considered only if they enter a frozen
mechanics model, and the manifest still requires their current-candidate
recheck.

## Source joins and limits

The producer joins the exact component IDs and receiver member references in
the source-to-topology map to the candidate axes and modeled geometry records
in full-frame manifest attempt03. It verifies all five roles per axis, all
receiver references, and the separation between the 92 candidate axes and 12
retained axes. The geometry records are candidate model data; they do not
establish delivered part dimensions, purchase length, thread engagement,
hardware grade, or physical head-to-nut order.

The elastic values and sensitivity cases come from the pinned steel helper.
The current material scenarios authorize reusing those generic values for
current candidate bolt, washer, and nut component roles while explicitly
excluding the older helper's 32-body identity and scope. This map does not
identify alloy, grade, heat treatment, yield strength, plastic response,
preload, fastener resistance, or connection acceptance. No physical
receiving, CAD rebuild, solver deck, body/element/DOF mapping, native solve, or
release is represented. Full-frame readiness remains false.

## Reproduction

From the repository root, verify the record against its pinned source files
and canonical digest:

```sh
python3 docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-steel-elastic-role-map-attempt01/produce.py --verify
```

To create the JSON once in a fresh attempt directory, use `--write`. It checks
all source SHA-256 pins and uses exclusive creation; it refuses to overwrite
an existing output. A changed source requires a new numbered attempt.

## Pinned inputs

| Source | SHA-256 |
| --- | --- |
| Current mass source-to-topology map, attempt03 | `308a329a0b40db454d5b0e27c9ec2eca92d66eec96bfb222df5f7b7185bef4d4` |
| Current full-frame input manifest, attempt03 | `2f5eed3e4fa01e62e776d8fc0e4fae12182f86e1d84c63c956dbe7b44fbb5896` |
| Current material scenarios | `dd76354c0fa68a01a336cef22fe1cf854baaaf1ceda22dd11ceb881a274bb3c4` |
| Steel elastic scenario source | `e97f7df51e6553698e1542079d722022cdbbedad83f740ee42d85b56e6b394c3` |
| Steel material helper | `0cf45f5194231f61500df14ed580adb9742f6b0c7df659382ea658c7598e8d02` |
| Referenced CalculiX 2.21 manual | `16b6bab5a3f1a40a21fff62379f95c804a58d93758ab2e9a489b18d911dc20c8` |
| Topology-map producer | `16645507e1910e038e83b5acc0026b9fb12940db0f194732b355b4ef76a982f9` |
| Full-frame manifest producer | `1d9f1417b33d6d6ef2626c6f1b3957579361c960f59f963e3b8157df5fbf35f2` |
