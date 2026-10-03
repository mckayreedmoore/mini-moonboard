# Top rail: current local pressure placement at recorded bore sections

## Finite decision

The earlier [top-host net-section worksheet](top-host-net-sections.md) found a nominal compatible-face shear/reference index of **1.168694** under its conditional `CD=1.25` timber reference. Its deciding cut lies inside the top-right cleat footprint, where the original integrated-frame point allocation differs from the completed local joint load distribution. That original result remains preserved as a sensitivity.

This adapter replaces only the two top-cleat interfaces on `base_rail_top` with their frozen, compatible first-order `physical_host_actions`. It retains every other source member load, all six source cases, the 100 mm hold lever, the twelve existing rail stations, both before/after traces and both original duration references. The deliverable is **144 current-placement cuts and 288 finite nominal comparisons**. It does not produce a new frame response or qualify the complete joint.

Parent completed `rawlocal/top-host-physical-actions/attempt01`. Under the conditional `CD=1.25` reference, all 144 recorded current-pressure traces have sufficient nominal rectangle bounds below one; the peak is **0.976479**. The original `CD=1` comparison remains above one. Geometry, hardware, material laws, the full 47-criterion authority and all joint/release HOLD boundaries remain unchanged.

## Replacement and source binding

| Interface | Removed original operator rows | Current saved spatial actions per case |
| --- | --- | --- |
| Top-left cleat / top rail | 1800–1803; 1834–1851 | 48 bore station resultants, 512 washer quadrature measures, 16 face cells |
| Top-right cleat / top rail | 1808–1811; 1870–1887 | Same census |

The four lateral rows, sixteen face rows and two axial ties are removed once per interface. Numeric row IDs, exact string identities and both incident bodies must match the authenticated operator inventory. Saved local washer forces already carry the bolt-end rocking effect; original axial ties and additional end couples are not superposed.

The producer authenticates the original section receipt, executed snapshot, member arrays, current first-order receipt, contact geometry and helper bytes. It inherits their source closure, including the finished STEP, material and original response evidence. Preparation found **102 unchanged input pins**; the running producer adds its own hash. It does not load those STEP files into CAD.

| Deciding frozen input | SHA-256 |
| --- | --- |
| Original section `attempt02/checks.json` | `7e0977645a79d11b3456ff82cc987f2466becd135f192e6aca3c4c53875487a9` |
| Original section receipt | `486b7d5f5da12e78e94b0deb0c2ab8631f27c1992ee9b49f32c0554249eeff29` |
| First-order local joint `checks.json` | `b15b57d3879fdca2dac607d11a2ad127acd1008f6c2a6f546333a1b26c754cfe` |
| `top-corner-contact-geometry.json` | `987af6908d6677165b6a712537ecca0c02827d558ca386ced96f4c1f6436008f` |
| Contact geometry producer | `a077c8636f504a2d4a7437f0f68722411c16911dbddc2734a96e444bf2b4655a` |

## Practical placement assumptions

### Face contact

The owner-directed MVP assumption is uniform pressure within each **source-clipped** face cell. The authenticated contact producer creates a 4×4 rectangular mask grid and intersects each mask with the finished cleat face. Its saved cells are clipped areas and centroids; equal gross rectangles would incorrectly put pressure over the two rail bolt holes.

The adapter reconstructs those finite masks analytically from the authenticated face polygon and subtracts the known circular bore-mouth fragments. Circle-strip area and first moments are integrated exactly. Every saved cell area and GLOBAL centroid, the finished whole-face area and the operator/contact-row binding must match. The patch must remain on the supported rail face, within its stock bounds and outside additional openings. A circle crossing an unsupported grid boundary or any unexplained trim raises `STOP`.

At each grain cut, supported negative-half area and first moments give that cell's partial force and moment. The uniform pressure is the saved force divided by the reconstructed supported area; it must agree with the saved pressure/force record within existing accounting tolerances. Zero-force cells remain zero. No pressure acts through a bore or outside the polygon, and no balancing free couple is introduced.

### Bore contact

All 24 original axial Gauss measures per bolt remain unchanged. Each saved host point and force must match its bolt field. The adapter reuses [corner-bore-wall.py](corner-bore-wall.py)'s explicit, nonunique half-cosine radial pressure hypothesis and exact angular force/moment integration on the actual 7.5 mm cylindrical walls.

The helper checks full-circumference support in retained stock and clearance from other bores. Each angular partition must recover its complete signed force and torque. A radial offset crossed with its own radial force contributes zero torque; the actual axial-station moment arm supplies the moment. This is a declared pressure placement, not a uniquely recovered timber contact solution.

### Washer contact

The exact saved 8-radial × 32-angular weighted pressure measures are retained for each host washer. Their identities, 256 indices per bolt, pressure/area/force relation and supported annular points are checked. Their actual grain positions determine which half receives each measure.

This uses the frozen finite quadrature measure. It does not fit a new continuous annular pressure field or bound the error of a grain cut through that quadrature. The original hypothetical seat law and washer assumptions remain visible; catalog washer acceptance or new flexure behavior is not transferred here.

## Force and torque accounting

Each of the twelve case/interface groups records all removed row identities, original and replacement spatial actions, bore profiles and full wrenches at the same rail-start datum. Both saved-action replacement and represented full pressure placement must recover the original interface wrench. Existing rail-method accounting tolerances remain **0.001 N and 0.2 N mm**; they are unchanged numerical bookkeeping tolerances, not physical margins.

