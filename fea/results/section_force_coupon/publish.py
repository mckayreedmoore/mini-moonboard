"""Publish the frozen bounded native-section diagnostic; never overwrite."""
import hashlib
import json
import tarfile
from pathlib import Path

from fea.section_force_coupon import audit, deck


def main():
    source = Path("fea/generated/section-force-ygws9_ba")
    destination = Path(__file__).parent
    if any((destination/name).exists() for name in ("report.json", "evidence.tar.gz", "section_force_coupon.launch.py")):
        raise ValueError("Published native-section evidence must not be overwritten")
    names = [f"section{n}.{suffix}" for n in (2, 4) for suffix in ("inp", "json", "dat", "log", "sta", "cvg")]
    names.append("section_force_coupon.launch.py")
    raw = {name: (source/name).read_bytes() for name in names}
    records = {}
    for n in (2, 4):
        record = json.loads(raw[f"section{n}.json"])
        expected, context = deck(n)
        assert expected.encode() == raw[f"section{n}.inp"]
        assert record["exit_code"] == 0
        assert hashlib.sha256(raw[f"section{n}.inp"]).hexdigest() == record["deck_sha256"]
        assert hashlib.sha256(raw["section_force_coupon.launch.py"]).hexdigest() == record["source_sha256"]
        for name, expected_hash in record["output_sha256"].items():
            assert hashlib.sha256(raw[name]).hexdigest() == expected_hash
        assert audit(raw[f"section{n}.dat"].decode(), context) == record["endpoints"]
        records[str(n)] = record
    for name, expected_hash in records["2"]["helper_sha256"].items():
        assert records["4"]["helper_sha256"][name] == expected_hash
        content = Path(name).read_bytes()
        assert hashlib.sha256(content).hexdigest() == expected_hash
        raw["helpers/"+Path(name).name] = content
    archive_path = destination/"evidence.tar.gz"
    with tarfile.open(archive_path, "x:gz") as archive:
        for name in names:
            archive.add(source/name, arcname=name)
        for name in records["2"]["helper_sha256"]:
            archive.add(name, arcname="helpers/"+Path(name).name)
    report = {
        "status": "NATIVE SECTION DIAGNOSTIC; BENDING RESULTANTS NOT CONVERGED; NO FRAME OR CONNECTION VALIDATION",
        "source_directory": str(source), "solver": "CalculiX 2.21, mini-moonboard-fea:box-v1, OMP_NUM_THREADS=2",
        "assumptions": "Homogeneous linear C3D8 beam10x10x100mm; E7000MPa,nu0; clamped Z0; no gravity; independent120N axial and1200Nmm pure bending end tractions; opposite internal faces atZ50; native SOF/SOM only, no custom stress integration.",
        "limitations": "Native stresses are extrapolated/averaged then integrated. Midmember coupon only; not a material-interface or fastener-force method. C3D10 frame formulation unqualified; no converged bending result claimed. Linear reference-coordinate external equilibrium, not geometrically nonlinear balance.",
        "manual": "https://www.dhondt.de/ccx_2.21.htm.tar.bz2 (node332, SECTION PRINT)",
        "archive": archive_path.name, "archive_bytes": archive_path.stat().st_size,
        "archive_sha256": hashlib.sha256(archive_path.read_bytes()).hexdigest(),
        "archive_contents": {name: hashlib.sha256(content).hexdigest() for name, content in raw.items()},
        "comparisons": {},
    }
    for n, record in records.items():
        axial, bending = [row["sections"]["LOWER_CUT"] for row in record["endpoints"]]
        report["comparisons"][n] = {
            "mesh": f"{n}x{n}x{5*int(n)} C3D8", "element_count": 5*int(n)**3,
            "axial_force_n": axial["native_force_moment"][2],
            "axial_error_percent": 100*axial["error"][2]/120,
            "bending_magnitude_nmm": abs(bending["native_force_moment"][4]),
            "bending_shortfall_percent": 100*abs(bending["error"][4])/1200,
            "endpoints": record["endpoints"], "status": record["status"],
        }
    (destination/"section_force_coupon.launch.py").write_bytes(raw["section_force_coupon.launch.py"])
    with (destination/"report.json").open("x") as handle:
        handle.write(json.dumps(report, indent=2, allow_nan=False)+"\n")
    print(destination/"report.json")


if __name__ == "__main__":
    main()
