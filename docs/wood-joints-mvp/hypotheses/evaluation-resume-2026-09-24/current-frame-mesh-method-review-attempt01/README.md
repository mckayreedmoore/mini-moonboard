# Gmsh 4.12.1 mesh-method source review — attempt01

Date: 2026-09-29. Scope: read-only method/source review for a proposed
geometry-only mesh of the 50 bodies in revision
`led-clearance-2x6-runner-seated-blocks-v1`. This is not an executable mesh
freeze, a mesh launch authorization, a mechanics method validation, or a
readiness/acceptance result.

## Exact-version source basis

The official [Gmsh 4.12.1 source archive](https://gmsh.info/src/gmsh-4.12.1-source.tgz)
was downloaded to `/tmp/gmsh-4.12.1-source.tgz` from the official source
index. Its SHA-256 is
`59ee2118ba7b099e9d1502572c9af4221501af955103d2b687aaa3890d13325e`.
The pinned extracted source-file hashes are:

| Source file inside official archive | SHA-256 | Relevant API/evidence |
|---|---|---|
| `api/gmsh.py` | `fa69936fc45646eca8b29ab0fd9e32ebaf45216414cbc75c380b4c0db7b6f485` | Exact 4.12.1 Python API signatures and docs for `occ.importShapes`, `occ.getMass`, `occ.getCenterOfMass`, and `mesh.getElementQualities`. |
| `api/gmsh.h` | `af694b54a7b166e93c26f4afa4485f9fe22d3bc60287a535f6ffe5387d1b9f94` | Exact 4.12.1 API definitions/comments for OCC import and per-volume mass/center-of-mass and mesh quality. |
| `tutorials/python/t20.py` | `de8a377b1cf4445d4d0235ef2552411249ea527f783d1228ff41e5394ceb2d89` | STEP import with `occ.importShapes`, highest-dimensional entity tags, bounding box, default millimeter target unit, and `mesh.generate(3)`. |
| `examples/api/mesh_quality.py` | `894a60c3b568b50bacad25b818dbae766d59d51ca24503448f9ed4da90d4e843` | 3D mesh generation, `getElements(dim=3)`, and `getElementQualities(..., "minSICN")`. |

The environment record pins the official Linux binary tarball as
`cca67edc8895ded021652171439d02a2e606d0b14ccd5476b246759da3557216` and
reports a successful `gmsh -version` result of `4.12.1`. Parent rechecked that
CLI result on 2026-09-29. The Python binding is **not present** in the current
shell (`importlib.util.find_spec("gmsh")` returns `None`; the extracted
runtime has no `gmsh.py`). The source API documentation therefore confirms
that the methods exist in 4.12.1; it does not establish that a Python API
runtime is installed or usable here.

## Method assessment

A suitable bounded mesh-only implementation can import each STEP separately,
map its returned volume tag to the frozen member ID, avoid Boolean operations
and duplicate removal, and compare each imported solid's volume, bounds, and
center of mass with the pinned source summaries. After 3D generation, it can
record element types, element/node ownership, and per-element `minSICN` values.
The member/STEP/imported-solid/mesh identity must remain one-to-one; do not
merge bodies or nodes or infer a mechanical joint from coincident geometry.

Gmsh defines the quality calculation but supplies no project acceptance
threshold. Element order, size controls, exact API/CLI route, quality metrics,
and numeric limits still need to be chosen and frozen before any full mesh.
A small analytic solid and a representative source STEP are appropriate
known-answer tests of the chosen import, geometry comparison, and extraction
path, but **neither test was meshed in this review**. The current root
continuation note does not authorize mesh generation. Any such smoke test
requires a new parent go/no-go; the all-50-body mesh requires its own reviewed
freeze and parent authorization after the smoke test passes.

Even a successful mesh would establish only source identity, geometry
representation, and the declared mesh-quality checks. It would not establish
material axes, panel layups, supports, contact/attachment laws, loads,
receiver force sharing, solver mappings, demands, mechanics readiness,
or acceptance. The current source audit records 47 of 50 bodies absent from
the old local patch mesh and all full-frame solver mappings null.

## Bound records

- [Parent-reported environment attempt02](../current-frame-mesh-preparation-environment-attempt02/README.md),
  SHA-256 `477a1c30bdca538ab63aac00d7c635f836cd86afc68b016e1eaf714de580c0ed`.
- [Exact 50-body source audit](../current-frame-mesh-source-audit-attempt01/README.md),
  SHA-256 `e323692e6a45a5c35a2c11567dd5da1a513bb90599b3df7abdcf1b938aac0410`.
- [Official Gmsh source archive index](https://gmsh.info/src/), which lists
  `gmsh-4.12.1-source.tgz` dated 2024-01-11.
