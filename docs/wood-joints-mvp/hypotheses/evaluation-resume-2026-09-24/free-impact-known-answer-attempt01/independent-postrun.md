# Independent post-run review

This is a read-only diagnosis of attempt01's frozen verifier result and raw trace output. It does not change or replace the frozen FAIL, and it makes no joint-acceptance claim.

## Finding

The trace failure is a method-identity expectation error. The frozen contract expects `map_pressure_law=1`, but the pinned source and the input require integer law code `2` for `PRESSURE-OVERCLOSURE=LINEAR`. The trace contains 7,896 MAP rows; each has `nmethod=4`, `tie=1`, and pressure-law code `2`. The other two identity fields therefore match. The surface-contact formulation and the pressure-overclosure law are separate fields: `TYPE=SURFACE TO SURFACE` selects contact-pair mode `mortar=1`, while the surface behavior stores the law in `elcon(3,1,imat)`.

In pinned CalculiX 2.23 source, `surfacebehaviors.f` maps the LINEAR option to `L` (lines 66–67) and assigns `elcon(3,1,imat)=2.5d0` in its linear branch (lines 194–200). The contact-generation path uses `int(elcon(3,1,imat))` (for example, `gencontelem_f2f.f` lines 554–560); the trace instrumentation records that same integer conversion. Thus the observed and expected linear-law code is `int(2.5)=2`. `contactpairs.f` lines 115–118 separately maps `TYPE=SURFACE TO SURFACE` to `mortar=1` and `TYPE=MORTAR` to `mortar=2`.

## Captured evidence

The frozen input is SHA-256 `2b253f63f9e8cee1bcb471ba3fb6b8150e72df781432bcfe6a1019e66d44caea`; it contains both `*SURFACE BEHAVIOR,PRESSURE-OVERCLOSURE=LINEAR` and `*CONTACT PAIR,...,TYPE=SURFACE TO SURFACE`. The frozen input manifest is `534d22546dc808e97fedd0c3ac82b77aec8ff4f4230a5e64de471c57ff245637`; serialized execution record is `dbeff556550e51c485da9dc778afb6f003a9d59f2dc8aefb3c4c7ed5422bff17`.

The original result remains [verifier.json](verifier.json), SHA-256 `7632ca5f04e4d91feb55f1f5c6e3f92a021da97709470da7b26d0314121a11c4`: baseline PASS, trace FAIL with the sole error `MAP method/tie/pressure-law identity differs`, overall FAIL. The native captures completed normally in the frozen serial order. Trace case execution record SHA-256 is `f43504e6da9bf1ef46927073af2adc4103f1e36087c633d437717e0eb0fadfe9`; stdout is `7e477bac2115adba748419eb2400ce930d912042d64d1e4619928fd563649065`. Captured trace DAT/CVG/FRD/STA hashes are respectively `2b0fe3d61ba8aa67e40a0a845235bdf8da94cf409b670182706f1a2757b6d996`, `eb9798fe5fe2aa071989e07f1f9ec6f711c92f8edf7d566609f000fc4ca4a883`, `aa59debef3f335ac946206e0a221a537d929d6d6ad9ea4162386b65288ae7193`, and `b0409c83c04b9b230d8a1abf8cd5b28858cd363d24713eac0ea5335606b164d2`.

The solver archive is SHA-256 `9c88385c10fb04f5dc6c4e98027a51bebdd8aee3920e05190d6c1dd08357d6e7`; relevant source member hashes are `surfacebehaviors.f` `f0088a364b9b069aa10be9c4b4f38d72df875295f339830d7e2df6762ad9e161`, `contactpairs.f` `e2b7e8176adc70f02f5140308a0c6a591fc9f7f620026867708e6345a9d9c488`, and `gencontelem_f2f.f` `853e2159f37666bc1430516bb4e5c65b6ba484ef1866454930e66cf317fb8afe`.

The frozen trace diagnostic patch is SHA-256 `8fb9e5a88a72109a095ccb1dab650860535102f7d806f0dd6d230c23127af7ff`; its `CCXPT_MAP` write explicitly emits `int(elcon(3,1,imat))` as the pressure-law field. Attempt01's freeze manifest pins this patch hash.

## Bounded correction

The defensible correction for a new attempt is to set only `acceptance.json:trace_contract.map_pressure_law` from `1` to `2`, and update the verifier's synthetic MAP fixture to emit the same source-defined code. Keep the native input, mechanics and numerical gates, tolerances, and all other MAP expectations unchanged. The post-run in-memory diagnostic `parent-law-id-diagnostic.json` (SHA-256 `2828a47576265346eec4070f49453989af9fea248b49957f2e8c7ebba56e22c8`) corroborates that changing this identity expectation alone makes the existing analytical trace checks pass; it is not a replacement for a newly frozen, serialized attempt.

Attempt01 remains a captured FAIL. A corrected contract must be frozen as a distinct attempt and verified against its own execution. Even a corrected known-answer fixture result qualifies only this method fixture, not the wood joint's mechanics, energy acceptance, or release.
