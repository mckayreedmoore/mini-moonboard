# Independent review: current-CAD taper geometry preflight attempt01

Review date: 2026-09-28  
Verdict: PASS, bounded to current CAD input geometry preflight. No actionable implementation findings. Both full taper criteria remain pending.

## Scope boundary

This review covered the producer, focused tests, and packet named below. The result supports the measured current STEP input dimensions and their comparison with the two geometry expressions. It does not dispose either full criterion.

The criteria ledger says its rules govern six fresh compact-floor-flush-development cases. It assigns both taper rows to FR-3 and a fresh case. The floor_taper_checks helper’s candidate guard does not include compact-floor-flush-wood-joints-development. The preflight checks the exact two formula expressions at source lines 116–118 and explicitly leaves both dispositions pending; its remaining-requirements list calls for a per-scope criterion contract and fresh cases. This is the right boundary for this artifact. Do not surface its CAD booleans as full wood-joints criterion acceptance before that contract and case evidence exist.

No solver was run. No producer, test, STEP, candidate, criterion, queue, ledger, or status artifact was changed.

## Independent STEP geometry

I read each exact STEP BRep directly with CadQuery, checked its SHA-256 against the member bundle, confirmed one valid solid, projected BRep vertices onto global X and the frame-map cross-grain axis, and measured the unique oblique planar face independently of the producer report.

| Member | STEP SHA-256 | Stock X width | Stock cross-grain depth | Recess run | Recess depth | Run / depth |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| lumber_leg_left | 1416e3aec21eea2993542f8266649ebe0aec50b3ec6444f445f18f88cbffa065 | 88.89999999999986 mm | 139.70000000044342 mm | 457.20000000009406 mm | 38.09999999999991 mm | 12.000000000002498 |
| lumber_leg_right | e346646efb8bdf9c03d45dfa024900622abcd65fe0d58bf11c6dcd3735bedff4 | 88.89999999999986 mm | 139.70000000044342 mm | 457.20000000009406 mm | 38.09999999999991 mm | 12.000000000002498 |

Each selected face independently had four corners, one wire, four straight edges, and 139.70000000029495 mm cross-grain extent. The measured values agree with the packet within its stated 1e-5 mm geometry tolerance and with the 88.9 × 139.7 × 457.2 × 38.1 mm design dimensions.

The read-only extraction command was:

~~~sh
.venv/bin/python -B - <<'PY'
import cadquery as cq, hashlib, json
from pathlib import Path
root=Path('.').resolve()
bundle_dir=root/'docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-full-frame-member-solids-attempt01/bundle'
bundle=json.loads((bundle_dir/'current-full-frame-member-solids.json').read_text())
frame_doc=json.loads((root/'docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-frame-timber-material-frame-map-attempt01/current-frame-timber-material-frame-map.json').read_text())
rows={row['member_id']:row for row in bundle['members']}
frames={row['member_id']:row for row in frame_doc['members']}
dot=lambda a,b:sum(x*y for x,y in zip(a,b))
for name in ('lumber_leg_left','lumber_leg_right'):
    row=rows[name]
    step=(bundle_dir.parent/row['step_file']).resolve()
    digest=hashlib.sha256(step.read_bytes()).hexdigest()
    assert digest==row['step_sha256']
    grain=tuple(frames[name]['conditional_grain_assignment']['proposed_global_xyz'])
    cross=(0.0,grain[2],-grain[1])
    shape=cq.importers.importStep(str(step)).val()
    assert shape.isValid() and len(shape.Solids())==1
    vertices=[tuple(v.Center().toTuple()) for v in shape.Vertices()]
    candidates=[]
    for face in shape.Faces():
        if face.geomType()!='PLANE':
            continue
        normal=tuple(face.normalAt().toTuple())
        if 1e-8 < abs(normal[0]) < 1-1e-8 and abs(dot(normal,grain))>1e-8:
            points=[tuple(v.Center().toTuple()) for v in face.Vertices()]
            stations=[dot(p,grain) for p in points]
            xs=[p[0] for p in points]
            qs=[dot(p,cross) for p in points]
            candidates.append((max(stations)-min(stations),
                max(xs)-min(xs),max(qs)-min(qs),face))
    assert len(candidates)==1
    run,removed,face_width,face=candidates[0]
    stock_width=max(p[0] for p in vertices)-min(p[0] for p in vertices)
    stock_depth=max(dot(p,cross) for p in vertices)-min(dot(p,cross) for p in vertices)
    assert all(abs(a-b)<1e-8 for a,b in (
        (run,457.2),(removed,38.1),(face_width,139.7),
        (stock_width,88.9),(stock_depth,139.7)))
    print(json.dumps({'member':name,'step_sha256':digest,'run_mm':run,
        'recess_mm':removed,'stock_width_mm':stock_width,
        'stock_depth_mm':stock_depth,'run_over_recess':run/removed,
        'corners':len(face.Vertices()),'wires':len(face.Wires()),
        'edge_types':[edge.geomType() for edge in face.Edges()]}))
