# Compact bolted frame development

This is the main entry for `compact-bolted-frame-development`.
The current geometry is **`eoere-local-front-bolt-moves-v4`**:
**20 sawn members, four trimmed nominal ¾-inch plywood leaves, 24 angles and
92 bolt stacks**. The two lower front-post/runner bolts now sit60mm above
the floor; their upper companions stay100mm. All four stay80mm from the
common front end. Timber sections, member lengths, six panels,32 LED passages,
66 Hillman axes and hardware specifications remain unchanged.

[Current viewer](https://mckayreedmoore.github.io/mini-moonboard/?model=eoere-current-frame-development&view=rear) ·
[geometry and changes](owner-frame-v4/geometry.json) ·
[own six-case engineering review](owner-frame-v4/engineering-review.json).
All1011 occupied parts clear nominally. This is a design-review revision,
not a fabrication or climbing release. The selected
[screw-and-bracket baseline](../../current-candidate.json) retains separate authority.

The proposed10mm cleat-row move was rejected: those bolts also pass through
existing under-header angle factory holes, and the proposed axes intersect
solid steel. Their height stays173.8125mm. A drop-in5/8in upper long-support
bolt also fails the adopted loaded-edge check:63.5mm is needed, versus
53.041mm in the rim and58.447mm in the support. The1/2in upper bolts and
their axes stay unchanged. Neither rejected trial supplies a strength pass.

## Active builder reading path

| Need | Current record |
| --- | --- |
| Current model and two moved axes | [Viewer](https://mckayreedmoore.github.io/mini-moonboard/?model=eoere-current-frame-development&view=rear) · [receipt](owner-frame-v4/geometry.json) · [92 axes and66 screws](owner-frame-v4/axes.json) |
| Strength results | [Own revised six-case review](owner-frame-v4/engineering-review.json) · [execution and rejected trials](../wood-joints-mvp/completion-ledger.md#current-front-bolt-moves) |
| Member and receiver dimensions | [30 member records](owner-frame-v4/members.csv) · [112 receiver occurrences](owner-frame-v4/receiver-holes.csv) · [four revised drawings](owner-frame-v4/layout.md) |
| Other drawings and stock allocation | [Preserved unchanged member sheets and13-stick allocation](owner-frame-v3/layout.md); the four revised post/runner drawings supersede their old coordinates |
| Hardware | [Unchanged92 proposed stacks](owner-frame-v3/hardware-review.csv) · [length-window limits](owner-frame-v3/hardware-length-windows.json); delivery and affected strength remain separate |
| Assembly instructions | [Current scope and preserved102-bolt instructions](builder-plan.md); review coordinates are not issued cutting/drilling directions |

The frame's own six cases use the same declared four-host floor and perfect-bond
beam assumptions as the preceding working comparison. Every case passes raw
force and two-plywood-operator replay at the1e-5N full-gradient admission limit.
Loads remain250lbf times2.0 plus300N horizontally and nominal gravity, withCD1.
The front comparison uses the new forces, not the earlier same-force estimate.

The [climber-weight study](../wood-joints-mvp/completion-ledger.md#climber-weight-studies)
accepts kg or lb, with separate downward-multiplier and horizontal-force
inputs. It preserves this 250 lb reference, all dead loads and the 25 kg accessory
allowance, reruns the six responses and reports governing comparisons. It
does not change the current geometry or establish a climber rating. The 2.0
multiplier and 300 N lateral action remain declared assumptions; they are not
presented as a standard load combination.

The [assumption and reference audit](../wood-joints-mvp/completion-ledger.md#current-assumption-and-reference-audit)
reproduces the current timber arithmetic. Tighter same-state probes still
exceed 1.0; reduced-core assumptions, large saved operator motions and the
floor/bond hypotheses limit physical interpretation. Load-duration adjustments
are legitimate only within their supported scope; no factor or allowable
exceedance is adopted. The next priority is a conventional compatible check
of the governing joint/support load path before selecting physical remedies.

| Conditional reference, limit1.0 | Previous geometry | Current geometry |
| --- | ---: | ---: |
| Left front pair, maximum wood bearing | 1.130332 | **0.937383** |
| Left front pair, maximum bolt axial/bending | 1.112321 | **0.893340** |
| Right front pair, maximum wood bearing | 1.076144 | **0.890992** |
| Right front pair, maximum bolt axial/bending | 1.047572 | **0.840875** |
| Bonded cleat, nominal38.1mm | 1.038427 | **1.066325** |
| Bonded cleat,36.5mm wall allowance | 1.099545 | **1.129031** |
| Header net shear/torsion | 1.083581 | **1.128148** |
| Top rail net shear/torsion | 1.177439 | **1.176955** |
| Left/right sloping sides | 1.341049 /1.303191 | **1.343708 /1.306019** |

The front change clears its reported bolt/wood references. Its changed load
sharing slightly increases the cleat and header comparisons; the full frame
still does not pass. The upper long-support joint still exceeds in both wood
bearing1.113637 and bolt axial/bending1.089846. All82 ordinary bolt layouts
meet their own mandatory end/edge/row minima. The ten dedicated header/cleat
joint factors, complete steel, end/group/seat and washer/spacer duties remain
separate; no complete-joint pass is inferred from individual references.

The owner retains the two ordinary¾-inch leaves at each corner. Perfect
bonding is an analytical hypothesis, with no adhesive selected or qualified.
The full203.2mm-width beam operator approximates the trimmed perimeter; it
is not a variable-width plate or physical force bound. The36.5mm wall check
changes bearing/reference credit at nominal response, not actual-thickness
stiffness. Panel/Hillman strength remains explicitly deferred and unresolved.

The support model credits centroidXY at the two long supports and two center
posts, keeps all32 compression-only normals and leaves rotations free. Other
feet are normal-only. Floor friction, local sticking, yaw resistance and
finite-motion equilibrium are not established. The preceding two-host
sensitivity retains its original geometry and is not a current-force bound.

The [remedy proposals](../wood-joints-mvp/completion-ledger.md#current-exceedance-proposals)
remain sizing options. Only the compatible front move is integrated here;
the proposed cleat move and larger upper bolt need different compatible joint
layouts before evaluation. No outboard knees, packers or extended top rail
are reintroduced. The next design decisions concern those joints and the
remaining timber references, within the owner's retained design scope.

<a id="revision-map"></a>
<a id="revision-map-and-retention"></a>
## Preserved evaluations and retention

The [preceding92-bolt geometry](owner-frame-v3/geometry.json),
[50/100mm front layout](owner-frame-v3/layout.md),
[bonded-frame review](owner-frame-v3/engineering-review.json) and
[preserved viewer](https://mckayreedmoore.github.io/mini-moonboard/?model=eoere-owner-frame-v3-development&view=rear)
retain their exact sources. Its same-force lamination0.926488 screen is not
an updated-frame result. The [102-bolt geometry](paired-frame-v2/geometry.json),
[complete conditional evaluation](paired-frame-v2/engineering-evaluation.json)
and [viewer](https://mckayreedmoore.github.io/mini-moonboard/?model=eoere-retained-2x6-frame-development&view=rear)
keep their extended-top/outboard-return scope; their0.989083 maximum does not
transfer. The [106-bolt packet](paired-frame-v1/geometry.json),
[revision index](development-revisions.json) and [history catalog](../history/design-history.md)
preserve earlier options.

The active raw work is `frame-completion-v1/owner-bolt-moves-v4/`: the failed
six-axis geometry, compatible front-only geometry, six new bonded fields,
force/operator replays, worksheets and browser captures. Earlier raw packets
and byte-locked producers stay active and unchanged. The new viewer patch
contains only14 replacements and inherits unchanged meshes; four new drawings
replace only the changed post/runner sheets. The ledger records permanent
artifact size, source-applicability limits and commands. No archive or prune
operation is performed.

The basis remains dryDF-LNo2, recorded loads, declared joint/plywood properties,
conditional factory steel and unverified floor assumptions. Actual material,
hardware, cuts, tools, floor and fit remain unobserved. These are conditional
DIY development records, without manufacturer, inspected-build, fabrication
or climbing qualification. Actual/Disposition cells stay blank.
