"""Prepare one parent-scoped native scalar-law fixture, never a frame run."""
import hashlib,json
from pathlib import Path
from fea.horizontal_panel_frame import Structure
from fea.wood_joint_reduced_native import freeze
HERE=Path(__file__).resolve().parent
model=Structure()
for i in range(5):model.node([0.,0.,0.])
model.element('SPRING2',[2,3],'POSITIVE');model.element('SPRING2',[4,5],'NEGATIVE')
model.fixed.update([3,5])
model.equations=[[(2,1,1.),(1,1,-1.)],[(4,1,1.),(1,1,-1.)]]
model.loads={1:[10.,0.,0.]}
metadata={'candidate':'compact-floor-flush-wood-joints-development',
 'geometry_revision_id':'led-clearance-2x6-runner-seated-blocks-v1',
 'scope':'One disconnected five-node scalar nonlinear SPRING2/MPC known-answer fixture; 3 load steps; no frame or joint',
 'parent_run_budget':{'max_launches':1,'timeout_seconds':60,'run_id':'reduced-nonlinear-spring2-known-answer-attempt01'},
 'manual':{'url':'https://www.dhondt.de/ccx_2.23.pdf','sections':['6.2.41 SPRING2 (pp128-129)','7.122 SPRING (pp598-599)'],
  'interpretation':'Scalar component force-displacement table, decimal real fields, ascending elongation; constant extrapolation outside table range'},
 'known_answer':{'steps':[{'time':1.,'external_force_N':10.,'u_mm':.1,'positive_internal_force_N':10.,'negative_internal_force_N':0.},
  {'time':2.,'external_force_N':-20.,'u_mm':-.1,'positive_internal_force_N':0.,'negative_internal_force_N':-20.},
  {'time':3.,'external_force_N':10.,'u_mm':.1,'positive_internal_force_N':10.,'negative_internal_force_N':0.}]},
 'tolerances':{'u_abs_mm':2e-6,'force_abs_N':.002},
 'limits':['No bearing-conditional floor tangent rule','No actual member/bolt/screw stiffness or capacity',
           'Opposing laws keep the single physical coordinate supported; an isolated open carrier can leave a mechanism',
           'Native output force meaning must be checked before reuse; old linear K*deltaU audit is not applicable'],
 'native_solve_executed':False,'qualified_for_design':False}
lines=['*HEADING','Nonlinear scalar SPRING2 known answer; not a frame or joint','*NODE,NSET=N',
       *[f'{i},0.,0.,0.' for i in range(1,6)],'*ELEMENT,TYPE=SPRING2,ELSET=POSITIVE','1,2,3',
       '*ELEMENT,TYPE=SPRING2,ELSET=NEGATIVE','2,4,5',
       '*SPRING,ELSET=POSITIVE,NONLINEAR','1,1','0.,-10.','0.,0.','1000.,10.',
       '*SPRING,ELSET=NEGATIVE,NONLINEAR','1,1','-2000.,-10.','0.,0.','0.,10.',
       '*EQUATION','2','2,1,1.,1,1,-1.','*EQUATION','2','4,1,1.,1,1,-1.',
       '*BOUNDARY','3,1,3','5,1,3','1,2,3','2,2,3','4,2,3']
for force in [10.,-20.,10.]:
 lines+=['*STEP,NLGEOM,INC=40','*STATIC','0.1,1.,1.e-6,0.25','*CLOAD,OP=NEW',f'1,1,{force:.1f}',
         '*NODE PRINT,NSET=N','U','RF','*END STEP']
packet=freeze(HERE/'native',model,metadata,extra_sources=[Path(__file__).resolve()],deck_text='\n'.join(lines)+'\n')
print('Frozen one-run fixture',hashlib.sha256((HERE/'native/freeze.json').read_bytes()).hexdigest())
