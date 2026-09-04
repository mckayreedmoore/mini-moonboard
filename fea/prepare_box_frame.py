"""Export the current bulk frame for an explicitly ideal-bonded FEA screen."""
import json
from pathlib import Path

import cadquery as cq

from mini_moonboard.box_frame import HALF, LENGTH, frame_parts, point


def main():
    directory=Path("fea/generated")
    directory.mkdir(parents=True,exist_ok=True)
    parts=frame_parts(drilled=False)
    cq.exporters.export(cq.Compound.makeCompound([p.shape for p in parts]),str(directory/"box_frame_bulk.step"))
    info={"parts":[p.name for p in parts],
          "load_targets_mm":[point(x,LENGTH,-18).toTuple() for x in (-HALF,-HALF/2,0,HALF/2,HALF)],
          "assumptions":"Bulk geometry without holes/reliefs; all timber contacts perfectly bonded; fixed floor; isotropic screening E=7000MPa nu=.3. No joint strength validation."}
    (directory/"box_frame_bulk.json").write_text(json.dumps(info,indent=2)+"\n")
    print(directory/"box_frame_bulk.step")


if __name__=="__main__":
    main()
