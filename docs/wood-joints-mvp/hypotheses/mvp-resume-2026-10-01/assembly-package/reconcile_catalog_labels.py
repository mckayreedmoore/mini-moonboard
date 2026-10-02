"""Export readable retained catalog labels using the frozen reconciliation.

The legacy producer expects catalog_references to be a list; retained inputs
also supply strings. Normalize that field before both joins in the producer.
"""

import hashlib
from pathlib import Path

import reconcile

HERE = Path(__file__).resolve().parent
LEGACY_SHA = "6b698475a02b172857f7891efd2347e8f7c88415315303a9a30b51c84ba5fd74"
OUTPUT = HERE / "rawlocal/catalog-labels-attempt01"


def main():
    legacy = Path(reconcile.__file__)
    if (
        legacy.resolve() != HERE / "reconcile.py"
        or hashlib.sha256(legacy.read_bytes()).hexdigest() != LEGACY_SHA
    ):
        raise ValueError("frozen reconciliation producer changed")
    original_read, original_output = reconcile.read_json, reconcile.RAW

    def read_source(relative_path):
        data = original_read(relative_path)
        if isinstance(data, dict):
            for family in data.get("retained_family_coverage", []):
                references = family.get("catalog_references", [])
                if isinstance(references, str):
                    family["catalog_references"] = [references]
        return data

    # ponytail: reuse the frozen builder; normalize its one mixed-shape field.
    reconcile.read_json, reconcile.RAW = read_source, OUTPUT
    try:
        return reconcile.main()
    finally:
        reconcile.read_json, reconcile.RAW = original_read, original_output


if __name__ == "__main__":
    raise SystemExit(main())
