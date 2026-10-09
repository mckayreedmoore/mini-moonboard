"""Use authentic saved snapshot schemas and optional inventory observations.

Three guarded AST substitutions reuse the frozen99 source joins and selectors.
The exact v3 writer supplies the whole output guard. No saved JSON is rewritten.
"""
import argparse
import ast
import hashlib
import json
from pathlib import Path
from types import ModuleType

OWN = Path(__file__).resolve()
LOADED_SHA = hashlib.sha256(OWN.read_bytes()).hexdigest()
SUMMARY_ROOT = OWN.parent.parent
V3 = SUMMARY_ROOT/"review-fix-v3/summarize.py"
V3_SHA = "787626079340ea3999f940cd7e057dd5c095720d42a54e44e30711ebc8f1a36e"
ORIGINAL_SHA = "99ead1194671c82e0e28f905e84c4208cf2a82dc1ed4532aaf1aeb13c0c7124d"
SNAPSHOT_SCHEMA = "eoere_z180_component_process_source_snapshot/v1"
OLD_SCHEMAS = ("eoere_z180_component_source_snapshot_before/v1", "eoere_z180_component_source_snapshot_after/v1")
HISTORY_ACCESS = 'snapshots["source_pins_before"]["inventory_only_historical_receipts"]'


def require(ok, message):
    if not ok:
        raise ValueError(message)


def load_writer():
    raw = V3.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == V3_SHA, "exact frozen v3 writer required")
    writer = ModuleType("exact_z180_summary_v3_writer_78762607")
    writer.__file__ = str(V3)
    exec(compile(raw, str(V3), "exec"), writer.__dict__)  # noqa: S102 -- authenticated source-only writer
    return writer


# Capture the exact v3 source-owned root identity on import, before callbacks.
_writer = load_writer()
_original_loader = _writer.original


def original():
    require(hashlib.sha256(OWN.read_bytes()).hexdigest() == LOADED_SHA, "v4 adapter source changed")
    a = _original_loader()
    require(a.OWN == SUMMARY_ROOT/"summarize.py", "exact original summary path required")
    raw = a.checked({"path": str(a.OWN.relative_to(a.ROOT)), "sha256": ORIGINAL_SHA}, {})
    tree = ast.parse(raw)
    selected = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in ("case_records", "build")]
    require(len(selected) == 2 and {node.name for node in selected} == {"case_records", "build"}, "two exact original definitions required")
    target = ast.dump(ast.parse(HISTORY_ACCESS, mode="eval").body, include_attributes=False)
    class SnapshotShape(ast.NodeTransformer):
        schemas, history = [], 0
        def visit_Constant(self, node):
            if isinstance(node.value, str) and node.value in OLD_SCHEMAS:
                self.schemas.append(node.value)
                return ast.copy_location(ast.Constant(SNAPSHOT_SCHEMA), node)
            return node
        def visit_Subscript(self, node):
            if ast.dump(node, include_attributes=False) == target:
                self.history += 1
                return ast.copy_location(ast.Call(func=ast.Attribute(value=node.value, attr="get", ctx=ast.Load()),
                    args=[node.slice, ast.List(elts=[], ctx=ast.Load())], keywords=[]), node)
            return self.generic_visit(node)
    change = SnapshotShape()
    adapted = ast.Module(body=[change.visit(node) for node in selected], type_ignores=[])
    require(tuple(change.schemas) == OLD_SCHEMAS and change.history == 1, "exact two-schema/one-history seam required")
    exec(compile(ast.fix_missing_locations(adapted), str(OWN), "exec"), a.__dict__)  # noqa: S102 -- three guarded substitutions only
    original_verify = a.verify
    def verify(pins):
        require(hashlib.sha256(OWN.read_bytes()).hexdigest() == LOADED_SHA, "v4 adapter source changed")
        a.merge(pins, {str(OWN.relative_to(a.ROOT)): LOADED_SHA})
        original_verify(pins)
    a.verify = verify  # Own correction source joins the unchanged before/after union checks.
    return a


def build(manifest, manifest_ref):
    """Saved-data replay in memory, retaining the exact supplied raw manifest."""
    return original().build(manifest, manifest_ref)


def output_original():
    a = original()
    adapted_build = a.build
    def build_with_pin(manifest, manifest_ref):
        require(manifest["source_sha256"].get(str(OWN.relative_to(a.ROOT))) == LOADED_SHA,
                "exact v4 adapter manifest pin required")
        return adapted_build(manifest, manifest_ref)
    a.build = build_with_pin
    return a


_writer.original = output_original  # Private verified writer instance; guard code unchanged.


def write_to_file(manifest_ref, out):
    return _writer.write_to_file(manifest_ref, out)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--manifest-sha256", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    result = write_to_file({"path": args.manifest, "sha256": args.manifest_sha256}, args.out)
    print(json.dumps({"schema": result["schema"], "cases": len(result["cases"]), "output": str(args.out)}))


if __name__ == "__main__":
    main()
