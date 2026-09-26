# Current force-run energy readiness review

Reviewed 2026-09-25 from the immutable 20-state output prefix and the pinned
CalculiX 2.21 source. I ran the bounded Python reader in this folder; I did not
run a solver, build native code, or read the live output directory.

## What the prefix establishes

The snapshot is `force-every-increment-seating-prefix-attempt01`, manifest
SHA-256
`001cefdb37a52bdf6bc6d1d590310c93d91d7f5b2f7cf0a35ad2e10c097e0d8a`.
It contains 20 accepted states from 0.001 through 0.020 s, no rejected
attempts, and every-accepted-increment energy output. It is a prefix of the
0.025 s run, not a terminal result. Its input freeze is SHA-256
`f054d6b911fb0d9c9b0a183fa007d16d8a34a422904fd5cbcf73634e87797e66`;
the child `pilot.inp` pin is
`a9f891c92fed7eaa7e3b78f0656c5829d330a28a3df450ea7128b9ea52eb49c4`, while
the parent-source lineage pin is separately
`48649259ba8441429a5dd094ae08487e3713d6b5b860ac39ca1acf71b837d963`.

For all 20 accepted states, full-set `.dat` ELSE and ELKE totals match the
corresponding LOG internal and kinetic totals within their printed precision.
The nut-carrier totals are a subset of the full element totals and must not be
added again. This verifies two usable pieces of the sampled energy history;
it does not qualify the contact-energy term or the complete energy balance.

At 0.019 s, the LOG reports ALLWK 4.573027 N·mm, internal energy
0.05192561 N·mm, kinetic energy 4.520602 N·mm, contact energy
0.0004953528 N·mm, and relative balance 0.000506%. At 0.020 s, those values
are 5.891622, 0.1110754, 5.314116, 0.001345491 N·mm, and 44.068010%.
The 0.020 s full reported energy residual is −0.4650846 N·mm. These are
source-generated solver diagnostics, not accepted closure measurements: the
contact term follows the index path below. The abrupt residual change is real
in this captured LOG, but this evidence does not determine its cause.

The current load is force-driven CLOAD. `nonlingeo.c:3174–3178` forms ALLWK
from the force/displacement arrays through `worparll`; prescribed-target
actuator work omission belongs to a different historical case. A separate
direct CLOAD-work reconstruction is still useful as an independent check, but
it should compare against, not be added to, native ALLWK. The separate
reaction-work audit owns that comparison.

No numerical dissipation is inferred from the partial `ELSE + ELKE − ALLWK`
residual. Contact spring energy is not yet independently qualified, and a
nonzero residual in this implicit dynamic run is not by itself a measure of
numerical dissipation. The accepted prefix also stops before the requested
0.025 s endpoint.

## Source path and consequence

The source-index concern is confirmed, with two different `ne0` meanings that
must not be conflated:

1. In `nonlingeo.c:903`, `ne0=*ne` saves the original element count before
   generated contact elements are appended. This value is passed to
   `resultsmech`; the face-to-face writer at `resultsmech.f:421–439` reads
   `igauss` from contact connectivity and stores `ener` at
   `original_element_count + igauss`.
2. `gencontelem_f2f.f:295–300,671–715` assigns surface-point IDs to `igauss`,
   increments the generated element number only for active contact points,
   and retains `igauss` in each generated `ESPRNGC` element's connectivity.
   Thus generated element numbers are compact while their stored energy slot
   is indexed by the surface point. Dense ordered active points can make the
   indices coincide; gaps from inactive points can make them differ.
3. `calcenergy.f:189–196` reads contact-spring energy at compact `nelem`,
   without consulting the trailing `igauss`. `results.c:416–469` aggregates
   that calculation into the shared energy vector. `nonlingeo.c:3493–3524`
   prints the vector in the LOG, and `checkconvergence.c:274` passes it into
   `checkimpacts`. The LOG contact energy, energy-balance calculation, and
   dynamic contact-control path therefore share the compact reader; the LOG
   is not an independent contact-energy calculation.
4. Separately, `printout.f:458–489` computes a *local* `ne0`, the first
   generated contact-element number, by scanning the element list. It equals
   original element count plus one. The prepared CELS printer patch passes
   `local_ne0 - 1` as the original-element-count base, then uses the stored
   `igauss` to select the writer slot. The `-1` in that output-only patch is
   intentional and is different from the `ne0` passed through mechanics.

The original CCX 2.21 source archive is pinned at SHA-256
`52a20ef7216c6e2de75eae460539915640e3140ec4a2f631a9301e01eda605ad`; direct
source-file hashes are in `source-pins.json`. An independent read-only review
at
`../contact-energy-index-source-review-attempt01/independent-review.md`
confirms the write/read asymmetry and the limitation of the existing
reader-only probe.

The 20-state snapshot has no `.cel` file and does not preserve an
`igauss`-to-compact-`nelem` map or the per-contact energy values at write and
read. Therefore the source identifies a possible sparse-index hazard, but
this prefix does not establish that its active contact set is sparse, that
the observed 44% residual came from the hazard, or that any particular
increment was rejected or accepted because of it. Original DAT CELS reads
the compact slot at `printoutelem.f:301–304`; FRD CELS does too at
`frd.c:1713–1728` (it uses the compact zero-based element row `i`). Neither
output independently proves the writer-layout values.

## Bounded next method

Keep the force-driven mechanics input and convergence settings fixed. For
energy qualification, use the prepared output-only CELS patch in this folder
as a short reader fixture first; it does not alter `resultsmech`, `calcenergy`,
`checkimpacts`, mechanics, or tolerances. The existing controlled sparse
fixture seeds writer-layout slots for `(original extent=1, igauss=1)` and
`(original extent=1, igauss=7)`, including a deliberately conflicting compact
slot. After applying the patch to a separate copy of the pinned
`printoutelem.f`, the driver must pass `contactenergybase=1`, and expected DAT
CELS values are `[7.5, 7.5, 7.5]`; currently the unpatched reader returns
`[7.5, 0, 2.25]`. This would validate only the proposed DAT printer lookup;
the patch leaves FRD CELS on its compact lookup, as well as all mechanics,
energy aggregation, and control. No fixture build or native run was performed
here.

That printer test cannot validate the LOG or solver energy controller. The
next evidence needed for those is a small pinned writer-to-reader fixture or
a future serialized run that records, for each active contact point, the
generated compact element number, its `igauss`, the written
`ener(original_count+igauss)` value, and the corresponding `calcenergy` read
slot. Compare that record with an independent per-pair contact-energy
calculation before interpreting global closure or changing any convergence
setting. The `printoutcontact.f` per-pair diagnostic being prepared separately
can provide a useful second calculation, but it is not automatically
equivalent to native spring energy. Do not use the CELS printer patch to
retroactively qualify this captured LOG or the current solver-control path.

## Prepared artifacts and pins

`audit_energy_prefix.py` hashes the immutable snapshot files before parsing;
`energy-prefix-audit.json` is its result. The prepared
`cels-printer-index.patch` has SHA-256
`b87b409dbd9acb637a7e401df02b331c99f4b6d912f4d0bdf4ecddec01ce211b` and is
not applied. `source-pins.json` identifies the pinned source bytes and patch
hash. No files in the upstream source tree or native output folder were
changed.
