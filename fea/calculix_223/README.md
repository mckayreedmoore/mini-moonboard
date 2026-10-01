# CalculiX 2.23 development toolchain

The owner requested this update on September 27, 2026. The locally installed
image is `mini-moonboard-fea:ccx-upstream-2.23-v1`. Use the immutable image ID,
explicit binary path and binary hash in `solver-profile.json` for new wood-joint
diagnostics. The binary is `/usr/local/bin/ccx-upstream-2.23`; invoking the
inherited `/usr/bin/ccx` would still run the preserved 2.21 package.

The selected baseline, existing 2.21 images, frozen inputs and previous
evidence retain their original pins. Existing historical runners have not
been rewritten to silently use a different solver. A new joint runner must
consume the new profile explicitly and bind it into its input manifest.

The six unchanged method fixtures reproduce the 2.21 numerical audit values
exactly at the available output precision. Balanced-force loading passes;
the prescribed dynamic average-MPC route remains unsuitable. These tests do
not validate the actual joint's C3D10 elements, contact or bolt/nut coupling.
See the [upgrade record](../../docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/calculix-2.23-upgrade-attempt01/README.md).

The official 2.23 source archive is pinned by SHA-256. The build uses the
existing immutable development image for its compilers and libraries. No
upstream source files are patched. `Makefile.upstream` adapts library paths
and uses `-cpp`, as required by the official 2.23 Makefile. The first attempt
omitted that flag and failed on `ifport.mod`; its record is retained.

To reproduce on a machine with the recorded base image and no existing 2.23
tag, use a fresh output directory:

```bash
python3 fea/calculix_223/build.py fea/generated/calculix-2.23-build-NEW
.venv/bin/python fea/calculix_223/replay.py \
  fea/generated/calculix-2.23-build-NEW \
  fea/generated/calculix-2.23-replay-NEW
```

The builder refuses to replace an existing evidence image. Replays copy
source-bound input decks and auditor implementations into a new directory,
run jobs serially, and preserve raw output and executable identity. A failed
motion fixture is a retained diagnostic, not an overall structural pass.
