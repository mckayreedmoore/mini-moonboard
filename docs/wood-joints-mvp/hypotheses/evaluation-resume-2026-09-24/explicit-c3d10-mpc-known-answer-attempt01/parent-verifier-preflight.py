"""Synthetic verifier control tests only. Never invokes a native solver."""

import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile

HERE = Path(__file__).resolve().parent


def output(case, wrong_motion=False, missing_field=False):
    dat, frd = [], []
    counter = 0
    for increment in range(1, 101):
        time = increment / 1000
        u = {n: [time * time / 2, 0, 0] for n in range(1, 11)}
        if wrong_motion:
            u[2][0] += 1e-4
        vectors = {"U": u, "V": {n: [time, 0, 0] for n in u},
                   "RF": {n: [0, 0, 0] for n in u}}
        for quantity, word, label in (("U", "displacements", "DISP"),
                                      ("V", "velocities", "VELO"),
                                      ("RF", "forces", "FORC")):
            dat.append(f" {word} (x,y,z) for set PHYSICAL and time {time:.9E}")
            dat.extend(f"{n} " + " ".join(f"{x:.9E}" for x in vec)
                       for n, vec in vectors[quantity].items())
            dat.append("")
            if missing_field is True and increment == 50 and label == "FORC":
                continue
            counter += 1
            frd.extend([f"    1PSTEP {counter:12d}{increment:12d}{1:12d}",
                        f" 100CL 101 {time:.9E} 10 0 1 1 1",
                        f" -4 {label} 4 1", " -5 X", " -5 Y", " -5 Z"])
            frd.extend(" -1" + f"{n:10d}" + "".join(f"{x:12.5E}" for x in vec)
                       for n, vec in vectors[quantity].items())
            frd.append(" -3")
        if case == "mapped":
            dat.extend([f" displacements (x,y,z) for set CONTROLLER and time {time:.9E}",
                        f"11 {time * time / 2:.9E} 0 0", ""])
        for name, value in (("internal energy", 0), ("kinetic energy", time * time / 2),
                            ("mass", 1), ("volume", 1 / 6)):
            dat.extend([f" total {name} for set BODY and time {time:.9E}",
                        "", f"{value:.9E}", ""])
        if missing_field == "ENER" and increment == 50:
            continue
        counter += 1
        frd.extend([f"    1PSTEP {counter:12d}{increment:12d}{1:12d}",
                    f" 100CL 101 {time:.9E} 10 0 1 1 1", " -4 ENER 1 1", " -5 ENER"])
        frd.extend(" -1" + f"{n:10d}{0:12.5E}" for n in range(1, 11))
        frd.append(" -3")
    return {"coupon.dat": "\n".join(dat), "coupon.frd": "\n".join(frd),
            "coupon.stdout": "Synthetic control only; no native execution.\n",
            "coupon.stderr": "", "coupon.sta": "HEADER ONLY\n", "coupon.cvg": "HEADER ONLY\n"}


def main():
    spec = importlib.util.spec_from_file_location("fixture_verifier", HERE / "verifier.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    expected = json.loads((HERE / "expected.json").read_text())
    preflight = json.loads((HERE / "preflight.json").read_text())
    results = {}
    with tempfile.TemporaryDirectory(prefix="wj-explicit-verifier-") as temporary:
        module.HERE = Path(temporary)
        (module.HERE / "input").mkdir()
        for case in ("direct", "mapped"):
            (module.HERE / expected["inputs"][case]).write_bytes((HERE / expected["inputs"][case]).read_bytes())
        for name, case, wrong, missing in (("direct_complete", "direct", False, False),
                                           ("mapped_complete", "mapped", False, False),
                                           ("mapped_wrong_motion", "mapped", True, False),
                                           ("direct_missing_field", "direct", False, True),
                                           ("direct_missing_energy", "direct", False, "ENER")):
            folder = module.HERE / "output" / case
            folder.mkdir(parents=True, exist_ok=True)
            for filename, text in output(case, wrong, missing).items():
                (folder / filename).write_text(text)
            record = {"status": "completed", "docker_cli_exit_code": 0,
                      "container_state": {"ExitCode": 0, "OOMKilled": False, "Running": False},
                      "outputs_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                                         for p in folder.iterdir()}}
            result = module.evaluate_case(case, expected, preflight, record)
            wanted = "FAIL" if wrong or missing else "PASS"
            assert result["status"] == wanted, (name, result["errors"], result.get("gate_results"), result.get("coverage_errors"))
            if wrong:
                assert result["gate_results"]["physical_U"] is False, name
            if missing is True:
                assert result["coverage_errors"], name
            if missing == "ENER":
                assert result["FRD_ENER_diagnostic"]["status"] == "FAIL", name
            assert len(result["states"]) == 100, name
            assert result["first_state"] and result["final_state"], name
            results[name] = {"observed_status": result["status"], "preserved_states": len(result["states"])}
    print(json.dumps({"status": "PASS_PARENT_SYNTHETIC_VERIFIER_CONTROLS", "controls": results,
                      "native_execution": False, "joint_acceptance": False}, indent=2))


if __name__ == "__main__":
    main()
