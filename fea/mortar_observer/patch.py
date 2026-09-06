"""Hash-gated, logging-only patch for the two official CalculiX 2.21 files.

Produces new files; never updates the supplied source directory.
"""
import argparse
import hashlib
import json
from pathlib import Path

SOURCE_SHA256 = {
    "stressmortar.c": "d7cc1fa5d73aba85bbec7dd48f839e7b05514d91ab996025d089a12c45e84cd6",
    "nonlingeo.c": "0be7d7d6037868c364a621e12a3802a703f189b09ba200de95cf2e9d1b211f1b",
}


def record(kind, **fields):
    """Generate a single printf; i: integer, d: double, a: double array."""
    fmt = 'MORTAR_OBSERVER {"kind":"' + kind + '","call_id":%ld'
    args = ["mortar_observer_call_id"]
    for key, (typ, value) in fields.items():
        fmt += ',"' + key + '":'
        if typ == "a":
            fmt += "[" + ",".join(["%.17g"] * len(value)) + "]"
            args.extend(value)
        elif typ == "i":
            fmt += '%" ITGFORMAT "'
            args.append(value)
        else:
            fmt += "%.17g"
            args.append(value)
    fmt += "}\\n"
    # Escape JSON quotes, but retain C's integer-format string concatenation.
    fmt = fmt.replace('"', '\\"').replace('%\\" ITGFORMAT \\"', '%" ITGFORMAT "')
    return 'printf("' + fmt + '", ' + ", ".join(args) + ");\n"


def integer(value):
    return "i", value


def real(value):
    return "d", value


def vector(base, n):
    return "a", [f"{base}[{k}]" for k in range(n)]


def context(kind):
    return record(kind, step=integer("*istep"), inc=integer("iinc"),
                  cutback=integer("icutb"), iteration=integer("iit"),
                  time=real("time"), dtime=real("dtime"), ttime=real("*ttime"), tper=real("*tper"),
                  theta=real("theta"), dtheta=real("dtheta"),
                  icntrl=integer("icntrl"), nmethod=integer("*nmethod"),
                  iexpl=integer("*iexpl"), ithermal=integer("*ithermal"),
                  uncoupled=integer("uncoupled"), mortar=integer("*mortar"),
                  iflagdualquad=integer("iflagdualquad"))


def snapshots(kind, sparse=False):
    code = "{ ITG oi,oj,ok,on,op=0,os=0;\n"
    if sparse:
        code += "for(oi=0;oi<*ntie;oi++){if(tieset[oi*243+80]=='C'){op++;os+=nslavnode[oi+1]-nslavnode[oi];}}\n"
        code += record("INVENTORY", pair_count=integer("op"), slave_count=integer("os"))
    code += "for(oi=0;oi<*ntie;oi++){\nif(tieset[oi*243+80]=='C'){\n"
    if sparse:
        code += record("PAIR", pair=integer("oi"), start=integer("nslavnode[oi]"),
                       end=integer("nslavnode[oi+1]"))
    code += "for(oj=nslavnode[oi];oj<nslavnode[oi+1];oj++){on=islavnode[oj];\n"
    fields = {"pair": integer("oi"), "slot": integer("oj"), "node": integer("on"),
              "activity": integer("islavact[oj]"),
              "lambda_raw": vector("(cstress+mt*oj)", 3)}
    if sparse:
        fields.update(lambda_start=vector("(cstressini+mt*oj)", 3),
                      ddtil_count=integer("jqdtil[on]-jqdtil[on-1]"))
    else:
        fields["gap"] = real("gap[oj]")
    code += record(kind, **fields)
    if sparse:
        code += "for(ok=jqdtil[on-1]-1;ok<jqdtil[on]-1;ok++){\n"
        code += record("DDTIL", pair=integer("oi"), column_slot=integer("oj"),
                       source_slot=integer("islavnodeinv[on-1]-1"),
                       destination_slot=integer("islavnodeinv[irowdtil[ok]-1]-1"),
                       entry=integer("ok"), value=real("Ddtil[ok]")) + "}\n"
    return code + "}}}}\n"


