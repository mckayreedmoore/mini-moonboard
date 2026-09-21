"""PB07 native ten-station geometry with revised outer rail holes; no solve."""

import hashlib
from dataclasses import replace
from itertools import combinations
from pathlib import Path
from unittest.mock import patch

from mini_moonboard.box_frame import Part
from scripts import simple_pb03_bottom_outer_pair as bottom
from scripts import simple_pb03_cross_family as cross
from scripts import simple_pb03_lower_center_pair as lower
from scripts import simple_pb03_upper_center_pair as upper_center
from scripts import simple_pb03_upper_outer_pair as upper
from scripts import simple_pb05_narrow_outer_screen as narrow
from scripts import simple_pb05_native as pb05
from scripts import simple_pb05_outer_rail_revision as revision
from scripts import simple_pb05_short_block_screen as short
from scripts import simple_pb06_upper_center_native as pb06

SOURCE_ID = "pb07-ten-station-revised-outer-rail-v1"
OUTER_STATIONS = pb05.OUTER_STATIONS
RAIL_X_OFFSETS_MM = revision.TRIAL_OFFSETS_MM
UPPER_RAIL_N_MM = revision.TRIAL_UPPER_N_MM
_SPECS = {**lower.STATION_SPECS, **upper.STATION_SPECS, **bottom.STATION_SPECS}
_FALSE_FLAGS = {
    "solved": False,
    "force_transfer": False,
    "qualified_for_design": False,
    "acceptance": False,
    "drilling_released": False,
    "fabrication_released": False,
    "structural_released": False,
}


class PB07Native(pb06.PB06Native):
    """Keep PB06 topology while relocating only six outer rail-bolt rows."""

    KEY = SOURCE_ID

    def __init__(self):
        super().__init__()
        if (
            pb05.BLOCK_X_MM != 95.25
            or pb05.RAIL_X_OFFSETS_MM != (25.0, 70.0)
            or RAIL_X_OFFSETS_MM != (26.0, 70.0)
            or UPPER_RAIL_N_MM != 45.0
            or set(self._pb03_geometries)
            != set(OUTER_STATIONS)
            | set(lower.TARGET_STATIONS)
            | set(pb06.TARGET_STATIONS)
        ):
            raise ValueError("PB07 parent or trial geometry changed")
        parts, finished, panels, _, _ = lower._source_inventory()
        if tuple(map(pb05._axis, panels)) != tuple(
            map(pb05._axis, self.panel_connections())
        ):
            raise ValueError("PB07 fixed panel axes changed")
        axes = lower._fixed_axis_solids(panels)
        # ponytail: scoped producer constants rebuild six stations, not historical PB05/PB06.
        with (
            patch.object(lower, "BLOCK_X_MM", pb05.BLOCK_X_MM),
            patch.object(lower, "RAIL_X_OFFSETS_MM", RAIL_X_OFFSETS_MM),
        ):
            outer = {
                name: lower._build_station(
                    _SPECS[name],
                    parts,
                    finished,
                    axes,
                    rail_n_offset_mm=(
                        UPPER_RAIL_N_MM
                        if name in upper.TARGET_STATIONS
                        else lower.RAIL_N_OFFSET_MM
                    ),
                )
                for name in OUTER_STATIONS
            }
        self._pb03_geometries.update(outer)
        self._blocks = tuple(
            Part(
                row.block_name,
                row.block,
                (row.block_length_mm, *row.report["block_dimensions_mm"][:2]),
                "PB07 developmental solid timber block; hardware and drilling unselected",
                1,
            )
            for row in self._pb03_geometries.values()
        )
        self._pb03_bolts = tuple(
            bolt for row in self._pb03_geometries.values() for bolt in row.bolts
        )
        uncut = {part.name: part.shape for part in self.uncut_wood_parts()}
        for row in outer.values():
            for bolt in row.bolts:
                direction = bolt.direction.normalized()
                host_face = max(
                    vertex.Center().dot(direction)
                    for vertex in uncut[bolt.members[0]].Vertices()
                )
                block_face = min(
                    vertex.Center().dot(direction) for vertex in row.block.Vertices()
                )
                if abs(host_face - block_face) > 1e-6:
                    raise ValueError(f"{bolt.name}: PB07 host/block face changed")
                self._pb03_bolt_points[bolt.name] = bolt.start + direction * (
                    host_face - bolt.start.dot(direction)
                )
        if len(self._pb03_bolt_points) != 40:
            raise ValueError("PB07 bolt interface-point inventory changed")

    def parts(self):
        """Do not display the two PB06-converted upper-center legacy angles."""
        return tuple(
            part for part in super().parts() if part.name not in pb06.TARGET_STATIONS
        )

    def validate_prepared_case(self, structure, metadata):
        """Authenticate PB07 ownership without treating PB06 as the solved candidate."""
        pb06.PB06Native.validate_prepared_case(self, structure, metadata)
        metadata.pop("pb06_candidate", None)
        metadata.pop("pb06_preparation_validated", None)
        metadata.update(
            pb07_candidate=SOURCE_ID,
            pb07_preparation_validated=True,
            preparation_only=True,
            developmental_only=True,
            **_FALSE_FLAGS,
        )


