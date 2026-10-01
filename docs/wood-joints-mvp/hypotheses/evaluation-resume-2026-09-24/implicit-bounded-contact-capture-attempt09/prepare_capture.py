#!/usr/bin/env python3
"""Reproduce an additions-only CalculiX 2.23 capture patch."""
from __future__ import annotations

import difflib
import hashlib
import json
import re
import tarfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ARCHIVE = HERE / "build/context/source.tar.bz2"
PATCH = HERE / "build/context/capture.patch"
SINK = HERE / "capture-sink.inc"
META = HERE / "build/context/patch-preparation.json"
TARGETS = {
    "CalculiX/ccx_2.23/src/nonlingeo.c": "nonlingeo.c",
    "CalculiX/ccx_2.23/src/gencontelem_f2f.f": "gencontelem_f2f.f",
    "CalculiX/ccx_2.23/src/ccx_2.23.c": "ccx_2.23.c",
}
SOURCE_READS = ("CalculiX/ccx_2.23/src/contact.c",)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def after_once(source: str, anchor: str, text: str, label: str) -> str:
    n = source.count(anchor)
    if n != 1:
        raise RuntimeError(f"{label}: expected one anchor, found {n}")
    return source.replace(anchor, anchor + text, 1)


def before_once(source: str, anchor: str, text: str, label: str) -> str:
    n = source.count(anchor)
    if n != 1:
        raise RuntimeError(f"{label}: expected one anchor, found {n}")
    return source.replace(anchor, text + anchor, 1)


def load_archive_member(relative: str) -> bytes:
    with tarfile.open(ARCHIVE, "r:bz2") as archive:
        names = {m.name.removeprefix("./"): m for m in archive.getmembers() if m.isfile()}
        member = names.get(relative)
        if member is None:
            raise RuntimeError(f"missing source member {relative}")
        return archive.extractfile(member).read()


def _added_lines(before: str, after: str, label: str) -> list[str]:
    a = before.splitlines(keepends=True)
    b = after.splitlines(keepends=True)
    ops = difflib.SequenceMatcher(a=a, b=b, autojunk=False).get_opcodes()
    if any(tag not in ("equal", "insert") for tag, *_ in ops):
        raise RuntimeError(f"{label}: source delta is not additions-only")
    return [b[j] for tag, _i1, _i2, j1, j2 in ops if tag == "insert" for j in range(j1, j2)]


def _c_code_without_literals_or_comments(line: str) -> str:
    """Blank literals/comments while retaining offsets for statement checks."""
    out = list(line)
    i = 0
    quote: str | None = None
    escaped = False
    while i < len(line):
        if quote:
            if line[i] != "\n":
                out[i] = " "
            if escaped:
                escaped = False
            elif line[i] == "\\":
                escaped = True
            elif line[i] == quote:
                quote = None
            i += 1
            continue
        if line.startswith("//", i):
            for j in range(i, len(line)):
                if line[j] != "\n":
                    out[j] = " "
            break
        if line.startswith("/*", i):
            end = line.find("*/", i + 2)
            stop = len(line) if end < 0 else end + 2
            for j in range(i, stop):
                if line[j] != "\n":
                    out[j] = " "
            i = stop
            continue
        if line[i] in ('"', "'"):
            quote = line[i]
            out[i] = " "
        i += 1
    return "".join(out)


def _validate_c_caller_statement_boundaries(lines: list[str], label: str) -> None:
    """Reject packed statements and any tokens after an added statement."""
    depth = 0
    for raw in lines:
        code = _c_code_without_literals_or_comments(raw.rstrip("\r\n"))
        if "++" in code or "--" in code:
            if not re.fullmatch(r"for\s*\([^;]*;[^;]*;\s*[A-Za-z_]\w*\+\+\s*\)\s*\{?", code.strip()):
                raise RuntimeError(f"{label}: increment/decrement outside allowlisted loop header: {raw.strip()}")
        semicolons: list[int] = []
        for i, char in enumerate(code):
            if char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
                if depth < 0:
                    raise RuntimeError(f"{label}: unbalanced C parentheses: {raw.strip()}")
            elif char == ";" and depth == 0:
                semicolons.append(i)
        if len(semicolons) > 1:
            raise RuntimeError(f"{label}: multiple C statements on one added line: {raw.strip()}")
        if semicolons and code[semicolons[0] + 1:].strip():
            raise RuntimeError(f"{label}: tokens follow an added C statement: {raw.strip()}")
    if depth != 0:
        raise RuntimeError(f"{label}: unbalanced C parentheses in added lines")


