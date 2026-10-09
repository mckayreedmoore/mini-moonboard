"""Validate mixed contact schemas and preserve unchanged flange primitives.

One exact authenticated AST seam filters the frozen contact-update loop to
timber/panel rows after checking every original row and its source join. Flange
rows, domains and patches remain identical to the authenticated parent export.
All frozen geometry arithmetic, release and source corrections are reused.
"""
from __future__ import annotations

import argparse
import ast
import copy
import hashlib
import json
from pathlib import Path
from types import ModuleType

OWN = Path(__file__).resolve()
V3 = OWN.parent.parent / "review-fix-v3/descriptor.py"
V3_SHA256 = "b9540ab1612033194c8ae7ac230ab21082813cd63cf824cc77b58cba9bfa6b1b"
HOSTS = {"base_post_outer_left", "base_post_outer_right", "eoere_cleat_left", "eoere_cleat_right"}
PATCH_KEYS = {"bedding_n_mm3", "direction_xyz", "first", "id", "kind", "point_xyz_mm",
    "pressure_convergence_or_physical_contact_qualified", "reference_area_mm2", "second",
    "source_first_face_signature_sha256", "source_patch_id", "source_second_face_signature_sha256",
    "source_trimmed_region_signature_sha256", "stiffness"}
FLANGE_KEYS = {"direction_xyz", "first", "first_port_id", "id", "kind", "nominal_full_holed_flange_area_mm2",
    "point_xyz_mm", "reference_area_mm2", "rigid_translation_total_prior_only_no_old_rocking_or_forces", "second",
    "source_domain_id", "source_trimmed_region_signature_sha256", "stiffness"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def indexed(rows):
    result = {row["id"]: row for row in rows}
    require(len(result) == len(rows), "duplicate contact/source identity")
    return result


def verified_v3():
    raw = V3.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == V3_SHA256, "frozen release adapter bytes differ")
    module = ModuleType("eoere_z180_frozen_release_adapter")
    module.__file__ = str(V3)
    exec(compile(raw, str(V3), "exec"), module.__dict__)  # noqa: S102 -- exact bytes checked immediately above
    return module


def verified_patch_contacts(data, current, patch_index):
    require(data["flange_domains"] == current["flange_domains"]
            and data["flange_shared_face_patches"] == current["flange_shared_face_patches"], "flange source primitives changed")
    domains = indexed(current["flange_domains"])
    flange_patches = indexed(current["flange_shared_face_patches"])
    require(all(not ({p["first"], p["second"]} & HOSTS) for p in flange_patches.values())
            and all(not ({p["fitting"], p["receiver"]} & HOSTS) for p in domains.values()),
            "changed-host flange source requires own proof")
    parent_rows = indexed(current["direct_contacts"])
    require(indexed(data["direct_contacts"]) == parent_rows, "contact primitives changed before verified source join")
    patches = indexed(current["timber_and_panel_shared_face_patches"])
    require(set(patch_index) <= set(patches), "foreign changed patch identity")
    patch_cells = {cell["id"]: (patch, cell) for patch in patches.values() for cell in patch["cells"]}
    flange_cells = {}
    for patch in flange_patches.values():
        own_domains = [name for name in domains if patch["id"].startswith(name + "/")]
        require(len(own_domains) == 1, "unique original flange domain/patch namespace required")
        for index, cell in enumerate(patch["cells"]):
            # Original extract.flange_bank prefixes the patch and enumerates
            # its cells; local native cell IDs can repeat across half domains.
            identity = patch["id"] + "/cell-" + str(index)
            require(identity not in flange_cells, "duplicate flange domain/cell identity")
            flange_cells[identity] = patch, cell
    require(len(patch_cells) == sum(len(p["cells"]) for p in patches.values())
            and len(flange_cells) == sum(len(p["cells"]) for p in flange_patches.values())
            and not (set(patch_cells) & set(flange_cells))
            and set(parent_rows) == set(patch_cells) | set(flange_cells), "contact/source-cell census differs")
    selected = []
    for row in data["direct_contacts"]:
        if row["kind"] == "flange_contact":
            require(set(row) == FLANGE_KEYS and row["source_domain_id"] in domains
                    and row["id"] in flange_cells, "unknown flange contact schema or source join")
            domain = domains[row["source_domain_id"]]
            patch, cell = flange_cells[row["id"]]
            require(patch["id"].startswith(domain["id"] + "/")
                    and (row["first"], row["second"], row["first_port_id"]) == (domain["fitting"], domain["receiver"], domain["model_port_id"])
                    and row["point_xyz_mm"] == cell["point_xyz_mm"] and row["reference_area_mm2"] == cell["area_mm2"]
                    and row["source_trimmed_region_signature_sha256"] == patch["trimmed_region_signature_sha256"]
                    and row["nominal_full_holed_flange_area_mm2"] == domain["nominal_full_holed_flange_area_mm2"],
                    "flange contact does not join its original own domain/cell")
        else:
            require(row["kind"] in {"timber_face_contact", "panel_contact"} and set(row) == PATCH_KEYS
                    and row["source_patch_id"] in patches and row["id"] in patch_cells,
                    "unknown timber/panel contact schema or source join")
            patch, cell = patch_cells[row["id"]]
            require(row["source_patch_id"] == patch["id"] and (row["first"], row["second"]) == (patch["first"], patch["second"])
                    and row["point_xyz_mm"] == cell["point_xyz_mm"] and row["reference_area_mm2"] == cell["area_mm2"]
                    and row["direction_xyz"] == patch["normal_from_second_to_first_xyz"]
                    and row["source_first_face_signature_sha256"] == patch["source_first_face"]["signature_sha256"]
                    and row["source_second_face_signature_sha256"] == patch["source_second_face"]["signature_sha256"]
                    and row["source_trimmed_region_signature_sha256"] == patch["trimmed_region_signature_sha256"],
                    "timber/panel contact does not join its original own patch/cell")
            selected.append(row)
    return selected


