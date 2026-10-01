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
}


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


def patch_fortran(source: str) -> str:
    source = after_once(
        source,
        "      implicit none\n",
        "      integer wjcap_faceord,wjcap_valid,wjcap_reason\n"
        "      integer wjcap_master,wjcap_status,wjcap_start,wjcap_end\n"
        "      integer wjcap_law,wjcap_isol\n"
        "      real*8 wjcap_raw,wjcap_class,wjcap_nx,wjcap_ny,wjcap_nz\n",
        "capture local declarations",
    )

    # Count every runtime face slot, including a dead element and a zero span.
    face_anchor = "            if(ipkon(nelems).lt.0) cycle\n"
    face_block = (
        "            wjcap_faceord=jj-itiefac(1,i)+1\n"
        "            wjcap_start=islavsurf(2,jj)\n"
        "            wjcap_end=islavsurf(2,jj+1)\n"
        "            wjcap_status=1\n"
        "            if(ipkon(nelems).lt.0) wjcap_status=0\n"
        "            call ccxcap_face(i,iloop,wjcap_faceord,ifaces,\n"
        "     &           wjcap_start,wjcap_end,wjcap_status)\n"
    )
    source = before_once(source, face_anchor, face_block, "face census")

    source = after_once(
        source,
        "              igauss=indexf+m\n",
        "              wjcap_valid=0\n"
        "              wjcap_reason=99\n"
        "              wjcap_master=0\n"
        "              wjcap_raw=0.d0\n"
        "              wjcap_class=0.d0\n"
        "              wjcap_nx=0.d0\n"
        "              wjcap_ny=0.d0\n"
        "              wjcap_nz=0.d0\n",
        "point defaults",
    )
    source = before_once(
        source,
        "              if(isol.eq.0) then\n",
        "              if(isol.eq.0) wjcap_reason=1\n",
        "unmapped reason",
    )
    source = after_once(
        source,
        "                endif\n                nelemm=int(ifacem/10.d0)\n",
        "                wjcap_master=ifacem\n",
        "master face identity",
    )
    source = after_once(
        source,
        "                clear=al(1)*xn(1)+al(2)*xn(2)+al(3)*xn(3)\n",
        "                wjcap_valid=1\n"
        "                wjcap_raw=clear\n"
        "                wjcap_class=clear\n"
        "                wjcap_reason=0\n"
        "                wjcap_nx=xn(1)\n"
        "                wjcap_ny=xn(2)\n"
        "                wjcap_nz=xn(3)\n",
        "mapped gap and normal",
    )

    source = after_once(
        source,
        "                  if((clear.gt.0.d0).and.\n"
        "     &                 (int(elcon(3,1,imat)).ne.4)) then\n",
        "                    wjcap_reason=2\n",
        "dynamic positive-clearance filter",
    )
    source = after_once(
        source,
        "                          if(clear.gt.0.d0) then\n",
        "                            wjcap_reason=5\n",
        "static positive-clearance filter",
    )
    source = before_once(
        source,
        "                        if(harvest.gt.(1.d0-alea)) isol=0\n",
        "                        if(harvest.gt.(1.d0-alea)) wjcap_reason=4\n",
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
                        "                            wjcap_reason=6\n",
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
        "                      if(dsqrt(xstateini(4,1,ne0+igauss)**2+\n"
        "     &                     xstateini(5,1,ne0+igauss)**2+\n"
        "     &                     xstateini(6,1,ne0+igauss)**2)\n"
        "     &                     .lt.1.d-30) wjcap_reason=7\n"
    )
    source = before_once(source, pass_two_cond, pass_two_probe, "pass-two prior-state filter")

    unsupported_skip = (
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
    )
    source = before_once(source, "                  cycle\n", unsupported_skip,
                        "unsupported-master skipped candidate")

    point_anchor = "              endif\n!     \n              if(isol.ne.0) then\n"
    point_call = (
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
    )
    if source.count(point_anchor) != 1:
        raise RuntimeError("point outcome instrumentation: final isol branch anchor mismatch")
    source = source.replace(
        point_anchor,
        "              endif\n!     \n" + point_call + "              if(isol.ne.0) then\n",
        1,
    )
    source = before_once(source, "      return\n      end\n",
                         "      call ccxcap_generation_end()\n",
                         "generation end before return")
    return source


