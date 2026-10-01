# Current SPRINGA frame input adapter, attempt 01

This packet assembles one fresh `a12-rear` stock-CalculiX input from the
reviewed current wood-joint source model. It converts the 1,292 unilateral
source carriers to native nonlinear `SPRINGA`, retains 348 bilateral
`SPRING2` rows, and replaces 200 finite floor-tangent rows with the audited
exact-stick constraint transform and scalar floor-reference nodes.

The model uses schema `current_springa_frame_input_model/v1`; legacy reduced
static linear response auditors are explicitly incompatible. `model.json`
preserves the source law inventory, ownership, carrier mappings, floor row
references, emitted source-load correction, and the response-output contract.
Fresh auxiliary source loads are expanded through the original MPCs to the
fresh physical external-load map before deck emission; that map matches the
pinned C11 input and the serialized `*CLOAD` values round-trip exactly. The
identity and transformed/permuted floor-reaction fixtures support the
reference RF mapping.
`audit.json` records source pins, material-card comparison, node uniqueness,
decimal-point real formatting, and the residuals computed from the serialized
floor equations, including their omitted and rounded coefficients.

The floor branch is conditional on strictly positive paired normal force at
every state used. The packet contains no solver result, force solution, active
state, capacity comparison, joint acceptance, freeze, or native execution.
Whole-frame response readiness remains false. The first later demand review
should focus on the left outer BG001/BG003/BG045 corner path; this packet only
binds its source ownership contract and does not calculate demands.

To rebuild this input-only packet, run `uv run --no-sync python3 prepare.py`
from this directory. The command assembles one deck and writes only
`a12-rear/model.inp`, `a12-rear/model.json`, `a12-rear/audit.json`, and
`source-pins.json`; it does not invoke CalculiX.
