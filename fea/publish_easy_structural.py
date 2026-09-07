"""Publish compact, replayable A/B screening evidence without changing CAD."""
import gzip
import json
import math
import shutil
import subprocess
from pathlib import Path

from fea.hybrid_results import deck_geometry
from fea.prepare_easy_structural import KEYS, ROOT, digest, save
from fea.solve_easy_frame import audit, make_deck, target_mapping
from mini_moonboard.stability import evaluate_load, load_cases

DESTINATION = Path("fea/results/square-cut")


def checked_run(directory, size):
    prefix = directory/f"box_audited_{size}_7000"
    report = json.loads(prefix.with_suffix(".json").read_text())
    for name, expected in report["evidence_sha256"].items():
        if digest(directory/name) != expected:
            raise ValueError("Raw solver evidence changed")
    text = prefix.with_suffix(".inp").read_text()
    data = prefix.with_suffix(".dat").read_text()
    context = json.loads(prefix.with_suffix(".context.json").read_text())
    info = report["frozen_geometry"]
    prepared = directory/"box_frame_bulk.json"
    if (info != json.loads(prepared.read_text()) or digest(prepared) != context["input_sha256"]
            or digest(prefix.with_suffix(".inp")) != context["deck_sha256"]
            or report["candidate"] != directory.name or context["candidate"] != directory.name
            or report["mesh_size_mm"] != size or context["size_mm"] != size
            or report["modulus_mpa"] != 7000 or context["modulus_mpa"] != 7000
            or report["source_sha256"] != context["source_sha256"]
            or any(context["source_sha256"].get(p) != h for p, h in info["geometry_source_sha256"].items())):
        raise ValueError("Prepared input, launch context and result identity differ")
    audited = audit(text, data, info)
    if any(report[k] != v for k, v in audited.items()):
        raise ValueError("Replayed result differs")
    cases = [(c["name"], tuple(v/1200 for v in c["force_n"])) for c in info["audited_cases"]]
    nodes, feet, top = deck_geometry(text, cases)
    mapping = target_mapping(nodes, info["audited_load_targets_mm"], size)
    if (sorted(r["node"] for r in mapping) != top or top != report["load_nodes"]
            or top != context["load_nodes"]):
        raise ValueError("Published target mapping differs from actual loaded nodes")
    # Reconstruct the launched physical deck; the first comment was clarified
    # after A60, but is not part of the stiffness/load/boundary configuration.
    mesh_text = text.split("\n", 1)[1].split("*NSET,NSET=FEET")[0][:-1]
    expected = make_deck(mesh_text, feet, top, info["audited_cases"], 7000)
    if expected.split("\n", 1)[1] != text.split("\n", 1)[1]:
        raise ValueError("Material, section or physical deck differs from declared screen")
    u = audited["max_top_displacement_mm"]
    if not math.isclose(u["Downward 2.4 kN"], 2*u["Downward 1.2 kN"], rel_tol=1e-5):
        raise ValueError("Linear load doubling witness failed")
    if not math.isclose(u["Outward/downward normal"], u["Inward/upward normal"], rel_tol=1e-5):
        raise ValueError("Reversed linear load witness failed")
    return report, mapping


def main():
    checked = {(key, size): checked_run(ROOT/key, size) for key in KEYS for size in (60, 40)}
    DESTINATION.mkdir(parents=True, exist_ok=False)
    sources = ("fea/publish_easy_structural.py", "fea/solve_easy_frame.py", "fea/prepare_easy_structural.py",
               "fea/box_results.py", "fea/floor_contact.py", "fea/floor_contact_results.py", "fea/hybrid_results.py",
               "mini_moonboard/stability.py")
    report = {"status": "SCREENING ONLY; NEITHER DESIGN QUALIFIED FOR CONSTRUCTION",
              "publication_observed_image_id": subprocess.check_output([
                  "docker", "image", "inspect", "mini-moonboard-fea:box-v1",
                  "--format", "{{.Id}}"], text=True).strip(),
              "audit_source_sha256": {p: digest(p) for p in sources}, "candidates": {}}
    for key in KEYS:
        source, output = ROOT/key, DESTINATION/key
        output.mkdir()
        for name in ("stability.json", "box_frame_bulk.json"):
            shutil.copyfile(source/name, output/name)
        result = {"meshes": {}}
        state = json.loads((source/"stability.json").read_text())["state"]
        point = json.loads((source/"box_frame_bulk.json").read_text())["audited_load_targets_mm"][0]
        result["legacy_sagittal_normals"] = []
        for load in load_cases()[-2:]:
            screen = evaluate_load(mass_kg=state["mass_kg"], centre_y_mm=state["centre_xy_mm"][1],
                kicker_toe_y_mm=min(p[1] for p in state["support_polygon_mm"]),
                leg_toe_y_mm=max(p[1] for p in state["support_polygon_mm"]),
                load_y_mm=point[1], load_z_mm=point[2], load=load)
            result["legacy_sagittal_normals"].append({"case": load.name, "basis": load.basis,
                "load_yz_mm": point[1:], "force_yz_n": [load.force_y_n, load.force_z_n],
                "status": screen.status, "kicker_reaction_n": screen.kicker_reaction_n,
                "leg_reaction_n": screen.leg_reaction_n})
        for size in (60, 40):
            record, mapping = checked[key, size]
            prefix = f"box_audited_{size}_7000"
            for extension in ("inp", "dat", "log", "json", "context.json"):
                name = prefix+"."+extension
                (output/(name+".gz")).write_bytes(gzip.compress((source/name).read_bytes(), mtime=0))
            result["meshes"][str(size)] = {"nodes": record["nodes"], "min_jacobian": record["min_jacobian"],
                "load_target_mapping": mapping, "displacement_mm": record["max_top_displacement_mm"]}
        coarse, fine = (result["meshes"][str(s)]["displacement_mm"] for s in (60, 40))
        result["refinement_change_percent"] = {k: 100*(fine[k]/coarse[k]-1) for k in fine}
        result["artifact_sha256"] = {p.name: digest(p) for p in output.iterdir()}
        report["candidates"][key] = result
    save(DESTINATION/"report.json", report)
    print(DESTINATION/"report.json")


if __name__ == "__main__":
    main()
