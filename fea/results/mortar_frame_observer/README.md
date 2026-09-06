# Completed observer run: rejected diagnostic qualification

[Results and limitations](../../../docs/mortar-frame-observer.md) explain the
32-increment solve, cleanup-report bug, separate recovery, and retained failures.
`report.json` inventories every original file, direct publication file and
compressed archive by SHA256. The original terminal report is unchanged.

The four archives separate the observer log, solver fields, launch sources/context,
and local replay so each is below 100 MB. Identical copied raw files are stored
once. The existing `../full_frame_refinement/0.0625.tar.gz` and its publication
report are referenced by hash, not duplicated. `publish.py` packages already
existing evidence; it cannot launch a solver or numerical replay.

```sh
uv run pytest tests/test_mortar_frame_observer_publication.py
```

Those portable tests verify all compressed members, original/recovered source
and output hashes, baseline references, and explicit rejected diagnostics.
They do **not** independently recompute the numerical replay.

For a fresh audit of archived data, first run the integrity tests above, then
assemble the frozen package in a new temporary directory (Linux shell, from the
repository root). This runs no FEA solver and does not modify published evidence:

```sh
audit_repo=$(pwd)
audit_root=$(mktemp -d /tmp/moonboard-observer-audit-XXXXXX)
mkdir -p "$audit_root/evidence" "$audit_root/fea/results/full_frame_refinement"
for archive in observer-log solver-fields launch-provenance; do
  tar -xzf "fea/results/mortar_frame_observer/$archive.tar.gz" -C "$audit_root/evidence"
done
cp fea/results/mortar_frame_observer/recovered-report.json "$audit_root/evidence/report.json"
cp "$audit_root/evidence/launch.py" "$audit_root/fea/mortar_frame_observer.py"
cp "$audit_root/evidence/launch_sources/"*.py "$audit_root/fea/"
cp fea/results/full_frame_refinement/0.0625.tar.gz fea/results/full_frame_refinement/report.json "$audit_root/fea/results/full_frame_refinement/"
cd "$audit_root"
env -u PYTHONPATH timeout 330 "$audit_repo/.venv/bin/python" -c 'import json; from pathlib import Path; from fea.mortar_frame_observer import run_audit; p=Path("evidence").resolve(); r=json.loads((p/"report.json").read_text()); run_audit(p,r); raise SystemExit(r["audit_exit_code"])'
```

Expected outcome is **audit exit 1**, with `audit.json`, `local_replay.json`,
`coupling_resultants.json` and `audit.log` retained in that temporary directory.
The original runner applies its 300-second audit wait and 6 GiB address-space
limit; the outer timeout is an additional shell bound. The copied terminal
report is updated only in this new replay directory. An unexpected failure
before diagnostic artifacts exist is not reproduction of the retained result.

The original recovery is historical post-hoc evidence, not a claim that another
machine has independently observed the old container. A fresh replay verifies
archived arithmetic/source integrity, not real contact, material or joint capacity.

An independent agent executed this recipe on 2026-09-06. It reproduced audit
exit 1 and byte-identical `audit.json`, `local_replay.json` and
`coupling_resultants.json`; the new audit child terminated normally. This checks
the documented frozen-package replay in addition to the 75 focused software
and publication tests. No solver was rerun and no published evidence was changed.
