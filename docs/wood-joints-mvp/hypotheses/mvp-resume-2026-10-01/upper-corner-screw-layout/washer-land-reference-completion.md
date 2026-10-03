# Actual top-side washer support and reference completion

## Scope and current status

This is a parent-executed continuation of the completed generic washer-land
packet. The parent completed `rawlocal/washer-land-reference-completion/attempt01`
with status `COMPLETE_MATCHED_TOP_SIDE_NOMINAL_REFERENCES`: all eight actual
top-side annuli are supported, all 48 geometry queries are finite and all 48
fresh own-end force/moment states are bound. The worker authenticated the
returned receipt and its 245 source pins and nine output artifacts; it did not
execute the producer or geometry queries.

The reviewed joint geometry, frozen response, hardware profiles and previous
packets are preserved. All complete-joint, fabrication and physical release
flags remain false. This packet does not qualify a joint or assign a washer
capacity.

## Completed parent result

The actual annulus returned inward support fraction 1.0 and outward overlap
fraction 0.0 at all three depths for every head and nut end of top-side bolts
1 and 2, left and right. All eight seat-plane checks succeeded. The child exited
zero after 2.3203 seconds within the fixed 120-second bound.

| Same-state reference | Witness and value |
| --- | --- |
| Peak mean/reference ratio | `k12-right`, right top `side_2`, head on `base_side_right`: 0.3876062484 |
| Mean wood pressure at that witness | 1.670281880 MPa against the declared 4.309223308 MPa base reference |
| Simultaneous force and own moment there | T = 508.9271523 N; M = 2524.746099 Nmm |
| Peak own-end moment | Same case and bolt, nut on `top_outer_right_cleat`: M = 2539.363827 Nmm; T = 508.9271523 N |
| Peak eccentricity | `k12-rear`, left top `side_2`, head: 5.454495054 mm; T = 116.9152322 N; M = 637.7135556 Nmm |

This closes the actual-profile nominal support and mean/reference applicability
gap. It does not turn the mean ratio into a peak-pressure, washer-stress or
complete-joint result. The previous quarter-inch clipping result remains a
preserved generic probe observation.

| Completed artifact | SHA256 |
| --- | --- |
| `attempt01/receipt.json` | `0218731514788a808ea8cb313945fe1000cbf63b51c181c9415b366ab374a46a` |
| `attempt01/washer-land-reference-completion.json` | `63579cdf8ec20291170d189f558255bb6ec54768f809c730c56263cca9b0fc63` |
| `attempt01/own-end-references.jsonl` | `472a16e81db38f24ba348de275e01cf565385bb5160cb41a3c6a727ba8a565c4` |
| Consumed producer snapshot | `96c8f7c0e2e47ff7bf6d31491b4ae2327ad0251252c7a256f65c6b92caa54273` |

## Correction to the generic probe interpretation

The completed 120-probe packet queried a quarter-inch generic washer annulus
with inner/outer radii 4.1529/9.2329 mm. Eight top-side seats returned about
0.955831947 inward support fraction because that generic inner radius is smaller
than the actual 4.5 mm bore radius. Their outward overlap was zero.

The frozen top-side load source uses a **5/16-inch bolt and washer profile**:

| Study quantity | Value |
| --- | ---: |
| Bolt diameter | 7.9375 mm |
| Timber bore diameter | 9.0 mm |
| Washer inner diameter | 9.906 mm |
| Washer outer diameter | 22.0472 mm |
| Washer thickness hypothesis | 1.6256 mm |
| Circular head/nut pressing radius hypothesis | 6.0 mm |

The actual washer inner radius, 4.953 mm, already exceeds the bore radius. The
generic 4.4% area deficit therefore does not establish a support deficit for
this washer. Its outer radius, 11.0236 mm, exceeds the generic queried radius,
so the prior result also does not establish support for the larger actual ring.
The new queries resolve that specific applicability gap without changing a bore,
washer, seat or receiver.

## Bounded parent execution

Producer: [washer-land-reference-completion.py](washer-land-reference-completion.py).
Import is inert; the callable API is `build(output: Path)`.

From the repository root, the parent runs:

```sh
uv run --no-sync python docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/washer-land-reference-completion.py --output docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/washer-land-reference-completion/attempt01
```

The output must be a fresh, unaliased immediate child of the named raw folder.
The producer authenticates the generic packet, its source and artifact pins,
the fresh corner response, actual profile and reused methods. It launches one
child with a fixed 120-second timeout and preserves logs, the producer snapshot,
probe progress, results and source hashes. There are no automatic retries or
additional probe depths.

