# Static coupon regression for the contact-point trace build

This packet prepares a one-case, static, mortar-contact regression for the
final output-only trace binary from parent build-attempt04. It compares that
binary's solver outputs and inherited attempt04 contact-count/convergence
events with the frozen old result at
`../../ordinary-external-force-transient-attempt04-diagnostic/coupon-known-answer-attempt02/`.
The exact shared input SHA-256 is
`73f32786bf6dee6c88e78f8e3d4e24f67afb9548225868fd10850c77e27298ab`.

The comparison requires byte identity for `coupon.12d`, `.cel`, `.cvg`,
`.dat`, `.sta`, and `spooles.out`. For each FRD, the only normalization is
replacing the clock on exactly one `1UTIME` record; all other bytes must
match. The old `solver.stdout` is retained as the event baseline. New
`CCX223_ATTEMPT04_CONTACT` and `CCX223_ATTEMPT04_CONVERGENCE` JSON records
must match the old event lines exactly and in order. New `CCXPT_MAP`,
`CCXPT_UNMAPPED`, and `CCXPT_TRIAL` records are parsed strictly, checked for
finite numeric values, and summarized by coverage counts. For each exact
`.cvg` state identity, trial-row count must equal the native contact-element
count; trial element and Gauss-point IDs must be unique within that identity.

Trace parsing does not claim that a generation row and a trial row belong to
the same accepted state. `native_isol` is preserved as an integer; a map is
marked generated when `native_isol != 0`, including native values greater
than one. A `CCXPT_TRIAL` energy field is unavailable unless
`energy_enabled == 1`; the emitted zero placeholder when it is disabled is
not treated as a measured zero. These traces do not qualify force,
convergence, physical contact, or the current joint.

The run limits are one CPU, 1 GiB memory, no network, 60 seconds wall time,
and a 16 MiB aggregate native-output cap. The runner has separate `--check`,
`--freeze`, and `--run --freeze-sha ...` modes. It cannot start a native run
until the parent-created input freeze exists and its hash is supplied. This
packet was prepared only: it has not been frozen or executed here. Parent
owns freeze, serialized execution, and final validation.

Run `python3 prepare.py --check`, `python3 run.py --check`,
`python3 verifier.py --self-test`, and
`python3 verifier.py --integration-self-test` for read-only/synthetic
preflight. The integration check creates and removes a disposable synthetic
capture under this packet and never invokes CalculiX. `run.py --freeze` is parent-only after review;
`run.py --run --freeze-sha <hash>` performs the one authorized native
invocation after the freeze is recorded.