def validate_fortran_additions(before: str, after: str) -> None:
    """Allow only capture-local stores/calls in added executable Fortran."""
    lines = _added_lines(before, after, "Fortran executable policy")
    statements: list[str] = []
    current = ""
    for raw in lines:
        line = raw.rstrip("\r\n")
        if not line.strip() or line.lstrip().startswith("!") or line[:1].lower() == "c":
            continue
        if len(line) <= 6:
            continue
        continuation = line[5] not in (" ", "0")
        field = line[6:72].strip()
        if not field:
            continue
        if continuation:
            if not current:
                raise RuntimeError("Fortran insertion begins with an orphan continuation")
            current += " " + field
        else:
            if current:
                statements.append(current)
            current = field
    if current:
        statements.append(current)

    declarations = re.compile(r"^(?:integer|real\*8)\s+[a-z][a-z0-9_,]*$", re.I)
    external = re.compile(r"^external\s+ccxcap_is_active$", re.I)
    local_store = re.compile(r"^(?:if\s*\(.*\)\s*)?wjcap_[a-z0-9_]+\s*=(?!=).*$", re.I)
    call = re.compile(r"^(?:if\s*\(wjcap_active\.eq\.1\)\s*)?call\s+ccxcap_(?:face|point|generation_end)\s*\(.*\)$", re.I)
    if_then = re.compile(r"^if\s*\(.*\)\s*then$", re.I)
    for statement in statements:
        normalized = re.sub(r"\s+", " ", statement.strip())
        if (declarations.fullmatch(normalized) or external.fullmatch(normalized)
                or local_store.fullmatch(normalized) or call.fullmatch(normalized)
                or if_then.fullmatch(normalized) or normalized.lower() == "endif"):
            continue
        raise RuntimeError(f"Fortran executable statement is outside capture allowlist: {normalized}")


