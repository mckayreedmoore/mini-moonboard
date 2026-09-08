"""Derive current hardware quantities without building CAD or changing exports."""
import csv
import hashlib
import io
import json
from collections import Counter
from pathlib import Path

KEY = "wide-principal-development"
EXPORT = Path("exports")/KEY
OUTPUT = Path("docs/wide-purchase-bom.csv")
REFERENCE = Path("docs/panel-insert-reference.json")
BOLTS = "https://www.fastenersplus.com/cdn/shop/files/CQ-Hex-Head-Bolts-Spec-Sheet.pdf?v=17509241941931126534"
NUT = "https://www.fmwfasteners.com/products/3-8-16-grade-2-finished-hex-nut-zinc-plated"
WASHER = "https://cdefasteners.com/sites/default/files/product-specs/washerssae.pdf"
SIMPSON = "https://ssttoolbox.widen.net/content/iczmiabsx6/pdf/L-C-MLZ25.pdf"


def build():
    manifest = json.loads((EXPORT/"manifest.json").read_text())
    if manifest["design"]["key"] != KEY:
        raise ValueError("Unexpected export candidate")
    if any(hashlib.sha256(Path(p).read_bytes()).hexdigest() != sha
           for p, sha in manifest["sources"].items()):
        raise ValueError("Export source identity differs")
    if str(REFERENCE) not in manifest["sources"]:
        raise ValueError("Insert reference missing from source closure")
    tables = {}
    for name in ("parts", "connections"):
        filename = f"{KEY}_{name}.csv"
        raw = (EXPORT/filename).read_bytes()
        if hashlib.sha256(raw).hexdigest() != manifest["artifacts"][filename]:
            raise ValueError("Export inventory hash differs")
        tables[name] = list(csv.DictReader(io.StringIO(raw.decode())))
    parts, connections = tables["parts"], tables["connections"]
    if len({r["part"] for r in parts}) != len(parts) or len({r["connection"] for r in connections}) != len(connections):
        raise ValueError("Duplicate inventory identity")
    reference = json.loads(REFERENCE.read_text())
    bolts = Counter()
    panel, sds = [], []
    for row in connections:
        if row["kind"] == "bolt" and float(row["diameter_mm"]) == 9.525:
            bolts[float(row["length_mm"])] += 1
        elif row["kind"] == "screw" and row["connection"].startswith("clip_timber_"):
            sds.append(row)
        elif row["kind"] == "screw" and "FMDD14114" in row["status"]:
            panel.append(row)
        else:
            raise ValueError("Unclassified connection")
    inserts = [r for r in parts if r["part"].startswith("insert_timber_")]
    angles = [r for r in parts if r["part"].startswith("clip_timber_")]
    if (sum(bolts.values()) != 24 or len(panel) != len(inserts) or len(panel) != 56
            or len(angles) != 18 or len(sds) != 6*len(angles)):
        raise ValueError("Current candidate hardware counts differ")
    if (any(float(r["length_mm"]) != 38.1 or float(r["diameter_mm"]) != 6.35 for r in sds)
            or any(float(r["length_mm"]) != reference["screw"]["nominal_overall_length"]
                   or float(r["diameter_mm"]) != reference["screw"]["nominal_thread_diameter"] for r in panel)):
        raise ValueError("Screw product dimensions differ")
    rows = []
    def add(item, product, quantity, length, url, limit):
        rows.append({"item": item, "product": product, "quantity": quantity,
            "nominal_length_mm": length, "nominal_length_in": round(length/25.4, 8) if length else "",
            "source_url": url, "qualification": limit})
    for length, quantity in sorted(bolts.items()):
        add("bolt", "Conquest-family 3/8-16 A307 Grade A plain hex bolt", quantity, length,
            BOLTS, "Nominal candidate length; verify exact orderable SKU, thread engagement and connection resistance")
    add("nut", "FMW 3/8-16 ASTM A563 Grade A finished hex nut zinc", sum(bolts.values()), "", NUT,
        "One per bolt; fit, tightening and locking practice unqualified")
    add("washer", "CDE 599192 3/8 SAE carbon-steel zinc washer", 2*sum(bolts.values()), "", WASHER,
        "Two per bolt; washer material certificate and bending resistance unqualified; not F844-certified")
    add("insert", "E-Z LOK "+reference["insert"]["sku"], len(inserts), reference["insert"]["nominal_length"],
        reference["sources"]["insert_product"], "Effective engagement, torque and wood anchorage unqualified")
    add("machine screw", "L.H. Dottie "+reference["screw"]["sku"]+" 1/4-20 flat head", len(panel),
        reference["screw"]["nominal_overall_length"], reference["sources"]["screw_product"],
        "Length includes head; engagement, seating and panel pull-through unqualified")
    add("angle", "Simpson Strong-Tie ML24Z", len(angles), "", SIMPSON,
        "Installation orientation and resistance unqualified; screws purchased separately")
    add("connector screw", "Simpson Strong-Tie SDS25112 1/4 x1-1/2 in", len(sds), 38.1, SIMPSON,
        "Six per ML24Z; installation and directional resistance unqualified")
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue()


if __name__ == "__main__":
    OUTPUT.write_text(build())
