# PB-02 displaced right-center clips: old duties and geometry

Status: bounded inventory on the named
[post/rear edge-reserve pose](simple-center-edge-reserve-probe.md).
No replacement joint, bolt demand, resistance, or drilling is established. This
packet covers only `clip_split_base_center_right` and
`clip_split_header_center_right`; the other 22 old ML24Z stations are outside it.
Coordinates use the frame's global XYZ in millimeters.

## Pose and old ownership

The nominal solid right post occupies X=88.75…177.65, Y=−175.7…−86.8,
Z=0…238.9. The single rear 2×4 cleat occupies X=89.05…177.95,
Y=−213.8…−175.7, Z=0…460. The post bolt axes are at X=140, Z=110/190;
the cleat-link bolt remains at X=114.45, Z=370. These are illustrative
pose coordinates, not selected fasteners. The edge-reserve CAD probe reports
both old clips displaced by collision with changed wood. Its nominal wood
clearances for the illustrative bores do not restore the old clips.

| Old station | Old timber path | Old clip origin | Clip local u / v | Inferred historical separation |
| --- | --- | --- | --- | --- |
| `clip_split_base_center_right` | `base_header` ↔ `base_principal_center_right` | (89.05, −124.9, 277) | +X / +Z | principal +Z from header; header −Z from principal |
| `clip_split_header_center_right` | `base_header` ↔ `base_post_center_right` | (89.05, −105.85, 238.9) | +X / −Z | post −Z from header; header +Z from post |

The header is the old beam-side host in both rows. Its live uncut CAD bounds
span Z=238.9…277; the old right principal starts at Z=277 and the old right
post ends at Z=238.9. Each partner's XY bounding interval overlaps the
header's. The extractor derives ±Z from these abutting old wood bounds and
stops if the relation changes. These are inferred historical face-normal
senses, not validated active contact normals in the changed pose. They do not establish
which direction is loaded in any new joint, nor a separation force. In-plane
X/Y transfer and moments likewise require a changed-topology action basis.

Each station used one purchased ML24Z and **six separately purchased Simpson
SDS25112** screws: `beam_1..3` into `base_header`, and `upright_1..3` into
the named principal or post. Thus this two-station inventory contains two
old angles and 12 old structural SDS axes. The CAD/schedule occupied shaft
is 38.1 mm long and 6.35 mm in diameter; those are modeled dimensions, not
a pilot or installation instruction. The extractor emits every old screw ID,
receiving timber, start XYZ, and installation direction. For the base clip,
beam screws point −Z and upright screws −X. For the header/post clip, beam
screws point +Z and upright screws −X. The six axes per clip are distinct;
they are not one through-bolt group.

## Old local action basis, bounded to the old topology

The [kerf-right reference packet](center-reference-diagnostic.json) has five
numerically accepted proxy cases with these exact station names, old wood
owners, and current old clip origins. The extractor checks their reported
convergence flags and records their reported source report/input SHA-256
digests, but does not independently authenticate the underlying artifacts.
It reports the signed
`via_clip` action on each old partner timber. Each force is N and each moment
is N·mm about that station's old origin, in global XYZ. The values include the
old ML24Z/SDS proxy behavior; direct timber transfer is excluded from this
table. Values below are rounded for reading; the script returns source
precision and reported report/input digests per case. The five cases are
incomplete old-topology context, not a full old-duty envelope.

| Case | Principal via old base clip: F XYZ; M XYZ | Post via old header clip: F XYZ; M XYZ |
| --- | --- | --- |
| a1-rear | (−22.284, 95.356, 15.136); (1890.008, −736.033, 1080.122) | (5.741, −64.677, 3.540); (−1056.241, −189.230, −156.418) |
| a12-left | (60.968, 138.275, −67.334); (4706.037, 2504.767, −1809.818) | (28.814, −137.403, 26.097); (−2662.253, −1073.272, 1027.502) |
| a12-rear | (−44.247, −126.593, 23.092); (10238.627, −1316.379, 3296.161) | (51.945, −118.534, 45.537); (−1818.387, −1921.146, 2788.389) |
| k12-rear | (42.406, 79.129, −54.350); (8918.364, 1904.310, −3.819) | (55.216, −87.677, 53.329); (−1913.069, −2118.376, 5148.605) |
| k12-right | (−44.012, 11.630, 23.428); (9778.262, −1314.904, 4001.226) | (20.762, −175.631, 16.310); (−1921.353, −732.176, 663.360) |

The archived selected-baseline [angle ledger](../floor-runner-mvp-angle-demands.json)
has six cases, but its base clip origin is Y=−135 rather than −124.9 mm.
Those values are not substituted here. The kerf-right proxy has no accepted
`a12-forward` case. Its five old-clip action vectors are neither a complete
old-duty envelope nor forces on proposed bolts. The changed post, cleats, and
removed clips alter load sharing; no old response is adopted as new demand.

## Duties still to replace

- Provide a verified header-to-principal path formerly supplied by the base
  clip and its three header plus three principal SDS attachments, including
  separation in either relevant sense, in-plane transfer, and moment action.
- Provide a separate verified header-to-post path formerly supplied by the
  header clip and its three header plus three post SDS attachments. The new
  post is displaced and cannot silently inherit the old receiver identity.
- Recover signed simultaneous actions and demonstrate the shared header and
  changed wood load path before any joint sizing or rating. The two duties
  meet at one header region but are not automatically one connection.

Ambiguity: nominal face separation is known; the active signed load direction,
new force split, changed receiver behavior, and complete case envelope are
not. This inventory makes no contact, half-lap, custom-metal, or panel change.
It does not assess replacement geometry or resistance.

The later [link-edge side-cleat trial](simple-center-link-edge-probe.md)
retains the post/rear bounds but changes the side cleat and illustrative link
axis. This extraction does not inspect that later trial. The old station
identities and displacement conclusion apply there only after its CAD and
connection inventory are checked for that exact trial.

Reproduce from the repository root with
`.venv/bin/python -m scripts.simple_center_displaced_clip_duties` (JSON on
stdout, no files written), then run
`.venv/bin/python -m pytest -q tests/test_simple_center_displaced_clip_duties.py`.
Sources are the live `compact_floor_flush_frame.py` station/connection model,
the kerf-right `connection-axes.csv`, the named post/rear edge-reserve probe,
and the reported old-proxy packet named above.
