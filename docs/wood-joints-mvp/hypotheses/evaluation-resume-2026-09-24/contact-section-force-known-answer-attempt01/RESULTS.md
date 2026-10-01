# Section-force fixture: failed output coverage

Both small CalculiX 2.23 cases completed, but this packet fails its frozen
output-coverage gate. The penalty result file contains empty opening and
reopening nodal datasets and incomplete compression nodal coverage. The
original `verifier.json` failure is preserved. No joint method is accepted.

On resumption, the parent independently reran the existing audit in memory and
recorded its detailed result in [resume-diagnostic.json](resume-diagnostic.json).
All frozen input and native output hashes match. MORTAR passes the inherited
fixture checks; penalty fails with `Empty/untimed FRD block`. The separate
section audits pass for both cases: the six section reports per case satisfy
the original force, moment, area, centroid and normal checks. Both compression
section-force magnitudes are 399.5159 N against the frozen 400 N reference.
Nodal DAT results and accepted/convergence row tokens exactly match the
preceding full-step fixture. These partial checks do not override the failed
combined output contract.

## Source diagnosis and next decision

In the pinned official 2.23 source archive, `resultsprint.f` extrapolates
stresses for `SOF` at lines 129–145 and sets `iextrapolate=1`. Later,
face-to-face penalty contact output calls `extrapolatecontact` at lines
246–255, replacing the node-activity array `inum`. The fallback `createinum`
call at lines 408–420 requires `iextrapolate=0`; it therefore does not repair
that array in this combination. `frd.c` filters nodes through `inum`. The
source comment at lines 242–244 explicitly requires a subsequent extrapolation
to correct this array. The observed empty and partial fields agree with this
source path; the mechanical response has not been shown to change.

The result-blocking decision is whether documented additional stress output
restores the complete nodal output contract without changing the accepted
solution. A separate output-only packet may request `*EL FILE` stress `S`,
whose extrapolation follows contact output at lines 261–278. Before execution,
freeze a verifier that retains all mechanical, section and nodal-coverage
gates, explicitly validates the additional stress field, and requires the
original DAT and convergence parity. Parent review and serialized execution
remain required. Do not modify this failed packet or relax its nodal gate.

The source archive is the preserved
`ordinary-external-force-transient-attempt04-diagnostic/build-attempt02/source.tar.bz2`,
SHA-256 `9c88385c10fb04f5dc6c4e98027a51bebdd8aee3920e05190d6c1dd08357d6e7`.
The [official 2.23 manual](https://www.dhondt.de/ccx_2.23.pdf) remains locally
pinned in `fea/generated/ccx_2.23.pdf`.

## Evidence identities

| Record | SHA-256 |
| --- | --- |
| Frozen input | `eeced8a094e46672831a4d2236cb984f6217f47af8cf331bb106df03a5c063ec` |
| Execution | `1dcf538de97cbd720e952facda23ad63e8989458411b2d3b7d1b3a9a86093703` |
| Resumed detailed audit | `06926f9be46a722ad7a67c91c188eb46bfef5446df71b69bc5f61e42c35ca36f` |

Section resultants here are bulk-stress integration proxies. This small
fixture does not qualify pair-local contact-force recovery at shared joint
boundaries. Reviewed geometry and all structural and release gates remain
unchanged.
