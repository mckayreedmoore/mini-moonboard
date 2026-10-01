# SPRING2 reversal failure diagnosis

This is a bounded diagnosis of the one frozen nonlinear SPRING2 known-answer
run. It is not a design or joint acceptance result.

## Finding

The failure is strongly consistent with an inconsistent nonlinear tangent at
the zero-force branch switch, caused by the pinned CalculiX 2.23 SPRING2
tangent branch selecting its table interval with `val` without assigning
`val` in that branch. This is source evidence for a likely cause, not direct
proof of the runtime value or a binary-level causal demonstration. The failed
run does not establish that the negative table law itself is wrong: accepted
output stops just on the positive side of zero and contains no negative-branch
state.

## Run evidence

The frozen input hash is
`e2886f9bcd08f5b8ba6a89c19f9594409f4ca281ad381a279ad6dbb2eee20d72`.
The execution record reports the pinned 2.23 image, return code 201, and a
0.64-second run. The solver reports `*ERROR: increment size smaller than
minimum` in `native.stdout:4941`; the last retry was reduced at line 4937.
The status file shows repeated 16-iteration failed attempts near total time
1.333333 (`native/model.sta:26-37`).

Step 2 ramps the physical load from +10 N toward -20 N, so the intended
physical displacement reaches zero at total time 1.333333. The last accepted
data block is at that rounded time with `u1=+1.525879e-7 mm`; its positive
spring output is `+1.525879e-5 N` and the negative spring output is zero
(`native/model.dat:315-329`). Thus the accepted results confirm the positive
branch law and equilibrium up to the reversal, but do not demonstrate any
accepted evaluation on the negative branch. The solver's failed Newton trial
may have crossed zero internally; the emitted files do not show its trial
elongation or selected table segment.

## Pinned source evidence and limits

The source snapshot used to build the pinned executable is the unmodified
upstream 2.23 source archive recorded in
[`build_manifest.json`](../../evaluation-resume-2026-09-24/calculix-2.23-upgrade-attempt01/build_manifest.json).
In `/tmp/ccx223-src/CalculiX/ccx_2.23/src/springforc_n2f.f:196-202`, the
SPRING2 force calculation forms the current scalar displacement and passes it
to the nonlinear force interpolation. In
`/tmp/ccx223-src/CalculiX/ccx_2.23/src/springstiff_n2f.f:217-271`, the SPRING2
tangent branch loads the table arrays, then calls `ident(xiso,val,...)`
without assigning `val` in that branch. The SPRING1 tangent branch does the
same at lines 159-207, so SPRING1 is not a source-supported workaround.

By comparison, the SPRINGA tangent branch computes current minus initial
length (`val=dd-dd0`) at `springstiff_n2f.f:69-102` before selecting the
nonlinear interval. Its force branch also computes this elongation before
interpolation (`springforc_n2f.f:71-96`). The pinned manual is
[`fea/generated/ccx_2.23.pdf`](../../../../../fea/generated/ccx_2.23.pdf),
SHA-256 `a0bf3fc03f374912ff2bf28da3f7dfb6a61428dd7f41b281a2e7e1fdb318f330`;
sections 6.2.42 and 7.122 document SPRINGA and nonlinear spring tables.

The source omission can leave the SPRING2 tangent interval stale or
undefined while the force routine uses the current elongation. That is a
plausible explanation for the repeated Newton failure at reversal, where the
active slope changes. The run does not expose the value consumed by the
tangent routine, so this remains an inference. The evidence does not support
blaming or clearing the negative table interpolation: it was not reached in
an accepted state.

## Smallest method correction to check

Use the separate frozen straight-line SPRINGA coupon in
[`../nonlinear-springa-known-answer-attempt01/README.md`](../nonlinear-springa-known-answer-attempt01/README.md).
It keeps the two opposing signed laws, three load ramps, and answer unchanged,
but represents each scalar spring by a 100 mm initial X span. The first
endpoints (nodes 2 and 4) are MPC-tied to the physical X coordinate; nodes 3
and 5 are grounded, and transverse motion is fixed. For physical movements
`+0.1, -0.1, +0.1 mm`, the expected force pairs are `(+10, 0)`, `(0, -20)`,
and `(+10, 0) N`. Elongation remains within the ±10 mm tables, and the
100 mm spans remain positive. This is a proposed method check only; those
SPRINGA answers require the parent's separately scoped native run before the
method can be considered verified.
