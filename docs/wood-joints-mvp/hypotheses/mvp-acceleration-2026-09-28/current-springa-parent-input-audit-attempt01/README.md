# Parent serialized frame-input audit

`check.py` independently compares the forthcoming adapter to the pinned
reviewed C11 input, without reading that run's rejected response. It checks
physical bodies, load and interface ownership, material constants and
orientation/section cards, original nodes, unique dependent equations and
fixed-DOF compatibility. It reconstructs the original floor constraints from
the actual serialized deck coefficients and compares the source-load
reaction correction to the emitted reference-transfer coefficients.

No result is recorded until the adapter emits its model and deck. Run with
`OPENBLAS_NUM_THREADS=1 uv run --no-sync python3 check.py` from this directory.
A passing input comparison is not native readiness, floor qualification,
usable corner forces or joint acceptance. It does not freeze or launch a run.


## Source-point mapping result

`source_wrench_check.py` passes all 200 original floor channels. Nodal
reactions from each unit source multiplier reproduce its owned tangent
force and moment at the recorded floor point: maximum force error
1.82e-13 and moment error 2.27e-10 mm per unit force. This verifies the
source mapping only. It does not yet check the adapter deck or recover any
physical case reaction. Reproduce with `OPENBLAS_NUM_THREADS=1 uv run
--no-sync python3 source_wrench_check.py`.


## Emitted frame input result

The independent check now passes on the emitted a12-rear adapter: all 50
physical bodies, geometry/ownership, physical load maps, and material/
orientation/section cards match the pinned source input. The serialized
floor constraints reconstruct the source rows within 7.54e-14; reference
transfer error is 4.76e-14. Each unit reaction channel preserves its physical
force and moment within 3.61e-13 and 4.45e-10 mm. The emitted-load correction
matches its declared value exactly. All 21,998 equation pivots are distinct
and none is also fixed. These are input results, not frame force results.

`check.py --input-directory PATH --output-name NAME.json` can independently
check a subsequent parent freeze without changing the prepared source input.
The physical response implementation and native case remain unverified.