def _new_pair_interactions(geometry):
    """Screen revised outers against PB06's added pair, including nominal shafts."""
    outer = {name: geometry[name] for name in OUTER_STATIONS}
    added = {name: geometry[name] for name in pb06.TARGET_STATIONS}
    generic = cross.screen_cross_family(outer, added)
    installed = {name: revision._installed(row) for name, row in outer.items()}
    hits = {}
    for outer_name, row in outer.items():
        for added_name, neighbor in added.items():
            targets = {
                f"block/{added_name}": neighbor.block,
                **{
                    f"bore/{added_name}/{bolt}": shape
                    for bolt, shape in neighbor.bores.items()
                },
                **{
                    f"stack/{added_name}/{bolt}/{role}": shape
                    for bolt, stack in neighbor.stacks.items()
                    for role, shape in stack.items()
                },
                **{
                    f"tool/{added_name}/{bolt}/{end}": shape
                    for bolt, ends in neighbor.tools.items()
                    for end, shape in ends.items()
                },
            }
            for bolt, stack in installed[outer_name].items():
                for role, shape in stack.items():
                    hits.update(
                        {
                            f"{outer_name}/{bolt}/{role}|{target}": volume
                            for target, volume in narrow._hits(shape, targets).items()
                        }
                    )
            outer_targets = {
                f"block/{outer_name}": row.block,
                **{
                    f"bore/{outer_name}/{bolt}": shape
                    for bolt, shape in row.bores.items()
                },
                **{
                    f"stack/{outer_name}/{bolt}/{role}": shape
                    for bolt, stack in installed[outer_name].items()
                    for role, shape in stack.items()
                },
                **{
                    f"tool/{outer_name}/{bolt}/{end}": shape
                    for bolt, ends in row.tools.items()
                    for end, shape in ends.items()
                },
            }
            for bolt, stack in neighbor.stacks.items():
                for role, shape in stack.items():
                    hits.update(
                        {
                            f"{added_name}/{bolt}/{role}|{target}": volume
                            for target, volume in narrow._hits(
                                shape, outer_targets
                            ).items()
                        }
                    )
    return {
        "generic_cross_family": generic,
        "full_nominal_outer_stack_hits_mm3": hits,
        "passes": generic["all_cross_family_collision_gates_pass"] and not hits,
        "limitation": "Added upper-center stacks are PB06 generic envelopes; purchased hardware unselected.",
    }


def _nominal_stack(geometry, bolt):
    """Retain interface-specific seats and extend the full nominal shaft."""
    if geometry.station in OUTER_STATIONS and bolt.members[0] == geometry.upright_name:
        return narrow._installed_upright(bolt)
    stack = dict(geometry.stacks[bolt.name])
    direction = bolt.direction.normalized()
    near = bolt.start + direction * lower.END_ALLOWANCE_MM
    hardware = narrow.hardware
    length = (8 if bolt.members[0] == geometry.upright_name else 5) * hardware.MM_PER_IN
    stack["shaft"] = hardware._cylinder(
        (near - direction * 2).toTuple(),
        direction.toTuple(),
        length,
        lower.BOLT_DIAMETER_MM,
    )
    return stack


