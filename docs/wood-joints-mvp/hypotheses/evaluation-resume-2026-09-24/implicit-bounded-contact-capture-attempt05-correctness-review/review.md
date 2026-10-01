# Attempt05 correctness review

## Hash binding and scope

This review is bound to the attempt05 package whose `source-pins.json` SHA-256 is `a671a0c53266cfae4986c403d63fb31c9180c8fafbf885e5018e52621efb2570`. I verified every path in its packet inventory against the recorded SHA-256 values. Key inputs reviewed were:

- Pinned source archive: `9c88385c10fb04f5dc6c4e98027a51bebdd8aee3920e05190d6c1dd08357d6e7`
- Generated patch: `e536c707f83c9ef11ffdfc55480d750ffd7b9dc68a73abd3e72c648eb20b4dba`
- Patch-preparation record: `807a54891435ed85173885af3da070c34241382da3c3b60866eea9a2e89930da`
- Contract: `6bc77a005a1f21cf83c77d7bf47514030e8fe4e7d35562629b28971b7a12db38`
- Sink: `8ca64a40d8f5c4a093cd0750b9c31de85109dc9acc3158cb8502a5b512907a52`
- Reader: `ab2d466508895e28a4e45656f60bbd0aee6b27997fc5378d6f9044333223a1e4`

I read the repository `AGENTS.md`. I did not consult prior review reports. I reproduced patch generation in a temporary copy after removing only the copied generated artifacts; the generated patch and preparation record were byte-identical to the package. Applying that patch to the extracted pinned sources produced the three recorded modified-source hashes. The generation path checks each source delta for insertions/equal lines only. I inspected the C and Fortran hooks, pass-two roster checks, bounded counters, publication/error handling, and reader validation. I did not build the production solver, invoke Docker, run a solver or coupon, or execute the offline test suite.

## Finding

### P1 — Missing spring energy can still be marked as complete

The frozen contract requires energy rows for generated trial points whenever `nener==1` and says missing force or energy is unavailable rather than zero (`capture-contract.json:44`). The sink can violate that invariant while declaring the trial and run complete. In `capture-sink.inc:571-572`, a non-finite or absent energy row only clears `energy_complete`; it does not set `wjcc_error`. `capture-sink.inc:577-580` then sets `trial_complete` from only `wjcc_error` and `wjcc_overflow`, without checking `energy_rows == count`. The summary correctly emits `NA` for the incomplete energy at `capture-sink.inc:327`, but only sets the writer error for a count mismatch or unjoined row at `capture-sink.inc:332`.

Static fixture proof: with `nener==1`, matched law-2 trials, complete finite force inputs, and one trial energy set to NaN, the affected tie has `energy_rows < count` and `energy_complete == 0`, while no path above sets `wjcc_error`. The sink therefore can emit `trial_complete=1`; with an accepted convergence link, that flag can flow into `ITERATION_LINK` and `RUN_END.complete`. The reader permits this stream when `expected` omits `require_energy` or sets it false: `capture_reader.py:391-396` allows the `NA` energy field and only checks row coverage when the optional `require_energy` flag is true. This violates the contract even though the unavailable value remains `NA`.

Impact: a capture can claim complete map/trial coverage and receive `PASS_CAPTURE_STRUCTURE` despite lacking required stored-energy evidence, so a consumer following the contract’s complete-trial gate can treat an incomplete trace as usable. The offline `noenergy` fixture covers `nener==0` and explicitly disables the optional requirement (`tests/test_capture.py:348-355`); it does not cover incomplete energy while `nener==1`.

The sink should mark the generation/run incomplete whenever `nener==1` and any expected generated trial lacks an energy row. The reader should unconditionally require `energy_rows == count` for `nener==1`; `require_energy` can continue to control whether a run with `nener!=1` is acceptable for a caller that does not need energy.

## Other reviewed areas

No additional correctness finding was identified in the reviewed source pins, patch regeneration, C/Fortran hook arguments and placement, pass-two identity/completion logic, combined candidate cap, output publication/error path, or record-order and conservation checks. These checks establish source and offline-contract properties only; attempt05 still has no patched solver build or native runtime qualification.