def verify_output_reuse(current, result):
    before, after = indexed(current["direct_contacts"]), indexed(result["direct_contacts"])
    require(set(before) == set(after), "contact identity census changed")
    proof = result["geometry_delta_proof"]
    changed = {p["id"] for key in ("rebuilt_patches", "changed_host_inherited_regions") for p in proof[key]}
    unchanged = [identity for identity, row in before.items()
                 if row["kind"] == "flange_contact" or row["source_patch_id"] not in changed]
    require(all(before[identity] == after[identity] for identity in unchanged), "unaffected contact row changed")
    require(current["flange_domains"] == result["flange_domains"]
            and current["flange_shared_face_patches"] == result["flange_shared_face_patches"], "flange source primitives changed")
    return {"flange_contact_rows_preserved": sum(r["kind"] == "flange_contact" for r in before.values()),
        "all_unchanged_contact_rows_preserved": len(unchanged), "changed_patch_ids": sorted(changed),
        "flange_domains_and_patches_preserved": True, "native_geometry_or_operator_revalidation_claimed": False}


def contact_contract_tree(tree):
    target = ast.parse('data["direct_contacts"]', mode="eval").body
    matches = [node for node in ast.walk(tree) if isinstance(node, ast.For) and isinstance(node.target, ast.Name)
               and node.target.id == "contact" and ast.dump(node.iter) == ast.dump(target)]
    require(len(matches) == 1, "exact single frozen direct-contact update loop required")
    matches[0].iter = ast.copy_location(ast.Call(func=ast.Name(id="verified_patch_contacts", ctx=ast.Load()),
        args=[ast.Name(id=name, ctx=ast.Load()) for name in ("data", "current", "patch_index")], keywords=[]), matches[0].iter)
    return ast.fix_missing_locations(tree)


def corrected_v3():
    v3 = verified_v3()
    original_tree, original_module, original_record = v3.release_contract_tree, v3.corrected_frozen_module, v3.source_correction_record
    v3.release_contract_tree = lambda raw, filename: contact_contract_tree(original_tree(raw, filename))
    def record(inp):
        value = original_record(inp)
        ref = v3.source_ref(OWN)
        require(inp["sources"].get("mixed_contact_contract_adapter") == ref, "exact mixed-contact correction provenance required")
        value["mixed_contact_contract_adapter"] = ref
        return value
    v3.source_correction_record = record
    def module(v2):
        frozen = original_module(v2)
        frozen.verified_patch_contacts = verified_patch_contacts
        original_build = frozen.build_descriptor
        def build(bundle):
            result = original_build(bundle)
            result["mixed_contact_source_contract"] = verify_output_reuse(bundle["records"]["current"], result)
            return result
        frozen.build_descriptor = build
        return frozen
    v3.corrected_frozen_module = module
    return v3


def source_contract_audit(current):
    """Metadata-only audit of the frozen late joins; no candidate arithmetic."""
    view = copy.deepcopy(current)
    selected = verified_patch_contacts(view, current, {})
    floor_keys = {"centroid_XY_enabled", "host", "normal_reference_points_xyz_mm", "observed_normal_reference_points_xyz_mm",
        "own_floor_face_confirmation_required", "own_floor_face_confirmed_from_current_cached_solid"}
    require(len(current["floor_observations"]) == 8
            and all(set(row) == floor_keys and len(row["observed_normal_reference_points_xyz_mm"]) == 4
                    and all(len(point) == 3 for point in row["observed_normal_reference_points_xyz_mm"])
                    for row in current["floor_observations"]), "unknown late floor source schema")
    return {"timber_panel_contact_rows": len(selected), "flange_contact_rows": len(current["direct_contacts"])-len(selected),
        "flange_domains": len(current["flange_domains"]), "flange_patches": len(current["flange_shared_face_patches"]),
        "floor_rows": 8, "floor_reference_points": 32, "candidate_descriptor_build_called": False,
        "flange_contact_ID_join": "original flange_bank prefixed patch ID plus enumerated cell index",
        "flange_direction_sources_remain_distinct": "original fitting_face contact normal; saved native patch normal"}


def write_descriptor(inputs_path, inputs_sha256, out):
    return corrected_v3().write_descriptor(inputs_path, inputs_sha256, out)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--inputs-sha256", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    print(json.dumps(write_descriptor(args.inputs, args.inputs_sha256, args.out), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