PY
~~~

## Source, predicate, test, and packet checks

The source-pins file names 216 inputs. An independent read-only pass confirmed that all 216 paths exist as regular, non-symlink files and each SHA-256 matches the recorded value. The pinned sources include the wood-joints candidate/revision, current-frame map, 50-member bundle and its STEP files, stock record, criteria, predicate source, producer, and focused tests.

The measured taper predicates match the source expressions in scripts/floor_taper_checks.py:116–118:

- run ≥ 10 × recess depth − 1e-6 mm;
- section width 88.9 mm, depth 139.7 mm, recess 38.1 mm within math.isclose tolerances, and run ≥ 457.2 − 1e-5 mm.

The producer preserves math.isclose’s 1e-9 default relative tolerance and the listed absolute tolerances. The focused boundary tests exercise nextafter values immediately below and above both run thresholds, and reject a wrong stock width. Positive finite-number and malformed-face tests also pass.

The packet report and verification JSON mark CAD preflight supported while retaining both full-criterion dispositions as pending. Fresh-case prerequisites, engineering completion, release, native run, and delivered-stock observation all remain false. The README and report limit claims to current STEP input geometry and exclude native/CAD equivalence, mesh volume, section coverage, stock receipt, mechanics, resistance, and acceptance.

## Exact validation commands and results

From the repository root:

~~~sh
.venv/bin/python -B scripts/build_current_taper_geometry_preflight_attempt01.py --check
~~~

Exit 0. Packet replay matched every generated byte; verification reported 216 source pins, two members, both criteria pending, current-CAD-input-only scope, and release false. Report SHA-256: d1c0b701d1b8d2ec265b1ebe44399a3172002c8cd2afd2e5f7ec61bd2028a401.

~~~sh
.venv/bin/python -B -m pytest -q -p no:cacheprovider tests/test_current_taper_geometry_preflight_attempt01.py
~~~

Exit 0: 33 passed in 1.50s.

~~~sh
.venv/bin/ruff check --no-cache scripts/build_current_taper_geometry_preflight_attempt01.py tests/test_current_taper_geometry_preflight_attempt01.py
~~~

Exit 0: All checks passed.

The standalone BRep extraction above exited 0 for both exact STEP hashes and asserted the independently measured dimensions.

From the preflight packet directory:

~~~sh
sha256sum -c SHA256SUMS
~~~

Exit 0: README.md, current-taper-geometry-preflight.json, source-pins.json, and verification.json all verified.

The independent source-pin pass exited 0: 216 checked, zero missing paths, symlinks, or hash mismatches.

## Reviewed artifact fingerprints

- Producer: 48c4ff48937750ca60bc89f84566122b8aaae1ee479c3b36dfc8fde8eb4adc8d
- Focused tests: 5ca4146bcf8bee37d5341ce45250fe4088b3d75bf13870af08d4a136ca86980a
- Criteria ledger: f6b5591bbbb2aaf87553095e04fbe5abd66d38a926a3efb66711420492f0f090
- Taper predicate source: bf15d8983b42d95dda0d0329bc2d8c2664f9c146813f21e1a0cc8f0f6a3bf1c3
- Preflight report: d1c0b701d1b8d2ec265b1ebe44399a3172002c8cd2afd2e5f7ec61bd2028a401

Actionable findings: none within the bounded CAD-input preflight scope.
