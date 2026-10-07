"""Render a static geometry overview without a browser or network service.

The interactive scene remains the detailed metal-stack view. This figure shows
receiving timber, existing legs/runners, panels and HL35 planning envelopes.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import struct
from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

ROOT = Path(__file__).resolve().parents[1]


def decoded_mesh(mesh: dict, topologies: dict) -> np.ndarray:
    vertex_type = {"int16": "<i2", "int32": "<i4"}[mesh["vertex_component_type"]]
    vertices = np.frombuffer(base64.b64decode(mesh["vertices_base64"]), vertex_type).reshape(-1, 3)
    vertices = vertices * mesh["vertex_quantization_mm"]
    row = topologies[mesh["triangle_topology_sha256"]]
    binary = base64.b64decode(row["triangle_indices_base64"])
    if hashlib.sha256(binary).hexdigest() != mesh["triangle_topology_sha256"]:
        raise ValueError("display topology differs")
    index_type = {"uint16": "<u2", "uint32": "<u4"}[row["triangle_component_type"]]
    return vertices[np.frombuffer(binary, index_type).reshape(-1, 3)]


def model_meshes(scene_path: Path | None = None) -> list[tuple[str, str, np.ndarray]]:
    scene_path = scene_path or ROOT / "site/hl35-candidate-scene.json"
    scene = json.loads(scene_path.read_text())
    parent_path = ROOT / "site" / scene["parent_scene"]["url"]
    if hashlib.sha256(parent_path.read_bytes()).hexdigest() != scene["parent_scene"]["sha256"]:
        raise ValueError("reviewed parent scene differs")
    parent = json.loads(parent_path.read_text())
    meshes = []
    for row in scene["solids"]:
        kind = row["fabrication"]["kind"]
        if kind in {"bolt", "screw", "wire"}:
            continue
        template = scene["mesh_templates"][row["template_id"]] if "template_id" in row else row
        triangles = decoded_mesh(template["mesh"], scene["triangle_topologies"])
        if "transform" in row:
            matrix = np.asarray(row["transform"]).reshape(4, 4).T
            triangles = triangles @ matrix[:3, :3].T + matrix[:3, 3]
        meshes.append((row["name"], kind, triangles))
    for row in parent["solids"]:
        if row["display_class"] == "panel_replacement" and row["name"] not in scene.get("removed_parent_visual_names", []):
            meshes.append((row["name"], "panel", decoded_mesh(row["mesh"], parent["triangle_topologies"])))
    aliases = json.loads((ROOT / "site/mesh-aliases.json").read_text())["aliases"]
    baseline = json.loads((ROOT / "site/hybrid/compact-floor-flush-kerf-right/parts.json").read_text())
    names = {"lumber_leg_left", "lumber_leg_right", "base_floor_left", "base_floor_right", "main_upper_left"}
    dtype = np.dtype([("normal", "<f4", (3,)), ("points", "<f4", (3, 3)), ("attribute", "<u2")])
    for row in baseline["parts"]:
        if row["name"] not in names:
            continue
        source = row["path"]
        binary = (ROOT / "site" / aliases.get(source, source)).read_bytes()
        if hashlib.sha256(binary).hexdigest() != parent["baseline_asset_sha256"][source]:
            raise ValueError(f"retained mesh differs: {source}")
        count = struct.unpack_from("<I", binary, 80)[0]
        if len(binary) != 84 + count * 50:
            raise ValueError("expected source binary STL")
        triangles = np.frombuffer(binary, dtype, count=count, offset=84)["points"].astype(float)
        meshes.append((row["name"], "panel" if row["name"].startswith("main_") else "timber", triangles))
    return meshes


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scene", type=Path, default=ROOT / "site/hl35-candidate-scene.json")
    parser.add_argument("--out", type=Path, default=ROOT / "docs/wood-joints-mvp/hypotheses/hl35-candidate/overview.png")
    args = parser.parse_args()
    args.scene = args.scene.resolve()
    args.out = args.out.resolve()
    meshes = model_meshes(args.scene)
    scene = json.loads(args.scene.read_text())
    fig = plt.figure(figsize=(14, 8), facecolor="#f6f5f1")
    ax = fig.add_subplot(111, projection="3d")
    all_points = np.concatenate([triangles.reshape(-1, 3) for _, _, triangles in meshes])
    low, high = all_points.min(axis=0), all_points.max(axis=0)
    for _, kind, triangles in meshes:
        color, alpha = {"panel": ("#879ba2", .09), "timber": ("#ad733c", .88), "bracket": ("#d94136", 1.)}[kind]
        ax.add_collection3d(Poly3DCollection(triangles, facecolor=color, alpha=alpha,
                                           edgecolor="none", rasterized=True))
    ax.set(xlim=(low[0] - 80, high[0] + 80), ylim=(low[1] - 80, high[1] + 80),
           zlim=(0, high[2] + 80), xlabel="Width X (mm)", ylabel="Depth Y (mm)", zlabel="Height Z (mm)")
    ax.set_box_aspect(high - low)
    ax.view_init(elev=20, azim=-65)
    ax.set_facecolor("#f6f5f1")
    fig.suptitle(f"HL35 replacement candidate · {scene['status']}", fontsize=20, fontweight="bold")
    fig.text(.5, .025, f"{scene['counts']['hl35_angles']} red HL35 planning envelopes; timber and panels/legs/runners.\n"
             "Metal stacks and service hardware omitted from this overview. No structural or fabrication release.",
             ha="center", fontsize=11)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.out, dpi=140, bbox_inches="tight", metadata={"Software": "Mini MoonBoard source-bound CAD overview"})
    plt.close(fig)
    packet = args.out.parent
    manifest_path = packet / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["rendering"] = {
        "command": "MPLCONFIGDIR=/tmp/mini-moonboard-matplotlib .venv/bin/python -m scripts.render_hl35_candidate"
                   + (f" --scene {args.scene.relative_to(ROOT)} --out {args.out.relative_to(ROOT)}"
                      if args.scene.name != "hl35-candidate-scene.json" else ""),
        "versions": {"matplotlib": matplotlib.__version__, "numpy": np.__version__},
        "source_sha256": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                          for p in [Path(__file__), args.scene,
                                    ROOT / "site/owner-wood-joints-wj24-scene.json"]},
        "outputs": {str(args.out.relative_to(ROOT)): hashlib.sha256(args.out.read_bytes()).hexdigest()},
        "scope": "Static overview only; metal stacks and service hardware omitted; browser launch unavailable in this sandbox.",
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Rendered {len(meshes)} source-bound mesh bodies: {args.out} ({args.out.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
