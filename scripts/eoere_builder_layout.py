"""Present authenticated issued shop coordinates without rebuilding geometry."""

import argparse
import csv
import hashlib
import io
import json
import math
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = Path("docs/bolted-frame-development/development-revisions.json")
OUTPUT = INDEX.parent / "builder-layout.md"
REVISION = "eoere-raised-kicker-screws-v1"
HARDWARE = "eoere-selected-purchase-hardware-v1"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_bound(root, binding):
    payload = (root / binding["path"]).read_bytes()
    require(hashlib.sha256(payload).hexdigest() == binding["sha256"],
            f"Source hash differs: {binding['path']}")
    return payload


def load_sources(root=ROOT):
    index = json.loads((root / INDEX).read_bytes())
    require(index["geometry"]["revision"] == index["shop"]["revision"] == REVISION
            and index["hardware_model"]["revision"] == HARDWARE,
            "Builder guide revision requires review")
    require(index["hardware_model"]["shop_override"] in index["shop"]["overrides"],
            "Hardware overlay does not bind the shop selection")
    result = json.loads(read_bound(root, index["shop"]["result"]))
    folder = Path(index["shop"]["result"]["path"]).parent

    def issued(name):
        return read_bound(root, {"path": str(folder / name), **result["files"][name]})

    def rows(payload):
        return list(csv.DictReader(io.StringIO(payload.decode())))

    return {
        "profiles": json.loads(issued("current_profiles.json")),
        "members": rows(issued("members.csv")),
        "selected": rows(issued("hardware-selection.csv")),
        "drilling": rows(issued("drilling-requirements.csv")),
        "holes": rows(read_bound(root, result["reused_files"]["receiver-holes.csv"])),
        "shop_result": index["shop"]["result"],
    }


def validate(data):
    profiles, holes = data["profiles"], data["holes"]
    require(len(profiles) == len(data["members"]) == 28
            and Counter(p["kind"] for p in profiles.values()) == {"timber": 22, "panel": 6},
            "Member inventory differs")
    require({r["member"] for r in data["members"]} == set(profiles), "Member identities differ")
    selected = {r["axis_id"]: r for r in data["selected"]}
    drilling = {r["axis_id"]: r for r in data["drilling"]}
    require(len(data["selected"]) == len(selected) == len(data["drilling"]) == len(drilling) == 100
            and set(selected) == set(drilling) == {r["axis_id"] for r in holes},
            "Bolt identities differ")
    require(len(holes) == len({(r["axis_id"], r["receiver"]) for r in holes}) == 120,
            "Receiver occurrences differ or repeat")
    for table in (data["members"], data["selected"], data["drilling"], holes):
        require(all(not value for row in table for key, value in row.items()
                    if key.startswith("Actual") or key == "Disposition"),
                "Issued observation cells must remain blank")
    lengths = Counter()
    for row in holes:
        axis, member = row["axis_id"], row["receiver"]
        profile = profiles[member]
        require(profile["kind"] == "timber", "Receiver must be timber")
        require(float(row["nominal_shaft_diameter_mm"]) == float(selected[axis]["selected_diameter_mm"]),
                f"Selected diameter differs: {axis}")
        for end in ("entry", "exit"):
            local = [float(row[f"{end}_in_receiver_{a}_mm"]) for a in "luv"]
            world = [profile["datum_xyz_mm"][j]
                     + sum(local[i] * profile["basis_grain_u_v_xyz"][i][j] for i in range(3))
                     for j in range(3)]
            expected = [float(row[f"axis_point_{a}_mm"])
                        + float(row[f"{end}_from_axis_point_mm"])
                        * float(row[f"axis_direction_{a}_unitless"]) for a in "xyz"]
            require(all(math.isfinite(v) for v in world + expected)
                    and math.dist(world, expected) < 1e-7,
                    f"Receiver coordinate differs from world axis: {axis}/{member}/{end}")
        path = float(row["exit_from_axis_point_mm"]) - float(row["entry_from_axis_point_mm"])
        require(path > 0, f"Reversed or empty receiver interval: {axis}/{member}")
        lengths[axis] += path
    for axis, length in lengths.items():
        receivers = {r["receiver"] for r in holes if r["axis_id"] == axis}
        require(receivers == set(selected[axis]["receiver_member_ids"].split(";")),
                f"Selected receiver identities differ: {axis}")
        require(abs(length - float(drilling[axis]["nominal_wood_path_mm"])) < 1e-7,
                f"Drilling path differs: {axis}")


def number(value):
    rounded = f"{float(value):.6f}".rstrip("0").rstrip(".")
    return "0" if rounded == "-0" else rounded


def vector(values):
    return "(" + ", ".join(number(v) for v in values) + ")"