For a cut, the adapter independently replays the original complete signed member wrench. It then removes the original target-interface negative-half contribution and adds the supported current negative-half contribution. Every other point force and free couple is retained. The negative-half internal sign is preserved. Continuous face and wall placement gives the same limit on both sides of a station unless a retained discrete measure lies there; original unrelated point loads retain their source partition rule.

The frozen nominal-section helper translates moments to the actual net centroid and recovers all six signed components after regional sharing. The prior common longitudinal strain, transverse area sharing and equal-modulus rectangular common-twist assumptions remain unchanged. Four signed face-midpoint vectors retain same-face torsion/transverse additions and cancellations. An exceeded face reference is an exceedance within that declared nominal field; a face maximum below one alone does not bound its interior. The sufficient rectangle and original scalar bounds are reported separately.

Both `CD=1` and the parent's conditional `CD=1.25` peak timber references are retained. No bolt, washer or panel allowance gains that multiplier here. No splitting/local concentration, end-bridge strength, full orthotropic perforated-body stress, new global compatibility feedback or continuous station maximum is claimed.

## Parent execution

API: `build(output: str | Path) -> dict` in [top-host-physical-actions.py](top-host-physical-actions.py). It requires a fresh owned child beneath `rawlocal/top-host-physical-actions` and refuses existing output directories.

```sh
.venv/bin/python docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/top-host-physical-actions.py --output docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/top-host-physical-actions/attempt01
```

Parent owns serialized finite arithmetic. The worker prepared the two scoped files, inspected source schemas, authenticated fixed inputs, parsed the producer and checked Ruff formatting/lint. The worker ran no producer, software tests, frame/native/CAD solves or review loop.

The adapter reauthenticates inputs after calculation and writes ignored `checks.json`, `receipt.json` and `producer.py.snapshot`. Its compact return includes both duration scenarios' deciding witnesses and accounting residuals. All inherited qualification and physical-release flags remain false.

## Completed parent result

The worker authenticated the parent's checks and receipt, both output hashes and all **103 recorded source pins**, including the unchanged producer bytes. The completed census is twelve stations, 144 signed traces and 288 duration comparisons. No second arithmetic run or review loop was performed.

| Current pressure placement comparison | Original `CD=1` | Conditional peak `CD=1.25` |
| --- | ---: | ---: |
| Signed same-face shear/reference peak | **1.220531** | **0.976425** |
| Sufficient nominal rectangle-bound peak | **1.220599** | **0.976479** |
| Diagnostic normal reference-sum peak | 0.168236 | 0.134589 |
| Traces with a declared face exceedance | 14 | **0** |
| All recorded sufficient bounds below one | No | **Yes** |

The deciding current-placement trace is **K12-right, before 2210.3953125 mm**, region 0, `u-` face. This is a recorded station within the right bore interval, 1.5796875 mm before its center. Same-face transverse v shear **0.241707 MPa** and torsional v shear **1.273041 MPa** add to **1.514748 MPa**, compared with the conditional reference **1.551320 MPa**. The current signed complete cut is `[-706.541178, -20.405250, 774.146978, -43549.904659, -21320.378819, 25474.861296]` in grain/u/v N and N mm. The sufficient bound leaves approximately **2.35% of the declared reference**; that is a small conditional model margin, not a measured physical reserve.

For the same conditional reference, the earlier original point allocation had peak face index **1.168694** and eight exceeded traces. Current supported pressure placement reduces that peak to **0.976425**, with zero exceeded traces and a sufficient bound below one at every recorded trace. Both results remain preserved with their load-allocation assumptions.

| Accounting check | Largest recorded residual |
| --- | ---: |
| Whole replacement force | `1.20e-6 N` |
| Whole replacement moment | `5.23438e-4 N mm` |
| Represented pressure force versus saved actions | `2.84e-12 N` |
| Represented pressure moment versus saved actions | `5.12e-9 N mm` |
| Regional force recovery | `2.27e-13 N` |
| Regional moment recovery | `1.46e-11 N mm` |

These recoveries retain the complete simultaneous interface loads; the changed interior cut follows their spatial distribution. Accounting success alone supplies no additional resistance or joint acceptance.

| Artifact | SHA-256 |
| --- | --- |
| Executed producer snapshot / unchanged live producer | `0f005656656d26d1003c3ff4317c696172f2399de438c287ff9a8ea12e926b49` |
| `attempt01/checks.json` | `fe36bd516c29286e632a82df31be44f28ae49c621947962dd195e4269d0c923c` |
| `attempt01/receipt.json` | `4b6ae2e4cb9b4dd4ea6be1914c669c00e0dfeabc15281fc9e2868d1f980add93` |

## Practical next decision

This finite result supports retaining the current top-rail geometry in the parent's conditional working scenario. Its conclusion depends on `CD=1.25`, the declared local seat/bolt laws, uniform pressure on source-clipped face cells, the bore pressure hypothesis and the saved washer quadrature. The original `CD=1` reference still exceeds at fourteen traces. The small conditional margin gives no basis to erase these assumptions.

Parent should integrate this scoped result alongside the current bottom-corner replay and existing joint ledger. Local bore concentrations/splitting, pressure-placement uncertainty, end-bridge behavior and complete-joint qualification retain their recorded boundaries. No new geometry correction or qualification claim follows from this receipt.
