# Current ordinary-patch resistance preflight

This pre-demand preparation is bound to the current three-timber, four-bolt
ordinary patch. The producer pins the current patch inventory, washer-seat
classification, and proposal-only material map by SHA-256. It reports only
per-seat wood-bearing reference bounds and geometry-only bolt-group pitches;
it emits no criterion pass or joint acceptance.

The eight frozen washer-to-wood seat pairs have finite opposed planar geometry.
For the documented 1/4-in Type A Wide dimensional envelope, a 7.5 mm CAD bore,
and conditional dry DF-L No. 2 compression-perpendicular value
`Fc⊥ = 625 psi`, the ideal full-annulus reference is **920.57–1,019.16 N
(206.95–229.12 lbf) per seat**. This assumes uniform bearing over the full
washer annulus on sound wood, and applies no preload or bearing-area increase.
The current stock grade and washer product remain unverified; source geometry
does not establish active pressure. Values are listed per seat and are not
summed.

The two bolt groups each have a 33.0 mm axis-center pitch, about 5.197 times
the 6.35 mm unthreaded CAD shaft envelope. This is not an NDS spacing, end,
edge, splitting, tear-out, or group check. No source-bound loaded end/edge
projections or current signed fastener force directions are provided here.

NDS dowel-yield and member-bearing checks remain unresolved because delivered
bolt `D`/`Dr`, thread-bearing lengths in each 88.9 mm / 38.1 mm member, and an
applicable ASTM F1575 or evaluated ASTM F606 `Fyb` basis are absent. Fresh
per-bolt actions and a validated load-sharing response are separately needed
to compare any completed component reference with joint demand.
The NDS full-body-`D` exception threshold is computable per receiver: thread
bearing may occupy at most **22.225 mm** of the 88.9 mm cleat and **9.525 mm**
of the 38.1 mm host in each member holding threads. Those values are screening
limits only; the frozen 6.35 mm shaft envelope does not locate delivered
threads, so `D` cannot be selected and `Dr` remains unbound.
Washer-steel bending/spreading, direct bolt tension/shear, nut engagement, and
the separate unbolted rail-to-principal butt path remain open.

Primary method sources are ANSI/AWC NDS-2024 Chapter 12 and the 2024 NDS
Supplement Table 4A (linked through
[`bolt-resistance-basis.md`](../../../bolt-resistance-basis.md)),
[ASTM F1575/F1575M-24](https://store.astm.org/f1575_f1575m-24.html),
[ASTM F606/F606M-26a](https://store.astm.org/f0606_f0606m-26a.html), and
[ASME B18.21.1-2009 (R2016)](https://www.asme.org/codes-standards/find-codes-standards/b18-21-1-washers-helical-spring-lock-tooth-lock-plain-washers).
The repository's
[`representative-fastener-resistance-method.md`](../../../representative-fastener-resistance-method.md)
and [`current-ordinary-hardware-basis.md`](../../../current-ordinary-hardware-basis.md)
bound the helper, dimensional range, and candidate-versus-delivered limits.
The separate [current-material-scenarios.md](../../../current-material-scenarios.md)
is an elastic scenario for the 24-block geometry, not resistance evidence for
this patch.

Run the deterministic producer with:

```text
.venv/bin/python -m scripts.wood_joint_current_patch_resistance_preflight
```

It writes `resistance-preflight.json` beside this note and refuses changed
source-manifest hashes. No CAD generation or native solve is performed by the
producer.