def _bore_block_hits(first_name, first, second_name, second):
    """Check the bore-to-opposite-block mode absent from cross-family."""
    hits = {}
    for source_name, source, target_name, target in (
        (first_name, first, second_name, second),
        (second_name, second, first_name, first),
    ):
        for bolt, bore in source.bores.items():
            if hit := narrow._hits(bore, {target.block_name: target.block}):
                hits[f"{source_name}/{bolt}|{target_name}"] = hit
    return hits


def screen_short_stock(module=None):
    """Detached 152.4-mm PB07 screen; static envelopes are not an install sequence."""
    module = PB07Native() if module is None else module
    reference = module.pb03_geometries()
    parts, finished, panels, _, source_connections = lower._source_inventory()
    legacy = set(module.legacy_proxy_stations())
    source_frame = tuple(row for row in source_connections if row.kind == "bolt")
    actual_frame = tuple(
        row
        for row in module.connections()
        if row.kind == "bolt" and not row.name.startswith("pb03_")
    )
    source_sds = tuple(
        row
        for row in source_connections
        if row.name.startswith("clip_")
        and any(row.name.startswith(f"{station}_") for station in legacy)
    )
    actual_sds = tuple(
        row for row in module.connections() if row.name.startswith("clip_")
    )
    angles = {part.name: part.shape for part in module.parts() if part.name in legacy}
    actual_wood = {part.name: part.shape for part in module.wood_parts()}
    if (
        type(module) is not PB07Native
        or module.KEY != SOURCE_ID
        or len(reference) != 10
        or tuple(map(pb05._axis, panels))
        != tuple(map(pb05._axis, module.panel_connections()))
        or len(legacy) != 12
        or set(angles) != legacy
        or len(source_frame) != 12
        or tuple(map(pb05._axis, actual_frame)) != tuple(map(pb05._axis, source_frame))
        or len(source_sds) != 72
        or tuple(map(pb05._axis, actual_sds)) != tuple(map(pb05._axis, source_sds))
        or not all(
            row.block_name in actual_wood
            and pb05._shape(actual_wood[row.block_name]) == pb05._shape(row.block)
            and actual_wood[row.block_name].distance(row.block) <= 1e-8
            for row in reference.values()
        )
    ):
        raise ValueError("PB07 short-stock source changed")
    axes = lower._fixed_axis_solids(panels)
    specs = {**_SPECS, **upper_center.STATION_SPECS}
    groups = (
        (lower.TARGET_STATIONS, lower.BLOCK_X_MM, lower.RAIL_X_OFFSETS_MM),
        (OUTER_STATIONS, pb05.BLOCK_X_MM, RAIL_X_OFFSETS_MM),
        (pb06.TARGET_STATIONS, lower.BLOCK_X_MM, lower.RAIL_X_OFFSETS_MM),
    )
    geometries = {}
    for names, width, offsets in groups:
        with (
            patch.object(lower, "BLOCK_X_MM", width),
            patch.object(lower, "RAIL_X_OFFSETS_MM", offsets),
        ):
            geometries.update(
                {
                    name: lower._build_station(
                        specs[name],
                        parts,
                        finished,
                        axes,
                        rail_n_offset_mm=(
                            UPPER_RAIL_N_MM
                            if name in upper.TARGET_STATIONS
                            else upper_center.RAIL_N_OFFSET_MM
                            if name in pb06.TARGET_STATIONS
                            else lower.RAIL_N_OFFSET_MM
                        ),
                        block_length_mm=short.SIX_INCH_MM,
                    )
                    for name in names
                }
            )
    if set(geometries) != set(reference) or any(
        tuple(map(pb05._axis, row.bolts))
        != tuple(map(pb05._axis, reference[name].bolts))
        for name, row in geometries.items()
    ):
        raise ValueError("152.4-mm trial moved a PB07 bolt axis")
    installed = {
        name: replace(
            row,
            stacks={bolt.name: _nominal_stack(row, bolt) for bolt in row.bolts},
        )
        for name, row in geometries.items()
    }
    fixed = {
        **{f"panel_axis/{name}": shape for name, shape in axes.items()},
        **{f"frame_axis/{row.name}": narrow._axis(row) for row in source_frame},
        **{f"legacy_angle/{name}": shape for name, shape in angles.items()},
        **{f"legacy_sds/{row.name}": narrow._axis(row) for row in source_sds},
        **{
            f"panel/{name}": shape
            for name, shape in finished.items()
            if name.startswith(("main_", "kicker_"))
        },
    }
    rows = {}
    for name, row in installed.items():
        openings = short._openings(row)
        end_gates, offsets, _ = short._end_gates(row, openings)
        local = row.report
        other_stack = {
            f"{bolt}/{role}": shape
            for bolt, components in row.stacks.items()
            for role, shape in components.items()
        }
        hits = {
            "block": narrow._hits(row.block, fixed),
            "bores": {
                bolt: hit
                for bolt, shape in row.bores.items()
                if (hit := narrow._hits(shape, fixed))
            },
            "tools": {
                f"{bolt}/{end}": hit
                for bolt, ends in row.tools.items()
                for end, shape in ends.items()
                if (hit := narrow._hits(shape, fixed))
            },
            "stacks": {},
            "tool_to_other_installed": {},
        }
        for bolt, components in row.stacks.items():
            physical_bolt = next(item for item in row.bolts if item.name == bolt)
            targets = {
                **fixed,
                **{
                    f"retained_wood/{wood_name}": shape
                    for wood_name, shape in finished.items()
                    if wood_name not in physical_bolt.members
                    and not wood_name.startswith(("main_", "kicker_"))
                },
                **{
                    f"own/{key}": shape
                    for key, shape in other_stack.items()
                    if not key.startswith(bolt + "/")
                },
                **{
                    f"own_bore/{key}": shape
                    for key, shape in row.bores.items()
                    if key != bolt
                },
            }
            for role, shape in components.items():
                if hit := narrow._hits(shape, targets):
                    hits["stacks"][f"{bolt}/{role}"] = hit
        for bolt, ends in row.tools.items():
            other_installed = {
                key: shape
                for key, shape in other_stack.items()
                if not key.startswith(bolt + "/")
            }
            for end, shape in ends.items():
                if hit := narrow._hits(shape, other_installed):
                    hits["tool_to_other_installed"][f"{bolt}/{end}"] = hit
        gates = {
            "local": local["contact_verified"]
            and local["complete_bores"]
            and local["collision_clear"]
            and local["access_clear"],
            "fixed_and_installed_clear": not any(hits.values()),
            **end_gates,
        }
        rows[name] = {
            "rail_x_offsets_mm": offsets,
            "end_openings_mm": openings,
            "gates": gates,
            "hits_mm3": hits,
        }
    envelopes = {name: short._envelope(row) for name, row in installed.items()}
    pairs = {}
    blocking_pairs = {}
    bore_block_hits = {}
    for first, second in combinations(installed, 2):
        if not short._envelopes_overlap(envelopes[first], envelopes[second]):
            continue
        bore_block_hits.update(
            _bore_block_hits(first, installed[first], second, installed[second])
        )
        result = cross.screen_cross_family(
            {first: installed[first]}, {second: installed[second]}
        )
        hits = {
            key: value
            for key, value in result.items()
            if key.endswith("hits_mm3") and value
        }
        if hits:
            pairs[f"{first}|{second}"] = hits
            blockers = {
                key: value
                for key, value in hits.items()
                if key != "cross_family_tool_tool_hits_mm3"
            }
            if blockers:
                blocking_pairs[f"{first}|{second}"] = blockers
    passed = (
        not blocking_pairs
        and not bore_block_hits
        and all(all(row["gates"].values()) for row in rows.values())
    )
    fingerprint = pb05._digest(
        {
            "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "short_screen_sha256": hashlib.sha256(
                Path(short.__file__).read_bytes()
            ).hexdigest(),
            "cross_family_sha256": hashlib.sha256(
                Path(cross.__file__).read_bytes()
            ).hexdigest(),
            "upper_center_sha256": hashlib.sha256(
                Path(upper_center.__file__).read_bytes()
            ).hexdigest(),
            "length_mm": short.SIX_INCH_MM,
            "bolts": {
                name: tuple(map(pb05._axis, row.bolts))
                for name, row in geometries.items()
            },
            "blocks": {
                name: pb05._shape(row.block) for name, row in geometries.items()
            },
        }
    )
    return {
        "schema": "simple_pb07_short_stock_screen/v1",
        "source_id": SOURCE_ID,
        "source_fingerprint_sha256": fingerprint,
        "common_block_length_mm": short.SIX_INCH_MM,
        "inventory": {
            "blocks": len(installed),
            "bolts": sum(len(row.bolts) for row in installed.values()),
            "panel_kicker_axes": len(axes),
            "original_frame_bolt_axes": sum(
                row.kind == "bolt" for row in source_connections
            ),
            "legacy_duties": len(module.legacy_proxy_stations()),
            "legacy_angle_solids": len(angles),
            "legacy_sds_axes": len(source_sds),
            "retained_timber_solids": sum(
                not name.startswith(("main_", "kicker_")) for name in finished
            ),
        },
        "stations": rows,
        "pair_hits_mm3": pairs,
        "blocking_pair_hits_mm3": blocking_pairs,
        "bore_to_other_block_hits_mm3": bore_block_hits,
        "outer_second_rail_far_x_edge_mm": pb05.BLOCK_X_MM - RAIL_X_OFFSETS_MM[1],
        "conditional_4d_far_x_margin_mm": (
            pb05.BLOCK_X_MM - RAIL_X_OFFSETS_MM[1] - 4 * lower.BOLT_DIAMETER_MM
        ),
        "decision": "ADVANCE_STATIC_GEOMETRY_ONLY" if passed else "REVISE",
        "limits": [
            "Nominal 8/5-in shafts and dimensional washer/nut envelopes are not SKU-controlled delivered hardware.",
            "Tool envelopes clear already-installed other bolts only where checked; approach/insertion and real sequence are unverified.",
            "Tool/tool overlap is reported but is not a blocker for sequential, one-tool-at-a-time assembly.",
            "No PB07 native solve, joint strength check, or drilling release.",
            "Second outer rail row is 25.25 mm from the far X edge, 0.15 mm below 4D if that edge is loaded; bidirectional case signs and tolerance remain unchecked.",
        ],
        **_FALSE_FLAGS,
    }


