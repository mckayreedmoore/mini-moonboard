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
REVISION = "eoere-centred-enclosed-passages-v1"
HARDWARE = "eoere-4x6-front-posts-v1"


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
    if index['schema'] == 'bolted_frame_development_revisions/v5':
        require(index['geometry']['revision'] == index['shop']['revision'] ==
                index['hardware_model']['revision'] == 'eoere-single-leg-bolts-header-angles-v3',
                'Combined leg/header revision requires review')
        result_ref = index['shop']['result']
        result = json.loads(read_bound(root, result_ref))
        require(result_ref == index['geometry']['receipt'] and result['counts']['bolt_stacks'] == 96,
                'Combined shop and geometry binding differs')

        def combined(name):
            return read_bound(root, result['files'][name])

        def combined_rows(name):
            return list(csv.DictReader(io.StringIO(combined(name).decode())))

        return {'profiles': json.loads(combined('current_profiles.json')),
                'members': combined_rows('members.csv'), 'selected': combined_rows('hardware-selection.csv'),
                'drilling': combined_rows('drilling-requirements.csv'), 'holes': combined_rows('receiver-holes.csv'),
                'shop_result': result_ref, 'revision': result['revision'], 'hardware_revision': result['revision'],
                'expected_bolt_count': 96, 'expected_receiver_count': 112,
                'expected_spacer_count': result['counts']['spacer_pieces']}
    passage_result = index['shop']['result'] if index['schema'] == 'bolted_frame_development_revisions/v4' else None
    passages = json.loads(read_bound(root, passage_result)) if passage_result else None
    if passages:
        require(index['geometry']['revision'] == REVISION, 'Enclosed passage revision requires review')
        index = index['preceding_revision']
    channel_result = index['shop']['result'] if index['schema'] == 'bolted_frame_development_revisions/v3' else None
    channels = json.loads(read_bound(root, channel_result)) if channel_result else None
    if channels:
        require(index['geometry']['revision'] == 'eoere-narrow-channel-openings-v1', 'Channel revision requires review')
        index = index['preceding_revision']
    require(index["schema"] == "bolted_frame_development_revisions/v2"
            and index["geometry"]["revision"] == index["shop"]["revision"] == HARDWARE
            and index["hardware_model"]["revision"] == HARDWARE,
            "Builder guide revision requires review")
    current_result = index["shop"]["result"]
    revision = json.loads(read_bound(root, current_result))
    overrides = {Path(r["path"]).name: r for r in index["shop"]["overrides"]}
    index = index["preceding_revision"]
    require(index["hardware_model"]["shop_override"] in index["shop"]["overrides"],
            "Hardware overlay does not bind the shop selection")
    result = json.loads(read_bound(root, index["shop"]["result"]))
    folder = Path(index["shop"]["result"]["path"]).parent

    def issued(name):
        return read_bound(root, {"path": str(folder / name), **result["files"][name]})

    def rows(payload):
        return list(csv.DictReader(io.StringIO(payload.decode())))

    data = {
        "profiles": json.loads(issued("current_profiles.json")),
        "members": rows(issued("members.csv")),
        "selected": rows(issued("hardware-selection.csv")),
        "drilling": rows(issued("drilling-requirements.csv")),
        "holes": rows(read_bound(root, result["reused_files"]["receiver-holes.csv"])),
        "shop_result": current_result,
    }
    require(revision["parent_shop"] == index["shop"]["result"], "Post revision has a different shop parent")
    data["profiles"].update(revision["profile_overrides"])
    members = {r["member"]: r for r in revision["member_overrides"]}
    data["members"] = [members.get(r["member"], r) for r in data["members"]]
    selected = {r["axis_id"]: r for r in rows(read_bound(root, overrides["hardware-selection.csv"]))}
    require(len(selected) == 8, "Eight revised bolt selections required")
    data["selected"] = [{**r, **selected.get(r["axis_id"], {})} for r in data["selected"]]
    holes = {(r["axis_id"], r["receiver"]): r for r in rows(read_bound(root, overrides["receiver-holes.csv"]))}
    require(len(holes) == 16, "Sixteen revised receiver rows required")
    data["holes"] = [holes.get((r["axis_id"], r["receiver"]), r) for r in data["holes"]]
    data["drilling"] = [{**r, **({"nominal_wood_path_mm": "127.0"} if r["axis_id"] in selected else {})}
                        for r in data["drilling"]]
    if channels:
        require(channels['parent_geometry'] == current_result, 'Channel parent differs')
        data['profiles'].update(channels['profile_overrides'])
        data['shop_result'] = channel_result
    if passages:
        require(passages['parent_geometry']['receipt'] == channel_result, 'Passage parent differs')
        data['profiles'].update(passages['profile_overrides'])
        data['shop_result'] = passage_result
    return data


