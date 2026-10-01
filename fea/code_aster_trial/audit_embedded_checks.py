"""Record explicit TEST_RESU outcomes, never infer them from process exit alone."""

import argparse
import hashlib
import json
from pathlib import Path
import re


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("attempt", type=Path)
    p.add_argument("--expected-analytic", type=int, required=True)
    p.add_argument("--scope", required=True)
    a = p.parse_args()
    raw = (a.attempt / "native.stdout").read_bytes()
    text = raw.decode(errors="replace")
    execution = json.loads((a.attempt / "execution.json").read_text())
    checks = [line.strip() for line in text.splitlines()
              if re.match(r"\s*(OK|NOOK)\s+(NON_REGRESSION|ANALYTIQUE)", line)]
    analytic = [line for line in checks if re.match(r"(OK|NOOK)\s+ANALYTIQUE", line)]
    ok = (execution["returncode"] == 0 and not execution["timed_out"]
          and not execution["changed_frozen_inputs"]
          and len(analytic) == a.expected_analytic
          and all(line.startswith("OK ") for line in checks)
          and "DIAGNOSTIC JOB : OK" in text)
    d = {"status": "PASS" if ok else "FAIL", "scope": a.scope,
         "expected_analytical_check_count": a.expected_analytic,
         "observed_analytical_check_count": len(analytic), "checks": checks,
         "stdout_sha256": hashlib.sha256(raw).hexdigest(),
         "limits": "Only the embedded checks and tolerances in this frozen fixture; no full-joint acceptance."}
    (a.attempt / "embedded-check-audit.json").write_text(json.dumps(d, indent=2) + "\n")
    print(json.dumps(d, indent=2))
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
