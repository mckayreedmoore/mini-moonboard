"""Prepare/audit contact-free curved-leg section output; no launch or rating."""
import hashlib
import math
import tarfile

from fea import independent_leg_response as profile
from fea import leg_section_preflight as selection
from fea.floor_contact_results import cross
from fea.section_force_coupon import sections

GATES = {"force_n": .001, "moment_nmm": .01, "relative_component": .01,
         "relative_area": .0001}
OUTPUT = ("*SECTION PRINT,SURFACE=LOWER_CUT,NAME=LOWER\nSOF\n"
          "*SECTION PRINT,SURFACE=UPPER_CUT,NAME=UPPER\nSOF\n")


def prepare(size):
    if size not in (40, 25):
        raise ValueError("Only the two archived mesh sizes are selected")
    preflight = selection.preflight()
    row = preflight["meshes"][str(size)]
    with tarfile.open(selection.ARCHIVE) as archive:
        import json
        source = archive.extractfile(f"mesh{size}.inp").read().decode()
        metadata = json.load(archive.extractfile(f"mesh{size}.json"))
        original = archive.extractfile(f"independent{size}.inp").read().decode()
    rebuilt, context = profile.deck(source, metadata, True)
    if rebuilt != original or "*SECTION PRINT" in original or original.count("*END STEP\n") != 9:
        raise ValueError("Archived fixture/output scope differs")
    surface = ""
    for side in ("lower", "upper"):
        surface += f"*SURFACE,NAME={side.upper()}_CUT\n"
        surface += "".join(f"{face[side][0]},S{face[side][1]}\n" for face in row["cut"])
    text = original.replace("*STEP\n", surface+"*STEP\n", 1)
    text = text.replace("*END STEP\n", OUTPUT+"*END STEP\n")
    if text.replace(surface, "", 1).replace(OUTPUT, "") != original:
        raise ValueError("Non-output change to archived fixture")
    context.update(section_reference=preflight["reference_mm"], section_cases=row["loads"],
                   original_sha256=hashlib.sha256(original.encode()).hexdigest(),
                   deck_sha256=hashlib.sha256(text.encode()).hexdigest(), size=size)
    return text, context


def within(error, reference):
    if len(error) != 6 or len(reference) != 6 or not all(map(math.isfinite, [*error, *reference])):
        raise ValueError("Finite six-component vectors required")
    return all(abs(e) <= max(GATES["force_n"] if i < 3 else GATES["moment_nmm"],
                             GATES["relative_component"]*abs(r))
               for i, (e, r) in enumerate(zip(error, reference, strict=True)))


def audit(data, context, areas):
    if set(areas) != {"LOWER_CUT", "UPPER_CUT"} or not all(math.isfinite(a) and a > 0 for a in areas.values()):
        raise ValueError("Positive independently integrated cut areas required")
    fixture = profile.audit(data, context)
    native = sections(data)
    if set(native) != {(name, float(t)) for name in areas for t in range(1, 10)}:
        raise ValueError("Missing/extra native section endpoints")
    rows = []
    for time, (case, fixed) in enumerate(zip(context["section_cases"], fixture, strict=True), 1):
        reference = case["expected_upper_on_lower_force_moment"]
        compared = {}
        for name, sign in (("LOWER_CUT", 1), ("UPPER_CUT", -1)):
            values = native[name, float(time)]
            force, moment = values[0][:3], values[0][3:]
            translated = force + [m-shift for m, shift in zip(moment, cross(context["section_reference"], force), strict=True)]
            expected = [sign*v for v in reference]
            error = [a-b for a, b in zip(translated, expected, strict=True)]
            area = values[3][0]
            area_error = abs(area/areas[name]-1)
            compared[name] = {"force_moment_at_reference": translated, "expected": expected,
                              "error": error, "native_area_mm2": area, "relative_area_error": area_error,
                              "pass": within(error, expected) and area > 0 and area_error <= GATES["relative_area"]}
        opposed = [a+b for a, b in zip(compared["LOWER_CUT"]["force_moment_at_reference"],
                                      compared["UPPER_CUT"]["force_moment_at_reference"], strict=True)]
        rows.append({"sharing": case["sharing"], "axis": case["axis"], "sections": compared,
                     "opposed_residual": opposed, "fixture": fixed,
                     "pass": fixed["pass"] and all(v["pass"] for v in compared.values()) and within(opposed, reference)})
    return {"rows": rows, "gates": GATES, "pass": all(r["pass"] for r in rows),
            "qualified_for_design": False}


def compare_meshes(coarse, fine):
    if len(coarse["rows"]) != 9 or len(fine["rows"]) != 9:
        raise ValueError("Two complete nine-case reports required")
    checks, compliance = [], []
    for a, b in zip(coarse["rows"], fine["rows"], strict=True):
        if (a["sharing"], a["axis"]) != (b["sharing"], b["axis"]):
            raise ValueError("Unmatched mesh cases")
        ca, cb = (r["fixture"]["unit_load_compliance_mm_per_n"] for r in (a, b))
        if not all(math.isfinite(v) and v > 0 for v in (ca, cb)):
            raise ValueError("Positive finite fixture compliance required")
        change = abs(cb/ca-1)
        compliance.append({"sharing": a["sharing"], "axis": a["axis"],
                           "relative_change": change, "pass": change <= profile.GATES["relative_mesh_compliance"]})
        for name in ("LOWER_CUT", "UPPER_CUT"):
            x, y = a["sections"][name], b["sections"][name]
            error = [v-u for u, v in zip(x["force_moment_at_reference"], y["force_moment_at_reference"], strict=True)]
            checks.append({"sharing": a["sharing"], "axis": a["axis"], "side": name,
                           "difference": error, "pass": within(error, x["expected"]) and within(error, y["expected"])})
    return {"checks": checks, "fixture_compliance": compliance,
            "pass": coarse["pass"] and fine["pass"] and all(c["pass"] for c in checks+compliance),
            "qualified_for_design": False}
