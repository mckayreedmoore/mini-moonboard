"""Strict offline reader for the bounded CCXCAP sidecar stream."""
from __future__ import annotations

from collections import defaultdict
import json
import math
import re
from pathlib import Path
from typing import Any

SCHEMA = "ccx223_bounded_contact_capture/v1"
HASH = re.compile(r"^[0-9a-f]{64}$")
CAPTURE_CAP = 134_217_728
MAX_NINTPOINT = 999_999
MAX_CANDIDATES_PER_GENERATION = 250_000
MAX_LINE = 2048


class CaptureError(ValueError):
    pass


def _fail(message: str) -> None:
    raise CaptureError(message)


def _int(row: list[str], i: int, where: str) -> int:
    try:
        value = int(row[i], 10)
    except (IndexError, ValueError):
        _fail(f"{where}: invalid integer field {i}")
    return value


def _num(token: str, where: str, allow_na: bool = False) -> float | None:
    if token == "NA" and allow_na:
        return None
    if token in {"NA", "NaN", "nan", "Inf", "-Inf", "+Inf", "infinity", "-infinity"}:
        _fail(f"{where}: unavailable/nonfinite value is not permitted here")
    try:
        value = float(token)
    except ValueError:
        _fail(f"{where}: invalid numeric token {token!r}")
    if not math.isfinite(value):
        _fail(f"{where}: nonfinite value")
    return value


def _expect_fields(row: list[str], count: int, where: str) -> None:
    if len(row) != count:
        _fail(f"{where}: expected {count} columns, got {len(row)}")


def linear_penalty_point(area: float, stiffness: float, gap: float,
                         normal: tuple[float, float, float], kscale: float = 1.0,
                         energy_enabled: bool = True) -> dict[str, Any]:
    """Pinned compression-only linear law convention for offline oracle checks."""
    if not all(math.isfinite(x) for x in (area, stiffness, gap, *normal, kscale)):
        _fail("analytic point law received nonfinite input")
    if area < 0 or stiffness < 0 or kscale <= 0:
        _fail("analytic point law received invalid area, K, or scale")
    pressure = -stiffness * gap / kscale
    force = tuple(-area * pressure * n for n in normal)
    energy = area * stiffness * gap * gap / (2.0 * kscale) if energy_enabled else None
    return {"pressure": pressure, "force": force, "energy": energy}


def _latest_map_by_tie(rows: list[list[str]], gen: int) -> dict[int, dict[str, Any]]:
    grouped: dict[int, list[tuple[int, list[str]]]] = defaultdict(list)
    for row in rows:
        if _int(row, 1, "MAP_SUMMARY") == gen:
            grouped[_int(row, 6, "MAP_SUMMARY")].append((_int(row, 7, "MAP_SUMMARY"), row))
    out: dict[int, dict[str, Any]] = {}
    for tie, vals in grouped.items():
        passno, row = max(vals, key=lambda p: p[0])
        out[tie] = {"pass": passno, "candidates": _int(row, 11, "MAP_SUMMARY"),
                    "mapped": _int(row, 12, "MAP_SUMMARY"),
                    "unmapped": _int(row, 13, "MAP_SUMMARY"),
                    "generated": _int(row, 14, "MAP_SUMMARY"),
                    "excluded": _int(row, 15, "MAP_SUMMARY")}
    return out


def check_capture_size(size: int, cap: int = CAPTURE_CAP) -> None:
    if size < 0 or size > cap:
        _fail("capture byte cap exceeded")


