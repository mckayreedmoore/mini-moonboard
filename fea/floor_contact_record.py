"""Publish bounded unresolved trials without converting stops into failure results."""
import hashlib
import json
import shutil
from pathlib import Path


def main():
    source = Path("fea/generated/floor-contact")
    output = Path("fea/results/floor_contact")
    output.mkdir(parents=True,exist_ok=True)
    report = {"status":"Whole-frame contact feasibility unresolved; no accepted climbing-load result",
              "sources_sha256":{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in
                  map(Path,("fea/floor_contact.py","fea/floor_contact_results.py","fea/floor_contact_toy.py","fea/floor_contact_record.py"))},
              "provenance_note":"Source digests here identify publication/re-audit code, not immutable code execution provenance of early trials. Each trial retains its actual pre-launch deck digest; do not backfill missing launch source hashes.",
              "trials":{},"toys":{}}
    for name in ("floor_mu0p3_k10000","floor_mu0p5_k10000","floor_mu0p5_k1000"):
        record = json.loads((source/f"{name}.json").read_text())
        if record.get("exit_code") not in (-15,-999):
            raise ValueError("This publisher handles the bounded interrupted trials only; completed solves require full contact audit")
        if (source/f"{name}.sta").read_text().strip():
            raise ValueError("An increment completed; characterize it explicitly before publication")
        actual = hashlib.sha256((source/f"{name}.inp").read_bytes()).hexdigest()
        if actual != record["deck_sha256"]:
            raise ValueError("Trial deck changed since launch")
        item = {k:v for k,v in record.items() if k not in ("ground_nodes","nodal_volume_mm3")}
        item["stop_interpretation"] = "Manual bounded-work stop" if record["exit_code"]==-15 else "240-second subprocess timeout"
        item["accepted_increments"] = 0
        item["climbing_load_reached"] = False
        item["evidence_sha256"] = {}
        for suffix in (".inp",".dat",".sta",".cvg",".log",".json"):
            path = source/(name+suffix)
            item["evidence_sha256"][path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
            if suffix in (".sta",".cvg",".log"):
                shutil.copyfile(path,output/path.name)
        report["trials"][name] = item
    for name in ("toy","toy_quadratic"):
        item = json.loads((source/f"{name}.json").read_text())
        for filename,digest in item["sha256"].items():
            if hashlib.sha256((source/filename).read_bytes()).hexdigest()!=digest:
                raise ValueError("Toy evidence changed after audit")
            shutil.copyfile(source/filename,output/filename)
        report["toys"][name] = item
    (output/"report.json").write_text(json.dumps(report,indent=2,allow_nan=False)+"\n")
    print(output)


if __name__ == "__main__":
    main()
