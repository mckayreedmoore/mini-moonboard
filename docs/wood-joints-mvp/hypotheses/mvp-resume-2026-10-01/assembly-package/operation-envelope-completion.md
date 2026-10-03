# N16 operation-envelope completion

The [producer](operation-envelope-completion.py) supplies concrete, finite
operation queries for all **104 original bolt-axis identities**, with their
eight named current top-correction planning stacks, and, separately, the
**four unadopted internal knee ties**. Reviewed station provenance and current
corrected geometry remain distinct. The parent's bounded exact continuation
completed **120 modeled route slots, 120 enclosure refusals and 192 unknowns**
in 222.564 seconds. These are scope/axis/stage slots, not distinct axes or
physical operations. The completed [actual batch and witness classification](#completed-exact-batch-and-witness-classification)
retains every refusal and unknown. **No preparation
or geometric comparison has been run by this worker, and N16 is not qualified
or closed.** Source authentication/joins, standard-library postprocessing,
AST parsing and Ruff are the only checks performed here.

The maintained [qualification register](../upper-corner-screw-layout/qualification-register.md)
defines N16 as full modeled turning, counterhold, installation and reverse
removal. N17 station datums, N18 tolerance/loaded clearance and N19 finished
geometry remain separate. This leaf changes no scene, member, hole, axis,
hardware order, load, acceptance criterion or physical flag. The selected
screw-and-angle candidate retains its separate authority.

## Frozen inputs and reuse

The existing [shop guide](shop-guide.md), [joint hardware map](joint-hardware-map.md),
[knee fit](knee-bridge-fit.md), [length fit](hardware-length-fit.md) and
[wire sequence](../../../current-retained-wire-sequence.md) remain unchanged.
The producer consumes the saved component arithmetic from
`rawlocal/ordinary-n-envelope/attempt01/envelope.json`, not its unadopted N17
datum comparisons. That supplies 540 five-role component enclosures for 108
axes, including current nominal lengths and thicker top-rail washers.

The obstacle map comes from the saved knee-fit preparation. Existing hardware
obstacles are replaced by those already frozen planning components, leaving
all timber, panel, screw, T-nut, light and wire entries available. The 104
screen uses the original knee spines. The separate 108 screen substitutes only
the two **already saved** proposal spine STEP files and includes four new
stacks. Neither screen regenerates a member or the complete scene.

Literal seed pins are in `PINS`. Preparation also authenticates the saved
envelope receipt, expands its source closure and the saved scene closure,
checks reused top-fit snapshots, binds the two saved proposal STEP hashes,
and binds the maintained producer bytes. Sources are checked before
publication and again afterward. Run output binds the prepared setup receipt
and rechecks sources before and after the comparisons. A changed input stops
the operation; the API does not adopt new hashes.

### Parent preparation STOP and external-source authentication

The parent's `prepare-parent01` stopped in `_verify` because its containment
check rejected `/tmp/nds2024-ch3.pdf`, although this PDF is an inherited source
in the frozen knee-fit closure and its authenticated top-fit snapshot manifest.
Read-only inspection found its bytes match the original expected SHA-256
`205df74e16f632dfe78211e99bfa5dfa8b9f8dd316e9c5fa1316493f795ec644`.
It is the only external path in the two consumed source closures. No source
was repinned, downloaded or altered.

The corrected guard permits precisely that literal path and digest, still
requires its resolved path to be that exact path, and verifies file bytes at
every original checkpoint. Unlisted external paths and changed hashes remain
rejected. The fresh immediate-child output guard is unchanged; this exception
grants no writes outside the owned output location.

The STOP preceded creation of an owned preparation output. Preserve its
**43,515-byte producer**, SHA-256
`10d9370ac812cb964ad9765998d49c0e57ce5909ee47c5baf7b835cbf3d3ffd9`,
through this lossless inverse edit of the corrected producer (or its next
prepared producer snapshot), specifically the preserved `6f2518` revision.
The current station-adapter revision is not that recovery input.
The reconstruction is read-only and verifies
the original bytes; the parent may retain them in its own frozen attempt
record. This keeps recovery within the two owned maintained leaves without
changing any historical/raw/tmp source.

```python
from hashlib import sha256
from pathlib import Path
import sys

corrected = Path(sys.argv[1]).read_bytes()  # Parent's preserved prepare-parent02 source snapshot.
if sha256(corrected).hexdigest() != "6f2518c74a3f08fc427eb5247b9f1740e9a59d047e35685f2e4e9b7e03af2b7d":
    raise ValueError("Use the preserved 6f2518 preparation source")
allowlist = b'''INHERITED_EXTERNAL_PINS = {
    "/tmp/nds2024-ch3.pdf": "205df74e16f632dfe78211e99bfa5dfa8b9f8dd316e9c5fa1316493f795ec644",
}
'''
corrected_guard = b'''        approved_external = (
            relative in INHERITED_EXTERNAL_PINS
            and path == Path(relative)
            and digest == INHERITED_EXTERNAL_PINS[relative]
        )
        require((path.is_relative_to(ROOT) or approved_external) and path.is_file() and sha(path) == digest,
'''
original_guard = b'''        require(path.is_relative_to(ROOT) and path.is_file() and sha(path) == digest,
'''
if corrected.count(allowlist) != 1 or corrected.count(corrected_guard) != 1:
    raise ValueError("Use the corrected preparation revision or its frozen snapshot")
stopped_producer_bytes = corrected.replace(allowlist, b"", 1).replace(corrected_guard, original_guard, 1)
if len(stopped_producer_bytes) != 43515 or sha256(stopped_producer_bytes).hexdigest() != "10d9370ac812cb964ad9765998d49c0e57ce5909ee47c5baf7b835cbf3d3ffd9":
    raise ValueError("Stopped producer recovery mismatch")
```

The parent subsequently prepared fresh `prepare-parent03`. The worker has
performed only source authentication, byte recovery, AST parsing and Ruff;
neither preparation nor a geometric query, CAD run, software test or staging
operation was executed by the worker.

### Parent preparation STOP and current top-station authority

The parent's `prepare-parent02`, producer SHA-256
`6f2518c74a3f08fc427eb5247b9f1740e9a59d047e35685f2e4e9b7e03af2b7d`,
stopped at the 0.005 mm station join for
`top_outer/clip_single_top_left_1/side_1`. The original manifest's descriptive
axis point remains `[-1119.632, 1410.7798853414977, 2131.9811378403647]` mm.
The genuine current correction records
`[-1119.632, 1383.2203665660159, 2099.1369823506348]` mm. The saved current
planning shaft underhead is
`[-1221.8416, 1383.2203665660159, 2099.1369823506348]` mm, exactly on the
corrected pure-X line. Comparing this shaft to the old station gives the
recorded 42.875 mm perpendicular relocation; it is not a tolerance error.

The adapter now uses the literal `proposed_axis_point_mm` in the frozen
[top correction](../top-corner-correction/proposal.json) for all eight corrected
top identities. Head-to-nut direction comes from its named head approach's
`outward_axis_xyz`, with its sign reversed. Every current component must still
equal its frozen corrected-scene cylinder, and the original identity must
join the correction's `old_axis_point_mm`. The original **0.005 mm** line
guard and **1e-8** orientation guard remain intact. No shift is synthesized;
no component geometry is moved by this fix.

| Named current side axis | Recorded local-T relocation |
| --- | ---: |
| `top_outer/clip_single_top_left_1/side_1` | −42.875 mm |
| `top_outer/clip_single_top_left_1/side_2` | −8.025 mm |
| `top_outer/clip_single_top_right_2/side_1` | −42.875 mm |
| `top_outer/clip_single_top_right_2/side_2` | −8.025 mm |

The four corresponding `rail_1/rail_2` lines retain their original stations;
their current grip/profile/washer components still bind to the correction.
Preparation records 96 original station authorities, eight current top
authorities, the four relocated side IDs and four separately named new ties.
Each axis records its station source/hash/pointer and historical contract
point. The `reviewed_104` scope denotes original inventory membership plus
the explicit current planning corrections; it does not certify unchanged
reviewed geometry for those eight stacks. The 108 scope adds only the four
unadopted internal ties and their two saved proposal spines.

Historical movement rows retain their identity/recipe provenance. The eight
current top stacks use the complete current nominal-shaft-length withdrawal
bound, without using an old movement station or old receiver-extrema travel.
Original `prepare-parent01/02` STOP records and the parent's preserved
43,851-byte `6f2518` source snapshot remain evidence. The worker modifies only
the two owned maintained leaves. Parent preparation `prepare-parent03`
succeeded and owns the actual bounded queries; this source join is not
operation qualification.

| Frozen record | SHA-256 |
| --- | --- |
| Component envelope | `278407d84e0061ab845ff73fb31dfc5551300a3afb9aa20327a5cca9e6b86ffc` |
| Envelope receipt | `8cec13103d82b262cdbd9446aefb2227ecc0270ebb241999366bc1be8f690fc2` |
| Knee-fit setup | `794f1aa45fa9f47955f16a083a3637b2821615ede47640817305a60ddab4ddfb` |
| 108 proposal manifest | `4c0d10a86a6018813b5f8efcd7f438662037e458ef3f2ce535d1e0860ca25bd0` |
| Current top-correction authority | `5932768c7a7d91535f69a90787b32222eb4d165ac6353d3e2ed4daf9e248e2b2` |
| Candidate movement | `bd2b97c0677b2e0ab5b09898ba7f2227758088744cd93f7e3c9b266bce5c5215` |
| Retained movement | `fffa0027926a57583cc13ffbcef552fc8e5f8da96964d50c64ef63ffd4ce4c97` |
| Captured-nut movement | `83c905bec64010695c769a73d7b8923869ef1aef5bda9b8591cdad0d443b21a4` |
| Proposal gravity operator assessment | `ce69ba58e3c6265d31ab0dfdec1ffac4c019b93fc1106c8f9677ed9b5b2c3f95` |
| Proposal frame comparison | `c3a8ff024fb494032d947aedfd6f00cda8698587b8751b2cec66e4b3af243729` |
| Proposal frame response, hashed only | `62bd4116cfb577a0846f4de0d43fbeec6bb704bac7feee530ee673ded1820f90` |

The last three paths stay under `upper-corner-screw-layout/rawlocal/knee-bridge-{gravity,frame}/`.
Loads retain **250 lb × 2**, signed **300 N**, the original **100 mm** hold
lever, recorded gravity and **25 kg** equipment allowance. The operation API
does not recalculate forces, read numerical arrays or transfer their passes.

## Actual parent phases and bounded continuation

The parent succeeded at `prepare-parent03` with producer SHA-256
`fa5d055af3d669e1d1b1f10a94c08744bac20ab6ffceddbcbc565e59fdb3ba86`
and setup SHA-256
`d5b942388150bc174ad999f6c53497989c55bea8bba6ab4566bf68079425494a`.
Its exact `attempt01` terminated with exit 137/SIGKILL under the 300-second
cap, without final result, receipt or stdout. Preserve its
`rawlocal/operation-envelope-completion/attempt01/execution-stop.json`,
SHA-256 `c0c66e9fe6f69046dbe9b2faed440951cc146f7f6990cb2fa374d793e056f85c`.
That STOP establishes no accepted route or physical failure.

The distinct parent `attempt02-aabb` completed with exit 0. Read-only
authentication and the continuation's source join consumed these exact bytes:

| Frozen parent record | SHA-256 |
| --- | --- |
| `prepare-parent03/setup.json` | `d5b942388150bc174ad999f6c53497989c55bea8bba6ab4566bf68079425494a` |
| `prepare-parent03/receipt.json` | `8c7bc4abdac49696149cb332b8074b5a8a29fcf2f5cbc58f9accae9e25bdfd4d` |
| `prepare-parent03/producer.py.snapshot` | `fa5d055af3d669e1d1b1f10a94c08744bac20ab6ffceddbcbc565e59fdb3ba86` |
| `attempt02-aabb/result.json` | `5e6ae7a6dd6bd2184aac6fd80e2aaddf686c8ea5c191e19b19f23c6d65c044e2` |
| `attempt02-aabb/receipt.json` | `3e01d6b3f56dfab643cdb8495d471bc3a77d050f60963487bdd70818ef513e01` |

Both receipts retain the identical **622 original source pins**. Continuation
authenticates the historical producer against its existing frozen snapshot;
the historical path/digest map is retained verbatim. The current executable
gets a separate continuation pin. This permits the new adapter to consume
the old preparation without repinning its producer or regenerating queries,
stations, AABBs, scene bodies or inputs. Original `prepare-parent01/02/03`
records and the SIGKILL STOP remain unchanged.

The cheap phase contains **12,992 query summaries, 156,204 undecided scene
overlap records, 6,784 counterhold records and 432 scope/axis/stage slots**.
Of the counterhold records, 2,048 have overlapping AABBs and remain undecided;
the other 4,736 are conservatively separated. These counts are a scheduling
census, not operation qualification.

The pure plan join reduces the required graph to **32,935 unique candidate
tasks**, including **1,531 shared hardware-stroke candidates**. The first
heading alternative per slot would require 9,190 unique tasks; execution does
not commit to evaluating that whole set. Geometry is represented for at least
one complete alternative in **212 initial-frame slots, 20 retained-route slots
and eight two-wire diagnostic slots**. The other **192 retained-route slots**
have missing screw/T-nut/light representations in every heading alternative;
they remain named unknowns without expending native queries. There are 3,184
unique unsupported candidate tasks. No installed route or obstacle is removed
to obtain these counts.

### Query order, journal and runtime plan

The first planned route is `reviewed_104 / initial_frame_open /
lumber_leg_bolt_left_1`, initially heading 0 degrees at both ends, with **21
candidate pairs** including all hardware strokes, tool approach/turn and
counterhold. Its six hardware queries have respectively 2/0/1/1/1/0 candidates
in the prepared query order. Every slot checks the common hardware strokes
before its tool alternatives. Alternatives are ordered by represented basis
and unique candidate count. Query checks stop at the first refused or unknown
requirement. A separated alternative requires all six requirement nodes:
counterhold approach and seated pose, active-tool approach and full turning
travel, plus the two simultaneous tool-pair checks. Execution stops exploring
headings for that slot immediately after one complete modeled route is proved.

The first continuation used **270 seconds inside the API, 64 native comparison
requests, 15 seconds per request and 15 seconds for engine startup**, within
the parent's unchanged **300-second hard cap**. Parent `attempt03-route-first`
finished 64 requests with no timeout: 56 separated pairs and eight enclosure
overlaps. Native requests totaled 1.078517 seconds, mean 0.016852 seconds,
maximum 0.146216 seconds; engine startup took about 1.609 seconds. The result
recorded 4.763526 seconds elapsed, two modeled route slots, 28 refused slots
and 402 unknown slots. Its 64 results included 44 shared hardware pairs.

For the distinct final batch, only the operational count guard and precise
authentication of that preserved journal were extended. Producer
`737d7f7731d35ca53ab2a20de21501a1efc1c0b5830b66e9b53bc567a6febbbe`
retains the identical geometry/kernel/helper source fingerprint
`666a91bc3fd23f88c13c1cc391b96993fad312a390c82dc396945c8631e57b4f`
to the preceding `b20596ca` producer. Cached starts/finishes still bind exact
input geometry, method and versions. The original 64-request default remains;
the permitted count ceiling is now the finite prepared exact graph, **29,751**
tasks, with every time limit unchanged. Parent explicitly selected **24,043**
requests, the pending graph upper bound, for one continuation. The 6,707
first-alternative candidates suggested about 113 native seconds at the first
batch's measured rate; all-alternative completion was not promised from that
small timing sample. Actual completion and counts are recorded below.

A single parent-launched child imports only needed saved STEP BReps and caches
validated query/fixed solids. It shares the parent's process group so the
300-second hard termination reaches it too. Each request begins with a flushed,
`fsync`-bound `pair_begin` record before any query geometry or STEP import for
that request. `pair_finish` records the outcome and elapsed time. Startup,
per-route dispositions and execution end are also journaled. A request timeout
kills that child, records an unknown and permits other candidates to proceed
within the same remaining cap. Failed startup stops further native requests.
No background geometry work survives a normal return.

The exact method retains the original 1e-6 mm³ volume threshold. Positive
volume refuses the chosen enclosure and skips an unnecessary distance call;
zero-volume cases retain the exact distance/contact calculation. This changes
execution cost only. An overlap for the declared **26 mm head / ±30 degree
(60 degree total) envelope** does not justify redesigning the physical model.
A later single 30-degree stroke with twelve-point reindexing would need its
own declared recipes and query; this continuation does not adopt that change.

Cache keys bind both geometries, saved STEP bytes, exact dependency versions
and the query method. Journal reuse additionally requires the same executable,
original setup and cheap-result hashes. A new preparation pins any explicitly
provided existing journal; only complete, validated finish records are reused.
An interrupted start remains unknown and is not silently retried. A torn final
journal append remains preserved. Earlier outputs are never rewritten.
One route proof requires every common hardware and selected tool/counterhold
node to be separated. Budget STOPs, missing geometry, errors, timeouts and
unexamined requirements remain distinct unresolved basis. Intermediate journal
dispositions remain provisional until final source authentication and receipt.

## Completed exact batch and witness classification

Parent `attempt04-route-first` completed with exit 0 in **222.564014 seconds**,
executing **10,859 new exact requests and reusing all 64 authenticated results**.
Neither the 24,043-request count ceiling nor the 270-second internal cap was
reached. There are no remaining budget stops, timeouts, native errors or engine
startup stops in its pair results. Source/receipt authentication remains stable.
The 10,923 unique cached results comprise **10,545 exact separations and 378
positive-volume enclosure overlaps**. Of the separations, 1,175 record
zero-volume/zero-distance contact; those contacts are not clashes.

| Scope and stage | One complete modeled route | Enclosure refusal | Unrepresented geometry |
| --- | ---: | ---: | ---: |
| Original 104 identities, initial frame open | 58 | 46 | 0 |
| Proposal 108 identities, initial frame open | 62 | 46 | 0 |
| Original 104 identities, installed route retained | 0 | 10 | 94 |
| Proposal 108 identities, installed route retained | 0 | 10 | 98 |
| Original 104 identities, two-wire lower bound | 0 | 4 | 0 |
| Proposal 108 identities, two-wire lower bound | 0 | 4 | 0 |
| **Total scope/axis/stage slots** | **120** | **120** | **192** |

All 120 complete slots occur in the declared initial-frame state: **58
original-inventory axes plus four unadopted ties**, with the original 58
appearing separately in both scopes. This is not 120 distinct axes, a staged
service-route proof or an observed assembly. All four proposed ties have a
complete modeled initial-frame route; their four installed-route slots remain
unknown. For the eight current top-correction stations, six have complete
initial-frame routes and the two `side_2` axes have enclosure refusals in both
scopes. Their literal corrected stations, original identity provenance and
all 16 installed-route unknown slots remain explicit. No result adopts 108
axes or transfers a reviewed-geometry/structural pass to changed planning parts.

### Every positive-volume witness

The standard-library [postprocessor](rawlocal/operation-envelope-completion/postprocess-attempt04/classify.py)
authenticated the completed result, receipt, plan, preserved executable and
the original 622-pin closure. It wrote an ignored
[structured summary](rawlocal/operation-envelope-completion/postprocess-attempt04/summary.json)
and [witness CSV](rawlocal/operation-envelope-completion/postprocess-attempt04/refusal-witnesses.csv).
Every **625 refused query/stage nodes** is included, covering all **378 unique
positive exact pairs** and **1,652 actual route/heading witness uses**. This
includes rejected headings on routes that subsequently found a complete
alternative. The summary retains all 120 terminal refused routes, their
actual witness links and all 192 unknown routes' 16 missing-geometry
alternatives. A canonical cached query ID is kept separately from each named
axis/stage query; geometry-identical reuse does not relabel the axis.

Each CSV row records scope, axis, station provenance, stage, action, moving
component, heading, obstacle/component identity, volume, distance basis and
classification. **Positive-volume requests intentionally did not evaluate
distance.** Their distance cells remain empty with
`not_evaluated_positive_volume_shortcut`; they are not invented zero-distance
measurements. Exact zero-volume distances remain in the untouched kernel
result. Postprocessing did not run intersections, import CAD, create shifted
queries, change geometry or alter a disposition.

| Witness classification | Query/stage nodes | Unique exact pairs | Observed union volume, mm³ |
| --- | ---: | ---: | ---: |
| Retained washer intended seat / source padding | 44 | 12 | 0.440579–0.804648 |
| Retained head AABB proxy / saved wire sequence | 4 | 3 | 238.204029–294.256861 |
| Full loose-washer stroke / saved wire sequence | 4 | 3 | 411.474384–464.383818 |
| Ordinary-tool enclosure / neighboring hardware proxy | 290 | 175 | 1.011417–2630.302912 |
| Ordinary-tool enclosure / saved timber obstacle | 283 | 185 | 10.044931–415546.213337 |
| **Total** | **625** | **378** | |

The 120 terminal refusals comprise **44 washer-seat witnesses, four retained
head/wire witnesses, four loose-washer/wire witnesses and 68 tool-route
refusals**. The 68 tool slots correspond to 34 original-inventory axes in
both initial-frame scopes; all 16 declared heading combinations are refused
there. The named axes and every heading's witness are in the summary. A
positive-volume witness is a refusal of its chosen enclosure/domain, not an
actual tool/hardware failure or authority for hardware or frame changes.

**Retained washer seating/source-profile inference.** All twelve retained
washer/wood pairs preserve the source's explicitly padded wood-face point;
the reconstructed washer far face joins it with zero recorded point error.
Their headward sweeps move away from that seat but their union includes the
initial pose. Existing scalar `CYLINDRICAL_SURFACE` records in authenticated
saved STEP files contain bore radii 7.14375 mm for leg seats and 5.55625 mm for
front/rear seats. Standard-library arithmetic gives
`π × (washer_outer_radius² − saved_bore_radius²) × 0.001 mm`, agreeing with
each observed overlap within 9.1e-11 mm³. This supports the recorded
approximately 0.001 mm export-padding layer at an intended bearing interface.
It does not locate the exact contact patch or phase of a union intersection,
prove a delivered washer profile or reclassify positive volume as separation.
Original refusals, the 1e-6 mm³ threshold and source-padded faces stay unchanged.
These dimensions explain existing geometry; they are not machining instructions.

**Saved wire / removal-sequence domain.** The head-box and full loose-washer
strokes meet exactly `wire_010_A10_A11` or `wire_130_K10_K11`, both preserved
saved wire BReps. Retained heads remain padded AABB proxies without supported
delivered catalog profiles. The additional washer query slides the washer
nutward over the fully extracted bolt while that bolt remains on its original
axis at the extraction endpoint. The shop guide requires staging the intact
harness before bolt movement and keeping hardware together; it does not
establish this in-place loose-washer sorting pose, a reachable alternative
pose or actual refeeding. These are real modeled installed-route obstacles
to the declared recipes, with proxy and sequence limits. The two-wire subset
still refuses the retained washer-seat enclosures; it supplies no complete
service route. No wire was moved, erased, cut or spliced by this work.

**Tool envelopes against other hardware and timber.** All neighboring-hardware
witnesses involve another axis, not the excluded target hex/shaft interface.
Nuts/heads use circumscribed cylinders or retained head boxes, washers use
filled outer disks and the tool uses a filled circular boss plus widened
continuous handle sector. Those representations do not contain delivered
clocking, open tool slots or exact exterior profiles. Timber witnesses use
authenticated saved obstacle STEPs, but the moving tool exterior remains a
conservative hypothesis. Other axes remain installed in these query states;
the shop's joint-by-joint and top rail-before-side removal instructions are
not a fully modeled inter-axis operation schedule. A sequential-removal
exemption cannot be inferred or silently applied. The two corrected top
`side_2` refusals explicitly witness `base_rail_top` and the corresponding
`side_1` shaft/nut, so removing rail stacks alone would not establish those
tool routes. Four captured bottom `rail_2` stacks retain separated full
hardware/captured-pair strokes in the initial-frame comparisons, while their
ordinary-tool alternatives remain refused. Existing captured-nut routes are
preserved rather than converted to a direct nut slide.

### Exact limits and preserved records

The **192 unknowns are geometry-basis unknowns**, all in `route_retained`:
94 original axes in each scope plus four new ties in the proposal scope.
Every one of their 16 heading alternatives has a named unrepresented panel
screw, T-nut or light witness. The 784 examined unknown query nodes split into
148 screw, 400 T-nut and 236 light witnesses; the plan retains additional
unexamined requirements. This is not a collision or a budget failure. The
completed graph needs disposition of its proxy/sequence refusals and supported
exact representations for these named obstacles. An unchanged rerun would not
supply those missing bases.

The method remains CadQuery **2.8.0**, `cadquery-ocp` **7.9.3.1.1**, saved
STEP imports only, conservative AABB separation, filled operation enclosures,
1e-6 mm³ positive-volume threshold and exact zero-volume distance/contact.
Tools retain all recorded sizes and **±30 degrees / 60 degrees total**; no
single-30-degree alternative was adopted. Physical operation, tool mating,
torque, human capture, receiver support, tolerance/loaded motion and actual
harness staging remain outside this comparison. **N16 is not qualified or
closed.** N17 datum, N18 tolerance/motion and N19 finished geometry remain
separate; all physical/adoption/release flags stay false.

| Completed record | SHA-256 |
| --- | --- |
| `attempt03-route-first/result.json` | `221cad5172672de43b59b554e49b092d3695d5a8f721e0df250352da2ff7c608` |
| `attempt03-route-first/journal.jsonl` | `07fa1d7bd3cfd7399a4aaac07993e487d504f4a3ae33c72013cda7f1d7e0faf6` |
| `prepare-route-first02/continuation-plan.json` | `4d27d4083e5056fbd146cb5611bad1fd667b67430d45f05cb7f07ed3a68ef37d` |
| `prepare-route-first02/receipt.json` | `8460d555e12989013b7ec311b21cc3af512b6231ad1969c564af107ba2723eb8` |
| Frozen producer | `737d7f7731d35ca53ab2a20de21501a1efc1c0b5830b66e9b53bc567a6febbbe` |
| `attempt04-route-first/result.json` | `66cdb7688b612a64771540cc63493d8b84f5a38ff6229f62156789e6211b12b6` |
| `attempt04-route-first/receipt.json` | `84b20294c7e723c710af87539e2c09ebeeab89346e7b7cfda887721caaf24a99` |
| `attempt04-route-first/journal.jsonl` | `5ad1814f6efa157ea97c7fa7bf9ffc61011bcba770c986edece9acc4de66b8ca` |
| `postprocess-attempt04/summary.json` | `1a9e361319c9ae0966015d3bde19b644fce7468b22133394e5fdff23375fa86f` |
| `postprocess-attempt04/refusal-witnesses.csv` | `daaca52c69f7be34e51c75628e200f9f6095847da977557d26680877f0640756` |
| `postprocess-attempt04/receipt.json` | `79a224a054d675b5a2792702468878c20349ab9f46464b837537b4c34c163275` |

Paths in this table are under `rawlocal/operation-envelope-completion/`,
except the maintained frozen producer. The ignored postprocess directory
contains about 3.4 MB of derived JSON/CSV and its reproducible stdlib script;
no CAD or source assets are duplicated. Recovery/postprocess command:

```sh
.venv/bin/python -B docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/assembly-package/rawlocal/operation-envelope-completion/postprocess-attempt04/classify.py
```

Publication is exclusive: this command refuses existing outputs. Preserve
the current postprocess records and use a separately named owned location if
an independently justified reconstruction is needed. Parent owns publication,
integration and any future geometry execution. The source/STEP/kernel records,
failed preparations and original SIGKILL STOP remain active and recoverable;
none was replaced, archived or pruned.

## Ordinary-tool and motion assumptions

These are explicit ordinary straight box-end tool **design envelopes**, not
new catalog claims, delivered-tool observations or selected products. The
existing 22 × 3 × 100 mm micromechanics wrench proxy is historical. Its thin
section is not used to make this screen fit.

| Bolt diameter | Nominal hex size | Tool head width | Thickness | Overall length | Handle width |
| --- | --- | ---: | ---: | ---: | ---: |
| 1/4 in | 7/16 in | 26 mm | 8 mm | 150 mm | 12 mm |
| 5/16 in | 1/2 in | 30 mm | 9 mm | 170 mm | 14 mm |
| 3/8 in | 9/16 in | 34 mm | 10 mm | 180 mm | 16 mm |
| 1/2 in | 3/4 in | 42 mm | 12 mm | 230 mm | 20 mm |

Each end has four finite headings, 0/90/180/270 degrees about a reproducible
perpendicular world reference. Twelve-point, 30-degree reindexing is a
declared tool hypothesis. A circular head plus widened circular sector
encloses the complete rectangular handle through the continuous ±30-degree
stroke. Its axial extent includes the entire thread-release travel. This
continuous enclosure is broader than sampled wrench poses. It establishes
neither available torque nor actual hex clocking, socket conformity or hand
clearance.

The active end turns while the other end counterholds. Ordinary routes move
the nut outward; the four captured routes hold the nut while the bolt turns
and moves headward. Each axis has 16 heading combinations. Every combination
can check active-tool approach and turning against the stationary counterhold,
and joins those checks to both tools' external scene access. A separated tool
pair alone cannot establish a usable modeled route.

Approach and departure extend beyond the occupied tip or complete release
travel by 25 mm, with at least the ordinary tool thickness included. Repeated
tool release/reindex and axial thread advance are enclosed; no 50 mm approach
is substituted for a long projecting bolt. Target hex engagement and coaxial
shaft passage through a tool opening are explicitly recorded intended
interfaces, rather than clashes with filled exterior envelopes. Washers and
all other own-stack roles remain obstacles unless a named prerequisite removes
them. Detailed mating/thread geometry remains outside this enclosure method.

The pure arithmetic API calculates complete component strokes:

- Nut release moves its near face past the shaft tip by 1 mm. Turns equal
  axial release divided by UNC pitch; this assumes compatible right-hand threads.
- The nut washer slides far enough for its near face to clear the complete tip,
  after nut removal. Declared washer-hole/shaft radial margins are recorded.
- Bolt, head and head washer withdraw together. Saved receiver-extrema travel
  is adjusted by the nominal shaft delta and outward head-washer shift, then
  gains head-washer thickness plus 2 mm. This allows the subsequent washer
  slide to clear the tip by 1 mm and still end 1 mm outside the receiver.
  The eight corrected top stacks and four new ties use the conservative
  full-shaft-length-plus-2-mm bound.
- After extraction, the head washer slides **nutward over the complete bolt
  tip**. Sliding it through the bolt head is not an installation/removal route.

The four captured nut/washer pairs retain their exact saved X moves:
−50.9623, +48.9623, +53.9623 and −55.9623 mm at the shop guide's respective
axes. They retain at least the saved 151.368 mm bolt withdrawal and the
recorded 25 mm nutward follow-on. Reverse installation uses the same swept
occupancy in reverse order. Those follow-ons end at bounded local positions;
they do not establish a reachable place to hold loose parts.

## Stages and pair disposition

The finite screen reports each scope independently in these states:

- `route_retained`: the complete saved installed panel/hardware/harness route.
- `initial_frame_open`: the documented initial frame assembly before the six
  panels, their screw/T-nut hardware, lights and intact harness are installed.
  The exact omitted IDs and reasons are recorded once per stage. This initial
  assembly state does not prove the reverse support/harness/panel staging operation.
- `two_wire_lower_bound`, only for retained leg bolts: omit exactly
  `wire_010_A10_A11` and `wire_130_K10_K11`. All other installed obstacles remain.
  This preserves the existing two-span diagnostic; it is not a demonstrated
  harness service state or permission to change routing.

Disjoint AABBs certify conservative separation. **Overlapping AABBs establish
neither collision nor clearance.** With parent `exact=True`, the existing
CadQuery query/intersection method loads matching saved STEP obstacles only
as needed. Generated cylinders, continuous sectors and perpendicular
captured-pair capsule sweeps are query enclosures, not rebuilt scene parts.
The shared `uv.lock` and project metadata are frozen inputs. Exact execution
requires CadQuery **2.8.0** and `cadquery-ocp` **7.9.3.1.1**, with observed
package metadata recorded in the result; a mismatch stops before BRep imports.
Overlaps with unrepresented T-nut/light/screw geometry stay named undecided
pairs. An exact positive volume is an **enclosure overlap requiring
disposition**, not proof of physical blockage. Zero-volume seat contact is
recorded separately; zero distance is not a clash.

Temporary tool sweeps are kept separate from installed hardware. Shaft
diameters and washer holes here are occupancy/fit dimensions, **not drill-bit
or machining instructions**. Existing Hillman pilot/countersink policy stays
at its recorded source. No coupon or physical trial is requested by this API.

## Executable API and remaining basis

Import has no source reads, output writes or engineering execution. The public
APIs are:

```python
operation_arithmetic(components, pitch_mm, *, saved_travel_mm=None,
                     saved_length_mm=None, head_washer_delta_mm=0.0,
                     captured=None, washer_hole_diameters_mm=None)
make_queries(axis)  # Pure geometry recipes, bounds and simultaneous tool pairs.
summarize_operations(data, summaries, pair_results)  # Same-state arithmetic join.
prepare(output)  # Standard library only; returns the prepared setup path.
run(output, setup, *, parent_owned=False, exact=False)
build(output, setup, *, parent_owned=False, exact=False)  # Alias for run.
make_continuation_plan(data, aabb)  # Pure join of saved candidate records.
prepare_continuation(output, *, reuse_journals=())  # Standard library only.
run_continuation(output, plan, *, parent_owned=False, max_seconds=270.0,
                 max_exact_pairs=64, max_pair_seconds=15.0)
```

Every output must be a fresh immediate child of
`assembly-package/rawlocal/operation-envelope-completion/`. Preparation writes
the setup, producer snapshot and receipt for the original full-screen API.
Those entry points preserve the prior finite method. They are not the next
execution path for the successful frozen preparation. `prepare_continuation`
instead publishes `continuation-plan.json`, the current producer snapshot and
receipt from existing cheap results. This worker has invoked only the pure
join for its scheduling census, not either publication API.

The parent alone calls `run_continuation(parent_owned=True)`. It publishes the
durable journal, worker stderr, bounded results and receipt, retaining selected
route proofs, refused/unknown alternatives, checked candidate pairs and the
unexamined requirement references in the plan. Role exclusions and exact
stage-excluded obstacle IDs remain bound to their named frozen AABB summaries
and stage records. Fixed query geometries are shared within the plan rather
than copied for each candidate; no source installation or STEP is copied.
If the process is killed, the preserved journal remains useful even without
a final result/receipt. It supplies no physical acceptance. Unresolved route
slots are emitted even when the native request/time ceiling has been reached.

Recorded final parent commands, already completed from the repository root.
Their existing output directories must not be reused:

```sh
operation_leaf=docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/assembly-package/operation-envelope-completion.py
operation_raw=docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/assembly-package/rawlocal/operation-envelope-completion

.venv/bin/python -B "$operation_leaf" --prepare-continuation \
  --reuse-journal "$operation_raw/attempt03-route-first/journal.jsonl" \
  --output "$operation_raw/prepare-route-first02"

OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 timeout --signal=KILL 300s \
  .venv/bin/python -B "$operation_leaf" --run-continuation --parent-owned --exact \
  --plan "$operation_raw/prepare-route-first02/continuation-plan.json" \
  --output "$operation_raw/attempt04-route-first" \
  --max-seconds 270 --max-exact-pairs 24043 --max-pair-seconds 15
```

These commands were run by the parent, not this worker. No unchanged
continuation is requested. A separately justified future parent run must send
verbose progress/stdout to a new owned log **beside** its fresh run directory,
keeping `result.json`, `journal.jsonl` and `receipt.json` as untouched kernel
evidence. A sibling log does not pre-create the producer's guarded output
directory. For a future plan/run only, the logging pattern is:

```sh
operation_stdout="$operation_raw/future-parent.stdout.log"
(
  set -o noclobber
  OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 timeout --signal=KILL 300s \
    .venv/bin/python -B "$operation_leaf" --run-continuation --parent-owned --exact \
    --plan "$operation_raw/future-prepare/continuation-plan.json" \
    --output "$operation_raw/future-run" \
    --max-seconds 270 --max-exact-pairs 24043 --max-pair-seconds 15 \
    > "$operation_stdout" 2>&1
)
```

Use independently selected fresh names; `noclobber` preserves existing logs.
This example is not a request to execute another comparison or change inputs.
Journal reuse with the same frozen producer authenticates same-method results;
the literal `attempt03` compatibility exception also verifies its preserved
producer and unchanged exact-source fingerprint. No continuation is automatic.

Remaining modeled basis is precise: disposition of the completed
selected-route/common-hardware enclosure refusals; 192 retained-route slots
still lack exact representations for their named installed obstacles. This
completed batch has no leftover time/count STOP or interrupted query.
The candidate census supplies no qualification. Actual tool
exterior/clocking and mating profiles remain
declared hypotheses; the twelve retained heads retain saved modeled AABB
proxies with no supported delivered catalog head bound; and intact harness
staging, human capture, support fixtures and complete refeeding remain
unobserved. Existing saved wires provide installed-route geometry, not cable
flexibility, slack, anchoring or connector separation. No owner measurements
are needed to execute the declared finite model. Its result cannot establish
those unobserved operations, adopt the proposal or close the formal criterion.

Only this producer and this leaf belong to this worker. Parent owns integration,
serialized saved-BRep execution, final disposition, staging and commits. Frozen
shop/fit leaves and foreign tracked/untracked/raw/tmp/history files remain
preserved. Saved sources stay active; no evidence is archived or pruned.
The **737d7f77 producer and completed kernel/cache records are frozen** for
publication. This final worker action changes only this maintained leaf and
its ignored source-postprocessing summary; it launches no engineering run,
test, review loop, staging operation or physical work.
