"""V2 additive observer packet: physical kinematics and assembled contact forces.

Applies the unchanged V1 generator to official inputs, then inserts read-only
records. No solver arithmetic, state updates or control flow is replaced.
"""
import argparse
import hashlib
import json
from pathlib import Path

if __package__:
    from . import patch as v1
else:
    import patch as v1

SOURCE_SHA256 = v1.SOURCE_SHA256
record, integer, real, vector = v1.record, v1.integer, v1.real, v1.vector
COUPLED = "jqd[on]>jqd[on-1] || jqb[on]>jqb[on-1]"


def kinematics():
    code = "{ ITG on,oe,op=0,od=0,ob=0,os=0,oi,oj;\n"
    code += "for(on=1;on<=*nk;on++){\n"
    code += "od+=jqd[on]-jqd[on-1];ob+=jqb[on]-jqb[on-1];\n"
    code += f"if({COUPLED}){{op++;}}\n}}\n"
    code += "for(oi=0;oi<*ntie;oi++){if(tieset[oi*243+80]=='C'){os+=nslavnode[oi+1]-nslavnode[oi];}}\n"
    code += record("KIN_INVENTORY", all_node_count=integer("*nk"), physical_count=integer("op"),
                   dd_count=integer("od"), bd_count=integer("ob"), slave_count=integer("os"))
    code += f"for(on=1;on<=*nk;on++){{if({COUPLED}){{\n"
    code += record("KIN_NODE", node=integer("on"), dd_count=integer("jqd[on]-jqd[on-1]"),
                   bd_count=integer("jqb[on]-jqb[on-1]"), b2=vector("(b2+mt*on-3)", 3),
                   vold=vector("(vold+mt*on-3)", 3), vini=vector("(vini+mt*on-3)", 3))
    for kind, values, rows, columns in (("KIN_DD", "Dd", "irowd", "jqd"), ("KIN_BD", "Bd", "irowb", "jqb")):
        code += f"for(oe={columns}[on-1]-1;oe<{columns}[on]-1;oe++){{\n"
        code += record(kind, node=integer("on"), entry=integer("oe"), row_node=integer(rows+"[oe]"),
                       slave_slot=integer("islavnodeinv["+rows+"[oe]-1]-1"), value=real(values+"[oe]"))
        code += "}\n"
    code += "}}\nfor(oi=0;oi<*ntie;oi++){if(tieset[oi*243+80]=='C'){\n"
    code += "for(oj=nslavnode[oi];oj<nslavnode[oi+1];oj++){\n"
    code += record("KIN_GAP", pair=integer("oi"), slot=integer("oj"), node=integer("islavnode[oj]"), gap=real("gap[oj]"))
    return code + "}}}}\n"


def forces():
    code = "{ ITG on,op=0,oo=0;\n"
    code += f"for(on=1;on<=*nk;on++){{if({COUPLED}){{op++;}}}}\n"
    code += record("CFS_INVENTORY", all_node_count=integer("*nk"), physical_count=integer("op"))
    code += f"for(on=1;on<=*nk;on++){{if({COUPLED}){{\n"
    code += record("CFS_NODE", node=integer("on"), force=vector("(cfs+mt*on-3)", 3))
    code += "}else if(cfs[mt*on-3]!=0.0 || cfs[mt*on-2]!=0.0 || cfs[mt*on-1]!=0.0){oo++;\n"
    code += record("CFS_OUTSIDE", node=integer("on"), force=vector("(cfs+mt*on-3)", 3))
    code += "}}\n"
    code += record("CFS_END", scanned_nodes=integer("*nk"), physical_count=integer("op"), outside_nonzero_count=integer("oo"))
    return code + "}\n"


def replacements():
    return {
        "stressmortar.c": [
            ("  /* calculate hatu=D u^S+ B u^M for update in semi-smooth Newton,", kinematics(), "before"),
            ("  if(*nmethod==4){\n    for(i=0;i<*nk;i++){\n      for(j=jqdtil[i]-1;j<jqdtil[i+1]-1;j++){", forces(), "before"),
        ],
        "nonlingeo.c": [],
    }


def patched_sources(sources):
    outputs = v1.patched_sources(sources)
    for name, edits in replacements().items():
        source = outputs[name].decode()
        for anchor, addition, position in edits:
            if position != "before" or source.count(anchor) != 1:
                raise ValueError("Expected exactly one V2 insertion site: " + name)
            source = source.replace(anchor, addition+anchor, 1)
        outputs[name] = source.encode()
    return outputs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path, help="Must not exist")
    args = parser.parse_args()
    sources = {name: (args.source/name).read_bytes() for name in SOURCE_SHA256}
    outputs = patched_sources(sources)
    digest = lambda data: hashlib.sha256(data).hexdigest()
    manifest = {
        "source_sha256": SOURCE_SHA256,
        "v1_patched_sha256": {name: digest(data) for name, data in v1.patched_sources(sources).items()},
        "patched_sha256": {name: digest(data) for name, data in outputs.items()},
        "v1_patch_generator_sha256": digest(Path(v1.__file__).read_bytes()),
        "v2_patch_generator_sha256": digest(Path(__file__).read_bytes()),
        "patch_generator_sha256": digest(Path(__file__).read_bytes()),
        "status": "V2 ADDITIVE LOGGING PATCH ONLY; NOT A VERIFIED OBSERVER BINARY",
    }
    args.destination.mkdir(parents=True, exist_ok=False)
    for name, data in outputs.items():
        (args.destination/name).write_bytes(data)
    (args.destination/"patch_manifest.json").write_text(json.dumps(manifest, indent=2)+"\n")


if __name__ == "__main__":
    main()
