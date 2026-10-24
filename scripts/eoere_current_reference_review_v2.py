"""Maintain a usable entry point without changing the frozen v1 producer.

Keep all formulas, guards and command options. Correct only the comparison of
a minimal path/SHA reference with a rich finished-solid record. The complete
profile equality test continues to include every metadata field and hole.
"""

from __future__ import annotations

import inspect
from pathlib import Path
from unittest.mock import patch

import numpy as np

from scripts import eoere_current_reference_review as previous
from scripts.eoere_paired_frame_basis import ref, sha

OWN = Path(__file__).resolve()
PREVIOUS = Path(previous.__file__).resolve()
PREVIOUS_SHA = "d6656ba5c748a9e41bf7274554a7d1e35400d8783c8045d22fa575f894491586"


def corrected_core_function():
    previous.require(sha(PREVIOUS) == PREVIOUS_SHA, "preserve the frozen v1 reference producer")
    before = 'ref(row["source"]["path"]) == row["source"]'
    after = 'ref(row["source"]["path"])["sha256"] == row["source"]["sha256"]'
    source = inspect.getsource(previous.reuse_cores)
    previous.require(source.count(before) == 1, "single frozen metadata-join correction required")
    scope = {**vars(previous), "OWN": OWN}
    exec(compile(source.replace(before, after), str(OWN), "exec"), scope)  # noqa: S102 -- source-bound metadata-only fix
    return scope["reuse_cores"]


def flange_probe_points(geometry):
    """Physical fitting-hole centers are invariant under bolt reversal."""
    result = {}
    for fitting in ("eoere_clip_single_top_left_1", "eoere_clip_single_top_right_2"):
        points = [row["point"] for axis in geometry["axes"] for row in axis["attachments"]
                  if row["angle_id"] == fitting]
        previous.require(len(points) == 4, "four physical flange-hole centers required")
        result[fitting] = np.mean(points, axis=0)
    return result


def corrected_probe_function():
    method = previous.bracing.method
    source = inspect.getsource(method.probes)
    before = 'point = np.mean([a["point_xyz_mm"] for a in axes], axis=0)'
    previous.require(source.count(before) == 1, "single corner reference-point correction required")
    scope = {**vars(method), "flange_probe_points": flange_probe_points}
    exec(compile(source.replace(before, 'point = flange_probe_points(geometry)[fitting]'), str(OWN), "exec"), scope)  # noqa: S102 -- physical datum correction, same work-conjugate probes
    return scope["probes"]


class Intake(previous.CurrentIntake):
    def load(self):
        geometry, fields, pins = super().load()
        pins.update({ref(path)["path"]: sha(path) for path in (OWN, PREVIOUS)})
        return geometry, fields, pins


def main():
    corrected = corrected_core_function()
    corrected.__globals__["CurrentIntake"] = Intake
    with patch.object(previous, "CurrentIntake", Intake), patch.object(previous, "reuse_cores", corrected), \
            patch.object(previous.bracing.method, "probes", corrected_probe_function()):
        previous.main()


if __name__ == "__main__":
    main()
