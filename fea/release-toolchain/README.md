# Panel-edge diagnostic toolchain

The existing `mini-moonboard-fea:box-v1` image contains CalculiX and Gmsh but
not NumPy. The release diagnostic reuses the existing NumPy compliance audit.
This derived image adds that distribution package without changing historical
Dockerfiles or requiring host sudo access.

```bash
docker build -t mini-moonboard-fea:release-v1 fea/release-toolchain
docker run --rm --user 1000:1000 -e OMP_NUM_THREADS=2 \
  -v "$PWD:/work" -w /work mini-moonboard-fea:release-v1 \
  python3 -m fea.timber_release solve
```

Prepare first with `uv run python -m fea.timber_release prepare`. Preparation
and solving refuse to overwrite prior evidence; use a fresh work location for
reproduction. Heavy runs remain sequential. These commands do not publish or
approve a design.

Observed toolchain on 2026-09-08:

- Base image ID: `sha256:37671083a88ded305c4fcd83960a767dad4c2acb480976cb75fab5df261e2646`.
- Derived image ID: `sha256:083de8eefd4d9d9029d28ac1fdbb933a3b1e024225d8048165d6ef580d1b8f59`.
- CalculiX package: `2.21-1`.
- Python package: `3.12.3-0ubuntu2.1`.
- NumPy package: `1:1.26.4+ds-6ubuntu1`.

The Dockerfile uses distribution repositories, not a pinned package snapshot;
a later build may produce a different image ID. Record the actual environment
for a new solve. The initial attempt in the base image failed at Python import
before starting CalculiX or creating a solver launch record. The successful
three-step run used the derived image above with two OpenMP threads.