def replacements():
    law = record("LAW", pair=integer("i"), slot=integer("j"), node=integer("nodes"),
                 activity=integer("islavact[j]"), ndof=integer("ndof"),
                 normal=vector("(slavnor+3*j)", 3), tangents=vector("(slavtan+6*j)", 6),
                 ln=real("stressnormal"), lt=vector("stresst", 2),
                 lt_start=vector("stressinit", 2), q=real("ddispnormal-gap[j]"),
                 ut=vector("disp_tildet", 2), gn=real("gnc"), gt=vector("gtc", 2),
                 b=real("bp[j]"), constant_n=real("constantn"), constant_t=real("constantt"),
                 mu=real("mu"), normal_mode=integer("regmode"), tangent_mode=integer("regmodet"),
                 normal_inverse_stiffness=real("aninvloc"), tangent_inverse_stiffness=real("atauinvloc"),
                 p0=real("p0"), beta=real("beta"), iwan=integer("iwan"),
                 rn=real("ncf_n"), rt=vector("ncf_t", 2))
    summary = record("SUMMARY_PRE_OVERRIDE", ndiverg=integer("ndiverg"),
                     flag=integer("*iflagact"), keepset=integer("keepset"),
                     max_n=real("max_ncf_n"), max_t=vector("max_ncf_t", 2),
                     lm_t_av=("a", ["lm_t1_av", "lm_t2_av"]),
                     nstick=integer("nstick"), nslip=integer("nslip"),
                     ninactive=integer("ninacti"), nnogap=integer("nnogap"), nolm=integer("nolm"))
    return {
        "stressmortar.c": [
            ('#include "mortar.h"', '\nlong mortar_observer_call_id=0;\n', "after"),
            ('  /** generate cstressini2,cstresstil **/', snapshots("PRE_RAW", True), "before"),
            ('\tif( ncf_n<0.0)ncf_n=-ncf_n;', law, "before"),
            ('  if(debug==1){\n    if(keepset==1)printf', snapshots("POST_RAW_AFTER_ACTIVE_LOOP"), "before"),
            ('  if(*iit>ndiverg){*iflagact=0;}', summary, "before"),
            ('  if(*iit>ndiverg){*iflagact=0;}', record("SUMMARY_POST_OVERRIDE", flag=integer("*iflagact")), "after"),
        ],
        "nonlingeo.c": [
            ('#include "mortar.h"', '\nextern long mortar_observer_call_id;\n', "after"),
            ('\tstressmortar(bhat,adc2,auc2,jqc2,irowc2,neq,gap,b,islavact,irowddinv,',
             '++mortar_observer_call_id;\n' + context("BEGIN"), "before"),
            ('\tiflagact_old=iflagact;', record("RETURN"), "before"),
            ('\tcheckconvergence(co,nk,kon,ipkon,lakon,ne,stn,nmethod,',
             'if(*mortar>1){' + context("PRE_CHECK") + 'fflush(stdout);}\n', "before"),
            ('\t\t\t &dampwkini,energystartstep);',
             '\nif(*mortar>1){' + context("POST_CHECK") + 'fflush(stdout);}\n', "after"),
        ],
    }


def patched_sources(sources):
    for name, expected in SOURCE_SHA256.items():
        if hashlib.sha256(sources[name]).hexdigest() != expected:
            raise ValueError(f"Official unmodified source hash required: {name}")
    result = {}
    for name, edits in replacements().items():
        source = sources[name].decode()
        for anchor, addition, position in edits:
            if source.count(anchor) != 1:
                raise ValueError(f"Expected exactly one observer site: {name}: {anchor!r}")
            replacement = addition + anchor if position == "before" else anchor + addition
            source = source.replace(anchor, replacement, 1)
        result[name] = source.encode()
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path, help="Must not exist")
    args = parser.parse_args()
    outputs = patched_sources({name: (args.source / name).read_bytes() for name in SOURCE_SHA256})
    args.destination.mkdir(parents=True, exist_ok=False)
    for name, content in outputs.items():
        (args.destination / name).write_bytes(content)
    (args.destination / "patch_manifest.json").write_text(json.dumps({
        "source_sha256": SOURCE_SHA256,
        "patched_sha256": {name: hashlib.sha256(data).hexdigest() for name, data in outputs.items()},
        "patch_generator_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "status": "LOGGING PATCH ONLY; NOT A VERIFIED OBSERVER BINARY",
    }, indent=2) + "\n")


if __name__ == "__main__":
    main()
