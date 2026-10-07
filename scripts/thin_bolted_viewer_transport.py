"""Keep the complete review scene in a lossless gzip viewer transport.

The original source-bound JSON remains unchanged locally. The compressed file
contains every original byte, so it can restore the ignored raw export without
rebuilding CAD. No geometric simplification or authority selection occurs.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import sys

from scripts import thin_bolted_model as model

COMPRESSED = model.SCENE.with_suffix(".json.gz")
REPORT = model.LAYOUT.parent / "viewer-transport-v4.json"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--restore-raw", action="store_true")
    args = parser.parse_args()
    contract = json.loads(model.CONTRACT.read_text())
    expected = contract["viewer"]["sha256"]
    if args.check or args.restore_raw:
        raw = gzip.decompress(COMPRESSED.read_bytes())
        if hashlib.sha256(raw).hexdigest() != expected:
            raise ValueError("decoded source scene differs")
        if model.shared.sha(COMPRESSED) != contract["viewer"]["transport"]["sha256"]:
            raise ValueError("viewer transport differs")
        if args.restore_raw:
            if model.SCENE.exists() and model.shared.sha(model.SCENE) != expected:
                raise ValueError("preserve changed raw export")
            if not model.SCENE.exists():
                model.SCENE.write_bytes(raw)
        print(json.dumps({"verified": True, "decoded_sha256": expected,
                          "restored_or_retained": args.restore_raw}))
        return
    if COMPRESSED.exists() or REPORT.exists():
        raise FileExistsError("preserve existing viewer transport")
    raw = model.SCENE.read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected:
        raise ValueError("source scene differs")
    encoded = gzip.compress(raw, mtime=0)
    if gzip.decompress(encoded) != raw:
        raise ValueError("lossless transport round trip failed")
    COMPRESSED.write_bytes(encoded)
    transport = {"path": str(COMPRESSED.relative_to(model.ROOT)),
                 "encoding": "gzip", "sha256": model.shared.sha(COMPRESSED),
                 "decoded_sha256": expected, "encoded_bytes": len(encoded), "decoded_bytes": len(raw)}
    REPORT.write_text(json.dumps({"schema": "thin_bolted_viewer_transport/v1", **transport,
                                 "source_sha256": {
                                     str(model.SCENE.relative_to(model.ROOT)): expected,
                                     str(model.EVIDENCE.relative_to(model.ROOT)): model.shared.sha(model.EVIDENCE),
                                     str(__file__).removeprefix(str(model.ROOT) + "/"): model.shared.sha(model.ROOT / __file__),
                                 }, "python_version": sys.version.split()[0],
                                 "command": ".venv/bin/python -m scripts.thin_bolted_viewer_transport",
                                 "restore_command": ".venv/bin/python -m scripts.thin_bolted_viewer_transport --restore-raw",
                                 "decoded_scene_byte_identical": True}, indent=2) + "\n")
    contract["viewer"]["transport"] = transport
    contract["viewer"]["transport_report"] = {"path": str(REPORT.relative_to(model.ROOT)),
                                               "sha256": model.shared.sha(REPORT)}
    model.CONTRACT.write_text(json.dumps(contract, indent=2) + "\n")
    print(json.dumps(transport, indent=2))


if __name__ == "__main__":
    main()
