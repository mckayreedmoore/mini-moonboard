# Elastic matrix export method packet

This is an input-only known-answer proposal for checking CalculiX 2.23 global
stiffness-matrix export and an independent material oracle. It is a single free
1 mm C3D20 cube with 20 canonical nodes, density `1.0e-9 tonne/mm³`, and
engineering constants `E1/E2/E3 = 1200/800/600 MPa`,
`nu12/nu13/nu23 = 0.2/0.15/0.1`, `G12/G13/G23 = 300/250/200 MPa`. The
rectangular material axes rotate 37° about global Z. The terminal step uses
`*FREQUENCY,SOLVER=MATRIXSTORAGE,GLOBAL=YES` and has no restraints, MPCs,
springs, or applied loads.

The [generator and checker](elastic_matrix_packet.py) write only
`elastic-cube-matrixstorage.inp` in this folder.
That generated input remains local; published files are the code and this
summary. The generator does not start CalculiX or write result files. The
optional result checker reads `.sti` and `.dof` only when paths are explicitly
supplied. Run these commands from this packet's directory:

```sh
uv run --no-sync python elastic_matrix_packet.py --write-input
uv run --no-sync python elastic_matrix_packet.py --self-test
uv run --no-sync python elastic_matrix_packet.py --check-results cube.sti cube.dof
```

The parser requires a bijection over the 60 global node translations, one
stored triangle, one diagonal per DOF, bounded integer indices, finite values,
and no duplicate or mirrored entries. It reconstructs the opposite triangle
without doubling diagonal values. Matrix checks require six rigid modes, 54
positive non-rigid eigenvalues, zero work in all six translations/rotations,
and all 36 affine strain-basis cross energies to match the independent
rotated engineering-constant oracle. The built-in synthetic operator checks
exercise these validators; that matrix is algebraic test data, not an FE
result. Tolerances are provisional method settings for parent review.

Parent and independent Luna maximum-reasoning review reproduced the self-test:
15 malformed parser fixtures and three corrupted operators were rejected.
The independent strain-basis rotation agrees with the tensor oracle within
`2.3e-13`. Ruff passes. The connectivity test also checks the documented
16-plus-5 line-entry split. These results validate code and proposal checks;
the native gate below remains pending.

## Source and manual basis

The pinned manual is `fea/generated/ccx_2.23.pdf` (SHA-256
`a0bf3fc03f374912ff2bf28da3f7dfb6a61428dd7f41b281a2e7e1fdb318f330`). Its
§7.63, pp. 516–519, describes MATRIXSTORAGE as an export mode that writes the
stiffness and mass matrices as ASCII row/column/value triplets and a `.dof`
mapping whose entries identify node and global direction. It says absent
matrix entries are zero, `GLOBAL=YES` stores global directions, and the
program stops after writing the files; the frequency step therefore belongs
last. The parser follows that contract and the pinned 2.23
`matrixstorage.c` implementation, which writes each diagonal once and one
off-diagonal triangle.

The rectangular orientation follows §7.103: point `a` defines local X and
point `b` defines the local XY plane. The nine engineering constants follow
§7.47. Source provenance recorded for the intended runtime is
`mini-moonboard-fea:ccx-upstream-2.23-v1`, image ID
`sha256:31336f517557f5dd5f97d85b1e6e15947fd1c10b44edc1364dbba4c1a5ab6c38`,
and binary SHA-256
`c6882d262b44525a563250673420dff1506c41b95e6d82d50392f9af26111863`.
The pinned `matrixstorage.c` and `arpack.c` hashes are respectively
`2b2a502637761a7663e50e43a7f5afe9322c6c775aa6c44fd7b433976bbe59c4` and
`b0640e93347badb257c4c9e6b952043a5b51a39893abbee54605d115656f3c3e`.
The [recorded build Makefile](../evaluation-resume-2026-09-24/calculix-2.23-upgrade-attempt01/build-attempt02/context/Makefile.upstream)
includes `-DMATRIXSTORAGE`.

Manual reference: [CalculiX 2.23 User's Manual](https://www.dhondt.de/ccx_2.23.pdf).

## Limits and handoff

No native solver was run for this packet. Deck acceptance, actual `.sti`/`.dof`
format from the pinned binary, numerical thresholds, and agreement of the
exported cube matrix with this oracle remain untested. The cube checks only the
export method and regular-element affine oracle. It does not test distorted
element Jacobians, the actual frame's full elastic operator, gravity readiness,
or joint acceptance. No native pass, full elastic-rank finding, or full-frame
readiness is claimed.

**Parent-owned native exit gate:** after reviewing and freezing this packet,
the FEA coordinator may run only this cube in the pinned image, authenticate
the execution, and supply its untouched `.sti` and `.dof` files for checking
before considering any use of the method on the frame.
