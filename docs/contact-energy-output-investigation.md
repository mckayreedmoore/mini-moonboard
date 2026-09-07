# Contact-energy output indexing investigation

**Source-level finding, not a corrected solver or a structural result.** The
[first coarse moving audit](../fea/results/coarse_moving_control/README.md)
stopped at two signed-pressure rows before evaluating full balance. Both rows
print CELS=0. Their individual energy mappings cannot be recovered from the DAT
alone, so neither harmless rounding nor correct per-point energy is established.

## Pinned source and differing indices

The eight reviewed source files match the per-file hashes in the selected
build manifest, retained as `solve/frozen/build_manifest.json` inside
[preparation.tar.gz](../fea/results/coarse_moving_control/preparation.tar.gz).
Its upstream 2.21 source-archive SHA256 is
`52a20ef7216c6e2de75eae460539915640e3140ec4a2f631a9301e01eda605ad`.
No source was patched and no diagnostic binary was run for this investigation.

Let N denote the original element-array extent (`*ne`), before generated
contact elements are appended—not necessarily the count of populated element
IDs. On the ordinary surface-to-surface contact path:

| Stage | Source | Index used |
| --- | --- | --- |
| Preserve original count; reset before generation | `nonlingeo.c:903,1743` | N |
| Allocate/zero contact energy slots | `nonlingeo.c:1786–1790` | N plus all potential integration slots |
| Identify potential contact point | `gencontelem_f2f.f:300` | `igauss = indexf + m` |
| Append only active contact elements | `gencontelem_f2f.f:670–675,713` | Compact element index; connectivity also stores `igauss` |
| Store spring energy | `resultsmech.f:424–443` | `ener(1,1,N + igauss)` |
| Print each contact's energy | `printout.f:463,482–495`; `printoutelem.f:302,527` | `ener(1,1,nelem)` using the compact element index |

`results.c:225,478–490,519` and `resultsprint.f:117–123` pass the energy array
through this chain without an intervening remapping. `printout`'s local `ne0`
means the first compact contact element, unlike the original-count variable
in `nonlingeo`.

For example, if the first active integration slot is 7, its compact contact
element is N+1: the writer stores at N+7 while the printer reads N+1. That slot
may be unused, or belong to another contact point. This demonstrates the
source-level mismatch for sparse activation; it does not identify the hidden
`igauss` of either particular DAT row.

The printed CELS total is not an independent check: `printoutelem.f:503` sums
the same selected values, and `printout.f:608–615` prints that sum. Agreement
between rows and their total therefore cannot validate contact-energy extraction.

## Consequence and next checks

Do not use these printed CELS values to qualify total contact energy. Preserve
the original failed audit and all raw output; do not silently replace energy
values or relax its gates.

1. A separately labeled, fail-only replay can still investigate momentum,
   angular momentum and native kinetic energy. Any energy sum using printed
   CELS must remain explicitly unqualified.
2. Prepare a tiny, separately selected sparse-contact output check that exposes
   compact element index, `igauss`, and both energy-array slots. Validate the
   original output path before choosing a correction or different native build.
3. Only after output extraction and unilateral-contact behavior are addressed
   should a new qualified comparison be selected. No automatic refinement or
   frame alteration is justified by the present result.
