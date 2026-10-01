# Independent preflight: dynamic contact-point known-answer coupon

Reviewed the offline auditor, expected contract, and bounded runner read-only.
No build, freeze, or native solve was run for this review.

The reviewed bytes were `verifier.py` SHA-256
`2327ac4f6e94272e9a6ad0f023c43798448f72be9624c35e9a6d98d4a659a41d`,
parent `expected.json` SHA-256
`4cd7685658964f814fbffe8431072e70ee9fb19c34c624f9d5805aa3b756b618`,
`run.py` SHA-256
`27481e9644458a1f9d50e6d9f734876b3f20c3c02b612f82753e2df15ae2b602`,
and input SHA-256
`e9d0ec2252201fdaa249b5e884c9290a128fb31c135afff6e08c566cb504c61b`.
The trace-format, diagnostic-patch, and geometry-audit pins are respectively
`4b99257628d3a27723a02be6b547dad64ac9bbfe957697d89f19d14e53321917`,
`8fb9e5a88a72109a095ccb1dab650860535102f7d806f0dd6d230c23127af7ff`, and
`aefe734244119578634f5617d9946688248ceb72effc958ebf1e5e3592ecb645`.
The pinned source archive SHA-256 is
`9c88385c10fb04f5dc6c4e98027a51bebdd8aee3920e05190d6c1dd08357d6e7`; the
generated 2.23 manual SHA-256 is
`a0bf3fc03f374912ff2bf28da3f7dfb6a61428dd7f41b281a2e7e1fdb318f330`.
Within that archive, `gencontelem_f2f.f` is pinned as
`853e2159f37666bc1430516bb4e5c65b6ba484ef1866454930e66cf317fb8afe` and
`springforc_f2f.f` as
`3be67688eb16a95739e09990c34ae0d2614acff216b254ea474bbf7c4d9e1ba4`.

The contract is internally consistent for this one implicit `*DYNAMIC,DIRECT`
coupon: `nmethod=4`, 50 fixed 0.1-second accepted increments, prescribed
separation/closure, one contact pair, and a disconnected free-DOF witness.
The verifier keeps generator `MAP` decisions distinct from corrected active
spring `TRIAL` rows. It checks CVG-to-TRIAL counts, including legitimate
zero-count CVG states with no TRIAL rows; binds trial relative time to STA and
FRD time; checks all 58 displacement records per accepted FRD state; and
checks the linear pressure and spring-energy laws both per point and in
aggregate. The native FRD `1PSTEP` parser handles the real leading whitespace
and field order, and the synthetic capture now exercises that layout.

The source interpretation also matches the emitted fields. In the pinned
2.23 `gencontelem_f2f.f`, the generator indexes contact points with the global
`igauss=indexf+m`; `springforc_f2f.f` implements the linear law as
`stiff(1)=-area*K*clear/kscale`, stores `cstr(4)=stiff(1)/area`, and computes
spring energy as `-stiff(1)*clear/2`. The output patch reports pressure,
area, master normal, corrected gap, and conditional spring energy. Its normal
resultant is derived as `pressure*area*master_normal`; the patch reports
neither `fnl` nor `CFN`. That derived vector is not an independently observed
reaction or contact-force vector. The verifier does not claim inertia balance,
external work, equilibrium, a physical transient, or joint acceptance.

The native-free self-test passed on the reviewed verifier bytes. It retained
50 synthetic states, 172 synthetic TRIAL rows, and 57 zero-count CVG states
without TRIAL rows; all nine listed negative controls rejected. This confirms
the auditor paths, not solver behavior.

The runner validates the auditor's prepared source/input contract before
freeze and run, binds the matched static-regression packet's pass, freeze, and
execution hashes, and freezes the dynamic input, build, auditor, expected
contract, patch, and supporting audits. Its run limits are one CPU, 1 GiB
memory with equal swap cap, 60 seconds, 16 MiB aggregate native output, and
Docker network disabled. The auditor's `native_run` result field alone does
not authenticate execution; parent interpretation must remain bound to the
runner's frozen execution record and captured output hashes.

This review supports use as a bounded output-format and law known-answer
coupon only. It does not qualify the diagnostic for the wood-joint model or
accept any joint mechanics.