def patch_nonlingeo(source: str) -> str:
    prototypes = (
        "void ccxcap_generation_begin_(ITG*,ITG*,ITG*,ITG*,ITG*,ITG*,double*,double*,ITG*,ITG*,ITG*);\n"
        "void ccxcap_face_(ITG*,ITG*,ITG*,ITG*,ITG*,ITG*,ITG*);\n"
        "void ccxcap_point_(ITG*,ITG*,ITG*,ITG*,ITG*,ITG*,ITG*,ITG*,ITG*,ITG*,ITG*,double*,double*,double*,double*,double*,double*,double*,double*,double*,double*,double*,double*,double*,double*,double*);\n"
        "void ccxcap_generation_end_(void);\n"
        "void ccxcap_trial_(ITG*,ITG*,ITG*,ITG*,ITG*,double*,double*,double*,double*,double*,double*,double*,double*,double*,double*,double*,double*,double*);\n"
        "void ccxcap_trial_end_(void);\n"
        "void ccxcap_missing_pair_(void);\n"
        "void ccxcap_corrected_(ITG*,ITG*,ITG*,ITG*,ITG*,ITG*,double*);\n"
        "void ccxcap_iteration_link_(ITG*,ITG*,ITG*,ITG*,ITG*,double*,double*);\n"
        "void ccxcap_finish_(void);\n"
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
            indent + "if(*mortar==1) ccxcap_generation_begin_(&istep,&iinc,&icutb,&iit,nk,&mt,vold,\n"
            + indent + "\t\t\t\t    &kscale,nener,&ntie,nintpoint);\n"
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
        "      if(*mortar==1){\n"
        "        ITG wje,wjbase,wjnp,wjg,wjslot,wjt,wjpair;\n"
        "        double wjenergy;\n"
        "        ccxcap_corrected_(&istep,&iinc,&icutb,&iit,nk,&mt,vold);\n"
        "        if(*ithermal<2){\n"
        "          for(wje=ne0;wje<*ne;wje++){\n"
        "            if(ipkon[wje]<0) continue;\n"
        "            if(strncmp(&lakon[8*wje],\"ESPRNGC\",7)!=0) continue;\n"
        "            wjbase=ipkon[wje];wjnp=kon[wjbase-1];\n"
        "            wjg=kon[wjbase+wjnp];wjslot=kon[wjbase+wjnp+1];\n"
        "            wjpair=0;\n"
        "            for(wjt=0;wjt<*ntie;wjt++)\n"
        "              if((wjslot>=itiefac[2*wjt])&&(wjslot<=itiefac[2*wjt+1])){wjpair=wjt+1;break;}\n"
        "            if(wjpair==0||wjslot<1){ccxcap_missing_pair_();continue;}\n"
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
        "\tccxcap_iteration_link_(&istep,&iinc,&icutb,&iit,&icntrl,ttime,&time);\n",
        "accepted iteration link",
    )
    source = before_once(source, "  SFREE(iponoel);\n  \n  return;\n}\n",
                         "  ccxcap_finish_();\n", "run footer")
    return source + "\n" + SINK.read_text(encoding="utf-8")


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
            text = patch_fortran(text) if short.endswith(".f") else patch_nonlingeo(text)
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
        "schema": "ccx223_bounded_capture_patch_generation/v2",
        "status": "PREPARED_SOURCE_DELTA_ONLY",
        "source_archive_sha256": sha(ARCHIVE.read_bytes()),
        "sink_source_sha256": sha(SINK.read_bytes()),
        "patch_sha256": sha(patch_bytes),
        "targets": {rel: {"upstream_sha256": sha(original[rel]),
                          "modified_sha256": sha(patched[rel])} for rel in TARGETS},
        "addition_only": True,
        "mechanics_claim": "The delta only adds capture calls and a capture sink. No solver arrays, contact law, solver controls, loads, or contact decisions are assigned.",
    }
    with META.open("x", encoding="utf-8") as stream:
        json.dump(metadata, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print(json.dumps(metadata, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
