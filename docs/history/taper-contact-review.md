# Runner/leg contact review

The six preserved taper cases omit member-face contact and contain no clearance
monitors. Their passing empty-list gap flag does not establish that these
interfaces stay separated.

`scripts/taper_contact_review.py` recovers C3D20 nodal displacements from the
final native DAT files using the saved model meshes. It checks affine point
reconstruction and samples the coincident rear runner/leg side faces and the
separated runner-top/taper surfaces. This is a small-displacement, sampled
comparison, not an entire-surface contact solution.

[Recovered results](taper-contact-review.json) show side-face interpenetration
up to **0.5530 mm** (K12-right, right leg). The smallest sampled top clearance
is **1.9074 mm** (A12-rear, left leg). Thus the top gap remains open at the
samples, but the omitted touching-face contact cannot be dismissed as inactive.

The fresh flush revision uses an explicit compression-only face-contact model
at all six bolted timber joints, with no tangential friction or composite-action
credit. Its triangular area quadrature, stiffness and sensitivity still require
assessment. The initial setup uses 72 points, subtracts bore area uniformly,
rejects points in bolt bores and adds 18 explicit top-clearance monitors.
The old result is not relabeled as a contact-enabled pass.
