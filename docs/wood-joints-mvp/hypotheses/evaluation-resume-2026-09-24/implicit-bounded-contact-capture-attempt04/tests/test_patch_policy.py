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


class AdditionsOnlyPolicyTests(unittest.TestCase):
    def test_checked_in_build_patch_reproduces_from_pinned_archive_and_sink(self):
        original, patched = prepare.build_delta()
        rendered = prepare.render_patch(original, patched)
        self.assertEqual(rendered, prepare.PATCH.read_bytes())
        metadata = json.loads(prepare.META.read_text())
        self.assertEqual(metadata["patch_sha256"], prepare.sha(rendered))
        self.assertEqual(metadata["source_archive_sha256"], prepare.sha(prepare.ARCHIVE.read_bytes()))
        self.assertEqual(metadata["sink_source_sha256"], prepare.sha(prepare.SINK.read_bytes()))

    def test_three_upstream_targets_are_additions_only(self):
        original, patched = prepare.build_delta()
        for rel in prepare.TARGETS:
            before = original[rel].decode().splitlines(keepends=True)
            after = patched[rel].decode().splitlines(keepends=True)
            ops = difflib.SequenceMatcher(a=before, b=after, autojunk=False).get_opcodes()
            self.assertTrue(all(tag in {"equal", "insert"} for tag, *_ in ops), rel)
            self.assertGreater(sum(j2-j1 for tag, _, _, j1, j2 in ops if tag == "insert"), 0, rel)

    def test_fortran_allowlist_rejects_runtime_array_and_unknown_scalar_writes(self):
        original, patched = prepare.build_delta()
        rel = "CalculiX/ccx_2.23/src/gencontelem_f2f.f"
        before, after = original[rel].decode(), patched[rel].decode()
        self.assertTrue(after.startswith(before[:500]))
        for assignment in ("      isol=0\n", "      clear=0.d0\n", "      xstate(1,1,1)=0.d0\n"):
            with self.subTest(assignment=assignment.strip()):
                with self.assertRaises(RuntimeError):
                    prepare.validate_fortran_additions(before, after + assignment)

    def test_c_caller_allowlist_rejects_solver_array_write(self):
        original, patched = prepare.build_delta()
        rel = "CalculiX/ccx_2.23/src/nonlingeo.c"
        before = original[rel].decode()
        after = patched[rel].decode()
        bad = after.replace("ccxcap_iteration_link_(istep", "vold[0]=0.;\n\tccxcap_iteration_link_(istep", 1)
        self.assertNotEqual(bad, after)
        with self.assertRaises(RuntimeError):
            prepare.validate_c_capture_additions(before, bad, (HERE / "capture-sink.inc").read_text(), rel)
        bad_sink = (HERE / "capture-sink.inc").read_text() + "\nvoid injected(void){vold[0]=0.;}\n"
        with self.assertRaises(RuntimeError):
            prepare.validate_c_capture_additions(before, after, bad_sink, rel)

    def test_exact_production_hook_reachability_and_argument_types(self):
        original, patched = prepare.build_delta()
        nonlingeo = patched["CalculiX/ccx_2.23/src/nonlingeo.c"].decode()
        upstream_nonlingeo = original["CalculiX/ccx_2.23/src/nonlingeo.c"].decode()
        main_before = original["CalculiX/ccx_2.23/src/ccx_2.23.c"].decode()
        main = patched["CalculiX/ccx_2.23/src/ccx_2.23.c"].decode()
        contact = prepare.load_archive_member(prepare.SOURCE_READS[0]).decode()

        # contact() is the production route into the Fortran generator.
        self.assertEqual(contact.count("FORTRAN(gencontelem_f2f,(tieset,ntie,itietri,ne,ipkon,kon,"), 1)
        self.assertEqual(len(list(re.finditer(r"\bcontact\(&ncont", nonlingeo))), 2)
        hooks = list(re.finditer(r"ccxcap_generation_begin_\(istep,&iinc,&icutb,&iit,nk,&mt,vold,\s*&kscale,nener,ntie,nintpoint\);", nonlingeo))
        self.assertEqual(len(hooks), 1)
        calls = list(re.finditer(r"\bcontact\(&ncont", nonlingeo))
        self.assertLess(calls[0].start(), hooks[0].start())
        self.assertLess(hooks[0].start(), calls[1].start())
        kscale_pos = upstream_nonlingeo.index("kscale=1")
        declaration_pos = upstream_nonlingeo.rfind("ITG *inum=NULL", 0, kscale_pos)
        self.assertGreaterEqual(declaration_pos, 0)
        declaration = upstream_nonlingeo[declaration_pos:kscale_pos]
        self.assertLess(len(declaration), 1200)
        self.assertNotIn("double", declaration.lower())
        self.assertIn("ccxcap_generation_begin_(ITG*,ITG*,ITG*,ITG*,ITG*,ITG*,double*,ITG*,ITG*,ITG*,ITG*);", nonlingeo)
        self.assertRegex(upstream_nonlingeo, r"ITG\s*\*istep")
        self.assertIn("ccxcap_corrected_(istep,&iinc,&icutb,&iit,nk,&mt,vold);", nonlingeo)
        self.assertIn("ccxcap_iteration_link_(istep,&iinc,&icutb,&iit,&icntrl,ttime,&time);", nonlingeo)
        self.assertIn("ITG *kscale", (HERE / "capture-sink.inc").read_text())
        self.assertEqual(nonlingeo.count("ccxcap_trial_(&wje"), 1)
        self.assertIn("&pmastsurf[6*(wjg-1)+5],&kscale,&reltime);", nonlingeo)
        self.assertEqual(nonlingeo.count("ccxcap_generation_end_();"), 0)

        self.assertEqual(main_before.count("while(istat>=0){"), 1)
        self.assertEqual(main.count("ccxcap_finish_();"), 1)
        self.assertLess(main.index("while(istat>=0){"), main.index("FORTRAN(closefile,());"))
        self.assertLess(main.index("FORTRAN(closefile,());"), main.index("ccxcap_finish_();"))
        self.assertGreater(main.index("ccxcap_finish_();"), main.index("FORTRAN(closefile,());"))
        self.assertIn("ccxcap_finish_();\n\n  strcpy2(fneig,jobnamec,132);", main)

        gen_before = original["CalculiX/ccx_2.23/src/gencontelem_f2f.f"].decode()
        gen_after = patched["CalculiX/ccx_2.23/src/gencontelem_f2f.f"].decode()
        self.assertIn("do iloop=1,2", gen_before)
        self.assertIn("if((iact.ne.0).or.(iprev.eq.0).or.(nmethod.eq.4)) exit", gen_before)
        self.assertEqual(gen_after.count("call ccxcap_generation_end()"), 1)
        self.assertIn("call ccxcap_face(i,iloop,wjcap_faceord,ifaces,", gen_after)
        self.assertIn("call ccxcap_point(i,iloop,wjcap_faceord,ifaces,m,", gen_after)

    def test_job_footer_cleanup_pairs_and_capture_storage_policy(self):
        sink = (HERE / "capture-sink.inc").read_text()
        finish = sink.split("void ccxcap_finish_(void){", 1)[1]
        self.assertIn("free(wjcc_corrected);", finish)
        self.assertIn("wjcc_corrected=NULL;", finish)
        self.assertIn("wjcc_corrected_n=0;", finish)
        self.assertIn("if(wjcc_enabled!=1||!wjcc_pending)return;", sink)
        self.assertIn("ITG ccxcap_is_active_(void){return (wjcc_enabled==1&&wjcc_pending)?1:0;}", sink)
        self.assertIn("ccxcap_generation_end_", sink)
        self.assertIn('fopen(path,"wbx")', sink)
        self.assertIn("WJCC_MAX_POINTS 250000", sink)
        self.assertIn("WJCC_MAX_SWEEPS 64", sink)
        self.assertIn("wjcc_bytes+(uint64_t)n>limit", sink)
        self.assertIn("memcmp(wjcc_state,wjcc_corrected,n*sizeof(double))==0", sink)
        self.assertIn("-Werror=incompatible-pointer-types", (HERE / "build/context/Makefile.upstream").read_text())
        self.assertIn("if(*mortar==1&&ccxcap_is_active_())", prepare.patch_nonlingeo(
            prepare.load_archive_member("CalculiX/ccx_2.23/src/nonlingeo.c").decode()))


if __name__ == "__main__":
    unittest.main(verbosity=2)
