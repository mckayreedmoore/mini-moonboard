# Independent review: explicit current coupling feasibility

Reviewed 2026-09-27. This is a read-only source and input review. I did not
edit the reviewed README, pins, audit, model inputs, or run a native solve.

The bounded source conclusions in the corrected README are supported. I
independently checked the pinned archive and all seven source-member hashes,
the pinned model-input hashes, and the parent dependency-audit hash. The
actual `response_n_plus.inp` is a loaded `*STATIC` deck: it defines `WJ_RAMP`
and nonzero `*CLOAD` entries. The separate historical `input-freeze.json`
reports a zero-load matrix-storage scope, but does not hash this response
deck. The README now preserves that contradictory historical metadata
without treating it as provenance for the loaded deck or claiming the deck
was executed.

I parsed the two coupling inputs and carrier sets. Each input contains 24
user equations. In the historical controller-first input, the 24 first-term
dependent DOFs are exactly the four rigid bodies' REF/ROT control DOFs
(nodes 116163–116170, DOFs 1–3). In the current physical-pivot input, the 24
first-term DOFs are shaft/physical DOFs; all 24 controls occur as independent
terms. Its equation terms have no node overlap with the four rigid-carrier
NSETs, which contain 4,524 unique nodes. The A09 assembly has four matching
`*RIGID BODY` cards. This verifies the incidence distinction for these
serialized equations; it does not establish the behavior of every other
constraint in a future assembled deck.

The explicit prohibition is supported by the pinned CalculiX 2.23 source.
`dynamics.f` sets the dynamic perturbation level to at least 2 and selects
`iexpl=2` for `EXPLICIT`. `rigidbodys.f` documents that `*RIGID BODY` implies
nonlinear geometry and creates node constraints through `rigidmpc.f`;
`rigidmpc.f` labels them `RIGID` and places REF translations and ROT controls
among their independent terms. `cascade.c` classifies `RIGID` as nonlinear
and sets `icascade=2` when the dependency check finds a dependent term in
that chain. `nonlingeo.c` stops explicit dynamics when `icascade==2`.
Therefore the controller-first ordering is source-disallowed with these
rigid-body constraints in explicit dynamics. The current pivot ordering
avoids this particular shared dependent-DOF chain. The source finding is not
a native test, and it does not establish that the current ordering is
otherwise ready for explicit dynamics. The source also supports the stated
limit that this finding does not prohibit implicit use; it separately
rejects `*RIGID BODY` in perturbation steps.

The zero-density warning is also supported, with the README's source-inference
qualification. The four nut ELSETs are active C3D10 solids with assigned
solid sections, density 0, and elastic modulus 200000; the four rigid-body
cards constrain their nodes. The source scan skips inactive elements, but
does not show a rigid-body or zero-density exclusion for active solids.
`materialdata_me.f` returns the declared density, and
`calcstabletimeincvol.f` evaluates the isotropic wave-speed expression using
density in the denominator before calculating an increment inversely
proportional to wave speed. Under ordinary IEEE floating-point behavior, a
positive-modulus, zero-density element gives no finite positive stable
increment and reaches the source's small-increment scaling/error path. This
is a source-level inference only: no compiled runtime behavior or actual
explicit failure was observed here. Changing equation ordering cannot
resolve that separate material/mass issue.

The two earlier review issues are resolved in the current files: the README
now distinguishes the loaded response deck from the contradictory historical
freeze metadata, and `source-pins.json` now includes the `dynamics.f` pin that
connects the `EXPLICIT` keyword to the source guard. I found no remaining
concrete defect in the stated source disposition. The report should remain
limited to this pinned source and input graph; it does not establish explicit
solver readiness, finite-rotation thread behavior, or joint acceptance.

SHA-256 values reviewed:

- `README.md`: `7775df79c1d86f2788d4aefd4ad8d327772cfcbd9575cc0c3317e6a15bbc9ea4`
- `source-pins.json`: `76d6f04130e3f46b952c7d8eaaa457ae09ebf3b8f28b94a96848e25aa501bc4d`
- `parent-dependency-audit.json`: `842737f5141d850c1ed5846f91808377111900d9204075265c7ae92d5f85cbf9`
- Pinned CalculiX 2.23 source archive: `9c88385c10fb04f5dc6c4e98027a51bebdd8aee3920e05190d6c1dd08357d6e7`
- A09 `response_n_plus.inp`: `57c59a8d84694d74c2dd7b0de559e425d5d28ea81453addb68fece4d682f8720`
