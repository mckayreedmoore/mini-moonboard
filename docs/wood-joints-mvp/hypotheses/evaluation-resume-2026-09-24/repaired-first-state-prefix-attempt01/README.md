# Corrected first-state output from trajectory attempt03

The parent captured a fixed output prefix while the authenticated attempt03
container continued running. `capture.json` binds the live container identity,
mounts, executable, source index, eight unchanged inputs, and each captured
file's byte length and hash. These are prefix records, not a fabricated
terminal execution or a successful full-horizon run.

At accepted step 1, increment 1, time 0.0005 s (23 iterations), all 104,245
point-map rows join uniquely to their Fortran DAT identities. The writer
elastic-energy sum is `3.4786029442674645207833417000531865e-11 N mm`.
The corrected DAT CELS sum is `3.478602937091854873853287e-11 N mm`, and LOG
prints `3.478603e-11 N mm`. Both differences lie within the summed printed
token bounds. The largest pointwise writer/source-law difference is about
`6.31e-30 N mm`; C/Fortran clearance, pressure and area differences are zero
at their printed precision. Pointwise formula metrics are reported separately
from the bounded reader-equality checks.

The full acceleration stream contains a complete framed first state with
exactly ascending physical IDs 1–116,162 and finite acceleration components.
The native
runtime diagnostic reports `nk=120694`, `ne0=57643`, confirming the
source-derived generated-node count at this output call.

`capture_and_audit.py` uses the frozen `reader_helper.py` only for pure data
parsing and numerical comparisons. It does not call that helper's old-build
source validator or terminal-execution validator. Parent authentication is
performed explicitly against attempt03's live source and capture manifest.
The reused point-map parser's raw compact columns and FRD CELS are excluded
from the corrected-reader verdict. Raw CSV and DAT retain pointwise evidence;
the large joined row list is omitted from the summary JSON.

This result establishes the exercised first-state output boundary. It does
not establish angular equilibrium, physical thread engagement, time accuracy,
contact-transition behavior, complete-joint resistance, or any of the 47
formal criteria. The native run continues toward its separately recorded
contact-event observation goal. The [independent prefix review](independent-review.md)
reproduces these energy and acceleration results.

The original DAT capture ends at the final CFS master header, before its
numeric row. The separate `pilot.dat.angular-extension` preserves every byte
of that capture and appends 363 native output bytes through the final
pair-offset couple. `angular-extension.json` binds this extension to the same
running container and unchanged inputs. The reused angular parser verifies
all 315 expected records (35 pairs, three variables, three roles), with 1,575
finite numeric values at the first accepted time. This establishes angular
output coverage, not angular equilibrium. The original capture and its
independent review remain unchanged. The separate
[extension review](independent-angular-extension-review.md) confirms these
bindings and coverage. All 525 force-decomposition components, 315
action/reaction components and 315 pair-couple identities pass the existing
printer-bound checks; the parent replay reproduces the full result in
`angular-vector-identities.json`. These checks establish consistency of the
emitted contact records, not whole-joint force or moment balance.