def validate_c_capture_additions(before: str, after: str, sink: str, label: str) -> None:
    """Allow only declared capture hooks, bounded local scratch and control flow."""
    suffix = "\n" + sink
    if not after.endswith(suffix):
        raise RuntimeError("capture C sink is not the exact generated file suffix")
    caller = after[:-len(suffix)]
    lines = _added_lines(before, caller, label)
    _validate_c_caller_statement_boundaries(lines, label)
    prototypes = {
        "ITG ccxcap_is_active_(void);",
        "void ccxcap_generation_begin_(ITG*,ITG*,ITG*,ITG*,ITG*,ITG*,double*,ITG*,ITG*,ITG*,ITG*);",
        "void ccxcap_face_(ITG*,ITG*,ITG*,ITG*,ITG*,ITG*,ITG*);",
        "void ccxcap_point_(ITG*,ITG*,ITG*,ITG*,ITG*,ITG*,ITG*,ITG*,ITG*,ITG*,ITG*,double*,double*,double*,double*,double*,double*,double*,double*,double*,double*,double*,double*,double*,double*,double*);",
        "void ccxcap_generation_end_(void);",
        "void ccxcap_trial_(ITG*,ITG*,ITG*,ITG*,ITG*,double*,double*,double*,double*,double*,double*,double*,double*,double*,double*,double*,ITG*,double*);",
        "void ccxcap_trial_end_(void);",
        "void ccxcap_missing_pair_(void);",
        "void ccxcap_corrected_(ITG*,ITG*,ITG*,ITG*,ITG*,ITG*,double*);",
        "void ccxcap_iteration_link_(ITG*,ITG*,ITG*,ITG*,ITG*,double*,double*);",
    }
    allowed_conditions = (
        "if(*mortar==1)", "if(*iexpl<=1&&*mortar==1)",
        "if(*mortar==1&&ccxcap_is_active_())", "if(*ithermal<2)",
        "if(ipkon[wje]<0)", "if(strncmp(&lakon[8*wje],\"ESPRNGC\",7)!=0)",
        "if((wjslot>=itiefac[2*wjt])&&(wjslot<=itiefac[2*wjt+1]))",
        "if(wjpair==0||wjslot<1)",
    )
    assignment = re.compile(r"(?<![=!<>])\b([A-Za-z_]\w*)(?:\s*\[[^\]]+\])?\s*=(?!=)")
    allowed_calls = {"if", "for", "ccxcap_generation_begin_", "ccxcap_is_active_", "ccxcap_corrected_",
                     "ccxcap_missing_pair_", "ccxcap_trial_", "ccxcap_trial_end_",
                     "ccxcap_iteration_link_", "strncmp"}
    for raw in lines:
        line = raw.strip()
        if not line or line.startswith(("/*", "*", "//")):
            continue
        if line in prototypes:
            continue
        if line in {"{", "}", "} else {", "continue;", "break;"}:
            continue
        if line in {"&kscale,nener,ntie,nintpoint);",
                     "&stx[6*mi[0]*wje],&stx[6*mi[0]*wje+1],",
                     "&stx[6*mi[0]*wje+2],&stx[6*mi[0]*wje+3],",
                     "&stx[6*mi[0]*wje+4],&stx[6*mi[0]*wje+5],",
                     "&springarea[2*(wjg-1)],&wjenergy,",
                     "&pmastsurf[6*(wjg-1)+3],&pmastsurf[6*(wjg-1)+4],",
                     "&pmastsurf[6*(wjg-1)+5],&kscale,&reltime);"}:
            continue
        if line.startswith("ITG wje,") or line == "double wjenergy;":
            continue
        if line.startswith("for("):
            if line not in {"for(wje=ne0;wje<*ne;wje++){", "for(wjt=0;wjt<*ntie;wjt++)"}:
                raise RuntimeError(f"C loop outside capture allowlist: {line}")
            continue
        if line.startswith("if("):
            if not any(line.startswith(prefix) for prefix in allowed_conditions):
                raise RuntimeError(f"C conditional outside capture allowlist: {line}")
        for lhs in assignment.findall(line):
            if not lhs.startswith("wj"):
                raise RuntimeError(f"C caller insertion writes outside capture scratch: {lhs}")
        calls = re.findall(r"\b([A-Za-z_]\w*)\s*\(", line)
        if any(name not in allowed_calls for name in calls):
            raise RuntimeError(f"C call outside capture allowlist: {line}")
        if not calls and not line.startswith(("if(", "for(")) and "=" not in line:
            raise RuntimeError(f"C statement outside capture allowlist: {line}")

    # The appended module has a separate, explicit write target set: capture
    # globals and local scratch only. This policy is intentionally independent
    # of the solver's array names and fails closed for any unlisted target.
    sink_lhs = re.compile(r"(?<![=!<>])\b([A-Za-z_]\w*)(?:\s*\[[^\]]+\])?\s*=(?!=)")
    sink_targets = set("""wjcc_bytes wjcc_generation wjcc_run_faces wjcc_run_points
      wjcc_run_trials wjcc_run_links wjcc_expected_faces wjcc_expected_ties
      wjcc_enabled wjcc_overflow wjcc_error wjcc_io_error wjcc_closed wjcc_map_complete
      wjcc_trial_complete wjcc_pending wjcc_pass2_roster_error wjcc_allow_failed_emit
      wjcc_step wjcc_inc wjcc_attempt wjcc_iter
      wjcc_nintpoint wjcc_nener wjcc_ntie wjcc_kscale wjcc_pass_faces
      wjcc_pass1_faces wjcc_pass1_face_n
      wjcc_latest_pass wjcc_prev_latest wjcc_pass_spans wjcc_live_spans
      wjcc_tie_face_start wjcc_tie_face_end wjcc_last_tie wjcc_tie_face_seen
      wjcc_face_rows wjcc_point_rows wjcc_trial_rows wjcc_face_hash
      wjcc_outcome_hash wjcc_offset_base wjcc_offset_next wjcc_offset_initialized
      wjcc_fp wjcc_final_path wjcc_temp_path wjcc_published wjcc_temp_owned
      wjcc_state wjcc_corrected wjcc_state_n wjcc_corrected_n
      wjcc_corr_step wjcc_corr_inc wjcc_corr_attempt wjcc_corr_iter
      wjcc_state_token wjcc_corrected_token wjcc_state_finite
      wjcc_corrected_finite wjcc_prev_equal wjcc_points wjcc_previous
      wjcc_points_n wjcc_points_cap wjcc_previous_n wjcc_key_table
      wjcc_gauss_index wjcc_gauss_n wjcc_map wjcc_trial wjcc_join
      table h p s t slot i n idx tie a cur v end errno value out limit
      path input includes source patch binary pairs faces ef et roster_valid
      x eligible old z span faceord face local igauss valid reason finite master law
      isol rawgap classgap area k initial nx ny nz sxi seta mxi meta px py pz
      kscale totalspan pass1span totalfaces pass1faces ix finite_force fx fy fz pass
      identity accepted control_valid iter_transition attempt_after attempt_transition
      cap previous expected pathlen finalpath templen face_index prior_faces
      ordinal start status prior fp saved close_status footer_complete
      face_roster trial_invalid""".split())
    for lhs in sink_lhs.findall(sink):
        if lhs not in sink_targets:
            raise RuntimeError(f"capture sink assignment target outside bounded-state allowlist: {lhs}")

    for raw in sink.splitlines():
        code = _c_code_without_literals_or_comments(raw)
        for match in re.finditer(r"\+\+|--", code):
            prefix = code[:match.start()].rstrip()
            suffix_code = code[match.end():].lstrip()
            if prefix.endswith("++") or prefix.endswith("--"):
                raise RuntimeError("capture sink contains a chained increment/decrement")
            target_match = re.search(
                r"([A-Za-z_]\w*)(?:\s*\[[^\]]+\])*(?:\s*(?:->|\.)\s*[A-Za-z_]\w*)?$",
                prefix,
            )
            if target_match:
                target = target_match.group(1)
            else:
                target_match = re.match(r"([A-Za-z_]\w*)", suffix_code)
                target = target_match.group(1) if target_match else ""
            if target not in sink_targets:
                raise RuntimeError(f"capture sink increment/decrement target outside bounded-state allowlist: {target or raw.strip()}")


