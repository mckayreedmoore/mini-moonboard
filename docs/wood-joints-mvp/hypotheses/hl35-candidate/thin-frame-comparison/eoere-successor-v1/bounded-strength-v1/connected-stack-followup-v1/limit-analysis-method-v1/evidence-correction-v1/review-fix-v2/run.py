"""Small launcher: execute captured body bytes and bind their loaded digest."""

import hashlib
import types
from pathlib import Path

HERE = Path(__file__).resolve().parent
LAUNCHER_BYTES_AT_LOAD = Path(__file__).read_bytes()
LAUNCHER_SHA_AT_LOAD = hashlib.sha256(LAUNCHER_BYTES_AT_LOAD).hexdigest()


def load_body():
    if Path(__file__).read_bytes() != LAUNCHER_BYTES_AT_LOAD:
        raise ValueError("Loaded launcher source changed before use")
    path = HERE / "body.py"
    body_bytes = path.read_bytes()
    module = types.ModuleType("synthetic_evidence_review_fix_v2")
    module.__file__ = str(path)
    module.EXECUTED_BODY_SHA256 = hashlib.sha256(body_bytes).hexdigest()
    module.LOADED_LAUNCHER_SHA256 = LAUNCHER_SHA_AT_LOAD
    # This local body is executed from the exact bytes captured above.
    exec(compile(body_bytes, str(path), "exec"), module.__dict__)  # noqa: S102
    return module


if __name__ == "__main__":
    load_body().main()
