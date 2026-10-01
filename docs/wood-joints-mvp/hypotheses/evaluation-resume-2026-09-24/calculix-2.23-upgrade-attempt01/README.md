# CalculiX 2.23 update and method comparison

Date: September 27, 2026. Scope: owner-requested development-toolchain update.
No candidate geometry changed and no candidate-joint solve ran.

## Outcome

CalculiX 2.23 is built and installed in a separate local Docker image. All six
unchanged method fixtures completed normally. Their numerical audit fields
are exactly equal to the saved 2.21 results at the available output precision;
see `cross-version-comparison.json`.

| Fixture | Observed 2.23 behavior | Disposition |
|---|---|---|
| Static direct motion | Expected uniform displacement and elastic energy | Known-answer response matches |
| Static average-MPC motion | Expected physical response; controller RF is zero | Controller RF still is not actuator force |
| Dynamic direct motion | Expected kinematics and independently calculated energy; native work remains zero | Preserve independent work accounting |
| Dynamic prescribed average-MPC motion | Maximum displacement difference from full-inertia reference is 0.00560773 mm; reference omitting prescribed inertia matches to 4.96723e-9 mm | The tested issue persists; keep this route disabled |
| Balanced direct forces | Independent displacement, velocity and energy checks pass for all 100 increments | Loading-method fixture passes |
| Balanced forces through free homogeneous controller | Same passing response as direct nodal forces | Loading-method fixture passes |

The balanced-force maximum displacement error is 4.98731e-10 mm, and applied
work minus elastic and kinetic energy is 1.47240e-12 N·mm. These small values
describe a linear unit-cube verification; they do not measure joint-model
accuracy or establish strength. The dynamics are intentionally not quasi-static.

The update does not resolve the known prescribed-motion issue or the
free-cleat/contact response blocker. Continue with an externally force-driven
joint diagnostic, retaining the reviewed cleat freedom and physical assumptions.
Full-patch inertia, contact, coupling, energy and numerical sensitivities remain
to be checked on the actual model before any joint interpretation or family reuse.

## Reproducible solver identity

- Image tag: `mini-moonboard-fea:ccx-upstream-2.23-v1`.
- Image ID: `sha256:31336f517557f5dd5f97d85b1e6e15947fd1c10b44edc1364dbba4c1a5ab6c38`.
- Executable: `/usr/local/bin/ccx-upstream-2.23`.
- Executable SHA-256: `c6882d262b44525a563250673420dff1506c41b95e6d82d50392f9af26111863`.
- Official source archive SHA-256: `9c88385c10fb04f5dc6c4e98027a51bebdd8aee3920e05190d6c1dd08357d6e7`.

`build_manifest.json` records upstream source hashes, compiler/library identity
and executable hashes. The source files were verified byte-identical to the
official archive after compilation. `solver-profile.json` also pins the
downloaded 2.23 manual. The old images, original decks and old evidence remain
unchanged; no selected-baseline or historical runner changes solver implicitly.

The first build failed because the adapted makefile omitted Fortran
preprocessing. Upstream's 2.23 Makefile includes `-cpp`; the second build uses
that flag and succeeds without source patches. Both build contexts and result
records are retained here. Full local logs are under
`fea/generated/calculix-2.23-build-attempt01/` and
`fea/generated/calculix-2.23-build-attempt02/`.

`input-freeze.json` binds the six unchanged input decks to their original
2.21 records. Each execution record contains the exact command, terminal
container state and output hashes. The isolated auditor implementations are
copied unchanged from the previous method checks; their outputs are in
`motion/independent-audit.json` and `force/independent-force-audit.json`.

Sources: [official download page](https://www.dhondt.de/),
[2.23 release notes](https://www.dhondt.de/new_calc.htm),
[2.23 manual](https://www.dhondt.de/ccx_2.23.pdf).
The release notes do not identify a fix for the tested prescribed-motion issue;
the unchanged-fixture comparison establishes its behavior in this build.