def render(data):
    validate(data)
    selected = {r["axis_id"]: r for r in data["selected"]}
    lines = [
        "# Current timber end and receiver coordinates", "",
        f"Applies to **`{REVISION}`** with **`{HARDWARE}`**, extra grid off.",
        "Use with the [builder plan](builder-plan.md); conditional nominal planning only.", "",
        "Generated from the checked shop-result binding and its unchanged issued tables.",
        f"Shop-result SHA-256: `{data['shop_result']['sha256']}`.",
        "The producer authenticates profiles, members, selected hardware, drilling paths",
        "and receiver rows, then checks both local endpoints against each world shaft axis.", "",
        "## Coordinate convention", "",
        "All dimensions are millimetres. Coordinates preserve the source L/U/V frame.",
        "L follows grain. U and V are member-specific section axes: most timbers use",
        "U across thickness and V across depth; **base_header uses U across its 139.7-mm",
        "depth and V across its 38.1-mm thickness**. Its U=0 reference is the narrow edge,",
        "and its bolt receivers run along V. Negative V values elsewhere are intentional.",
        "The per-member world datum and positive unit vectors identify",
        "each face and orientation; left/right members must retain their own labels.",
        "U=0 is the labeled reference face, not necessarily the installed bolt-entry face.",
        "An L=0 profile corner is not a square-end fence across the whole member.", "",
        "Raw U=0 vertex marks below retain source indices; their listing is not a polygon",
        "or saw path. End-plane marks identify vertices on each raw cut face. Use the",
        "issued projections and finished recess/channel details beside these numbers.",
        "Raw blank lengths can exceed the final L extent after angled cuts.", "",
        "Receiver entry/exit means increasing saved shaft-axis parameter, not a prescribed",
        "drill approach. Recessed entries remain on their recorded finished face. Join paired",
        "receivers in one supported setup; do not independently drill opposite marks.",
        "Bit choices are 13/32 in for 3/8-in bolts and 17/32 in for 1/2-in bolts.",
        "The selected underhead lengths supersede old modeled-length columns. Spacers",
        "go between nut washer and nut. No Actual/Disposition values are supplied.", "",
        "Six decimal places preserve nominal source detail; they are not machining tolerances.",
        "Panel and screw datums remain in the current shop tables linked by the builder plan.", "",
    ]
    for member, profile in data["profiles"].items():
        if profile["kind"] != "timber":
            continue
        vertices = profile["vertices_luv_mm"]
        lines += [f"## {member}", "",
                  f"Raw blank L × depth × thickness: **{' × '.join(number(v) for v in profile['blank_mm'])}**.",
                  f"World datum XYZ: `{vector(profile['datum_xyz_mm'])}`.",
                  "Positive L/U/V unit vectors: " + "; ".join(
                      f"`{vector(v)}`" for v in profile["basis_grain_u_v_xyz"]) + ".", "",
                  "Raw U=0 marks (vertex index: L, V): " + "; ".join(
                      f"{i}: `{vector((v[0], v[2]))}`" for i, v in enumerate(vertices)
                      if abs(v[1]) < 1e-7) + "."]
        for i, plane in enumerate(profile["end_planes"]):
            indices = [int(v) for v in str(plane["plane_source_vertex_indices"]).split(";")]
            marks = [f"{j}: `{vector((vertices[j][0], vertices[j][2]))}`"
                     for j in indices if abs(vertices[j][1]) < 1e-7]
            lines.append(f"Raw end plane {i + 1}, U=0 marks: " + "; ".join(marks) + ".")
        lines += ["", "| Axis | Entry (L, U, V) | Exit (L, U, V) | Bit (in) | Selected bolt Ø × underhead (mm) | Nut-side spacer (mm) |",
                  "| --- | --- | --- | --- | --- | --- |"]
        for row in data["holes"]:
            if row["receiver"] != member:
                continue
            hardware = selected[row["axis_id"]]
            ends = [vector(float(row[f"{end}_in_receiver_{a}_mm"]) for a in "luv")
                    for end in ("entry", "exit")]
            diameter = float(hardware["selected_diameter_mm"])
            bit = {9.525: "13/32", 12.7: "17/32"}[diameter]
            lines.append(f"| `{row['axis_id']}` | `{ends[0]}` | `{ends[1]}` | {bit} | "
                         f"{number(diameter)} × {number(hardware['selected_underhead_length_mm'])} | "
                         f"{number(hardware['nut_side_spacer_mm'])} |")
        lines.append("")
    lines += ["## Reproduction", "", "```sh",
              "uv run python -m scripts.eoere_builder_layout --check",
              "uv run pytest -q tests/test_eoere_builder_layout.py", "```", "",
              "Use `--write` after reviewing changed source revisions. This presentation",
              "adds no cuts, holes, hardware, capacity, observed fit or release.", ""]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--write", action="store_true")
    args = parser.parse_args()
    text = render(load_sources())
    if args.check:
        require((ROOT / OUTPUT).read_text() == text, "Builder layout is stale; review before --write")
    else:
        (ROOT / OUTPUT).write_text(text)
    print(f"{OUTPUT}: 22 timbers / 100 bolt axes / 120 receiver rows verified")


if __name__ == "__main__":
    main()
