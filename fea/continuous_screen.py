"""Freeze a current continuous-frame moment screen; not structural approval."""
import json
from pathlib import Path

from fea.lean_screen import ASSUMPTIONS, candidate_report, manifest_sources
from fea.prepare_easy_structural import digest, locations, mass_state


def main():
    from mini_moonboard import continuous_frame as frame

    output = Path("fea/results/continuous-frame/stability.json")
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite frozen evidence: {output}")
    manifest = Path("exports")/frame.KEY/"manifest.json"
    sources = manifest_sources(manifest)
    sources.update({name: digest(name) for name in (
        "fea/continuous_screen.py", "fea/lean_screen.py",
        "fea/prepare_easy_structural.py", "fea/user_load_envelope.py")})
    sources[str(manifest)] = digest(manifest)
    report = candidate_report(mass_state(frame.parts(True)), locations())
    report.update(candidate=frame.KEY, assumptions=ASSUMPTIONS, source_sha256=sources)
    if any(digest(name) != sha for name, sha in sources.items()):
        raise ValueError("Source changed during screening")
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x") as stream:
        stream.write(json.dumps(report, indent=2, allow_nan=False)+"\n")
    print(json.dumps(report["summaries"], indent=2))


if __name__ == "__main__":
    main()
