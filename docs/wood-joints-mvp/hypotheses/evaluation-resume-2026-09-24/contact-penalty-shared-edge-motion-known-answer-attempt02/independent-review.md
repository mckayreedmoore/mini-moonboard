# Independent native-evidence review

Read-only audit of the two completed static shared-edge penalty/full-cap-motion
method cases. I did not change frozen inputs or native outputs and did not
repeat a native run. I independently checked the raw DAT, FRD, STA and CVG
results against the frozen contracts, decoded pair output with the pinned
parser, and recomputed port coordinates and support-plus-section closure.

## Freeze, solver and execution

All 15 files in `input-freeze.json` match their pinned hashes. The freeze hash
is `6635c91f8d34cfb3d48964d31c985a43b4fe978866104b46bb007afc33a32bd0`;
the root execution record points to it and reports unchanged inputs. All nine
captured output hashes per case match their nested execution records. Both
executed decks match the frozen deck hashes shown below.

The lexical audit verifies a formatting-only repair from attempt01: each deck
retains exactly the same 1,409 numeric values, nonnumeric tokens and card
order, with maximum numeric token width eight. No geometry, equations, loads,
oracle values or tolerances changed. Both serial jobs completed on unpatched,
uninstrumented CalculiX 2.23; Docker and container exit codes are zero and
`OOMKilled=false`. The pinned image is
`sha256:31336f517557f5dd5f97d85b1e6e15947fd1c10b44edc1364dbba4c1a5ab6c38`
and binary SHA-256 is
`c6882d262b44525a563250673420dff1506c41b95e6d82d50392f9af26111863`.
Elapsed times were 0.319 s (`shared_slave_motion`) and 0.420 s
(`cross_role_motion`). Each raw STA has one accepted full increment at step 1,
increment 1, attempt 1, time 1, in two Newton iterations; CVG has two rows and
there is no cutback or rejected attempt.

## Raw result checks

Both cases report the two remote support reactions as 3.999953997 N. The
pinned pair parser returns six finite CF/CFN/CFS identities per case. CF=CFN,
CFS is zero, and each CFN tension-positive mean-normal projection is
−3.999954 N. The role-dependent force and origin-moment vectors are:

| Case and pair (slave / master) | CFN force (N) | CFN moment at origin (N·mm) |
| --- | --- | --- |
| Shared `Z_CENTRAL / Z_LOWER` | `(0, 0, 3.999954)` | `(3.999954, −3.999794, 0)` |
| Shared `X_CENTRAL / X_LEFT` | `(3.999954, 0, 0)` | `(0, 3.999794, −3.999954)` |
| Cross `Z_CENTRAL / Z_LOWER` | `(0, 0, 3.999954)` | `(3.999954, −3.999794, 0)` |
| Cross `X_LEFT / X_CENTRAL` | `(−3.999954, 0, 0)` | `(0, −3.999954, 3.999954)` |

The maximum pair force error is `4.6e−5 N`; maximum moment error is
`2.111e−4 N·mm`, within the frozen 0.041 vector-norm gates. Reversing the x
pair roles reverses the x resultant as expected. These are net pair
resultants, not cancellation-free local pressure or bearing-onset evidence.

Using restrained physical-node DAT reactions and deck coordinates, then
adding raw cap SOF resultants, I obtain force-closure norms `5.71418e−5 N`
and `5.71421e−5 N`, and moment-closure norms `5.71451e−5 N·mm` and
`5.71454e−5 N·mm` for shared and cross cases. Each is below its frozen 0.041
gate. The cap SOF forces are approximately −4 N in the prescribed normal
directions with the expected origin moments. SOF is the solver's bulk-stress
section integration proxy; it is not local contact force.

Applying the frozen six-component projection matrices to raw physical DAT U
reproduces the controller port coordinates to at most `2.1e−12` mm/rad. Raw
endpoint energies are CENTRAL ELSE `7.999958e−5`, LOWER/LEFT ELSE
`3.999987e−5` each, and CELS `3.999907e−5 N·mm`. Their combined
`ELSE+CELS` is `1.9999839e−4 N·mm` versus `2.0e−4`; this is an endpoint
channel check, not external work or path quadrature.

Each FRD DISP, FORC and STRESS dataset contains all 375 physical nodes with
finite components. DAT U/RF also cover 375 physical nodes; FRD/DAT maximum
differences are `5.0e−11 mm` for U and `5.0e−7 N` for RF. Contact and
incidental ERROR counts remain diagnostics.

## Scope and pinned references

The result supports only the tested static combination of two declared
penalty-contact role patterns and full six-component quadratic-cap motion
maps. `verifier.json` is `PASS_SHARED_EDGE_PENALTY_MOTION_METHOD_FIXTURE`;
mechanical, work-energy, joint-acceptance and release flags remain false. It
does not establish MORTAR or current-joint applicability, curved-bore local
pressure, bearing onset, resistance or release. The separate CalculiX 2.23
dynamic prescribed-MPC inertia failure remains unresolved; this static fixture
does not correct or re-enable that transient method.

| Artifact | SHA-256 |
| --- | --- |
| `input-freeze.json` | `6635c91f8d34cfb3d48964d31c985a43b4fe978866104b46bb007afc33a32bd0` |
| `execution.json` | `0fbbab8476ab1cc540977ff5ca91a75a73ad4a697bf46d4c9ce7ac809bff33a2` |
| `expected.json` | `f4b952f190c7c4e5815029857f7e2e92ad8bcfb723fab462c6988a93e2d75b48` |
| `lexical-audit.json` | `904d3f186afb8157dbf2e57fd5a9fbb8c7f7bc7b13987be22e04dddcd7f92284` |
| `verifier.py` / `verifier.json` | `4e10a3a565be8e12c880fab198a09919dd638e992559d2b090216f165f7868ec` / `f15267a20d5f75672fd60719f8e211e3e3c3ae14222095ef98f1c66adfd45283` |
| `input/shared_slave_motion.inp` | `c0ddf9f41426f8fcec400eb49ee40256c0e9a76eec541291440e9410f1f99241` |
| `input/cross_role_motion.inp` | `0dc51e0d4fb01927fa2a81140e2d05a329857ae407a955e8ef679dc582bd454b` |
| Pair-output parser | `c729729c9f7d520dfaa4d835e5a0c2ce633ab9e12e0e60aef931b1c98df03496` |
| Shared nested execution record | `9854174c52150e25249075d261768363e3f1333cc8a482f6accd7656ff9c6682` |
| Cross nested execution record | `c5a63d543b67880f72ba5779d157de1fec86f0505949121109bf080a08094906` |

The nested records pin all nine output hashes per case; all were independently
matched to files. No additional native run is proposed by this review.