def patch_fortran(source: str) -> str:
    source = after_once(
        source,
        "      implicit none\n",
        "      integer wjcap_faceord,wjcap_valid,wjcap_reason\n"
        "      integer wjcap_master,wjcap_status,wjcap_start,wjcap_end\n"
        "      integer wjcap_law,wjcap_isol,wjcap_active\n"
        "      integer ccxcap_is_active\n"
        "      real*8 wjcap_raw,wjcap_class,wjcap_nx,wjcap_ny,wjcap_nz\n",
        "capture local declarations",
    )

    # Count every runtime face slot, including a dead element and a zero span.
    face_anchor = "            if(ipkon(nelems).lt.0) cycle\n"
    face_block = (
        "            if(wjcap_active.eq.1) then\n"
        "            wjcap_faceord=jj-itiefac(1,i)+1\n"
        "            wjcap_start=islavsurf(2,jj)\n"
        "            wjcap_end=islavsurf(2,jj+1)\n"
        "            wjcap_status=1\n"
        "            if(ipkon(nelems).lt.0) wjcap_status=0\n"
        "            call ccxcap_face(i,iloop,wjcap_faceord,ifaces,\n"
        "     &           wjcap_start,wjcap_end,wjcap_status)\n"
        "            endif\n"
    )
    source = before_once(source, face_anchor, face_block, "face census")

    source = after_once(
        source,
        "      igauss=0\n",
        "      wjcap_active=ccxcap_is_active()\n",
        "one cached activity query per generator invocation",
    )

    source = after_once(
        source,
        "              igauss=indexf+m\n",
        "              if(wjcap_active.eq.1) then\n"
        "              wjcap_valid=0\n"
        "              wjcap_reason=99\n"
        "              wjcap_master=0\n"
        "              wjcap_raw=0.d0\n"
        "              wjcap_class=0.d0\n"
        "              wjcap_nx=0.d0\n"
        "              wjcap_ny=0.d0\n"
        "              wjcap_nz=0.d0\n"
        "              endif\n",
        "point defaults",
    )
    source = before_once(
        source,
        "              if(isol.eq.0) then\n",
        "              if(wjcap_active.eq.1) then\n"
        "                if(isol.eq.0) wjcap_reason=1\n"
        "              endif\n",
        "unmapped reason",
    )
    source = after_once(
        source,
        "                endif\n                nelemm=int(ifacem/10.d0)\n",
        "                if(wjcap_active.eq.1) wjcap_master=ifacem\n",
        "master face identity",
    )
    source = after_once(
        source,
        "                clear=al(1)*xn(1)+al(2)*xn(2)+al(3)*xn(3)\n",
        "                if(wjcap_active.eq.1) then\n"
        "                wjcap_valid=1\n"
        "                wjcap_raw=clear\n"
        "                wjcap_class=clear\n"
        "                wjcap_reason=0\n"
        "                wjcap_nx=xn(1)\n"
        "                wjcap_ny=xn(2)\n"
        "                wjcap_nz=xn(3)\n"
        "                endif\n",
        "mapped gap and normal",
    )

    source = after_once(
        source,
        "                  if((clear.gt.0.d0).and.\n"
        "     &                 (int(elcon(3,1,imat)).ne.4)) then\n",
        "                    if(wjcap_active.eq.1) wjcap_reason=2\n",
        "dynamic positive-clearance filter",
    )
    source = after_once(
        source,
        "                          if(clear.gt.0.d0) then\n",
        "                            if(wjcap_active.eq.1) wjcap_reason=5\n",
        "static positive-clearance filter",
    )
    source = before_once(
        source,
        "                        if(harvest.gt.(1.d0-alea)) isol=0\n",
        "                        if(wjcap_active.eq.1) then\n"
        "                          if(harvest.gt.(1.d0-alea)) wjcap_reason=4\n"
        "                        endif\n",
        "aleatoric filter",
    )
    cutback_condition = (
        "                          if((dsqrt(\n"
        "     &                         xstateini(4,1,ne0+igauss)**2+\n"
        "     &                         xstateini(5,1,ne0+igauss)**2+\n"
        "     &                         xstateini(6,1,ne0+igauss)**2)\n"
        "     &                         .lt.1.d-30).and.\n"
        "     &                         (clear.gt.0.d0)) then\n"
    )
    source = after_once(source, cutback_condition,
                        "                            if(wjcap_active.eq.1) wjcap_reason=6\n",
                        "cutback previous-state filter")
    # Mirror the exact pass-two condition before the original, unchanged
    # filter. This records reason 7 only when that condition is true.
    pass_two_cond = (
        "                      if(dsqrt(xstateini(4,1,ne0+igauss)**2+\n"
        "     &                     xstateini(5,1,ne0+igauss)**2+\n"
        "     &                     xstateini(6,1,ne0+igauss)**2)\n"
        "     &                     .lt.1.d-30) isol=0\n"
    )
    pass_two_probe = (
        "                      if(wjcap_active.eq.1) then\n"
        "                      if(dsqrt(xstateini(4,1,ne0+igauss)**2+\n"
        "     &                     xstateini(5,1,ne0+igauss)**2+\n"
        "     &                     xstateini(6,1,ne0+igauss)**2)\n"
        "     &                     .lt.1.d-30) wjcap_reason=7\n"
        "                      endif\n"
    )
    source = before_once(source, pass_two_cond, pass_two_probe, "pass-two prior-state filter")

    unsupported_skip = (
        "                  if(wjcap_active.eq.1) then\n"
        "                  wjcap_valid=0\n"
        "                  wjcap_reason=99\n"
        "                  wjcap_law=int(elcon(3,1,imat))\n"
        "                  wjcap_isol=isol\n"
        "                  call ccxcap_point(i,iloop,wjcap_faceord,ifaces,m,\n"
        "     &                 igauss,wjcap_valid,wjcap_reason,wjcap_master,\n"
        "     &                 wjcap_law,wjcap_isol,wjcap_raw,wjcap_class,\n"
        "     &                 0.d0,0.d0,0.d0,0.d0,0.d0,0.d0,0.d0,\n"
        "     &                 0.d0,0.d0,0.d0,0.d0,0.d0,0.d0,0.d0,\n"
        "     &                 0.d0)\n"
        "                  endif\n"
    )
    source = before_once(source, "                  cycle\n", unsupported_skip,
                        "unsupported-master skipped candidate")

    point_anchor = "              endif\n!     \n              if(isol.ne.0) then\n"
    point_call = (
        "              if(wjcap_active.eq.1) then\n"
        "              if(wjcap_valid.eq.1.and.isol.eq.0.and.\n"
        "     &             wjcap_reason.eq.0) wjcap_reason=99\n"
        "              if(wjcap_valid.eq.1) wjcap_class=clear\n"
        "              wjcap_law=int(elcon(3,1,imat))\n"
        "              wjcap_isol=isol\n"
        "              call ccxcap_point(i,iloop,wjcap_faceord,ifaces,m,\n"
        "     &             igauss,wjcap_valid,wjcap_reason,wjcap_master,\n"
        "     &             wjcap_law,wjcap_isol,wjcap_raw,wjcap_class,\n"
        "     &             springarea(1,igauss),elcon(2,1,imat),\n"
        "     &             springarea(2,igauss),wjcap_nx,wjcap_ny,\n"
        "     &             wjcap_nz,pslavsurf(1,igauss),\n"
        "     &             pslavsurf(2,igauss),xi,et,p(1),p(2),p(3))\n"
        "              endif\n"
    )
    if source.count(point_anchor) != 1:
        raise RuntimeError("point outcome instrumentation: final isol branch anchor mismatch")
    source = source.replace(
        point_anchor,
        "              endif\n!     \n" + point_call + "              if(isol.ne.0) then\n",
        1,
    )
    source = before_once(source, "      return\n      end\n",
                         "      if(wjcap_active.eq.1) call ccxcap_generation_end()\n",
                         "generation end before return")
    return source


