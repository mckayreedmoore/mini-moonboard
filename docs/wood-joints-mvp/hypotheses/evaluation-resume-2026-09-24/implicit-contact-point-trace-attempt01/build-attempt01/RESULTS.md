# Build attempt 01

FAILED before source compilation. BuildKit interpreted the local image ID in `FROM` as a registry reference and could not resolve it. No solver executable was built or run. The immutable execution record, input freeze and log retain this tooling failure. Attempt 02 uses the existing local image tag with its image ID verified before and after, `--pull=false`, and the same source/patch context.