The child reuses the unchanged worker in
[washer-land-completion.py](washer-land-completion.py), SHA256
`e6e42f901d08042c1c3ef1045af9b3f3cf0aea65bb1bcf8b051978bdc18ba0aa`.
It imports the same four effective STEP solids once each. The eight physical
seats are head and nut ends of side bolts 1 and 2 at both top corners. Each
receives three inward and three outward annular slab queries at
0.01, 0.05 and 0.1 mm: **48 geometry queries** in total. Only the probe annulus
changes to inner/outer radii 4.953/11.0236 mm. Current points, inward normals,
plane checks, source tolerances and STEP bodies are reused.

These are mean annular slab intersections from the seat to the stated depth,
not zero-thickness sections or loaded contact masks. Inward support and outward
overlap remain separate. All eight actual rings must have a matching seat plane,
full inward support and negligible outward overlap within the retained tolerance
before means are bound.

## Same-state demand and mean references

The separate **48 demand rows** are six cases times eight physical ends. Each
row retains its own bolt tension, signed force on its receiver, signed own-seat
moment, moment magnitude, seat point and inward normal from the fresh
simultaneous corner response. The producer checks the force sign, transverse
moment, saved contact moment and role/receiver/datum correspondence. A global
moment peak is never paired with a different state's tension.

For an established full actual ring, the declared mean wood-pressure reference
is `T / (pi * (11.0236**2 - 4.953**2))`. Its comparison uses the existing dry
DF-L No. 2 base perpendicular-to-grain compression hypothesis, 625 psi
(4.309223308 MPa). This reports a mean/reference ratio; it does not calculate
peak contact pressure, load-duration adjustments, timber splitting, group
applicability or complete timber resistance.

Output `own-end-references.jsonl` contains the 48 joined demand rows. The main
JSON reports separate tension, own-moment, eccentricity and mean/reference
peak witnesses, each with its own simultaneous tension and moment. It reports
`COMPLETE_MATCHED_TOP_SIDE_NOMINAL_REFERENCES` only when all eight actual rings
are supported and every planned geometry query is finite. An unresolved land,
timeout or source change retains an open or stopped result.

## Existing washer mechanics references

The actual profile matches the `side` family in
[upper-right-washer-flexure.py](upper-right-washer-flexure.py), SHA256
`782ded96afd5e02e27873bd72b77073a643ed7c2a7946703a3240b1f51b21eac`.
The saved `rawlocal/upper-right-washer-flexure/attempt01/checks.json`, SHA256
`a6ac3fb5587ed24926e5fbc3353f69db19fb7fe8a60eb2dee40fa911b2f2544a`,
contains a degree-four free-edge Mindlin/contact study with 24 side-family and
24 rail-family states under older independent-pair loads. It is a reusable
method/profile reference, not a fresh simultaneous-load stress result. The
degree-six saved refinement covered a rail end and does not refine these side
washers.

[upper-right-washer-edge.py](upper-right-washer-edge.py), SHA256
`ffe3db3e8c707851d44f0c60c43e6e6ef4aa4845f753dc6880c64186e3c75e61`,
provides the existing sparse polar coarse/fine method. Its `make_model` selects
`FAMILIES['rail']`; a future explicit side-family call must supply the declared
side profile in that slot without changing its dimensions. No such call is run
by this completion producer. The retained hypotheses are steel modulus
200,000 MPa, Poisson ratio 0.3, yield comparator 250 MPa, wood seat stiffness
20 MPa/mm and head contact stiffness 10,000 MPa/mm. Fresh side-family fine
stress and actual steel yield remain unqualified.

## Frozen inputs and remaining limits

| Input | SHA256 |
| --- | --- |
| Generic land `attempt01/receipt.json` | `7d541cef4b05b03a6d501243759dd1ea435eeb42be4ce2d71eda27cd9ea78679` |
| Fresh `knee-bridge-corner-replay/attempt01/checks.json` | `e699b5c662992abab1f646236cdd4037feb425c5476458d8629899bcb9948976` |
| Conditional material inputs | `0f33ad8fd517673a4ebbed36c4a30c1cfe07e0d8163165bdc804af91d958fc5a` |

The existing generic 120-probe receipt remains valid as a generic applicability
record. Quarter-inch retail washer results and ordinary N10 reference rows
remain separate packets. Actual thickness and material, delivered head/nut
profiles, washer flexure under these fresh loads, loaded shift/tilt and frame
feedback are not resolved here. No plate, frame or native mechanics solve,
software test, hardware redesign, source-authority change or release claim is
part of this bounded run.
