# Shared-edge penalty contact and full-cap motion: passing method fixture

Both frozen cases pass the unchanged mechanical, contact, motion-map and
output gates under pinned unmodified CalculiX 2.23. Each completed one static direct
increment at time 1 in two Newton iterations, with exit code zero, no OOM,
no cutback and no rejected attempt. The failed input-reading attempt01 remains
preserved. This separate correction changes numeric spelling only; all
numerical values, equations, geometry, material, contact and gates are equal.

| Case | Elapsed seconds | Support force, X / Z (N) | Force closure (N) | Moment closure (N·mm) |
| --- | --- | --- | --- | --- |
| `shared_slave_motion` | 0.319 | 3.999953997 / 3.999953997 | 5.714183e-05 | 5.714511e-05 |
| `cross_role_motion` | 0.420 | 3.999953997 / 3.999953997 | 5.714209e-05 | 5.714536e-05 |

The analytical force is 4 N per pair; force and moment tolerances remain
0.041 N and 0.041 N·mm. Every required pair CF, CFN and CFS record is finite
and passes its signed vector/origin-moment oracle. Maximum normal-profile
error is 8e−11 mm and gap error 1.2e−10 mm against 1e−7 mm. Area-normalized
compliance is approximately 5.0000575e−5 mm³/N against 5e−5.

Both cases print CENTRAL ELSE 7.999958e−5 N·mm, LOWER and LEFT ELSE
3.999987e−5 N·mm each, and penalty CELS 3.999907e−5 N·mm. Their sum is
1.9999839e−4 N·mm against 2e−4, within the frozen energy gate. These are
endpoint energy-channel checks, not a work-history integration result.

All 375 physical nodes have finite DAT/FRD U and RF, and the FRD stress field
covers all 375 nodes uniquely. Controller U is read from DAT. Reconstructing
each six-component cap coordinate from physical U matches its controller and
prescribed values. Only explicit physical support RF and cap SOF are used for
reaction closure; equation-dependent and controller RF are not generalized
reaction evidence. Incidental FRD ERROR output is parsed as diagnostic data.

Parent validation matches all 15 frozen artifacts and 18 captured output
hashes. The separate [independent raw-output review](independent-review.md)
confirms these scoped results and the static-only applicability. No current-joint
run is selected by this result. The fixture establishes the tested combination
of shared-edge penalty contact and off-contact-dependent full-six motion maps;
it does not establish curved-bore onset, an actual joint response, a complete
joint law, resistance, structural acceptance or release. MORTAR is excluded.
The separate [2.23 prescribed-MPC dynamic check](../calculix-2.23-upgrade-attempt01/README.md)
still fails its inertia reference; this static result does not repair or
re-enable the disabled prescribed-MPC transient producer.

| Artifact | SHA-256 |
| --- | --- |
| `input-freeze.json` | `6635c91f8d34cfb3d48964d31c985a43b4fe978866104b46bb007afc33a32bd0` |
| `execution.json` | `0fbbab8476ab1cc540977ff5ca91a75a73ad4a697bf46d4c9ce7ac809bff33a2` |
| `expected.json` | `f4b952f190c7c4e5815029857f7e2e92ad8bcfb723fab462c6988a93e2d75b48` |
| `verifier.py` | `4e10a3a565be8e12c880fab198a09919dd638e992559d2b090216f165f7868ec` |
| `verifier.json` | `f15267a20d5f75672fd60719f8e211e3e3c3ae14222095ef98f1c66adfd45283` |
| `lexical-audit.json` | `904d3f186afb8157dbf2e57fd5a9fbb8c7f7bc7b13987be22e04dddcd7f92284` |
