# Current taper bore clearance preflight — attempt02

This append-only packet screens the reviewed `led-clearance-2x6-runner-seated-blocks-v1` CAD geometry for bore-cylinder envelope overlap with the measured leg taper interval. It reads the exact full-frame member bundle, exact left/right leg STEP files, reviewed attempt04 manifest, upstream taper report and source pins. The upstream taper packet rechecked all 216 of its pinned sources before this result was produced.

This revision preserves attempt01 and pins its complete packet, producer and test bytes. It fixes the focused test's over-specific error-message match; no CAD inputs or geometry method changed.

The producer extracts every cylindrical face from each exact leg STEP with CadQuery 2.8.0 / OCP 7.9.3.1.1. It maps each face to one of four retained frame-bolt axes in that leg using the source member pair and analytic centerline; face ordinals are not used. It checks all 92 candidate `receiver_member_ids` against their corresponding per-receiver interval rows and finds 0 candidate receiver memberships in the legs. The full-circumference cylinder envelope is projected onto the pinned global grain station and compared with the taper interval from the upstream CAD preflight.

Result: **CLEAR_WITHIN_PINNED_CAD_ENVELOPES**. The measured minimum envelope-to-taper gap is 50.712771543 mm when all mappings resolve. The full adopted criterion `taper_taper_region_unbored_torsion_applicable` remains **pending** because its authoritative table requires a fresh current case.

This is geometry-only CAD evidence. It does not establish actual holes or cuts, physical hardware size or fit, native/CAD identity, mesh equivalence, fresh case results, torsion strength, or criterion acceptance. Release flags remain false.

From the repository root, reproduce with:

```sh
.venv/bin/python -B scripts/build_current_taper_bore_clearance_preflight_attempt02.py --check
```

The producer verifies fixed source hashes, the upstream taper packet's 216 source pins, exact member/axis inventories, unique cylinder-to-axis mappings, finite numeric data and byte-identical packet outputs. `--write` is exclusive and refuses an existing packet.
