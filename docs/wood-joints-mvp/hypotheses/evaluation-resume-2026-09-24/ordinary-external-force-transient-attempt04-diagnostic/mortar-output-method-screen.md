# CalculiX 2.23 MORTAR output-method screen

Pinned official source archive: [ccx_2.23.src.tar.bz2](https://www.dhondt.de/ccx_2.23.src.tar.bz2),
SHA-256 `9c88385c10fb04f5dc6c4e98027a51bebdd8aee3920e05190d6c1dd08357d6e7`.
Source paths below are archive members under `CalculiX/ccx_2.23/src/`.
Manual: [CalculiX 2.23 CCX manual](https://www.dhondt.de/ccx_2.23.pdf),
keyword sections `*NODE PRINT`, `*SECTION PRINT`, and `*CONTACT PRINT`.

## RF is not a MORTAR surface resultant

`*NODE PRINT,RF` writes the nodal `fn` vector: `results.c:391-395,455-472`,
`resultsprint.f:115-123`, and `printoutnode.f:94-101`. The manual defines RF as
external force at a node, including reactions and applied point/distributed
loads. `GLOBAL=YES` selects global components for the nodal vector; it does not
make the result surface-specific. In MORTAR, `stressmortar.c:659-679` forms
contact-force vectors `f_cs`/`f_cm` separately, and `nonlingeo.c:3293-3298`
uses them in the residual. Thus all-node DAT RF does not directly report a
selected slave/master contact resultant.

FRD RF differs: `nonlingeo.c:3700-3713,3726-3738` brackets FRD writing with
`mortar_prefrd.c:58-61` (adds `cfs` to `fn`) and
`mortar_postfrd.c:44-46` (subtracts it afterward). This temporary addition is
not made around the `.dat` `results()` call (`nonlingeo.c:3667-3687`).
`resultsforc.c:34-58,74-117` also removes and redistributes MPC forces in
`fn`; summing nodal RF therefore carries constraint-force effects. Shared
interface nodes have no slave/master-side RF distinction. Global-coordinate
all-node sums can be diagnostic, but cannot isolate the selected MORTAR face
force.

## Supported standard diagnostic routes

`*SECTION PRINT,SURFACE=<element-face-set>` with `SOF` reports a selected
surface resultant by integrating stress, not contact traction. `results.c:455-458`
describes extrapolation from integration points to nodes;
`printoutface.f:421-428,431-470,491-504` interpolates those nodal stresses and
integrates traction over the face. This route includes C3D10 faces:
`printoutface.f:143-151,299-320` sets the six-node triangular face and its
integration/shaping path. Treat it as stress-derived when interpreting a
contact-force comparison.

Do not request `CFN`/`CFS` as a MORTAR resultant. The manual's `*CONTACT PRINT`
description scopes CF/CFN/CFS to a selected face-to-face penalty contact pair;
source `contactprints.f:59-68` recognizes those labels, while
`printoutcontact.f:76-83` loops generated contact elements and their `stx`
data. MORTAR uses the separate nodal `cfs` path above; 2.23 provides no
documented CFN/CFS MORTAR output route.
