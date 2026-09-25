# Current ordinary-joint mesh

This is the first successful mesh of the frozen current three-timber,
four-bolt joint. It contains no material, contact law, load, restraint or solver
step and establishes no structural response or capacity. See
[`parent-audit.json`](parent-audit.json) for the independently recomputed
ownership, exterior-face and Gauss5 quality checks.

The complete `mesh/` directory is preserved byte-for-byte in
[`complete-mesh-evidence.tar.gz`](complete-mesh-evidence.tar.gz).
[`bundle-contents.json`](bundle-contents.json) records archive and member
hashes; every archived member was read back and verified against the source.
The expanded working copy is ignored by Git. From this directory, restore it
for the current contact/material consumers with:

```sh
tar -xzf complete-mesh-evidence.tar.gz
```

[`execution.json`](execution.json) records the pinned image, command, input
hashes and successful 13.50-second execution. The prior sibling attempt01
records a launch failure caused by using `python` instead of `python3`.
The two intermediate distortion warnings in `mesh.log` precede high-order
optimization. The independent saved-deck audit finds no nonpositive Jacobian
among 807,002 sampled integration points. That does not prove positivity at
every interior point or establish response accuracy.
