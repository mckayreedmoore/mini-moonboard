"""Mixed source-contract checks and actual frozen-loop synthetic controls."""
from __future__ import annotations

import ast
import copy
import importlib.util
import json
from pathlib import Path
from unittest.mock import patch

import pytest

OWN = Path(__file__).resolve()
spec = importlib.util.spec_from_file_location("z180_mixed_contact_contract_fix", OWN.with_name("descriptor.py"))
fix = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fix)


def mixed_fixture():
    current = {"flange_domains": [], "flange_shared_face_patches": [], "timber_and_panel_shared_face_patches": [], "direct_contacts": []}
    for identity, kind, bedding in (("timber/patch", "timber_face_contact", 1.), ("panel/patch", "panel_contact", 2.)):
        cell = {"id": identity+"/cell-0", "point_xyz_mm": [0., 1., 2.], "area_mm2": 3.}
        p = {"id": identity, "first": "one", "second": "two", "cells": [cell], "normal_from_second_to_first_xyz": [1., 0., 0.],
            "source_first_face": {"signature_sha256": "first"}, "source_second_face": {"signature_sha256": "second"},
            "trimmed_region_signature_sha256": "trimmed"}
        current["timber_and_panel_shared_face_patches"].append(p)
        current["direct_contacts"].append({"id": cell["id"], "kind": kind, "first": "one", "second": "two",
            "bedding_n_mm3": bedding, "direction_xyz": [1., 0., 0.], "point_xyz_mm": cell["point_xyz_mm"],
            "reference_area_mm2": 3., "pressure_convergence_or_physical_contact_qualified": False,
            "source_first_face_signature_sha256": "first", "source_second_face_signature_sha256": "second",
            "source_trimmed_region_signature_sha256": "trimmed", "source_patch_id": identity, "stiffness": bedding*3.})
    # Local native cell IDs repeat across two original half-domain namespaces.
    for sign in (-1, 1):
        identity = "fitting/beam/"+str(sign)
        port = "port/"+str(sign)
        current["flange_domains"].append({"id": identity, "fitting": "fitting", "receiver": "wood",
            "model_port_id": port, "nominal_full_holed_flange_area_mm2": 100.})
        p = {"id": identity+"/native-patch", "first": "fitting", "second": "wood",
            "trimmed_region_signature_sha256": "flange-trimmed", "normal_from_second_to_first_xyz": [0., 1., 1e-10],
            "cells": [{"id": "native-patch/cell-0", "point_xyz_mm": [2., 3., 4.], "area_mm2": 5.}]}
        current["flange_shared_face_patches"].append(p)
        current["direct_contacts"].append({"id": p["id"]+"/cell-0", "kind": "flange_contact", "first": "fitting", "second": "wood",
            "first_port_id": port, "nominal_full_holed_flange_area_mm2": 100., "point_xyz_mm": [2., 3., 4.],
            "reference_area_mm2": 5., "rigid_translation_total_prior_only_no_old_rocking_or_forces": True,
            "direction_xyz": [0., 1., 0.], "source_domain_id": identity,
            "source_trimmed_region_signature_sha256": "flange-trimmed", "stiffness": 50.})
    return current


def test_mixed_rows_select_only_patch_contacts_and_preserve_flange_namespaces():
    current = mixed_fixture()
    data = copy.deepcopy(current)
    selected = fix.verified_patch_contacts(data, current, {})
    assert [r["kind"] for r in selected] == ["timber_face_contact", "panel_contact"]
    assert data == current
    assert selected[0] is data["direct_contacts"][0]


@pytest.mark.parametrize("failure", ["unknown_kind", "mixed_keys", "missing_domain", "foreign_domain", "foreign_patch",
    "wrong_source_cell", "foreign_signature", "duplicate_row", "changed_host_flange"])
def test_unknown_mixed_schema_or_source_join_rejected(failure):
    current = mixed_fixture()
    row = current["direct_contacts"][-1]
    if failure == "unknown_kind":
        row["kind"] = "foreign"
    elif failure == "mixed_keys":
        row["source_patch_id"] = "foreign"
    elif failure == "missing_domain":
        row.pop("source_domain_id")
    elif failure == "foreign_domain":
        row["source_domain_id"] = "foreign"
    elif failure == "foreign_patch":
        current["direct_contacts"][0]["source_patch_id"] = "foreign"
    elif failure == "wrong_source_cell":
        row["point_xyz_mm"] = [99., 99., 99.]
    elif failure == "foreign_signature":
        row["source_trimmed_region_signature_sha256"] = "foreign"
    elif failure == "duplicate_row":
        current["direct_contacts"].append(copy.deepcopy(row))
    else:
        current["flange_domains"][0]["receiver"] = "eoere_cleat_left"
    with pytest.raises(ValueError):
        fix.verified_patch_contacts(copy.deepcopy(current), current, {})


def test_changed_inherited_flange_primitives_rejected():
    current = mixed_fixture()
    for key in ("flange_domains", "flange_shared_face_patches"):
        data = copy.deepcopy(current)
        data[key][0]["foreign"] = True
        with pytest.raises(ValueError, match="flange source primitives changed"):
            fix.verified_patch_contacts(data, current, {})