def screen(module=None):
    """Bind the revised solids, bolts and retained PB06 axes to new source bytes."""
    module = PB07Native() if module is None else module
    source = pb06.PB06Native()
    source_geometry = source.pb03_geometries()
    geometry = module.pb03_geometries()
    source_parts = {part.name: part.shape for part in source.wood_parts()}
    candidate_parts = {part.name: part.shape for part in module.wood_parts()}
    changed_names = {geometry[name].block_name for name in OUTER_STATIONS}
    fixed_names = set(source_parts) - changed_names
    source_connections = source.connections()
    candidate_connections = module.connections()
    source_bolts = {
        bolt.name for name in OUTER_STATIONS for bolt in source_geometry[name].bolts
    }
    fixed_connections = tuple(
        pb05._axis(row) for row in source_connections if row.name not in source_bolts
    )
    actual_fixed = tuple(
        pb05._axis(row) for row in candidate_connections if row.name not in source_bolts
    )
    outer = {name: geometry[name] for name in OUTER_STATIONS}
    if (
        module.KEY != SOURCE_ID
        or set(geometry) != set(source_geometry)
        or set(candidate_parts) != set(source_parts)
        or fixed_connections != actual_fixed
        or any(
            pb05._shape(candidate_parts[name]) != pb05._shape(source_parts[name])
            or candidate_parts[name].distance(source_parts[name]) > 1e-8
            for name in fixed_names
        )
        or any(
            row.report["block_dimensions_mm"] != [95.25, 57.15, 300.0]
            or pb05._shape(candidate_parts[row.block_name]) != pb05._shape(row.block)
            or row.report["rail_bore_n_offset_mm"]
            != (
                UPPER_RAIL_N_MM
                if name in upper.TARGET_STATIONS
                else lower.RAIL_N_OFFSET_MM
            )
            or len(row.bolts) != 4
            for name, row in outer.items()
        )
        or len(module.panel_connections()) != 66
        or sum(
            row.kind == "bolt" and not row.name.startswith("pb03_")
            for row in candidate_connections
        )
        != 12
        or len(module.legacy_proxy_stations()) != 12
        or sum(row.name.startswith("clip_") for row in candidate_connections) != 72
        or sum(row.name.startswith("pb03_") for row in candidate_connections) != 40
    ):
        raise ValueError("PB07 source or retained inventory changed")
    parent_fingerprint = pb05._digest(
        {
            "pb06_source_sha256": hashlib.sha256(
                Path(pb06.__file__).read_bytes()
            ).hexdigest(),
            "connections": tuple(map(pb05._axis, source_connections)),
            "wood": {name: pb05._shape(shape) for name, shape in source_parts.items()},
        }
    )
    trial = revision.screen()
    if trial["decision"] != "ADVANCE_TO_NEW_NATIVE_SOLVE":
        raise ValueError("PB07 detached source trial no longer passes")
    for name, row in outer.items():
        rail = [bolt for bolt in row.bolts if bolt.members[0] == row.rail_name]
        butt = row.report["butt_faces_x_mm"]["upright"]
        sign = 1 if row.rail_extension_direction == "right" else -1
        offsets = tuple(sign * (bolt.start.x - butt) for bolt in rail)
        if offsets != tuple(
            trial["geometry"]["stations"][name]["rail_x_offsets_from_butt_mm"]
        ):
            raise ValueError(f"{name}: PB07 rail axes differ from screened trial")
    interactions = _new_pair_interactions(geometry)
    if not interactions["passes"]:
        raise ValueError(
            "PB07 revised outer/upper-center geometry has blocking interference"
        )
    identity = {
        "source_id": SOURCE_ID,
        "pb06_parent_fingerprint": parent_fingerprint,
        "rail_x_offsets_mm": RAIL_X_OFFSETS_MM,
        "upper_rail_n_mm": UPPER_RAIL_N_MM,
        "connections": tuple(map(pb05._axis, candidate_connections)),
        "wood": {name: pb05._shape(shape) for name, shape in candidate_parts.items()},
        "bolts": {
            name: tuple(map(pb05._axis, row.bolts)) for name, row in geometry.items()
        },
    }
    fingerprint = pb05._digest(
        {
            "identity": identity,
            "sources": {
                "pb07": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                "pb06": hashlib.sha256(Path(pb06.__file__).read_bytes()).hexdigest(),
                "pb05": hashlib.sha256(Path(pb05.__file__).read_bytes()).hexdigest(),
                "producer": hashlib.sha256(
                    Path(lower.__file__).read_bytes()
                ).hexdigest(),
                "revision": hashlib.sha256(
                    Path(revision.__file__).read_bytes()
                ).hexdigest(),
                "nominal_screen": hashlib.sha256(
                    Path(narrow.__file__).read_bytes()
                ).hexdigest(),
                "cross_family": hashlib.sha256(
                    Path(cross.__file__).read_bytes()
                ).hexdigest(),
            },
        }
    )
    return {
        "schema": "simple_pb07_outer_rail_native/v1",
        "source_id": SOURCE_ID,
        "pb06_parent_fingerprint_sha256": parent_fingerprint,
        "source_fingerprint_sha256": fingerprint,
        "inventory": {
            "blocks": 10,
            "outer_blocks": 6,
            "original_frame_bolt_axes": 12,
            "panel_kicker_axes": 66,
            "legacy_sds_duties": 12,
            "legacy_sds_axes": 72,
            "new_bolt_axes": 40,
        },
        "geometry_gate": {
            "detached_six_outer_full_nominal_and_tool": trial["geometry_pass"],
            "fixed_action_signed_end_edge_sensitivity": trial[
                "fixed_action_signed_pass"
            ],
            "new_upper_center_pair_interactions": interactions,
            "passes": trial["geometry_pass"] and interactions["passes"],
            "outer_second_rail_far_x_edge_mm": pb05.BLOCK_X_MM - RAIL_X_OFFSETS_MM[1],
            "conditional_4d_far_x_margin_mm": (
                pb05.BLOCK_X_MM - RAIL_X_OFFSETS_MM[1] - 4 * lower.BOLT_DIAMETER_MM
            ),
            "limitation": "PB05 A12 signs are sensitivity only; 70-mm row is 0.15 mm below conditional 4D at far X edge if reverse-loaded. PB07 needs all-case signed checks, tolerance, its own solve, and complete joint checks.",
        },
        "native_solve": False,
        **{key: value for key, value in _FALSE_FLAGS.items() if key != "solved"},
    }
