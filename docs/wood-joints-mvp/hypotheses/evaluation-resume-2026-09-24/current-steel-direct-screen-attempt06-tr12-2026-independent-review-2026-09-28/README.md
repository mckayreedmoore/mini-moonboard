# Independent review of AWC TR-12 attempt06

**Disposition:** Supported within its stated source boundary. Attempt06 accurately records an official AWC index-only screen and the direct-access failure for the 2026 PDF. It keeps lateral-yield `Fyb` separate from direct bolt axial tension, leaves direct tension and simultaneous N+V+M unresolved, and adopts no method, capacity, or criterion result.

The review is bound to attempt06 README SHA-256 `4269b76a9e20c6ab30f14ae97ce17009d4b104cc1d28a9cb50cb88550bd6680f`, source-observations SHA-256 `5e89f63b580e104a29ad638409a87fe3745fa23f2bb6bf8baa6bff86fc054825`, and terminal manifest SHA-256 `d8650f3414989f38e1a903fcfaa9eb71750d876ccdfac57cbbc10e65bd1de5aa`. The terminal manifest’s README and source-observations hashes both reproduce. All 13 read-only context pins also match; see [`verification.json`](verification.json) and [`input-sha256.json`](input-sha256.json). Review artifacts are bound by [`SHA256SUMS`](SHA256SUMS).

## Source boundary and access

Every saved indexed query is scoped to the exact official AWC 2026 PDF URL, and every observation points to that URL. The packet records no retrieved 2026 PDF bytes and no PDF digest. I re-opened the official AWC report collection and direct PDF during review; both returned HTTP 403 Forbidden, matching the packet’s dated access record. Official AWC search-index results for the same PDF expose portions of Table 1-1, Appendix A Table A2, and notation. These are partial indexed excerpts, not a complete report review. The search recheck and access outcomes are documented in [`source-access-check.md`](source-access-check.md).

## Technical boundary

The indexed text supports a lateral connection-yield route: `P` is a reference 5%-offset lateral yield value, `Z` is a reference lateral design value, and the solid-member Table 1-1 shows lateral single-/double-shear modes with member bearing and dowel-bending terms. Appendix A Table A2 identifies `Fyb` as dowel bending yield strength; its visible bolt/lag-screw reference is 45 ksi for the listed diameter category `D ≥ 3/8 in`. `Fyb` is therefore an input to the lateral-yield method. It is not direct axial bolt-tension resistance. The appearance of fastener bending moments in lateral yield equations does not establish an interaction for direct axial tension, shear, and external bolt bending.

The indexed §1.2 mention of tension among broader NDS design considerations does not itself state a bolt-tension equation. Exact-URL searches for axial or combined-tension terms returned no resolving excerpt; those no-hits do not prove that the complete PDF lacks such a method. Direct bolt tension and simultaneous N+V+M remain unknown. Table 1-2’s hollow-side-member topology is correctly treated only as a boundary observation for the solid/solid target.

The attempt does not transfer the 2015 TR-12 or prior NDS text into the 2026 report. It changes no method map, criterion disposition, hardware, geometry, solver state, or release state. This matches the pinned context: the `steel_direct` row remains pending, NDS `Fyb` and direct steel strength remain separate, and the method-map N+V+M check is still open. The packet records zero capacity calculations and zero criterion dispositions changed.

No reviewer finding changes attempt06’s disposition. It is a bounded source observation only. The complete 2026 PDF remains the needed primary source for resolving the gap; this review stops at the requested handoff and does not pursue that source further.