def patch_nonlingeo(source: str) -> str:
    prototypes = (
        "ITG ccxcap_is_active_(void);\n"
        "void ccxcap_generation_begin_(ITG*,ITG*,ITG*,ITG*,ITG*,ITG*,double*,ITG*,ITG*,ITG*,ITG*);\n"
        "void ccxcap_face_(ITG*,ITG*,ITG*,ITG*,ITG*,ITG*,ITG*);\n"
        "void ccxcap_point_(ITG*,ITG*,ITG*,ITG*,ITG*,ITG*,ITG*,ITG*,ITG*,ITG*,ITG*,double*,double*,double*,double*,double*,double*,double*,double*,double*,double*,double*,double*,double*,double*,double*);\n"
        "void ccxcap_generation_end_(void);\n"
        "void ccxcap_trial_(ITG*,ITG*,ITG*,ITG*,ITG*,double*,double*,double*,double*,double*,double*,double*,double*,double*,double*,double*,ITG*,double*);\n"
        "void ccxcap_trial_end_(void);\n"
        "void ccxcap_missing_pair_(void);\n"
        "void ccxcap_corrected_(ITG*,ITG*,ITG*,ITG*,ITG*,ITG*,double*);\n"
        "void ccxcap_iteration_link_(ITG*,ITG*,ITG*,ITG*,ITG*,double*,double*);\n"
    )
    source = after_once(source, '#include "CalculiX.h"\n', prototypes, "C sink prototypes")

    contact_pattern = re.compile(
        r"^([ \t]*)contact\(&ncont,ntie,tieset,nset,set,istartset,iendset,",
        re.MULTILINE,
    )
    matches = list(contact_pattern.finditer(source))
    if len(matches) != 2:
        raise RuntimeError(f"expected two nonlingeo contact call sites, got {len(matches)}")
    def add_generation_begin(match: re.Match[str]) -> str:
        indent = match.group(1)
        return (
            indent + "if(*iexpl<=1&&*mortar==1) ccxcap_generation_begin_(istep,&iinc,&icutb,&iit,nk,&mt,vold,\n"
            + indent + "\t\t\t\t    &kscale,nener,ntie,nintpoint);\n"
            + match.group(0)
        )
    # The first source call initializes the contact state before the nonlinear
    # iteration loop and has no matching accepted-iteration event. Capture the
    # in-loop regeneration only: it is the sweep paired with the subsequent
    # results/corrected-state/trial/convergence hooks below.
    second = matches[1]
    replacement = add_generation_begin(second)
    source = source[:second.start()] + replacement + source[second.end():]

    post_results_anchor = (
        "      if(*mortar>1){\n"
        "\tfor(k=0;k<neq[1];k++){\n"
        "\t  b[k]=b[k]-f_cs[k]-f_cm[k];}\n"
        "      }\t \n\n"
        "      isiz=mt**nk;cpypardou(vold,v,&isiz,&num_cpus);\n"
    )
    post_results = (
        "      if(*mortar==1&&ccxcap_is_active_()){\n"
        "        ITG wje,wjbase,wjnp,wjg,wjslot,wjt,wjpair;\n"
        "        double wjenergy;\n"
        "        ccxcap_corrected_(istep,&iinc,&icutb,&iit,nk,&mt,vold);\n"
        "        if(*ithermal<2){\n"
        "          for(wje=ne0;wje<*ne;wje++){\n"
        "            if(ipkon[wje]<0) continue;\n"
        "            if(strncmp(&lakon[8*wje],\"ESPRNGC\",7)!=0) continue;\n"
        "            wjbase=ipkon[wje];\n"
        "            wjnp=kon[wjbase-1];\n"
        "            wjg=kon[wjbase+wjnp];\n"
        "            wjslot=kon[wjbase+wjnp+1];\n"
        "            wjpair=0;\n"
        "            for(wjt=0;wjt<*ntie;wjt++)\n"
        "              if((wjslot>=itiefac[2*wjt])&&(wjslot<=itiefac[2*wjt+1])){\n"
        "                wjpair=wjt+1;\n"
        "                break;\n"
        "              }\n"
        "            if(wjpair==0||wjslot<1){\n"
        "              ccxcap_missing_pair_();\n"
        "              continue;\n"
        "            }\n"
        "            wjenergy=(*nener==1)?ener[2*mi[0]*(ne0+wjg-1)]:NAN;\n"
        "            ccxcap_trial_(&wje,&wjg,&islavsurf[2*(wjslot-1)],&wjpair,nener,\n"
        "              &stx[6*mi[0]*wje],&stx[6*mi[0]*wje+1],\n"
        "              &stx[6*mi[0]*wje+2],&stx[6*mi[0]*wje+3],\n"
        "              &stx[6*mi[0]*wje+4],&stx[6*mi[0]*wje+5],\n"
        "              &springarea[2*(wjg-1)],&wjenergy,\n"
        "              &pmastsurf[6*(wjg-1)+3],&pmastsurf[6*(wjg-1)+4],\n"
        "              &pmastsurf[6*(wjg-1)+5],&kscale,&reltime);\n"
        "          }\n"
        "          ccxcap_trial_end_();\n"
        "        }\n"
        "      }\n"
    )
    source = after_once(source, post_results_anchor, post_results, "post-results capture")
    source = after_once(
        source,
        "\tif(*mortar>1){\n\t  SFREE(f_cs);SFREE(f_cm);\n\t} \n",
        "\tccxcap_iteration_link_(istep,&iinc,&icutb,&iit,&icntrl,ttime,&time);\n",
        "accepted iteration link",
    )
    return source + "\n" + SINK.read_text(encoding="utf-8")


