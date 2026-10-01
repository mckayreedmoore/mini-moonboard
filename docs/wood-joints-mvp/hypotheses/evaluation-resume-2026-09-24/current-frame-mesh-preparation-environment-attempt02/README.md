# Full-frame meshing environment evidence — attempt 02

Date: 2026-09-29. This append-only record supersedes the availability finding
in attempt01 only for the reported environment session. It preserves that
earlier probe unchanged.

The parent coordinator reports that a direct official Gmsh 4.12.1 Linux
tarball download succeeded (SHA-256
`cca67edc8895ded021652171439d02a2e606d0b14ccd5476b246759da3557216`). The
binary initially lacked `libGLU.so.1`. The parent then downloaded
`libglu1-mesa=9.0.2-1.1build1` (SHA-256
`4288833eebfbf6b00d1ae98159f429e1f7f6398288c9305edeeb185d9ed048d9`),
extracted it under `/tmp/gmsh-deps`, and reports the following command
returned `4.12.1`:

```sh
LD_LIBRARY_PATH=/tmp/gmsh-deps/usr/lib/x86_64-linux-gnu /tmp/gmsh-4.12.1/bin/gmsh -version
```

This is a temporary runtime path, not a system or `PATH` installation. The
present register author did not reproduce the command; `gmsh` remains
unavailable on this shell's `PATH`.

The parent also reports Docker Engine server 29.1.2 and the pinned image
`mini-moonboard-fea:ccx-upstream-2.23-v1` with image ID
`sha256:31336f517557f5dd5f97d85b1e6e15947fd1c10b44edc1364dbba4c1a5ab6c38`.
The observations and their limits are recorded in
[`environment-observations.json`](environment-observations.json), with
source identities in [`source-pins.json`](source-pins.json). The Gmsh tarball
and dependency package hashes are parent-reported artifact hashes; this packet
does not contain those binaries or their download logs.

This evidence supports a bounded mesh-only preparation as an operationally
plausible next task, subject to a separate parent-owned input freeze and
readiness decision. It does not authenticate the complete mesh, STEP import,
Python API, element quality, or any solver capability. No mesh or solver was
run for this evidence record. No material, connection, support, load-transfer,
readiness, acceptance, or release gate is closed.

The proposed mesh-only step must bind each of the 50 current member IDs to its
input STEP hash, imported solid, mesh body, and element/node IDs; establish a
one-to-one identity map with no missing, duplicate, or merged member; compare
per-body volume, bounds and centroid to source geometry; report element type,
count and predeclared quality bounds; and receive an independent identity and
quality review. Mesh completion must not assign solver DOFs or imply mechanics
readiness. The exact source manifest and existing patch-only mesh audit are
pinned in [`source-pins.json`](source-pins.json).

The Gmsh version and Docker observations are parent-reported environment
evidence, not reproduced output from this coordinator. Parent retains any
decision to freeze or launch the mesh-only attempt.
