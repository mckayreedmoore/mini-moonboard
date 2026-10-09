"""Observe served immutable viewer bytes after the exact successful Pages run."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import gzip, hashlib, json, subprocess, urllib.request

OWN = Path(__file__).resolve()
ROOT = Path.cwd()
COMMIT = "bca5f988f04d089537c037a33cd693c5b96ef093"
RUN = 37882883404
BASE = "https://mckayreedmoore.github.io/mini-moonboard/"
FILES = ["index.html", "eoere-cleat-extension-overlay.mjs", "eoere-cleat-extension-scene.json.gz",
         "eoere-2026-adjustments-overlay.mjs", "eoere-adjusted-base-v3-scene.json.gz",
         "eoere-2026-adjustments-v3-scene.json.gz"]
DECODED = {"eoere-cleat-extension-scene.json.gz": "6c39b4a240f8033491bbd43c437d60dc888c524e90b350e53351eaf28ddc5db6",
           "eoere-adjusted-base-v3-scene.json.gz": "dfeccf743c1e18f8fc2cadd81dd975c94d3057a88923155f3b2a7166f5ae40b7",
           "eoere-2026-adjustments-v3-scene.json.gz": "914dd1def234c0657b136f6d2aba0b78456f7ee4a7b8b8df449908f0f6b501d6"}
sha = lambda data: hashlib.sha256(data).hexdigest()
run = json.loads(subprocess.check_output(["gh", "run", "view", str(RUN), "--json", "status,conclusion,headSha,url"]))
assert run["status"] == "completed" and run["conclusion"] == "success" and run["headSha"] == COMMIT
assert subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip() == COMMIT
pins = {str(Path("site") / name): sha((Path("site") / name).read_bytes()) for name in FILES}
def observe(name):
    request = urllib.request.Request(BASE + name + "?publication=" + COMMIT, headers={"Accept-Encoding": "identity"})
    with urllib.request.urlopen(request, timeout=45) as response:
        data = response.read()
        assert response.status == 200 and sha(data) == pins[str(Path("site") / name)], name
        row = {"url": response.url, "status": response.status, "bytes": len(data), "sha256": sha(data),
               "content_encoding": response.headers.get("Content-Encoding")}
        if name in DECODED:
            raw = gzip.decompress(data); assert sha(raw) == DECODED[name], name
            json.loads(raw); row["decoded_sha256"] = sha(raw)
        return row
with ThreadPoolExecutor(max_workers=6) as pool: rows = list(pool.map(observe, FILES))
for name, expected in pins.items(): assert sha(Path(name).read_bytes()) == expected
out = OWN.parent / "receipt.json"
result = {"schema": "eoere_extended_cleats_publication_observation/v1", "passed": True,
          "observed_utc": datetime.now(timezone.utc).isoformat(), "commit": COMMIT, "pages_run": run,
          "served_assets": rows, "source_sha256": {**pins, str(OWN.relative_to(ROOT)): sha(OWN.read_bytes())},
          "viewer_url": BASE + "?model=eoere-extended-cleat-frame-development&view=rear",
          "preview_url": BASE + "?model=eoere-extended-cleat-2026-development&view=rear",
          "browser_or_CAD_or_mechanics_run": False, "physical_acceptance": False,
          "retention": "Active publication observation; existing raw/review sources remain active and unpruned."}
with out.open("x") as stream: stream.write(json.dumps(result, indent=2) + "\n")
print(json.dumps({"passed": True, "receipt": str(out), "sha256": sha(out.read_bytes()), "served_assets": len(rows)}))
