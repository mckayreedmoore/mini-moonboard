"""Prepare one parent-scoped native straight-line SPRINGA fixture, never a frame run."""
import hashlib,json
from pathlib import Path
from fea.horizontal_panel_frame import Structure
from fea.wood_joint_reduced_native import freeze
HERE=Path(__file__).resolve().parent
model=Structure()
for i in range(1,6):model.node([100. if i in (2,4) else 0.,0.,0.])
model.element('SPRINGA',[2,3],'POSITIVE');model.element('SPRINGA',[4,5],'NEGATIVE')
model.fixed.update([3,5])
model.equations=[[(2,1,1.),(1,1,-1.)],[(4,1,1.),(1,1,-1.)]]
model.loads={1:[10.,0.,0.]}
metadata={'candidate':'compact-floor-flush-wood-joints-development',
 'geometry_revision_id':'led-clearance-2x6-runner-seated-blocks-v1',
 'scope':'One disconnected five-node straight-line nonlinear SPRINGA/MPC known-answer fixture; 3 load steps; no frame or joint',
 'parent_run_budget':{'max_launches':1,'timeout_seconds':60,'run_id':'reduced-nonlinear-springa-known-answer-attempt01'},
 'manual':{'url':'https://www.dhondt.de/ccx_2.23.pdf','sections':['6.2.42 SPRINGA (p129)','7.122 SPRING (pp598-599)'],
  'interpretation':'Scalar component force-displacement table, decimal real fields, ascending elongation; constant extrapolation outside table range'},
 'known_answer':{'steps':[{'time':1.,'external_force_N':10.,'u_mm':.1,'positive_internal_force_N':10.,'negative_internal_force_N':0.},
  {'time':2.,'external_force_N':-20.,'u_mm':-.1,'positive_internal_force_N':0.,'negative_internal_force_N':-20.},
  {'time':3.,'external_force_N':10.,'u_mm':.1,'positive_internal_force_N':10.,'negative_internal_force_N':0.}]},
 'tolerances':{'u_abs_mm':2e-6,'force_abs_N':.002},
 'limits':['No bearing-conditional floor tangent rule','No actual member/bolt/screw stiffness or capacity',
           'Opposing laws keep the single physical coordinate supported; an isolated open carrier can leave a mechanism',
           'Native output force meaning must be checked before reuse; old linear K*deltaU audit is not applicable',
           'Auxiliary initial span 100mm is numerical only, not physical timber/bolt length; all Y/Z motion fixed',
           'Signed elongation equals scalar auxiliary displacement only while 100+delta remains positive'],
 'native_solve_executed':False,'qualified_for_design':False}
metadata['native_nonlinear_spring_laws'] = [
 {'element':1,'nodes':[2,3],'initial_span_mm':100.,'force_vs_elongation_N_mm':[[0.,-10.],[0.,0.],[1000.,10.]]},
 {'element':2,'nodes':[4,5],'initial_span_mm':100.,'force_vs_elongation_N_mm':[[-2000.,-10.],[0.,0.],[0.,10.]]}]
metadata['source_diagnosis'] = {'previous_fixture':'nonlinear-spring2-known-answer-attempt01',
 'scope':'Built-in SPRINGA workaround candidate for unassigned val in inspected SPRING2 nonlinear tangent branch; no patched runtime'}
lines=['*HEADING','Nonlinear straight-line SPRINGA known answer; not a frame or joint','*NODE,NSET=N',
       *[f'{i},{100. if i in (2,4) else 0.:.1f},0.,0.' for i in range(1,6)],'*ELEMENT,TYPE=SPRINGA,ELSET=POSITIVE','1,2,3',
       '*ELEMENT,TYPE=SPRINGA,ELSET=NEGATIVE','2,4,5',
       '*SPRING,ELSET=POSITIVE,NONLINEAR','','0.,-10.','0.,0.','1000.,10.',
       '*SPRING,ELSET=NEGATIVE,NONLINEAR','','-2000.,-10.','0.,0.','0.,10.',
       '*EQUATION','2','2,1,1.,1,1,-1.','*EQUATION','2','4,1,1.,1,1,-1.',
       '*BOUNDARY','3,1,3','5,1,3','1,2,3','2,2,3','4,2,3']
for force in [10.,-20.,10.]:
 lines+=['*STEP,NLGEOM,INC=40','*STATIC','0.1,1.,1.e-6,0.25','*CLOAD,OP=NEW',f'1,1,{force:.1f}',
         '*NODE PRINT,NSET=N','U','RF','*END STEP']
packet=freeze(HERE/'native',model,metadata,extra_sources=[Path(__file__).resolve(),HERE/'assess.py'],deck_text='\n'.join(lines)+'\n')
print('Frozen one-run fixture',hashlib.sha256((HERE/'native/freeze.json').read_bytes()).hexdigest())
