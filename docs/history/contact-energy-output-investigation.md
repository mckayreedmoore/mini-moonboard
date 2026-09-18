# Contact-energy output indexing investigation

**Source-level finding with a native reader reproduction, not a corrected
solver or a structural result.** The
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
No original source was patched. The initial source inspection was followed by
the separately bounded native printer probe below.

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

## Executed native reader probe

The [retained probe](../fea/results/contact_energy_output_probe/native-reader.tar.gz)
compiles and calls the **unmodified `printoutelem.f`** with its original
`gauss.f` include. Named fail-fast stubs satisfy only unused link dependencies;
calling any stub would fail the run. The driver supplies controlled energy-array
values and the ordinary `ESPRNGC6`, `mortar=1`, `CELS` path. It does **not** execute
contact generation or the energy writer.

With N=1 and compact element index 2, the actual native observations were:

| Controlled case | `igauss` | Value at N+`igauss` | Value at compact slot | Printed CELS and accumulated total |
| --- | --- | --- | --- | --- |
| Dense | 1 | 7.5 | 7.5 | 7.5 |
| Sparse, compact slot empty | 7 | 7.5 | 0 | 0 |
| Sparse, different compact-slot value | 7 | 7.5 | 2.25 | 2.25 |

This confirms the original native reader selects the compact slot. It does not
map either flagged moving-run row to its hidden `igauss`, calculate that row's
true spring energy, or validate a corrected solver.

The single run used the already pinned native-build Docker image, 2 GiB memory
and swap limit, one CPU, no network, a read-only input mount, 30-second compiler
and 5-second driver limits, and 45/65-second inner/outer bounds. Compilation,
driver execution and captured-container cleanup completed successfully; the
owned container was subsequently confirmed absent. The archive retains sources,
license, driver/stubs, compiler identity, executable, logs and hash inventories.

Preparation is reproducible from the pinned **checked-in** upstream archive:

```sh
uv run python -m fea.contact_energy_output_probe
uv run python -m fea.contact_energy_output_probe --launch PATH_PRINTED_ABOVE
```

Each prepared directory is single-use. A failure is retained, not retried
automatically. Portable tests replay the archived observations without compiling
or executing native code.

## Consequence and next checks

Do not use these printed CELS values to qualify total contact energy. Preserve
the original failed audit and all raw output; do not silently replace energy
values or relax its gates.

1. A separately labeled, fail-only replay can still investigate momentum,
   angular momentum and native kinetic energy. Any energy sum using printed
   CELS must remain explicitly unqualified.
2. The tiny reader check above is complete. A writer-to-printer integration
   check is still needed before choosing a correction or different native build;
   the reader-only result must not be represented as that integration test.
3. Only after output extraction and unilateral-contact behavior are addressed
   should a new qualified comparison be selected. No automatic refinement or
   frame alteration is justified by the present result.
