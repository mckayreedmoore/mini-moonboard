# T06: AWC NDS-2024 References 39–41 access attempt01

**Reviewed 2026-09-28.** This append-only, source-only packet follows the
official AWC reader route identified in the prior T06 packets. It records
whether the actual ANSI/AWC NDS-2024 References 39–41 could be directly
authenticated, the exact access routes tried, and the edition identity that
AWC itself exposes. It does not change any predecessor, queue, artifact
manifest, criteria, method map, candidate, geometry, or hardware.

## Result

AWC's 2024 NDS landing page was directly readable and identifies the
ANSI/AWC NDS-2024 edition, ANSI approval date October 16, 2023, and a free
view-only option. The page extraction exposes the viewer button but not its
destination. AWC's official LinkedIn announcement supplies the short viewer
URL `https://bit.ly/48dnXdB`; the web access tool could not resolve that URL,
and following it from the announcement returned a cache miss. AWC-domain
searches did not locate a 2024 References PDF or expose entries 39–41.

Therefore, this attempt **does not directly authenticate** the 2024 reference
list. The mapping remains only a transcription previously observed in the
non-AWC Studylib mirror: 39 = RCSC 2009, 40 = ANSI/AISC 360-22, and 41 = AISI
S240-20. Do not cite that mapping as AWC-confirmed. The AWC page authenticates
the edition designation and approval date, but not the edition/printing of an
unseen References page.

If the mirror mapping is accurate, those steel standards are candidate metal
design references. This packet does not establish that they provide an
applicable combined axial tension + shear + bolt bending method for a
through-bolt in a timber grip. The prior attempt03 source screen records the
scope boundaries found in the issuing-body texts, including the RCSC non-steel
grip exclusion and the absence of a demonstrated timber-grip N+V+M transfer
rule. This source-access attempt produces no new mechanics finding.

## Source record

[`source-observations.json`](source-observations.json) records the URLs,
search queries, access paths, observed page text, retrieval results, prior
packet hashes, edition boundary, provisional mirror mapping, and the method
applicability limit. The official AWC landing-page HTML was retrieved, but no
NDS References-page bytes or text were obtained. The linked viewer route was
identified from AWC's own announcement but remained inaccessible through the
available web tool. No external PDF-byte checksum is asserted.

## Preservation and scope

Only files inside this new attempt01 directory were created. The prior T06
attempt03, attempt05, attempt06, and attempt07 packets were read and their
relevant source-record files were SHA-256 checked before this packet was
written. No capacity, criterion result, method adoption, or candidate
disposition is emitted. No native solve, solver work, or physical work was
performed.

Run `python3 verify_source_packet.py` from this directory to verify the
packet-file checksums in [`SHA256SUMS`](SHA256SUMS).
