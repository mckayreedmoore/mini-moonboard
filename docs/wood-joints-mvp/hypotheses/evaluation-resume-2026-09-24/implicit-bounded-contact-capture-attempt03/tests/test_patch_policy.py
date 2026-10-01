from __future__ import annotations

import difflib
import importlib.util
import json
from pathlib import Path
import re
import sys
import unittest

HERE = Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True
spec = importlib.util.spec_from_file_location("prepare_capture", HERE / "prepare_capture.py")
prepare = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = prepare
assert spec.loader is not None
spec.loader.exec_module(prepare)

NATIVE_ARRAY_WRITE = re.compile(
    r"\b(?:vold|v|b|stx|springarea|pmastsurf|ener|xstate|xstateini|"
    r"islavsurf|ipkon|kon|nactdof|f|co)\s*(?:\[[^\]]+\]|\([^)]*\))\s*=(?!=)"
)


class AdditionsOnlyPolicyTests(unittest.TestCase):
    def test_checked_in_build_patch_reproduces_from_pinned_archive_and_sink(self):
        original, patched = prepare.build_delta()
        rendered = prepare.render_patch(original, patched)
        self.assertEqual(rendered, prepare.PATCH.read_bytes())
        metadata = json.loads(prepare.META.read_text())
        self.assertEqual(metadata["patch_sha256"], prepare.sha(rendered))
        self.assertEqual(metadata["source_archive_sha256"], prepare.sha(prepare.ARCHIVE.read_bytes()))
        self.assertEqual(metadata["sink_source_sha256"], prepare.sha(prepare.SINK.read_bytes()))

    def test_source_delta_is_additions_only_and_preserves_runtime_law_arrays(self):
        original, patched = prepare.build_delta()
        for rel in prepare.TARGETS:
            before = original[rel].decode().splitlines(keepends=True)
            after = patched[rel].decode().splitlines(keepends=True)
            ops = difflib.SequenceMatcher(a=before, b=after, autojunk=False).get_opcodes()
            self.assertTrue(all(tag in {"equal", "insert"} for tag, *_ in ops), rel)
            inserted = [after[j] for tag, _, _, j, k in ops if tag == "insert" for j in range(j, k)]
            self.assertGreater(len(inserted), 0, rel)
            for line in inserted:
                self.assertIsNone(NATIVE_ARRAY_WRITE.search(line), (rel, line))

    def test_contact_hooks_and_unclassified_candidate_are_source_anchored(self):
        original, patched = prepare.build_delta()
        nonlingeo = patched["CalculiX/ccx_2.23/src/nonlingeo.c"].decode()
        main = patched["CalculiX/ccx_2.23/src/ccx_2.23.c"].decode()
        calls = list(re.finditer(r"\bcontact\(&ncont", nonlingeo))
        hooks = list(re.finditer(r"ccxcap_generation_begin_\(&istep", nonlingeo))
        self.assertEqual(len(calls), 2)
        self.assertEqual(len(hooks), 1)
        self.assertLess(calls[0].start(), calls[1].start())
        self.assertGreater(hooks[0].start(), calls[0].start())
        self.assertLess(hooks[0].start(), calls[1].start())
        self.assertEqual(nonlingeo.count("ccxcap_finish_();"), 0)
        self.assertEqual(main.count("ccxcap_finish_();"), 1)
        self.assertEqual(main.count("while(istat>=0){"), 1)
        self.assertLess(main.index("while(istat>=0){"), main.index("FORTRAN(closefile,());"))
        self.assertGreater(main.index("ccxcap_finish_();"), main.index("FORTRAN(closefile,());"))
        begin_call = next(line for line in nonlingeo.splitlines()
                          if "ccxcap_generation_begin_(&istep" in line)
        self.assertNotIn("&ntie", begin_call)
        self.assertIn("&kscale,nener,ntie,nintpoint);", nonlingeo)
        before = original["CalculiX/ccx_2.23/src/gencontelem_f2f.f"].decode()
        after = patched["CalculiX/ccx_2.23/src/gencontelem_f2f.f"].decode()
        self.assertEqual(after.count("call ccxcap_generation_end()"), 1)
        self.assertIn("mint2d=islavsurf(2,jj+1)-islavsurf(2,jj)", before)
        self.assertIn("igauss=indexf+m", before)
        self.assertIn("wjcap_reason=99", after)
        self.assertIn("call ccxcap_point", after)
        self.assertIn("wjcap_reason=99\n                  wjcap_law", after)

    def test_job_footer_source_is_after_all_steps_and_sink_sizes_match_ownership(self):
        original, patched = prepare.build_delta()
        main_before = original["CalculiX/ccx_2.23/src/ccx_2.23.c"].decode()
        main_after = patched["CalculiX/ccx_2.23/src/ccx_2.23.c"].decode()
        self.assertEqual(main_after.count("ccxcap_finish_();"), 1)
        self.assertEqual(main_before.count("FORTRAN(closefile,());"), 1)
        self.assertLess(main_after.index("FORTRAN(closefile,());"),
                        main_after.index("ccxcap_finish_();"))
        self.assertIn("ccxcap_finish_();\n\n  strcpy2(fneig,jobnamec,132);", main_after)
        sink = (HERE / "capture-sink.inc").read_text()
        finish = sink.split("void ccxcap_finish_(void){", 1)[1]
        self.assertIn("free(wjcc_corrected);", finish)
        self.assertIn("wjcc_corrected=NULL;", finish)
        self.assertIn("wjcc_corrected_n=0;", finish)

    def test_instrumentation_has_no_solver_array_write_expression(self):
        sink = (HERE / "capture-sink.inc").read_text()
        self.assertIsNone(NATIVE_ARRAY_WRITE.search(sink))
        self.assertIn('fopen(path,"wbx")', sink)
        self.assertIn("WJCC_MAX_POINTS 250000", sink)
        self.assertIn("WJCC_MAX_SWEEPS 64", sink)
        self.assertIn("wjcc_bytes+(uint64_t)n>limit", sink)
        self.assertIn("memcmp(wjcc_state,wjcc_corrected,n*sizeof(double))==0", sink)
        self.assertIn("if(wjcc_enabled!=1||!wjcc_pending)return;", sink)


if __name__ == "__main__":
    unittest.main(verbosity=2)
