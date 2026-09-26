"""Independent check of the first current finite-actuator input, without CCX."""

import hashlib
import json
import math
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
SOURCE = BASE / "ordinary-transient-seating-100n-aligned-k1e4-attempt01"
CASE = BASE / "ordinary-finite-actuator-k1e4-attempt02"


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def cards(text):
    result = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("**"):
            continue
        if line.startswith("*"):
            result.append((line.upper().replace(" ", ""), []))
        else:
            result[-1][1].append(line)
    return result


def select(deck, name):
    return [(h, rows) for h, rows in deck if h.split(",")[0] == name]


def node_sets(path):
    return {
        header.split("NSET=")[1].split(",")[0]: {
            int(value) for line in rows for value in line.split(",")
        }
        for header, rows in cards(path.read_text())
        if header.startswith("*NSET,")
    }


def main():
    assert sha(SOURCE / "input-freeze.json") == (
        "4f5d892d6f6270ae2d645463255a048b8b719331a0906412c4c4b85fd304f367"
    )
    source = json.loads((SOURCE / "input-freeze.json").read_text())
    freeze = json.loads((CASE / "input-freeze.json").read_text())
    for folder, record in [(SOURCE, source), (CASE, freeze)]:
        for name, pin in record["artifacts_sha256"].items():
            assert sha(folder / name) == pin, (folder, name)
    unchanged = [
        "mesh.inp",
        "materials.inp",
        "nut-coupling.inp",
        "rigid-carriers.inp",
        "contact-fragment.inc",
        "output-sets.inp",
    ]
    for name in unchanged:
        assert (CASE / name).read_bytes() == (SOURCE / name).read_bytes(), name
    for key in [
        "monitor_nodes",
        "rotation_nodes",
        "serialized_unit_load_nodes",
        "sampled_travel_stop_mm",
        "sampled_loaded_node_displacement_stop_mm",
        "sampled_controller_rotation_stop_rad",
    ]:
        assert freeze[key] == source[key], key

    source_sets = node_sets(SOURCE / "pilot-sets.inp")
    new_sets = node_sets(CASE / "pilot-sets.inp")
    assert source_sets.keys() == new_sets.keys()
    for name, nodes in source_sets.items():
        expected = nodes | {117162, 117163} if name == "PILOT_ALL_NODES" else nodes
        assert new_sets[name] == expected, name

    pilot = (CASE / "pilot.inp").read_text()
    deck = cards(pilot)
    assert not select(deck, "*CLOAD") and not select(deck, "*TIMEPOINTS")
    assert "TIMEPOINTS=" not in pilot.upper().replace(" ", "")
    assert select(deck, "*DYNAMIC") == [
        ("*DYNAMIC,ALPHA=0", ["0.0005,0.1,1e-06,0.0005"])
    ]
    assert len(select(deck, "*STEP")) == 1
    assert "NLGEOM" in select(deck, "*STEP")[0][0]
    assert "INC=10000" in select(deck, "*STEP")[0][0]
    assert select(deck, "*SPRING") == [
        ("*SPRING,ELSET=ACTUATOR_SPRING", ["1,1", "200.0"])
    ]
    assert select(deck, "*ELEMENT") == [
        ("*ELEMENT,TYPE=SPRING2,ELSET=ACTUATOR_SPRING", ["57644,117162,117163"])
    ]
    assert select(deck, "*BOUNDARY") == [
        ("*BOUNDARY", ["117162,2,3,0", "117163,2,3,0"]),
        ("*BOUNDARY,AMPLITUDE=Q_TARGET_HISTORY", ["117163,1,1,1.15"]),
    ]
    equations = select(deck, "*EQUATION")
    assert len(equations) == 1 and equations[0][1][0] == "663"
    fields = [v for line in equations[0][1][1:] for v in line.split(",")]
    assert len(fields) == 663 * 3
    terms = [
        (int(fields[i]), int(fields[i + 1]), float(fields[i + 2]))
        for i in range(0, len(fields), 3)
    ]
    assert terms[0] == (117162, 1, 1.0)
    assert all(len(fields[i]) <= 20 for i in range(2, len(fields), 3))
    assert all(n not in {117162, 117163} for n, _d, _w in terms[1:])
    original = json.loads((SOURCE / "actuator.json").read_text())["equation"][
        "physical_terms_before_normalization"
    ]
    original = {(n, d): w for n, d, w in original}
    serialized = {(n, d): -w for n, d, w in terms[1:]}
    assert len(serialized) == len(original) == 662
    assert serialized.keys() == original.keys()
    error = max(abs(serialized[key] - original[key]) for key in original)
    assert error <= 5.1e-17

    amplitudes = select(deck, "*AMPLITUDE")
    assert len(amplitudes) == 1
    assert amplitudes[0][0] == "*AMPLITUDE,NAME=Q_TARGET_HISTORY"
    history = [[float(x) for x in row.split(",")] for row in amplitudes[0][1]]
    assert len(history) == 201
    amplitude_error = 0.0
    for i, (t, fraction) in enumerate(history):
        x = i / 200
        assert math.isclose(t, i * 0.0005, rel_tol=0, abs_tol=1e-16)
        exact_x = Decimal(i) / 200
        exact_fraction = exact_x**3 * (10 - 15 * exact_x + 6 * exact_x**2)
        actual_error = abs(Decimal(amplitudes[0][1][i].split(",")[1]) - exact_fraction)
        # Bound binary64 polynomial evaluation plus .15g serialization.
        # This is a generation/printing bound, not a mechanics tolerance.
        eps = math.ulp(1.0)
        gamma = 16 * eps / (1 - 16 * eps)
        rounding = (
            0.5 * 10 ** (math.floor(math.log10(fraction)) - 14) if fraction else 0
        )
        bound = gamma * (10 * x**3 + 15 * x**4 + 6 * x**5) + rounding
        assert float(actual_error) <= bound
        amplitude_error = max(amplitude_error, float(actual_error))
    outputs = [
        (h, r)
        for h, r in deck
        if h.startswith(
            ("*NODEFILE", "*NODEPRINT", "*ELPRINT", "*CONTACTPRINT", "*CONTACTFILE")
        )
    ]
    assert len(outputs) == 42 and all("FREQUENCY=1" in h for h, _r in outputs)
    node_files = select(deck, "*NODEFILE")
    assert len(node_files) == 1 and "NSET=PILOT_ALL_NODES" in node_files[0][0]
    assert node_files[0][1] == ["U,V,RF"]
    node_prints = select(deck, "*NODEPRINT")
    assert node_prints == [
        ("*NODEPRINT,NSET=PILOT_MONITOR,FREQUENCY=1", ["U"]),
        ("*NODEPRINT,NSET=ACTUATOR_DRIVER,FREQUENCY=1", ["U,RF"]),
    ]
    contacts = select(deck, "*CONTACTPRINT")
    assert len(contacts) == 36
    assert contacts[0] == ("*CONTACTPRINT,FREQUENCY=1", ["CDIS,CSTR,CELS,CNUM"])
    contacts = contacts[1:]
    for i, (header, rows) in enumerate(contacts, 1):
        assert f"SLAVE=WJCP_{i:03}_S,MASTER=WJCP_{i:03}_M" in header
        assert rows == ["CF,CFN,CFS"]
    assert freeze["mechanical_acceptance"] is False
    report = {
        "scope": "Independent input-only check; no native response or joint acceptance",
        "status": "PASSED_CURRENT_FINITE_ACTUATOR_INPUT_CHECK",
        "audit_sha256": sha(Path(__file__)),
        "input_freeze_sha256": sha(CASE / "input-freeze.json"),
        "pilot_sha256": sha(CASE / "pilot.inp"),
        "source_input_freeze_sha256": sha(SOURCE / "input-freeze.json"),
        "unchanged_physical_includes": unchanged,
        "source_and_child_pins_verified": True,
        "source_pin_count": len(source["artifacts_sha256"]),
        "child_pin_count": len(freeze["artifacts_sha256"]),
        "physical_mpc_term_count": 662,
        "maximum_unit_weight_serialization_error": error,
        "output_request_count": len(outputs),
        "every_accepted_increment_requested": True,
        "single_physical_and_driver_frd_union": True,
        "contact_pair_count": 35,
        "amplitude_samples": len(history),
        "maximum_amplitude_error_vs_exact_quintic": amplitude_error,
        "mechanical_acceptance": False,
    }
    (HERE / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
