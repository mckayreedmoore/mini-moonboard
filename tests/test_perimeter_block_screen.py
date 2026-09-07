"""Read-only packaging trials, NOT selected blocks, joints or design dimensions.

These envelopes locate obstacles in the existing clip variation. They do not
include new fasteners or establish material, edge-distance or tool suitability.
"""
import cadquery as cq
import pytest

from mini_moonboard import box_frame as b
from mini_moonboard import clip_frame
from mini_moonboard.box_exports import overlap


@pytest.fixture(scope="module")
def existing_geometry():
    return ({p.name: p.shape for p in clip_frame.parts()},
            {c.name: cq.Compound.makeCompound(c.components())
             for c in clip_frame.connections()})


def collisions(trial, shapes):
    # Reuse the existing exact-solid overlap gate; retain intentional failures.
    volumes = {name: overlap(trial, shape) for name, shape in shapes.items()}
    return {name: volume for name, volume in volumes.items() if volume > .01}


def test_ten_rear_block_trials_preserve_actual_transition_conflicts(existing_geometry):
    parts, hardware = existing_geometry
    checked = 0
    for side, sign in (("left", -1), ("right", 1)):
        x0, x1 = sorted((sign*b.HALF, sign*(b.HALF-76.2)))
        trials = {
            "main_bottom": b.block(x0, x1, 10, 78.9, 38.1, 76.2),
            "main_seam": b.block(x0, x1, 1159.35, 1279.05, 38.1, 76.2),
            "main_top": b.block(x0, x1, 2359.5, 2428.4, 38.1, 76.2),
            "kicker_bottom": cq.Solid.makeBox(x1-x0, 38.1, 40, cq.Vector(x0, -112.2, 5)),
            "kicker_top": cq.Solid.makeBox(x1-x0, 38.1, 40, cq.Vector(x0, -112.2, 180)),
        }
        for label, trial in trials.items():
            assert trial.isValid() and len(trial.Solids()) == 1
            body_hits, hardware_hits = collisions(trial, parts), collisions(trial, hardware)
            if label == "main_bottom":
                assert set(body_hits) == {f"cheek_splice_{side}"}
                assert body_hits[f"cheek_splice_{side}"] == pytest.approx(67896.875, abs=.001)
                assert set(hardware_hits) == {f"cheek_splice_{side}_3"}
            elif label == "kicker_top":
                assert set(body_hits) == {f"cheek_splice_{side}"}
                assert body_hits[f"cheek_splice_{side}"] == pytest.approx(34.728, abs=.001)
                assert hardware_hits == {}
            else:
                assert body_hits == hardware_hits == {}, (side, label, body_hits, hardware_hits)
            checked += 1
    assert checked == 10


def test_shorter_kicker_top_trial_avoids_existing_solids_only(existing_geometry):
    parts, hardware = existing_geometry
    for _, sign in (("left", -1), ("right", 1)):
        x0, x1 = sorted((sign*b.HALF, sign*(b.HALF-76.2)))
        # Global Z=180..218 removes the small original clash. This is a
        # packaging observation, not permission to use a 38 mm structural block.
        trial = cq.Solid.makeBox(x1-x0, 38.1, 38, cq.Vector(x0, -112.2, 180))
        assert collisions(trial, parts) == {}
        assert collisions(trial, hardware) == {}
