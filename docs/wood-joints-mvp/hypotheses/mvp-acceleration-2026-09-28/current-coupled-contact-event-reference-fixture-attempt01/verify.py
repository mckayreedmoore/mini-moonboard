"""Exact synthetic loading-history oracle; no native or frame calculation."""
import argparse
from fractions import Fraction as Q
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
OWNER = HERE.parent.parent / 'support-corner-review-2026-09-30/diagnostics.json'
OWNER_SHA = '174f8f945e41a273318a41fc401f1ef484160b500d624d80f57cd3480a343c98'


def free(ft, fq):
    return (2*ft-fq)/3, (2*fq-ft)/3


def held(ft, fq, reference):
    t = reference
    q = (fq-t)/4
    return t, q, ft-2*t-q


def state(ft, fq, reference=None, event=False):
    if reference is None:
        t, q = free(ft, fq)
        tangent = normal = Q(0)
        assert q <= 0 if event else q < 0
    else:
        t, q, tangent = held(ft, fq, reference)
        normal = 2*q
        assert q >= 0 if event else q > 0
    assert 2*t+q+tangent == ft
    assert t+2*q+normal == fq
    return {'external_Ft_Fq_N': [str(ft), str(fq)],
            't_mm': str(t), 'q_mm': str(q),
            'T_N': str(tangent), 'N_N': str(normal),
            'episode_reference_mm': None if reference is None else str(reference),
            'event_zero_normal_limit': event}


def refine_event(ft, start_fq, change_fq, expected_reference):
    rows = []
    for count in [3, 7, 15, 31, 63]:
        a, b = Q(count//2, count), Q(count//2+1, count)
        ta, qa = free(ft, start_fq+change_fq*a)
        tb, qb = free(ft, start_fq+change_fq*b)
        assert qa < 0 < qb
        event = a-qa*(b-a)/(qb-qa)
        tref, qevent = free(ft, start_fq+change_fq*event)
        assert event == Q(1,2) and qevent == 0 and tref == expected_reference
        rows.append({'odd_step_count': count, 'bracket_parameter': [str(a), str(b)],
                     'bracket_open_extension_q_mm': [str(qa), str(qb)],
                     'last_open_t_mm': str(ta),
                     'last_open_reference_error_mm': str(ta-tref),
                     'localized_event_parameter': str(event),
                     'captured_event_reference_mm': str(tref)})
    return rows


def produce():
    assert hashlib.sha256(OWNER.read_bytes()).hexdigest() == OWNER_SHA
    owner = json.loads(OWNER.read_text())
    assert owner['floor']['fixed_zero_reference_has_no_admissible_branch']
    samples = []
    # Synthetic settling force, not actual gravity from the frame source.
    for beta in [Q(1,4), Q(1,2), Q(3,4), Q(1)]:
        samples.append({'stage': 'synthetic_settle', 'parameter': str(beta),
                        **state(-4*beta, -3*beta)})
    for alpha in [Q(0), Q(1,4)]:
        samples.append({'stage': 'first_ramp_open', 'parameter': str(alpha),
                        **state(Q(-4), -3+2*alpha)})
    # Contact event has no normal or tangent reaction. Its captured reference
    # comes from the open branch's exact event, never from the final solution.
    event_open = state(Q(-4), Q(-2), event=True)
    event_closed = state(Q(-4), Q(-2), Q(-2), event=True)
    assert all(event_open[k] == event_closed[k] for k in ['t_mm','q_mm','T_N','N_N'])
    for alpha in [Q(3,4), Q(1)]:
        samples.append({'stage': 'first_ramp_bearing', 'parameter': str(alpha),
                        **state(Q(-4), -3+2*alpha, Q(-2))})
    assert samples[-1]['q_mm'] == '1/4' and samples[-1]['T_N'] == '-1/4'
    # Reverse the ramp: opening occurs at the same exact zero-reaction event.
    samples.append({'stage':'unload_before_opening', 'parameter':'3/4',
                    **state(Q(-4), Q(-3,2), Q(-2))})
    samples.append({'stage':'unload_after_opening', 'parameter':'1/4',
                    **state(Q(-4), Q(-5,2))})
    samples.append({'stage':'unload_open_end', 'parameter':'0',
                    **state(Q(-4), Q(-3))})
    # Change lateral loading while open, then re-engage at a different tangent
    # position. The previous -2 reference is discarded on opening.
    for lam in [Q(1,2), Q(1)]:
        samples.append({'stage':'open_lateral_change', 'parameter':str(lam),
                        **state(-4+2*lam, Q(-3))})
    new_event = state(Q(-2), Q(-1), event=True)
    new_held = state(Q(-2), Q(-1), Q(-1), event=True)
    assert all(new_event[k] == new_held[k] for k in ['t_mm','q_mm','T_N','N_N'])
    for lam in [Q(3,4), Q(1)]:
        samples.append({'stage':'reengaged_new_reference', 'parameter':str(lam),
                        **state(Q(-2), -3+4*lam, Q(-1))})
    assert samples[-1]['q_mm'] == '1/2' and samples[-1]['T_N'] == '-1/2'
    wrong_t, wrong_q, wrong_T = held(Q(-2), Q(1), Q(-2))
    assert wrong_t != Q(samples[-1]['t_mm'])
    return {
        'schema':'coupled_contact_event_reference_fixture/v1',
        'status':'PASS_EXACT_SYNTHETIC_EVENT_CAPTURE_RELEASE_RESET_AND_REFINEMENT',
        'structural_K_N_per_mm': [[2,1],[1,2]],
        'normal_law':'N=2 max(q,0); q>0 compression; open T=N=0',
        'synthetic_settle_force_N':[-4,-3], 'first_ramp_increment_N':[0,2],
        'first_contact_event':event_open, 'first_held_event_limit':event_closed,
        'second_contact_event':new_event, 'second_held_event_limit':new_held,
        'first_event_refinement':refine_event(Q(-4),Q(-3),Q(2),Q(-2)),
        'second_event_refinement':refine_event(Q(-2),Q(-3),Q(4),Q(-1)),
        'stage_samples':samples,
        'retaining_old_reference_would_give_final_t_q_T':list(map(str,[wrong_t,wrong_q,wrong_T])),
        'zero_load_limit':'t=q=T=N=0; SPD synthetic structural operator needs no gauge. This does not validate a frame gauge or its internal rank.',
        'limits':'Exact one-cell coupled analytical path and linear event interpolation only. Synthetic settling direction is not actual gravity. No 100-cell state selector, frame path existence/uniqueness, native constraint updates, nonlinear event locator, capacity or acceptance.',
        'source_sha256':{str(OWNER.relative_to(ROOT)):OWNER_SHA,
                         str(Path(__file__).relative_to(ROOT)):hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},
        'native_solver_run':False, 'frame_response_established':False,
        'joint_accepted':False,
    }


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--verify', action='store_true')
    args=parser.parse_args()
    data=json.dumps(produce(), indent=2, sort_keys=True, allow_nan=False)+'\n'
    target=HERE/'fixture.json'
    if args.verify:
        assert target.read_text()==data
        print('PASS_EXACT_SYNTHETIC_EVENT_CAPTURE_RELEASE_RESET_AND_REFINEMENT')
    else:
        target.write_text(data)
        print('Wrote exact event-reference fixture')
