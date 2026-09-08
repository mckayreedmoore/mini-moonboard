"""ESR-2236 nominal major diameter, not a manufactured maximum or pilot size."""
import cadquery as cq
import pytest
from test_mvp_fasteners import positive_overlap

from mini_moonboard import backing_end_relocated_trial as relocated
from mini_moonboard import backing_end_trial as end
from mini_moonboard import timber_connections as hardware
from mini_moonboard import wide_frame as frame

# January 2026 ESR-2236 section 3.2: 0.256 in major, not nominal 1/4 in.
MAJOR_MM = .256*25.4


@pytest.mark.parametrize("with_end_trial", [False, True])
def test_published_sds_major_envelopes_clear_hardware_and_fit_raw_receivers(with_end_trial):
    bodies = {p.name: p.shape for p in frame.parts()}
    raw = {p.name: p.shape for p in frame.wood_parts(True)}
    connections = relocated.connections() if with_end_trial else frame.connections()
    if with_end_trial:
        bodies.update({p.name: p.shape for p in end.brackets()})
    selected = [c for c in connections if isinstance(c, hardware.ConnectorScrew)]
    assert len(selected) == (116 if with_end_trial else 108)
    components = {c.name: c.components() for c in connections}
    for c in selected:
        components[c.name] = (cq.Solid.makeCylinder(MAJOR_MM/2, c.length, c.start, c.direction),
                              components[c.name][1])
    bounds, findings = {}, []
    for c in selected:
        thickness = end.REFERENCE["thickness_mm"] if c.name.startswith("trial_end_") else hardware.ML["thickness"]
        embedded = cq.Solid.makeCylinder(MAJOR_MM/2, c.length-thickness,
            c.start+c.direction*thickness, c.direction)
        assert embedded.cut(raw[c.members[1]]).Volume() < .01, c.name
        shape = components[c.name][0]
        for name, body in bodies.items():
            if name == c.members[1]:
                continue  # Intentional threads in the designated wood, not in steel.
            if positive_overlap(shape, body, bounds) > .01:
                findings.append((c.name, name))
        for name, shapes in components.items():
            if name != c.name and any(positive_overlap(shape, other, bounds) > .01 for other in shapes):
                findings.append((c.name, name))
    assert findings == [], findings