def patch_main(source: str) -> str:
    source = after_once(
        source,
        '#include "CalculiX.h"\n',
        "void ccxcap_finish_(void);\n",
        "job-level capture finish prototype",
    )
    source = after_once(
        source,
        "  FORTRAN(closefile,());\n",
        "\n  /* The sidecar spans every step and closes once at job completion. */\n"
        "  ccxcap_finish_();\n",
        "job-level capture footer after step loop and output close",
    )
    return source


def validate_c_main_additions(before: str, after: str) -> None:
    lines = _added_lines(before, after, "main finalizer additions")
    allowed_calls = {"ccxcap_finish_"}
    for raw in lines:
        line = raw.strip()
        if not line or line.startswith(("/*", "*", "//")) or line == "void ccxcap_finish_(void);":
            continue
        calls = re.findall(r"\b([A-Za-z_]\w*)\s*\(", line)
        if any(name not in allowed_calls for name in calls):
            raise RuntimeError(f"main addition calls outside finalizer allowlist: {line}")
        if "=" in line and "==" not in line:
            raise RuntimeError(f"main addition contains an assignment: {line}")


def build_delta() -> tuple[dict[str, bytes], dict[str, bytes]]:
    original: dict[str, bytes] = {}
    patched: dict[str, bytes] = {}
    with tarfile.open(ARCHIVE, "r:bz2") as archive:
        members = {m.name.removeprefix("./"): m for m in archive.getmembers() if m.isfile()}
        for rel, short in TARGETS.items():
            member = members.get(rel)
            if member is None:
                raise RuntimeError(f"missing source member {rel}")
            before = archive.extractfile(member).read()
            text = before.decode("utf-8")
            if short.endswith(".f"):
                text = patch_fortran(text)
                validate_fortran_additions(before.decode("utf-8"), text)
            elif short == "nonlingeo.c":
                text = patch_nonlingeo(text)
                validate_c_capture_additions(before.decode("utf-8"), text,
                                             SINK.read_text(encoding="utf-8"), rel)
            elif short == "ccx_2.23.c":
                text = patch_main(text)
                validate_c_main_additions(before.decode("utf-8"), text)
            else:
                raise RuntimeError(f"no patcher registered for {rel}")
            after = text.encode("utf-8")
            opcodes = difflib.SequenceMatcher(
                a=before.decode().splitlines(keepends=True),
                b=after.decode().splitlines(keepends=True),
                autojunk=False,
            ).get_opcodes()
            if any(tag not in ("equal", "insert") for tag, *_ in opcodes):
                raise RuntimeError(f"non-additive source edit detected in {rel}")
            original[rel], patched[rel] = before, after
    return original, patched