def validate_capture(data: bytes | str, expected: dict[str, Any]) -> dict[str, Any]:
    """Validate identities, full visited face spans, summaries, joins and footer.

    The parser treats FNV state/key tokens as auxiliary identifiers. The capture
    producer emits an exact binary ``memcmp`` equality result for state joins;
    no digest is accepted as proof of equality by itself.
    """
    configured_cap = int(expected.get("capture_byte_cap", CAPTURE_CAP))
    if configured_cap < 1 or configured_cap > CAPTURE_CAP:
        _fail("expected capture byte cap is outside compiled ceiling")
    if isinstance(data, bytes):
        check_capture_size(len(data), configured_cap)
        try:
            text = data.decode("utf-8", errors="strict")
        except UnicodeDecodeError as exc:
            _fail(f"capture is not UTF-8: {exc}")
    else:
        text = data
    raw = text.encode("utf-8")
    if not raw:
        _fail("capture is empty or exceeds configured byte cap")
    check_capture_size(len(raw), configured_cap)
    if not text.endswith("\n"):
        _fail("capture lacks final LF")
    lines = text.splitlines(keepends=True)
    if any(len(line.encode("utf-8")) > MAX_LINE for line in lines):
        _fail("capture record exceeds per-line cap")
    rows = [line[:-1].split("\t") for line in lines]
    if len(rows) < 2 or rows[0] != ["CCXCAP", "1"]:
        _fail("missing capture header")
    if sum(row[0] == "CCXCAP" for row in rows) != 1 or rows[1][0] != "RUN_BEGIN":
        _fail("capture needs one leading CCXCAP row followed by RUN_BEGIN")
    if rows[-1][0] != "RUN_END":
        _fail("missing terminal RUN_END")
    if sum(row[0] == "RUN_BEGIN" for row in rows) != 1 or sum(row[0] == "RUN_END" for row in rows) != 1:
        _fail("capture needs exactly one RUN_BEGIN and RUN_END")

    counts = {"GEN_BEGIN": 14, "FACE": 10, "MAP_SUMMARY": 52, "GEN_END": 10,
              "TRIAL_SUMMARY": 23, "STATE_CORRECTED": 8, "STATE_JOIN": 15,
              "ITERATION_LINK": 13, "RUN_END": 10}
    known = {"CCXCAP", "RUN_BEGIN", *counts.keys()}
    for n, row in enumerate(rows, 1):
        if not row or row[0] not in known:
            _fail(f"record {n}: unknown record type")
        if row[0] in counts:
            _expect_fields(row, counts[row[0]], f"record {n} {row[0]}")
    _expect_fields(rows[1], 13, "RUN_BEGIN")
    begin = rows[1]
    if _int(begin, 1, "RUN_BEGIN") != 1:
        _fail("unsupported capture schema version")
    for i, name in zip(range(2, 9), ("input", "include closure", "source archive", "patch", "binary", "pair roster", "face roster")):
        if not HASH.fullmatch(begin[i]):
            _fail(f"RUN_BEGIN: invalid {name} hash")
    run_cap = _int(begin, 9, "RUN_BEGIN")
    ties = _int(begin, 10, "RUN_BEGIN")
    total_faces = _int(begin, 11, "RUN_BEGIN")
    if run_cap != configured_cap:
        _fail("RUN_BEGIN byte cap differs from expected contract")
    if _int(begin, 12, "RUN_BEGIN") != 1:
        _fail("RUN_BEGIN has invalid provenance binding")
    expected_bindings = expected.get("run_bindings")
    binding_fields = ("input_sha256", "include_closure_sha256", "source_archive_sha256",
                      "patch_sha256", "binary_sha256", "pair_roster_sha256", "face_roster_sha256")
    if not isinstance(expected_bindings, dict) or any(
            not HASH.fullmatch(str(expected_bindings.get(key, ""))) for key in binding_fields):
        _fail("expected run provenance binding is incomplete")
    if [begin[i] for i in range(2, 9)] != [expected_bindings[key] for key in binding_fields]:
        _fail("RUN_BEGIN provenance differs from the frozen expected bindings")
    expected_by_tie = {int(k): int(v) for k, v in expected["face_count_by_tie"].items()}
    expected_face_ids_raw = expected.get("face_ids_by_tie")
    if not isinstance(expected_face_ids_raw, dict):
        _fail("expected exact face roster is missing")
    expected_face_ids = {int(k): [int(x) for x in v]
                         for k, v in expected_face_ids_raw.items()}
    if (expected.get("tie_count") != ties or set(expected_by_tie) != set(range(1,ties+1))
            or sum(expected_by_tie.values()) != total_faces
            or set(expected_face_ids) != set(range(1,ties+1))
            or any(len(expected_face_ids[t]) != expected_by_tie[t]
                   or len(set(expected_face_ids[t])) != expected_by_tie[t]
                   for t in expected_by_tie)):
        _fail("RUN_BEGIN tie/face census disagrees with frozen expectation")

    by_type: dict[str, list[list[str]]] = defaultdict(list)
    for row in rows[2:]:
        by_type[row[0]].append(row)
    gens: dict[int, list[str]] = {}
    gen_ends: dict[int, list[str]] = {}
    for row in by_type["GEN_BEGIN"]:
        gen = _int(row, 1, "GEN_BEGIN")
        if gen in gens or gen != len(gens) + 1:
            _fail("generation identity is duplicated or nonsequential")
        gens[gen] = row
        if _int(row, 11, "GEN_BEGIN") != 1:
            _fail(f"generation {gen}: nonfinite state snapshot")
        if not re.fullmatch(r"[0-9a-f]{16}", row[10]) or not re.fullmatch(r"[0-9a-f]{16}", row[13]):
            _fail(f"generation {gen}: invalid auxiliary state token")
        if min(_int(row, i, "GEN_BEGIN") for i in (2, 3, 4, 5)) < 1:
            _fail(f"generation {gen}: invalid step/increment/attempt/iteration identity")
        nintpoint = _int(row, 6, "GEN_BEGIN")
        state_n = _int(row, 8, "GEN_BEGIN")
        if nintpoint < 0 or nintpoint > MAX_NINTPOINT or state_n < 0 or state_n > 1_000_000:
            _fail(f"generation {gen}: face-point or state cap exceeded")
    for row in by_type["GEN_END"]:
        gen = _int(row, 1, "GEN_END")
        if gen in gen_ends or gen not in gens:
            _fail("orphan or duplicate generation end")
        gen_ends[gen] = row
        if _int(row, 9, "GEN_END") != 1:
            _fail(f"generation {gen}: incomplete map sweep")
    if set(gens) != set(gen_ends) or not gens:
        _fail("generation begin/end coverage is incomplete")

    faces_by_gen_pass: dict[tuple[int, int], list[list[str]]] = defaultdict(list)
    for row in by_type["FACE"]:
        gen = _int(row, 1, "FACE")
        tie, passno = _int(row, 2, "FACE"), _int(row, 3, "FACE")
        faceord, face = _int(row, 4, "FACE"), _int(row, 5, "FACE")
        start, end, span, status = (_int(row, i, "FACE") for i in range(6, 10))
        if gen not in gens or tie < 1 or tie > ties or passno not in (1, 2):
            _fail("FACE record has invalid generation, tie or pass identity")
        if faceord < 1 or face <= 0 or end < start or end - start != span or status not in (0, 1):
            _fail("FACE record has invalid source fields")
        roster = expected_face_ids[tie]
        if faceord > len(roster) or face != roster[faceord - 1]:
            _fail("FACE encoded identity differs from the exact frozen pair roster")
        faces_by_gen_pass[(gen, passno)].append(row)

    maps_by_gen: dict[int, list[list[str]]] = defaultdict(list)
    candidates_by_gen: dict[int, int] = defaultdict(int)
    map_seen: set[tuple[int, int, int]] = set()
    reason_fields = range(16, 25)
    for row in by_type["MAP_SUMMARY"]:
        gen, tie, passno = _int(row, 1, "MAP_SUMMARY"), _int(row, 6, "MAP_SUMMARY"), _int(row, 7, "MAP_SUMMARY")
        key = (gen, tie, passno)
        if gen not in gens or tie < 1 or tie > ties or passno not in (1, 2) or key in map_seen:
            _fail("MAP_SUMMARY has invalid or duplicate identity")
        if tuple(_int(row, i, "MAP_SUMMARY") for i in (2, 3, 4, 5)) != tuple(
                _int(gens[gen], i, "GEN_BEGIN") for i in (2, 3, 4, 5)):
            _fail("MAP_SUMMARY identity differs from generation sweep")
        map_seen.add(key);maps_by_gen[gen].append(row)
        faces = _int(row, 8, "MAP_SUMMARY");zero = _int(row, 9, "MAP_SUMMARY")
        span = _int(row, 10, "MAP_SUMMARY");candidates = _int(row, 11, "MAP_SUMMARY")
        candidates_by_gen[gen] += candidates
        if candidates_by_gen[gen] > MAX_CANDIDATES_PER_GENERATION:
            _fail(f"generation {gen}: combined pass candidate cap exceeded")
        mapped = _int(row, 12, "MAP_SUMMARY");unmapped = _int(row, 13, "MAP_SUMMARY")
        generated = _int(row, 14, "MAP_SUMMARY");excluded = _int(row, 15, "MAP_SUMMARY")
        reasons = [_int(row, i, "MAP_SUMMARY") for i in reason_fields]
        if min(faces, zero, span, candidates, mapped, unmapped, generated, excluded, *reasons) < 0:
            _fail("MAP_SUMMARY contains a negative count")
        if candidates != mapped + unmapped or mapped != generated + excluded:
            _fail("MAP_SUMMARY candidate partition does not conserve")
        if sum(reasons) != candidates or reasons[8] != 0:
            _fail("MAP_SUMMARY reason histogram does not conserve or has UNCLASSIFIED rows")
        if (reasons[0] != generated or reasons[1] != unmapped or reasons[3] != 0
                or reasons[4] != 0
                or sum(reasons[2:8]) != excluded):
            _fail("MAP_SUMMARY source reasons do not match outcomes or deterministic-contact policy")
        if _int(row, 47, "MAP_SUMMARY") + _int(row, 48, "MAP_SUMMARY") != mapped:
            _fail("MAP_SUMMARY law counts do not cover mapped candidates")
        if _int(row, 49, "MAP_SUMMARY") != 0 or _int(row, 51, "MAP_SUMMARY") != 0:
            _fail("MAP_SUMMARY duplicate or nonfinite candidate")
        if mapped:
            for i in (25, 28, 31, 34, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46):
                _num(row[i], f"MAP_SUMMARY field {i}")
        else:
            for i in (25, 28, 31, 34, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46):
                _num(row[i], f"MAP_SUMMARY field {i}", allow_na=True)

    # Pass 1 is the complete source-wide census. The native generator may
    # enter pass 2 only for ties carrying prior contact; those rows are an
    # observed subset, checked face-for-face against pass 1 rather than
    # mistaken for another complete global offset range.
    for gen, begin_row in gens.items():
        nintpoint = _int(begin_row, 6, "GEN_BEGIN")
        if gen == 1 and _int(begin_row,7,"GEN_BEGIN") != 0:
            _fail("first generation unexpectedly reports previous point rows")
        if gen > 1:
            previous_end=gen_ends.get(gen-1)
            if previous_end is None or _int(begin_row,7,"GEN_BEGIN") != _int(previous_end,3,"GEN_END"):
                _fail(f"generation {gen}: previous point-row census differs from prior sweep")
        passnos = sorted(p for (g, p), vals in faces_by_gen_pass.items() if g == gen and vals)
        if not passnos or passnos[0] != 1 or any(p not in (1, 2) for p in passnos):
            _fail(f"generation {gen}: required full pass 1 census is missing")

        face_total = span_total = point_total = 0
        pass1span = 0
        pass1_lookup: dict[tuple[int, int], tuple[int, int, int, int, int]] = {}
        pass1_rows = faces_by_gen_pass[(gen, 1)]
        if len(pass1_rows) != total_faces:
            _fail(f"generation {gen} pass 1: full face roster count mismatch")
        cursor = _int(pass1_rows[0], 6, "FACE")
        first_offset = cursor
        seen_per_tie: dict[int, int] = defaultdict(int)
        last_tie, last_ord = 0, 0
        for face_row in pass1_rows:
            tie, ordinal = _int(face_row, 2, "FACE"), _int(face_row, 4, "FACE")
            start, end, span, status = (_int(face_row, i, "FACE") for i in (6, 7, 8, 9))
            if start != cursor:
                _fail(f"generation {gen} pass 1: global face offsets are not contiguous")
            cursor = end
            seen_per_tie[tie] += 1
            if tie < last_tie or (tie == last_tie and ordinal != last_ord + 1) or (tie > last_tie and ordinal != 1):
                _fail(f"generation {gen} pass 1: tie/face roster order or ordinal gap")
            last_tie, last_ord = tie, ordinal
            if status not in (0, 1):
                _fail("invalid live/dead face status")
            pass1_lookup[(tie, ordinal)] = (_int(face_row, 5, "FACE"), start, end, span, status)
            pass1span += span
        if seen_per_tie != expected_by_tie:
            _fail(f"generation {gen} pass 1: complete per-tie face census differs")
        if pass1span != nintpoint or cursor - first_offset != nintpoint:
            _fail(f"generation {gen} pass 1: global offsets do not cover nintpoint")

        rows_by_pass_tie: dict[int, dict[int, list[list[str]]]] = defaultdict(lambda: defaultdict(list))
        for passno in passnos:
            for face_row in faces_by_gen_pass[(gen, passno)]:
                rows_by_pass_tie[passno][_int(face_row, 2, "FACE")].append(face_row)
        expected_map_keys: set[tuple[int, int, int]] = set()
        for passno in passnos:
            ties_seen = sorted(rows_by_pass_tie[passno])
            if passno == 1 and ties_seen != list(range(1, ties + 1)):
                _fail(f"generation {gen} pass 1: not every expected tie was visited")
            if passno == 2 and any(tie < 1 or tie > ties for tie in ties_seen):
                _fail(f"generation {gen} pass 2: tie outside expected roster")
            pass_span = pass_live_span = 0
            for tie in ties_seen:
                observed = rows_by_pass_tie[passno][tie]
                if len(observed) != expected_by_tie[tie]:
                    _fail(f"generation {gen} pass {passno} tie {tie}: partial face roster")
                previous_end = None
                for ordinal, face_row in enumerate(observed, 1):
                    actual_tie, actual_ord = _int(face_row, 2, "FACE"), _int(face_row, 4, "FACE")
                    face, start, end, span, status = (_int(face_row, i, "FACE") for i in (5, 6, 7, 8, 9))
                    if actual_tie != tie or actual_ord != ordinal:
                        _fail(f"generation {gen} pass {passno} tie {tie}: face order mismatch")
                    if previous_end is not None and start != previous_end:
                        _fail(f"generation {gen} pass {passno} tie {tie}: tie-local offsets are not contiguous")
                    previous_end = end
                    pass_span += span
                    if status == 1:
                        pass_live_span += span
                    if passno == 2 and pass1_lookup.get((tie, ordinal)) != (face, start, end, span, status):
                        _fail(f"generation {gen} pass 2 tie {tie}: face identity/offset differs from pass 1")
                if passno == 2:
                    base_rows = rows_by_pass_tie[1][tie]
                    if observed[0][6] != base_rows[0][6] or observed[-1][7] != base_rows[-1][7]:
                        _fail(f"generation {gen} pass 2 tie {tie}: source-wide offset interval differs from pass 1")
                key = (gen, tie, passno)
                expected_map_keys.add(key)
                if key not in map_seen:
                    _fail(f"generation {gen} pass {passno}: missing map summary for observed tie {tie}")
                mrow = next(r for r in maps_by_gen[gen]
                            if _int(r, 6, "MAP_SUMMARY") == tie and _int(r, 7, "MAP_SUMMARY") == passno)
                observed_faces = rows_by_pass_tie[passno][tie]
                face_count = len(observed_faces)
                zero_count = sum(_int(r, 8, "FACE") == 0 for r in observed_faces)
                total_tie_span = sum(_int(r, 8, "FACE") for r in observed_faces)
                live_tie_span = sum(_int(r, 8, "FACE") for r in observed_faces if _int(r, 9, "FACE") == 1)
                if (_int(mrow, 8, "MAP_SUMMARY") != face_count
                        or _int(mrow, 9, "MAP_SUMMARY") != zero_count
                        or _int(mrow, 10, "MAP_SUMMARY") != total_tie_span):
                    _fail(f"generation {gen} tie {tie} pass {passno}: face summary differs")
                if _int(mrow, 11, "MAP_SUMMARY") != live_tie_span:
                    _fail(f"generation {gen} tie {tie} pass {passno}: candidate count differs from live source span")
                point_total += _int(mrow, 11, "MAP_SUMMARY")
                face_total += face_count
                span_total += total_tie_span
            if passno == 1 and pass_span != nintpoint:
                _fail(f"generation {gen} pass 1: face spans differ from nintpoint")
            if passno == 2 and (pass_span > nintpoint or pass_live_span > pass_span):
                _fail(f"generation {gen} pass 2: selected tie spans exceed source-wide range")
        observed_map_keys = {(gen, _int(r, 6, "MAP_SUMMARY"), _int(r, 7, "MAP_SUMMARY"))
                             for r in maps_by_gen[gen]}
        if observed_map_keys != expected_map_keys:
            _fail(f"generation {gen}: map summaries do not exactly cover observed face-pass ties")
        end = gen_ends[gen]
        if (_int(end, 2, "GEN_END") != face_total
                or _int(end, 3, "GEN_END") != point_total
                or _int(end, 4, "GEN_END") != nintpoint
                or _int(end, 5, "GEN_END") != face_total
                or _int(end, 6, "GEN_END") != span_total):
            _fail(f"generation {gen}: GEN_END counters disagree with full/optional-pass records")

    trials_by_gen: dict[int, dict[int,list[str]]] = defaultdict(dict)
    for row in by_type["TRIAL_SUMMARY"]:
        gen,tie=_int(row,1,"TRIAL_SUMMARY"),_int(row,6,"TRIAL_SUMMARY")
        if gen not in gens or tie < 1 or tie > ties or tie in trials_by_gen[gen]:
            _fail("TRIAL_SUMMARY invalid or duplicate identity")
        if tuple(_int(row,i,"TRIAL_SUMMARY") for i in (2,3,4,5)) != tuple(
                _int(gens[gen],i,"GEN_BEGIN") for i in (2,3,4,5)):
            _fail("TRIAL_SUMMARY identity differs from generation sweep")
        trials_by_gen[gen][tie]=row
        expected_gen = _int(row,7,"TRIAL_SUMMARY");count=_int(row,8,"TRIAL_SUMMARY")
        unjoined,wronglaw,force_rows,energy_rows=(_int(row,i,"TRIAL_SUMMARY") for i in (9,10,11,12))
        if min(expected_gen,count,unjoined,wronglaw,force_rows,energy_rows)<0 or count!=expected_gen or unjoined:
            _fail("TRIAL_SUMMARY count mismatch or unjoined trial")
        if _int(row,22,"TRIAL_SUMMARY") != 1:
            _fail("TRIAL_SUMMARY expected generated count did not match trial count")
        if force_rows == count and wronglaw == 0 and count > 0:
            for i in (13,14,15,16):_num(row[i],f"TRIAL_SUMMARY force field {i}")
        else:
            for i in (13,14,15,16):
                if row[i] != "NA":_fail("incomplete force aggregate was reported as a number")
        nener = _int(row,21,"TRIAL_SUMMARY")
        if nener not in (0, 1):
            _fail("TRIAL_SUMMARY has unsupported energy mode")
        if nener == 1:
            if count == 0 or energy_rows != count:
                _fail("stored energy is unavailable or incomplete when nener==1")
            _num(row[17],"TRIAL_SUMMARY energy")
        elif energy_rows != 0 or row[17] != "NA":
            _fail("energy rows/value are present while nener==0")
        if count > 0 and (force_rows != count or wronglaw or unjoined):
            _fail("expected force resultant is unavailable or incomplete")
        _num(row[18],"TRIAL_SUMMARY minimum gap");_num(row[19],"TRIAL_SUMMARY maximum gap")
        if _int(row,20,"TRIAL_SUMMARY")<0: _fail("negative positive-gap trial count")

    # Trial rows must match generated points on each tie's latest map pass.
    for gen in gens:
        latest = _latest_map_by_tie(by_type["MAP_SUMMARY"], gen)
        expected_trial_ties={tie for tie,info in latest.items() if info["generated"]>0}
        if set(trials_by_gen.get(gen,{})) != expected_trial_ties:
            _fail(f"generation {gen}: TRIAL_SUMMARY tie coverage differs from generated map")
        for tie in expected_trial_ties:
            if _int(trials_by_gen[gen][tie],7,"TRIAL_SUMMARY") != latest[tie]["generated"]:
                _fail(f"generation {gen} tie {tie}: old spring count differs from generated map")
            if expected.get("require_linear_law") and _int(next(
                r for r in maps_by_gen[gen] if _int(r,6,"MAP_SUMMARY")==tie and _int(r,7,"MAP_SUMMARY")==latest[tie]["pass"]),47,"MAP_SUMMARY") != latest[tie]["mapped"]:
                _fail("known-answer contract requires law id 2 for every mapped candidate")

    corrected: dict[int,list[str]]={}
    for row in by_type["STATE_CORRECTED"]:
        gen=_int(row,1,"STATE_CORRECTED")
        if gen not in gens or gen in corrected:_fail("orphan/duplicate corrected-state snapshot")
        if _int(row,7,"STATE_CORRECTED")!=1:_fail("nonfinite corrected-state snapshot")
        begin_row=gens[gen]
        if tuple(_int(row,i,"STATE_CORRECTED") for i in (2,3,4,5)) != tuple(
                _int(begin_row,i,"GEN_BEGIN") for i in (2,3,4,5)):
            _fail("corrected-state identity differs from generation sweep")
        if not re.fullmatch(r"[0-9a-f]{16}",row[6]):_fail("invalid corrected-state token")
        corrected[gen]=row
    if set(corrected) != set(gens):_fail("corrected-state snapshot coverage differs from contact sweeps")
    joins: dict[int,dict[int,list[str]]]=defaultdict(dict)
    for row in by_type["STATE_JOIN"]:
        gen,tie=_int(row,1,"STATE_JOIN"),_int(row,6,"STATE_JOIN")
        if gen not in gens or tie<1 or tie>ties or tie in joins[gen]:_fail("STATE_JOIN duplicate/invalid identity")
        joins[gen][tie]=row
        begin_row=gens[gen]
        if tuple(_int(row,i,"STATE_JOIN") for i in (2,3,4,5)) != tuple(
                _int(begin_row,i,"GEN_BEGIN") for i in (2,3,4,5)):
            _fail("STATE_JOIN identity differs from generation sweep")
        same_state=_int(begin_row,12,"GEN_BEGIN");adjacent=(_int(begin_row,9,"GEN_BEGIN")+1==_int(begin_row,5,"GEN_BEGIN"))
        if _int(row,7,"STATE_JOIN")!=same_state or _int(row,8,"STATE_JOIN")!=int(adjacent):_fail("STATE_JOIN disagrees with exact state/iteration flags")
        measures=[_int(row,i,"STATE_JOIN") for i in range(9,15)]
        if any(value < 0 for value in measures):
            _fail("STATE_JOIN contains a negative count")
        if not (same_state and adjacent) and any(measures):_fail("ineligible states were pointwise joined")
        if same_state and begin_row[10] != begin_row[13]:
            _fail("equal-state marker has inconsistent auxiliary tokens")
        if same_state:
            previous=corrected.get(gen-1)
            if previous is None or previous[6] != begin_row[10]:
                _fail("exact-state marker does not match the preceding corrected-state token")
            previous_begin=gens.get(gen-1)
            if previous_begin is None or tuple(_int(previous_begin,i,"GEN_BEGIN") for i in (2,3,4)) != tuple(
                    _int(begin_row,i,"GEN_BEGIN") for i in (2,3,4)):
                _fail("exact-state marker crosses a step, increment, or attempt boundary")
    for gen in gens:
        if set(joins[gen]) != set(range(1,ties+1)):_fail(f"generation {gen}: state-link tie coverage incomplete")
    for gen in range(2,len(gens)+1):
        begin_row=gens[gen]
        if _int(begin_row,9,"GEN_BEGIN") != _int(corrected[gen-1],5,"STATE_CORRECTED"):
            _fail(f"generation {gen}: previous corrected iteration identity differs")
        eligible=(_int(begin_row,12,"GEN_BEGIN")==1 and _int(begin_row,9,"GEN_BEGIN")+1==_int(begin_row,5,"GEN_BEGIN"))
        if not eligible:continue
        old=_latest_map_by_tie(by_type["MAP_SUMMARY"],gen-1)
        new=_latest_map_by_tie(by_type["MAP_SUMMARY"],gen)
        for tie in range(1,ties+1):
            jrow=joins[gen][tie]
            same,remap,oldmiss,newmiss=(_int(jrow,i,"STATE_JOIN") for i in (9,10,11,12))
            oldn=old.get(tie,{"candidates":0})["candidates"]
            newn=new.get(tie,{"candidates":0})["candidates"]
            if same+remap+oldmiss!=oldn or same+remap+newmiss!=newn:
                _fail(f"generation {gen} tie {tie}: point identity join does not conserve")
            if _int(jrow,13,"STATE_JOIN")+_int(jrow,14,"STATE_JOIN")>same+remap:
                _fail("status-transition count exceeds identity matches")

    links: dict[int,list[str]]={}
    for row in by_type["ITERATION_LINK"]:
        gen=_int(row,1,"ITERATION_LINK")
        if gen not in gens or gen in links:_fail("orphan/duplicate accepted-state link")
        links[gen]=row
        b=gens[gen]
        for ri,bi in ((2,2),(3,3),(4,4),(5,5)):
            if _int(row,ri,"ITERATION_LINK")!=_int(b,bi,"GEN_BEGIN"):_fail("iteration link identity differs from sweep")
        icntrl,attempt_after,accepted=(_int(row,i,"ITERATION_LINK") for i in (7,6,8))
        captured_attempt=_int(b,4,"GEN_BEGIN")
        if icntrl not in (0,1):_fail("ITERATION_LINK has an unsupported convergence control value")
        if icntrl==0 and attempt_after!=captured_attempt:
            _fail("nonconverged iteration link changes the cutback attempt")
        if icntrl==1 and attempt_after not in (1,captured_attempt+1):
            _fail("converged iteration link has an impossible cutback attempt")
        if accepted != int(icntrl==1 and attempt_after==1):_fail("accepted flag differs from source convergence/cutback convention")
        _num(row[9],"ITERATION_LINK accepted time")
        if accepted and (_int(row,11,"ITERATION_LINK")!=1 or _int(row,12,"ITERATION_LINK")!=1):
            _fail("accepted state lacks complete face/trial capture")
        if gen not in corrected or row[10] != corrected[gen][6]:
            _fail("iteration link token differs from corrected-state snapshot")

    end=rows[-1]
    end_counts=[_int(end,i,"RUN_END") for i in range(1,10)]
    if end_counts[0]!=len(gens) or end_counts[1]!=len(by_type["FACE"]):_fail("RUN_END generation/face totals mismatch")
    if end_counts[2]!=sum(_int(r,11,"MAP_SUMMARY") for r in by_type["MAP_SUMMARY"]):_fail("RUN_END point total mismatch")
    if end_counts[3]!=sum(_int(r,8,"TRIAL_SUMMARY") for r in by_type["TRIAL_SUMMARY"]):_fail("RUN_END trial total mismatch")
    if end_counts[4]!=len(links):_fail("RUN_END accepted-link total mismatch")
    if set(links) != set(gens):_fail("every contact generation must link to its iteration outcome")
    footer_bytes=len(lines[-1].encode("utf-8"))
    if end_counts[5] != len(raw)-footer_bytes:_fail("RUN_END byte count differs from independent file scan")
    if end_counts[6]!=0 or end_counts[7]!=0 or end_counts[8]!=1:_fail("RUN_END indicates overflow, write error, or incomplete capture")
    if len(gens)>64 or len(by_type["FACE"])>2*64*13_001:
        _fail("capture face/sweep count exceeds frozen caps")
    positions_by_gen: dict[int,dict[str,list[int]]]=defaultdict(lambda:defaultdict(list))
    for pos,row in enumerate(rows):
        if row[0] in {"GEN_BEGIN","FACE","MAP_SUMMARY","STATE_JOIN","GEN_END",
                      "STATE_CORRECTED","TRIAL_SUMMARY","ITERATION_LINK"}:
            positions_by_gen[_int(row,1,row[0])][row[0]].append(pos)
    for gen in gens:
        p=positions_by_gen[gen]
        bpos=p["GEN_BEGIN"][0]; epos=p["GEN_END"][0]
        cpos=p["STATE_CORRECTED"][0]; lpos=p["ITERATION_LINK"][0]
        if not (bpos < min(p["FACE"]) <= max(p["FACE"]) < min(p["MAP_SUMMARY"])
                <= max(p["MAP_SUMMARY"]) < min(p["STATE_JOIN"]) <= max(p["STATE_JOIN"])
                < epos < cpos < lpos):
            _fail(f"generation {gen}: events are out of source order")
        if p["TRIAL_SUMMARY"] and not cpos < min(p["TRIAL_SUMMARY"]) <= max(p["TRIAL_SUMMARY"]) < lpos:
            _fail(f"generation {gen}: TRIAL_SUMMARY is outside corrected-state/iteration interval")
        if gen < max(gens) and lpos > positions_by_gen[gen+1]["GEN_BEGIN"][0]:
            _fail(f"generation {gen}: iteration outcome occurs after the next contact sweep")
    accepted_states=[{
        "generation": gen,
        "step": _int(row,2,"ITERATION_LINK"),
        "increment": _int(row,3,"ITERATION_LINK"),
        "attempt": _int(row,4,"ITERATION_LINK"),
        "iteration": _int(row,5,"ITERATION_LINK"),
        "time": _num(row[9],"ITERATION_LINK accepted time"),
    } for gen,row in sorted(links.items()) if _int(row,8,"ITERATION_LINK")==1]
    if expected.get("minimum_accepted_links",0)>len(accepted_states):_fail("too few accepted iteration links")
    trial_summaries=[]
    for row in by_type["TRIAL_SUMMARY"]:
        trial_summaries.append({
            "generation":_int(row,1,"TRIAL_SUMMARY"),"step":_int(row,2,"TRIAL_SUMMARY"),
            "increment":_int(row,3,"TRIAL_SUMMARY"),"attempt":_int(row,4,"TRIAL_SUMMARY"),
            "iteration":_int(row,5,"TRIAL_SUMMARY"),"tie":_int(row,6,"TRIAL_SUMMARY"),
            "expected_generated":_int(row,7,"TRIAL_SUMMARY"),"trial_count":_int(row,8,"TRIAL_SUMMARY"),
            "force_on_slave_N":tuple(_num(row[i],"TRIAL_SUMMARY force") for i in (13,14,15))
                if row[13] != "NA" else None,
            "sum_abs_point_force_N":_num(row[16],"TRIAL_SUMMARY absolute force") if row[16] != "NA" else None,
            "stored_energy_N_mm":_num(row[17],"TRIAL_SUMMARY energy") if row[17] != "NA" else None,
            "energy_enabled":_int(row,21,"TRIAL_SUMMARY")==1,
        })
    return {"status":"PASS_CAPTURE_STRUCTURE","schema":SCHEMA,"generation_count":len(gens),
            "face_rows":len(by_type["FACE"]),"point_candidates":end_counts[2],
            "trial_rows":end_counts[3],"iteration_links":len(links),"trial_summaries":trial_summaries,
            "accepted_states":accepted_states,"native_run_performed":False}


def load_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError,json.JSONDecodeError) as exc:
        _fail(f"cannot load JSON {path}: {exc}")
