"""Read the frozen PB01 a12-left hybrid response as diagnostic local actions."""

import argparse
import hashlib
import json
import math
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = (
    ROOT
    / "docs/bolted-candidate-prototypes/pb01-quarter-contact4-a12left-evidence.tar.gz"
)
ARCHIVE_SHA256 = "fc298a3a481437a5dc9f24c02bc9a234458074c2ffcba6753fe33875f4805546"
REPORT_SHA256 = "c10b2b2d1b979fe82ffc5bca31c60e374650610e4c44245e8e56431c7b0c4918"
CANDIDATE = "pb01-kerf-right-cleat-quarter-hybrid-preparation-only"
HOSTS = {
    "upright": "base_principal_center_right",
    "rail": "base_rail_service_lower_right",
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def vector(value, label):
    require(isinstance(value, list) and len(value) == 3, f"Invalid {label}")
    require(
        all(isinstance(x, (int, float)) and math.isfinite(x) for x in value),
        f"Invalid {label}",
    )
    return [float(x) for x in value]


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def wrench(point, force, datum):
    """Return force and right-hand-rule moment (point - datum) cross force."""
    p, f, d = vector(point, "point"), vector(force, "force"), vector(datum, "datum")
    r = [x - y for x, y in zip(p, d)]
    return f, [
        r[1] * f[2] - r[2] * f[1],
        r[2] * f[0] - r[0] * f[2],
        r[0] * f[1] - r[1] * f[0],
    ]


def read_member(bundle, name):
    member = bundle.extractfile(name)
    require(member is not None, f"Missing archive member: {name}")
    return member.read()


def checked_json(bundle, name, expected_hash):
    raw = read_member(bundle, name)
    require(
        hashlib.sha256(raw).hexdigest() == expected_hash, f"SHA-256 mismatch: {name}"
    )
    return json.loads(raw)


def extract(path=ARCHIVE):
    """Validate the frozen bundle and recover host/cleat forces without a solve."""
    path = Path(path)
    require(
        hashlib.sha256(path.read_bytes()).hexdigest() == ARCHIVE_SHA256,
        "Unexpected archive SHA-256",
    )
    with tarfile.open(path, "r:gz") as bundle:
        report = checked_json(bundle, "report.json", REPORT_SHA256)
        artifacts = report["artifact_sha256"]
        inputs = checked_json(
            bundle, "cycle-13/input.json", artifacts["cycle-13/input.json"]
        )
        cycle = checked_json(
            bundle, "cycle-13/report.json", artifacts["cycle-13/report.json"]
        )
        scope = checked_json(
            bundle, "diagnostic-scope.json", artifacts["diagnostic-scope.json"]
        )
        sources = report["source_sha256"]
        require(len(sources) == 260, "Unexpected source inventory")
        for name, digest in sources.items():
            require(
                hashlib.sha256(
                    read_member(bundle, "source_snapshots/" + name)
                ).hexdigest()
                == digest,
                f"Source SHA-256 mismatch: {name}",
            )

    require(inputs["candidate"] == report["candidate"] == CANDIDATE, "Wrong candidate")
    require(
        inputs["hold"] == "A12" and inputs["pb01_pose_variant"] == "quarter",
        "Wrong case or variant",
    )
    require(
        scope["case"] == "a12-left" and scope["pb01_pose_variant"] == "quarter",
        "Wrong scope",
    )
    require(
        scope["diagnostic_only"] is True and scope["v4_same_case_demand"] is False,
        "Scope no longer diagnostic",
    )
    require(
        inputs["pb01_same_case_demand"] is False and inputs["preparation_only"] is True,
        "Input claims design demand",
    )
    require(
        report["qualified_for_design"] is False
        and report["actual_joint_demands_qualified"] is False,
        "Report claims design qualification",
    )
    require(
        report["contact_active_set_converged"] is True
        and report["numerically_accepted"] is True,
        "Contact solve not accepted",
    )
    require(
        report["global_equilibrium_passed"] is True
        and report["member_equilibrium_passed"] is True
        and report["mpc_check_passed"] is True
        and report["closed_bearing_assumption_passed"] is True,
        "Reported equilibrium/contact audit failed",
    )
    require(
        all(
            cycle[k] == report[k]
            for k in (
                "force_residual_n",
                "moment_residual_nmm",
                "global_equilibrium_passed",
                "member_equilibrium_passed",
            )
        ),
        "Final-cycle audit differs",
    )
    require(
        max(map(abs, vector(report["force_residual_n"], "force residual"))) <= 0.1
        and max(map(abs, vector(report["moment_residual_nmm"], "moment residual")))
        <= 2.0,
        "Numeric equilibrium residual exceeded",
    )
    for member, balance in report["member_equilibrium"].items():
        require(
            balance["passed"] is True
            and max(vector(balance["force_interval_distance_n"], member + " force"))
            <= 0.1
            and max(vector(balance["moment_interval_distance_nmm"], member + " moment"))
            <= 20,
            f"Member equilibrium failed: {member}",
        )
    proxy = inputs["legacy_proxy_stations"]
    require(
        len(proxy) == len(set(proxy)) == 23
        and scope["old_ml24z_sds_proxy_stations"] == 23,
        "Expected 23 unique proxy stations",
    )
    require(
        {row["name"] for row in inputs["angle_stations"]} == set(proxy)
        and {row["name"] for row in report["angle_stations"]} == set(proxy),
        "Proxy station inventory differs",
    )
    require(
        scope["pb01_cleat_station"] == "clip_horizontal_lower_right_1"
        and scope["pb01_cleat_station"] not in proxy,
        "PB01 station still a proxy",
    )

    groups, contacts = inputs["pb01_bolt_groups"], inputs["pb01_contact_names"]
    require(
        set(groups) == set(HOSTS) and all(len(groups[f]) == 2 for f in HOSTS),
        "Expected two bolts on each serial interface",
    )
    require(len(contacts) == len(set(contacts)) == 8, "Expected four contacts per face")
    require(
        set(contacts)
        == {
            f"pb01_{family}_compression_{i}_{j}"
            for family in HOSTS
            for i in range(2)
            for j in range(2)
        },
        "Contact grid differs",
    )
    names = [name for family in HOSTS for name in groups[family]] + contacts
    require(len(set(names)) == 12, "Duplicate PB01 connector")
    ownership = inputs["connection_ownership"]
    physical = report["physical_connection_forces"]
    bearings = {row["name"]: row for row in report["bearings"]}
    springs = {
        name: [s for s in inputs["springs"] if s["name"] == name] for name in contacts
    }
    datum = [
        sum(ownership[name]["point"][i] for name in names[:4]) / 4 for i in range(3)
    ]
    vector(datum, "PB01 datum")
    interfaces = {}
    for family, host in HOSTS.items():
        bolts, face_contacts, actions = [], [], []
        for name in groups[family] + [
            n for n in contacts if n.startswith(f"pb01_{family}_")
        ]:
            owner, row = ownership[name], physical[name]
            require(
                owner["first"] == row["first"] == host
                and owner["second"] == row["second"] == "base_cleat_pb01",
                f"Wrong connector ownership: {name}",
            )
            point = vector(owner["point"], name + " point")
            require(
                vector(row["point"], name + " reported point") == point,
                f"Point mismatch: {name}",
            )
            force = vector(row["force_on_first_xyz_n"], name + " force")
            opposite = vector(row["force_on_second_xyz_n"], name + " opposite force")
            require(
                all(abs(a + b) <= 1e-8 for a, b in zip(force, opposite)),
                f"Unbalanced connector pair: {name}",
            )
            actions.append((point, force))
            if name in groups[family]:
                axis = vector(owner["axis"], name + " axis")
                require(abs(dot(axis, axis) - 1) < 1e-8, f"Non-unit bolt axis: {name}")
                axial = dot(force, axis)
                lateral = [f - axial * a for f, a in zip(force, axis)]
                require(
                    abs(row["axial_along_installation_direction_n"] - axial) < 1e-6
                    and abs(
                        row["transverse_shear_n"] - math.sqrt(dot(lateral, lateral))
                    )
                    < 1e-6,
                    f"Bolt decomposition differs: {name}",
                )
                bolts.append(
                    {
                        "name": name,
                        "point_xyz_mm": point,
                        "axis_xyz": axis,
                        "force_on_host_xyz_n": force,
                        "axial_n": axial,
                        "lateral_xyz_n": lateral,
                        "lateral_magnitude_n": math.sqrt(dot(lateral, lateral)),
                    }
                )
            else:
                normal = vector(owner["scalar_normal"], name + " normal")
                bearing = bearings[name]
                require(
                    len(springs[name]) == 1
                    and springs[name][0]["active"] is bearing["active"],
                    f"Contact active state differs: {name}",
                )
                compression = dot(force, normal)
                require(
                    compression >= -1e-8
                    and abs(compression - bearing["compression_force_n"]) < 1e-6
                    and (bearing["active"] == (compression > 0)),
                    f"Contact force differs: {name}",
                )
                face_contacts.append(
                    {
                        "name": name,
                        "point_xyz_mm": point,
                        "normal_xyz": normal,
                        "active": bearing["active"],
                        "force_on_host_xyz_n": force,
                        "compression_n": compression,
                    }
                )
        require(len(face_contacts) == 4, f"Missing {family} contacts")
        force = [sum(f[i] for _, f in actions) for i in range(3)]
        moment = [sum(wrench(p, f, datum)[1][i] for p, f in actions) for i in range(3)]
        interfaces[family] = {
            "host": host,
            "cleat": "base_cleat_pb01",
            "bolts": bolts,
            "contacts": face_contacts,
            "resultant_on_host": {"force_xyz_n": force, "moment_xyz_nmm": moment},
            "resultant_on_cleat": {
                "force_xyz_n": [-x for x in force],
                "moment_xyz_nmm": [-x for x in moment],
            },
        }
    return {
        "scope": "diagnostic_only",
        "case": "a12-left",
        "candidate": CANDIDATE,
        "archive_sha256": ARCHIVE_SHA256,
        "report_sha256": REPORT_SHA256,
        "proxy_station_count": 23,
        "datum_xyz_mm": datum,
        "interfaces": interfaces,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, default=ARCHIVE)
    args = parser.parse_args()
    print(json.dumps(extract(args.archive), indent=2))
