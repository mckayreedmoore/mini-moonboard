import tempfile
from pathlib import Path

import cadquery as cq
import ocp_vscode
from cadquery import exporters


def main() -> None:
    part = cq.Workplane("XY").box(10, 20, 3)
    bounds = part.val().BoundingBox()

    out_dir = Path(tempfile.mkdtemp(prefix="cq-verify-"))
    step_path = out_dir / "box.step"
    exporters.export(part, str(step_path))

    print(f"cadquery={cq.__version__}")
    print(f"ocp_vscode={getattr(ocp_vscode, '__version__', 'unknown')}")
    print(f"bounds=({bounds.xlen:.1f}, {bounds.ylen:.1f}, {bounds.zlen:.1f})")
    print(f"step={step_path} size={step_path.stat().st_size}")


if __name__ == "__main__":
    main()