def run_actual_frozen_update_loop(data, current, changed):
    v3 = fix.verified_v3()
    v2 = v3.verified_v2()
    raw = v2.FROZEN.read_bytes()
    assert v2.frozen_module().sha(v2.FROZEN) == v2.FROZEN_SHA256
    tree = fix.contact_contract_tree(ast.parse(raw))
    loop = next(node for node in ast.walk(tree) if isinstance(node, ast.For) and isinstance(node.iter, ast.Call)
                and isinstance(node.iter.func, ast.Name) and node.iter.func.id == "verified_patch_contacts")
    wrapper = ast.parse("def update(data, current, patch_index):\n    pass\n")
    wrapper.body[0].body = [copy.deepcopy(loop), ast.Return(value=ast.Name(id="data", ctx=ast.Load()))]
    namespace = {"verified_patch_contacts": fix.verified_patch_contacts}
    exec(compile(ast.fix_missing_locations(wrapper), "owned-frozen-loop-fixture", "exec"), namespace)  # noqa: S102 -- authenticated loop, owned data
    return namespace["update"](data, current, changed)


def test_actual_frozen_update_loop_changes_only_joined_patch_rows():
    current = mixed_fixture()
    data = copy.deepcopy(current)
    changed = copy.deepcopy(current["timber_and_panel_shared_face_patches"][0])
    changed["cells"][0].update(point_xyz_mm=[0., 2., 3.], area_mm2=4.)
    changed["analytic_source_region_sha256"] = "analytic"
    changed["source_region_identity"] = {"own": "source"}
    result = run_actual_frozen_update_loop(data, current, {changed["id"]: changed})
    own = result["direct_contacts"][0]
    assert own["point_xyz_mm"] == [0., 2., 3.] and own["reference_area_mm2"] == own["stiffness"] == 4.
    assert "source_first_face_signature_sha256" not in own
    assert result["direct_contacts"][1:] == current["direct_contacts"][1:]
    result["geometry_delta_proof"] = {"rebuilt_patches": [{"id": changed["id"]}], "changed_host_inherited_regions": []}
    proof = fix.verify_output_reuse(current, result)
    assert proof["flange_contact_rows_preserved"] == 2 and proof["all_unchanged_contact_rows_preserved"] == 3
    result["direct_contacts"][-1]["stiffness"] = 99.
    with pytest.raises(ValueError, match="unaffected contact row changed"):
        fix.verify_output_reuse(current, result)


@pytest.mark.parametrize("raw", ["pass", 'for contact in data["direct_contacts"]: pass\nfor contact in data["direct_contacts"]: pass'])
def test_loop_seam_requires_exactly_one_matching_original_loop(raw):
    with pytest.raises(ValueError, match="exact single frozen direct-contact update loop required"):
        fix.contact_contract_tree(ast.parse(raw))


def test_v4_correction_provenance_joins_exact_input_bytes():
    v3 = fix.corrected_v3()
    inp = json.loads((OWN.parent.parent / "review-fix-v3/inputs.json").read_bytes())
    ref = v3.source_ref(fix.OWN)
    inp["sources"]["mixed_contact_contract_adapter"] = ref
    assert v3.source_correction_record(inp)["mixed_contact_contract_adapter"] == ref
    inp["sources"]["mixed_contact_contract_adapter"]["sha256"] = "foreign"
    with pytest.raises(ValueError, match="exact mixed-contact correction provenance required"):
        v3.source_correction_record(inp)


def test_actual_current_late_source_schemas_audited_without_candidate_build():
    v3 = fix.verified_v3()
    frozen = v3.verified_v2().frozen_module()
    inp = json.loads((OWN.parent.parent / "inputs.json").read_bytes())
    path = frozen.exact_ref(inp["sources"]["current"])
    current = json.loads(path.read_bytes())
    result = fix.source_contract_audit(current)
    assert result["timber_panel_contact_rows"] == 1254 and result["flange_contact_rows"] == 352
    assert result["flange_domains"] == result["flange_patches"] == 88
    assert result["floor_rows"] == 8 and result["floor_reference_points"] == 32
    assert result["candidate_descriptor_build_called"] is False
    assert frozen.sha(path) == inp["sources"]["current"]["sha256"]


@pytest.mark.parametrize("kind", ["file", "dangling_link"])
def test_actual_v4_chain_preserves_fresh_output_guard(tmp_path, kind):
    v3 = fix.corrected_v3()
    frozen = v3.corrected_frozen_module(v3.verified_v2())
    frozen.OWN = tmp_path / "packet/descriptor.py"
    out = frozen.OWN.parent / "runs-v1/existing.json"
    out.parent.mkdir(parents=True)
    if kind == "file":
        out.write_text("preserved")
    else:
        out.symlink_to(out.with_name("missing.json"))
    with patch.object(fix, "corrected_v3", return_value=v3), patch.object(v3, "corrected_frozen_module", return_value=frozen), \
            patch.object(frozen, "load_inputs", side_effect=AssertionError("source intake reached")), pytest.raises(FileExistsError):
        fix.write_descriptor(tmp_path / "inputs.json", "wrong", out)
    assert out.read_text() == "preserved" if kind == "file" else out.is_symlink()