def render_patch(original: dict[str, bytes], patched: dict[str, bytes]) -> bytes:
    diff: list[str] = []
    for rel in TARGETS:
        diff.extend(difflib.unified_diff(
            original[rel].decode().splitlines(keepends=True),
            patched[rel].decode().splitlines(keepends=True),
            fromfile="a/" + rel, tofile="b/" + rel, n=3,
        ))
    return "".join(diff).encode()


def main() -> None:
    if not ARCHIVE.is_file() or not SINK.is_file():
        raise RuntimeError("pinned source archive or capture sink missing")
    if PATCH.exists() or META.exists():
        raise RuntimeError("refusing to overwrite prepared patch artifacts")
    original, patched = build_delta()
    patch_bytes = render_patch(original, patched)
    PATCH.parent.mkdir(parents=True, exist_ok=True)
    with PATCH.open("xb") as stream:
        stream.write(patch_bytes)
    metadata = {
        "schema": "ccx223_bounded_capture_patch_generation/v9",
        "status": "PREPARED_SOURCE_DELTA_ONLY",
        "source_archive_sha256": sha(ARCHIVE.read_bytes()),
        "sink_source_sha256": sha(SINK.read_bytes()),
        "patch_sha256": sha(patch_bytes),
        "targets": {rel: {"upstream_sha256": sha(original[rel]),
                          "modified_sha256": sha(patched[rel])} for rel in TARGETS},
        "addition_only": True,
        "mechanics_claim": "The delta only adds capture calls and a capture sink. No solver arrays, contact law, solver controls, loads, or contact decisions are assigned.",
        "lifecycle_fixes": {
            "tie_count_argument": "The in-loop generation begin receives ntie (ITG*) directly, matching its prototype and definition; it no longer receives &ntie (ITG**).",
            "footer_boundary": "ccxcap_finish_ is called once by the CLI top-level main after the complete step loop and standard output close, never from nonlingeo per-step returns.",
            "buffer_lifetime": "Sink snapshots remain allocated across step calls; the single finalizer frees pointers and resets each associated capacity/length pair.",
            "optional_pass_two": "Pass 1 is the required full source-wide offset census. Pass 2 is optional per tie; observed pass-2 face rows exactly match pass-1 tie/ordinal/face identities, start/end offsets, spans, and live/dead statuses in both writer and reader.",
            "disabled_path": "Capture enablement is queried once at generator entry from cached path availability and pending lifecycle state. With no path, face/point bookkeeping and post-results spring scans are bypassed.",
            "explicit_execution": "Generation capture starts only when iexpl<=1, the branch containing the matching corrected-state, trial, and iteration-link lifecycle. Explicit execution remains outside the capture contract and cannot publish an incomplete sidecar.",
            "energy_completeness": "When nener==1, every generated trial row must be joined, have a finite enabled energy, and contribute to a finite aggregate before trial_complete or RUN_END.complete can be true. The reader enforces this rule unconditionally.",
            "iteration_link": "The post-checkconvergence link validates the expected native iteration/cutback transition, records the generation's captured pre-checkconvergence identity, and closes pending state even when that transition is invalid.",
            "cutback_retry_reset": "A successful convergence resets icutb to zero; the link accepts attempt_after=1 for any captured retry attempt while preserving the generation's captured attempt identity.",
            "empty_state_join": "Eligible exact-state joins run even when either candidate domain is empty, count unmatched current points, and permit zero/zero per-tie joins supported by the face census.",
            "reader_attempt_transition": "The reader requires nonconverged links to retain the captured attempt and converged links to report either successful reset to one or exactly one cutback successor.",
            "kscale_type": "The pinned nonlingeo caller declares kscale as ITG; generation/trial hooks consistently use ITG* and copy/interpret the integer scale value at the sink boundary.",
            "candidate_cap": "At most 250000 candidate point rows are retained per generation across pass 1 plus every observed optional pass 2 combined.",
            "sidecar_publication": "Records are written to an exclusive temporary sibling path; checked fflush and fclose must succeed before a no-overwrite hard-link publishes the configured path. Reported write/flush/close/publication failures leave the configured path unpublished.",
            "temporary_ownership": "The sink only removes the temporary sibling after successful exclusive creation by this process; a failed `wbx` open never grants unlink ownership.",
            "coverage_controls": "Offline tests compare production hook order in one regenerated nonlingeo.c string and reject an order-swapped mutant; a two-generation prior-nonempty/current-empty join reports old_missing and rejects a compiled mutant that skips joins when the current candidate set is empty.",
        },
    }
    with META.open("x", encoding="utf-8") as stream:
        json.dump(metadata, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print(json.dumps(metadata, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
