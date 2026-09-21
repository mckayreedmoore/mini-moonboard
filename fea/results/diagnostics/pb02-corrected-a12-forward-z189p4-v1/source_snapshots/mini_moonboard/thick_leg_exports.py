"""Export the unselected centered 4x6 pivot with explicit development metadata."""
import argparse
from pathlib import Path

from . import no_shoes_exports as shared
from . import thick_leg_frame as model


def sources():
    return {**shared.sources(), **{str(path.relative_to(shared.ROOT)): shared.digest(path)
            for path in (Path(__file__).resolve(), Path(model.__file__).resolve())}}


def metadata(parts, connections):
    # Panel, kicker, electrical and hold datums are retained from the baseline.
    return {**shared.design_metadata(parts, connections), 'key':model.KEY,
            'status':'4×6 centered ⅝-inch pivot · development option · NOT build-ready',
            'description':model.LIMITS, 'leg_stock':'4x6', 'outer_rim_stock':'4x6',
            'physical_pivot_behavior_established':False,
            'joint_note':'Legs remain bolted to the frame. Free relative rotation is an analysis assumption, not an established property of the tightened joint.'}


def export(root=Path('site')):
    return shared.export(root,candidate=model,metadata=metadata,source_reader=sources)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=Path('site'))
    parser.add_argument('--check',action='store_true')
    args = parser.parse_args()
    print(shared.check(args.root,candidate=model,exporter=export) if args.check else export(args.root))
