# Full-frame meshing environment probe — attempt 01

This append-only probe records why the next T09 full-frame mesh-preparation step did not run for `led-clearance-2x6-runner-seated-blocks-v1`. The reviewed source audit binds the exact 50-member STEP bundle and confirms that the available current mesh remains a local ordinary-joint patch covering only three wood-member identities.

The repository patch mesh records Gmsh 4.12.1. Neither the system Python nor the workspace virtual environment can import Gmsh, and no `gmsh` executable is on `PATH`. Ubuntu noble advertises `4.12.1+ds1-1.1build2`, but the package is not installed or cached. A version-exact `apt-get download` was attempted into `/tmp`; it failed because DNS resolution for `archive.ubuntu.com` is unavailable, so no package was obtained. The existing Docker client reports version 29.1.2 but cannot access `/var/run/docker.sock` due to permissions; the pinned attempt09 image therefore cannot be used here.

No package was installed or extracted, no CAD or geometry changed, no mesh or solver deck was generated, no native solver ran, and readiness, acceptance, and release remain false. The source pins and raw observations are in [`source-pins.json`](source-pins.json) and [`environment-observations.json`](environment-observations.json).

The next executable step is to restore access to the pinned runtime or provide an authenticated offline Ubuntu noble Gmsh 4.12.1 package set. Then freeze a separate mesh-only attempt using all 50 exact member IDs and STEP hashes. Verify every body-to-member join and mesh quality. Keep solver DOF maps, materials, attachments/contact, supports, mass transfer, six-case loads, native readiness, and acceptance as separate unresolved gates.

This availability probe is not evidence that no package route exists. It records only the checked local caches, current DNS failure, and denied Docker socket.
