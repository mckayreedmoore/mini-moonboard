"""Immutable-source guard and loaded-root recovery around frozen4103 seam.

This adds no stiffness, support, gravity distribution or candidate reader.
The declared collector point-wrench scenario remains an interpolation choice.
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np

OWN = Path(__file__).resolve()
BASE = OWN.with_name("assembly_interface.py")
BASE_SHA = "4103015c05405e930e10c90edb5e147dd9d1ec2fb0575f17e3e4efc01a6cb66b"
LOADED_SHA = hashlib.sha256(OWN.read_bytes()).hexdigest()
SPEC = importlib.util.spec_from_file_location("eoere_frozen4103_assembly", BASE)
base = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(base)
four = base.four
ROUTE = base.ROUTE
model_from_reference_pose = base.model_from_reference_pose


def source_pins():
    four.require(four.sha(BASE) == BASE_SHA and four.sha(OWN) == LOADED_SHA,
                 "loaded guarded or frozen assembly source changed")
    return {**base.source_pins(), str(OWN.relative_to(four.ROOT)): LOADED_SHA}


def _canonical(value):
    if isinstance(value, np.ndarray):
        return {"shape": value.shape, "dtype": str(value.dtype), "data": value.tolist()}
    if isinstance(value, dict):
        return {key: _canonical(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_canonical(item) for item in value]
    return value


class GuardedFourPortAssemblyElement(base.FourPortAssemblyElement):
    """Reject changed inputs/operators/maps; recover roots at the loaded heel."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._sources_at_construction = source_pins()
        self._operator_at_construction = self._fingerprint()

    def _fingerprint(self):
        model = {key: value for key, value in vars(self.model).items()}
        state = {"model": model, "indices": self.indices, "scale": self.scale,
                 "body_id": self.body_id, "ndof": self.ndof, "rotation_scale": self.rotation_scale,
                 "source_sha256": self.source_sha256}
        return hashlib.sha256(json.dumps(_canonical(state), sort_keys=True,
            separators=(",", ":"), allow_nan=False).encode()).hexdigest()

    def _check(self):
        four.require(source_pins() == self._sources_at_construction,
                     "source contract changed after construction")
        four.require(self._fingerprint() == self._operator_at_construction,
                     "four-port scenario/operator/map changed after construction")

    def _call(self, name, *args, **kwargs):
        self._check()
        result = getattr(super(), name)(*args, **kwargs)
        self._check()
        return copy.deepcopy(result)

    def elastic_block(self):
        return self._call("elastic_block")

    def descriptor(self):
        result = self._call("descriptor")
        result.update(source_sha256=source_pins(), immutable_operator_snapshot_sha256=self._operator_at_construction,
                      loaded_root_recovery=True)
        return result

    def point_port(self, *args, **kwargs):
        return self._call("point_port", *args, **kwargs)

    def centroid_load_port(self, *args, **kwargs):
        return self._call("centroid_load_port", *args, **kwargs)

    def rigid_modes(self, *args, **kwargs):
        return self._call("rigid_modes", *args, **kwargs)

    def project_loads(self, *args, **kwargs):
        return self._call("project_loads", *args, **kwargs)

    def response(self, q_stored, *, loads=(), declared_route):
        self._check()
        result = self._call("response", q_stored, loads=loads, declared_route=declared_route)
        q = four.array(q_stored, (24,))*self.scale
        full = np.r_[result["loaded_heel_q_mm_rad"], q]
        roots, flanges = [], {}
        for element in self.model.elements:
            local = self.model.relative @ element["B"] @ full
            action = self.model.relative.T @ (self.model.tip_K @ local)
            root = np.r_[element["world_basis"] @ action[:3], element["world_basis"] @ action[3:6]]
            roots.append({"body": self.body_id, "port_id": element["id"], "flange": element["flange"],
                          "point_xyz_mm": element["root"].tolist(), "applied_to_strip_force_xyz_n": root[:3].tolist(),
                          "applied_to_strip_couple_at_root_xyz_nmm": root[3:].tolist(),
                          "on_internal_heel_force_xyz_n": (-root[:3]).tolist(),
                          "on_internal_heel_couple_at_root_xyz_nmm": (-root[3:]).tolist()})
            flanges.setdefault(element["flange"], np.zeros(6))
            flanges[element["flange"]] += four.wrench_at(root[:3], root[3:], element["root"], self.model.origin)
        root_total = sum(flanges.values(), np.zeros(6))
        result.update(strip_root_actions=roots,
            per_flange_applied_strip_root_wrench_about_heel_n_nmm={key: value.tolist() for key, value in flanges.items()},
            loaded_root_wrench_minus_source_body_wrench_n_nmm=(root_total-
                np.asarray(result["load_projection"]["heel_wrench_n_nmm"])).tolist(),
            source_sha256=source_pins(), immutable_operator_snapshot_sha256=self._operator_at_construction,
            root_recovery_uses_loaded_heel=True, frozen_unloaded_model_response_used_for_gravity=False)
        self._check()
        return copy.deepcopy(result)
