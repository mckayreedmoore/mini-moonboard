"""Freeze an actual foot100 upper-leg crop for a rigid-pin contact coupon."""
import hashlib
import json
import subprocess
from pathlib import Path

import cadquery as cq

from mini_moonboard import box_frame as b
from mini_moonboard import footprint_frame as frame
from mini_moonboard.hybrid import leg_normal

SOURCES = ('mini_moonboard/footprint_frame.py', 'mini_moonboard/shallow_frame.py',
           'mini_moonboard/hybrid_frame.py', 'mini_moonboard/hybrid.py',
           'mini_moonboard/box_frame.py', 'fea/prepare_joint_contact.py')


def reuse_snapshot(directory):
    """Never invalidate prior decks/results by rewriting their shared STEP."""
    if not directory.exists() or not any(directory.iterdir()):
        return False
    try:
        info = json.loads((directory/'geometry.json').read_text())
        expected = {p: hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in SOURCES}
        valid = (info['candidate'] == '2x8-foot100' and info['source_sha256'] == expected
                 and info['step_sha256'] == hashlib.sha256((directory/'leg.step').read_bytes()).hexdigest())
    except (OSError, ValueError, KeyError):
        valid = False
    if not valid:
        raise ValueError('Existing contact snapshot is incomplete or changed. Archive the complete '
                         'fea/generated/joint_contact directory manually before preparing a new generation; '
                         'nothing was overwritten.')
    return True


def main():
    directory = Path('fea/generated/joint_contact')
    if reuse_snapshot(directory):
        print('Reusing verified contact snapshot unchanged')
        return
    directory.mkdir(parents=True, exist_ok=True)
    shape = next(p.shape for p in frame.parts(100, False) if p.name == 'leg_right')
    normal = leg_normal('2x8')
    shape = shape.intersect(b.block(b.HALF+b.THICKNESS-1, b.HALF+2*b.THICKNESS+1,
                                   1480, 1880, normal-100, normal+100)).clean()
    bolts = [c for c in frame.connections() if c.name.startswith('analysis_leg_wall_bolt_right_')]
    for c in bolts:
        shape = shape.cut(cq.Solid.makeCylinder(5, c.length+2, c.start-c.direction, c.direction)).clean()
    shape = shape.translate(-b.point(0, 0, 0)).rotate((0, 0, 0), (1, 0, 0), -50).translate(
        (-b.HALF-b.THICKNESS, -1480, -normal))
    if not shape.isValid() or len(shape.Solids()) != 1:
        raise ValueError('Invalid contact coupon')
    step = directory/'leg.step'
    cq.exporters.export(shape, str(step))
    info = {'candidate': '2x8-foot100', 'model': 'rigid-pin/leg-bore coupon NOT complete leg/rim joint',
                'geometry_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
                'source_sha256': {p: hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in SOURCES},
                'step_sha256': hashlib.sha256(step.read_bytes()).hexdigest(),
                'stations_mm': [60, 140, 260, 340], 'hole_radius_mm': 5, 'thickness_mm': 38.1,
                'coordinates': 'X across thickness; Y uphill S minus1480; Z backing N minus74.075',
                'assumptions': 'Actual upper-leg crop; only four primary bolt bores, secondary holes omitted. '
                'Four fully fixed rigid pins replace rim-side anchorage: no rim flexibility, bolt bending, '
                'washer/preload, member face friction, glue layers, orthotropy, damage or strength rating. '
                'Driven lower crop face is guided in all translations; imposed slip is conditional, '
                'not a whole-frame force or service-load derivation.'}
    (directory/'geometry.json').write_text(json.dumps(info, indent=2)+'\n')


if __name__ == '__main__':
    main()
