# Native result review: affine annulus

**Conclusion: PASS for the frozen affine elastic software-method fixture.** The recorded single CalculiX 2.23 run completed successfully, and the raw output passes every frozen affine gate. This result is limited to the diagnostic C3D10 `nu = 0` annulus fixture. It is not candidate mechanical acceptance, contact-method acceptance, washer or wood property evidence, or a capacity result.

## Integrity and run record

The run references frozen input SHA-256 `093ab967c805858b33e3d0530cadab25625cc3b8c69f696d3c39885302fa6817`. `execution.json` SHA-256 is `2bfb59d1ad2762527e44286bf783f13efac59723d1c9958deb5b3ad5a167453f`; `frozen-output-audit.json` SHA-256 is `3f0225a5d9f6e7b70ee914be2b9b4afc181a844e5281780a22f54eddbabb7095`. Both hashes match `parent-result.json`.

Run ID: `wj-washer-annular-affine-20261001-a01`.

Every output listed in `execution.json` matches its recorded SHA-256. Key raw hashes are `model.dat` `32e09011944c5c31fb694040324d52a58241c87746628ebd7c16867faf2825b5`, `model.frd` `74712df286e552921472c173d9df840e1e57a7e84783658e3bc5907a64b41441`, `native.stdout` `b7b45f4c3cb68c3c663fbe2c599d8d4845dc973c8cc6decd40d477b59d6c49d0`, `model.cvg` `65086dedb4572132b815ace04b294909c7f6f337111f9704fc310b02320f67f7`, and `model.sta` `01e324ec0ea28f4d1fd7f5e2da1277af53812b873e218be1604c17a4c8e4990d`. The run record shows the pinned image, one CPU, 1 GiB, 60-second timeout, return code 0, and 0.286-second elapsed time. Standard error is empty; standard output and status files report job completion.

## Raw output and frozen gates

I reran the read-only affine audit against the recorded `model.dat`, frozen `model.json`, and coordinate map. It returned `PASS_AFFINE_ELASTIC_METHOD_FIXTURE`, matching the stored output audit. The raw result includes all 800 displacement rows, all 800 RF rows, all 1,536 stress rows (four integration points for each of 384 elements), and one final internal-energy value.

The maximum boundary and free-interior displacement errors are `2.71e-20 mm` and `2.76e-20 mm`, against `1e-8 mm`. Maximum stress-component error is `2.95e-14 MPa`, against `0.00025 MPa`. Top and bottom vertical RF resultants are `-1469.504208 N` and `+1469.504208 N`, respectively, matching the frozen compressive sign convention; each force error is `0.0001723 N`, below its `0.015695 N` limit. Their resultant moments are within `3.6e-13 N·mm` of zero. Whole-boundary force and moment closure errors are below `4.0e-13 N` and `1.7e-13 N·mm`, against `0.02 N` and `0.05 N·mm`. Internal energy is `0.1102128 N·mm`; its `2.85e-8 N·mm` error is below the `1.11e-6 N·mm` limit.

To check gate sensitivity without changing files, I mutated copies of the actual `.dat` text in memory. The audit rejected a missing displacement row, a duplicate displacement row, a `1e-4 mm` free-node displacement perturbation, a `1 MPa` integration-point stress perturbation, and reversal of all top-face vertical reactions. Each failed its corresponding inventory, field, stress, or signed-wrench check.

No substantial result-review finding remains for this bounded affine fixture. The parent result correctly keeps mechanical acceptance false and contact acceptance false. No contact result or candidate property is inferred here.
