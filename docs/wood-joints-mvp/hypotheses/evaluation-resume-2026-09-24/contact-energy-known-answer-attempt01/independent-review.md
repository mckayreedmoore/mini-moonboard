# Independent energy-output review, September 27

The independent read-only reviewer `section_output_review` supports
`PASS_MECHANICAL_FIXTURE_ONLY` and the separate energy dispositions in
[RESULTS.md](RESULTS.md). No correction to the result claims was identified.
This note records the review report; it does not change the frozen packet.

The reviewer verified all nine frozen input hashes and 22 native output hashes,
the root and per-case execution records, normal exit with no OOM, and serial
case execution. Nodal DAT U/RF and STA/CVG parity with the section-force fixture,
and the inherited mechanical gates, remain supported.

Raw compression energies independently agree with the verifier: both body
ELSE sums are 0.7996796 N·mm against 0.8. Penalty CELS is 0.1995202 against
0.2, and its combined total is 0.9991998 against 1.0. All pass their fixed
component and total tolerances. MORTAR actually prints 0.0 CELS at all three
states. Its compression contact error is 0.2 N·mm against a 0.002001 tolerance;
its combined error is 0.2003204 against 0.010001. This is an observed mismatch
in a source-unvalidated channel, not proof of zero physical contact energy.

The exact pinned source-interpretation check correctly denies mode-2 CELS
support. A printed CELS header does not establish source support. The pre-run
README is preserved as part of the freeze; the post-run results note supplies
the completed-run status. Aggregate energy, joint and release acceptance remain
false. This review does not validate work quadrature or current-joint behavior.

Reviewed freeze: `7ca80c4cdfe92b1f8dfcb0d71c9a97884dd7b6bdabb540b50902cf21c16396a0`.
Reviewed execution: `624c6b2fb3b4a72dff8fab08c4c724444bc46ecb4ad3fccea8af722e224656e1`.
Reviewed audit: `15ff0827a312df7b5c4e10860ed57f852532b1f5dc718da1a7ec94f260470951`.