def validate(data):
    profiles, holes = data["profiles"], data["holes"]
    require(len(profiles) == len(data["members"]) == 28
            and Counter(p["kind"] for p in profiles.values()) == {"timber": 22, "panel": 6},
            "Member inventory differs")
    require({r["member"] for r in data["members"]} == set(profiles), "Member identities differ")
    selected = {r["axis_id"]: r for r in data["selected"]}
    drilling = {r["axis_id"]: r for r in data["drilling"]}
    require(len(data["selected"]) == len(selected) == len(data["drilling"]) == len(drilling) == data.get('expected_bolt_count', 100)
            and set(selected) == set(drilling) == {r["axis_id"] for r in holes},
            "Bolt identities differ")
    require(len(holes) == len({(r["axis_id"], r["receiver"]) for r in holes}) == data.get('expected_receiver_count', 120),
            "Receiver occurrences differ or repeat")
    if 'expected_spacer_count' in data:
        pieces = 0
        for row in data['selected']:
            count = int(row['spacer_piece_count'])
            length = float(row['spacer_piece_length_mm'])
            require(count >= 0 and abs(count*length-float(row['nut_side_spacer_mm'])) < 1e-8
                    and length == (12.7 if count else 0.)
                    and row['selected_spacer_SKU'] == ('13731' if count else ''),
                    'Selected factory spacer inventory differs: '+row['axis_id'])
            pieces += count
        require(pieces == data['expected_spacer_count'], 'Selected factory spacer total differs')
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
        f"Applies to **`{data.get('revision', REVISION)}`** with **`{data.get('hardware_revision', HARDWARE)}`**, extra grid off.",
        "Use with the [builder plan](builder-plan.md); conditional nominal planning only.", "",
        ("Generated from the combined checked profiles and fresh 96-axis / 112-receiver tables."
         if data.get('expected_bolt_count') == 96 else
         "Generated from the checked post-revision binding and the preserved shop tables"),
        ("Twenty sawn members and two plywood cleats retain their individual nominal datums."
         if data.get('expected_bolt_count') == 96 else
         "with two stock, eight stack, sixteen receiver-row and eight enclosed-passage profile overrides."),
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
        "issued projections and finished recess/passage details beside these numbers.",
        "Raw blank lengths can exceed the final L extent after angled cuts.", "",
        "Receiver entry/exit means increasing saved shaft-axis parameter, not a prescribed",
        "drill approach. Recessed entries remain on their recorded finished face. Join paired",
        "receivers in one supported setup; do not independently drill opposite marks.",
        "Bit choices are 13/32 in for 3/8-in bolts and 17/32 in for 1/2-in bolts.",
        "The selected underhead lengths supersede old modeled-length columns. Spacers",
        "go between nut washer and nut. Each cleat/post stack uses two 12.7-mm",
        "factory spacers (25.4 mm total); shared-header stacks retain one 12.7-mm spacer.",
        "No Actual/Disposition values are supplied. Changed installation remains unqualified.", "",
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
        if profile.get("inner_kicker_facing_longitudinal_bevel_mm"):
            corner = "U=88.9, V=139.7" if member.endswith("left") else "U=0, V=139.7"
            lines += ["", "Finished profile: **9.525 × 9.525 mm, 45° longitudinal corner bevel**",
                      f"at **{corner}**, for the full L=0–238.9 mm height.",
                      "Raw marks above precede this T-nut clearance cut. Bolt receiver faces at",
                      "their own stations retain the full 88.9-mm width; actual cuts remain unverified."]
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
    data = load_sources()
    text = render(data)
    if args.check:
        require((ROOT / OUTPUT).read_text() == text, "Builder layout is stale; review before --write")
    else:
        (ROOT / OUTPUT).write_text(text)
    print(f"{OUTPUT}: 22 structural wood parts / {len(data['selected'])} bolt axes / {len(data['holes'])} receiver rows verified")


if __name__ == "__main__":
    main()
