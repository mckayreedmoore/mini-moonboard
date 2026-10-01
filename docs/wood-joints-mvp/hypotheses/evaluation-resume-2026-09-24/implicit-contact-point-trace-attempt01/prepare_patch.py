"""Prepare an additions-only, coupon-scoped contact-point trace from pinned source."""
from pathlib import Path
import difflib
import hashlib
import json
import subprocess
import tarfile
import tempfile

ROOT = Path(__file__).resolve().parents[5]
HERE = Path(__file__).resolve().parent
E = HERE.parent
ARCHIVE = E / 'ordinary-external-force-transient-attempt04-diagnostic/build-attempt02/source.tar.bz2'
BASE_PATCH = E / 'ordinary-external-force-transient-attempt04-diagnostic/diagnostic.patch'
ARCHIVE_SHA = '9c88385c10fb04f5dc6c4e98027a51bebdd8aee3920e05190d6c1dd08357d6e7'
BASE_PATCH_SHA = 'aea55ec88be569a39a06482723d5da22260b071bf072c55491448b22ab273e54'

def sha(b):
    return hashlib.sha256(b).hexdigest()

def insert_once(s, anchor, addition, before=False):
    assert s.count(anchor) == 1, (anchor[:80], s.count(anchor))
    return s.replace(anchor, addition+anchor if before else anchor+addition)


def main():
    assert sha(ARCHIVE.read_bytes()) == ARCHIVE_SHA
    assert sha(BASE_PATCH.read_bytes()) == BASE_PATCH_SHA
    names = ['nonlingeo.c', 'checkconvergence.c', 'gencontelem_f2f.f']
    original = {}
    with tarfile.open(ARCHIVE) as t:
        for n in names:
            original[n] = t.extractfile('./CalculiX/ccx_2.23/src/'+n).read().decode()
    with tempfile.TemporaryDirectory() as td:
        tree = Path(td)/'CalculiX/ccx_2.23/src'
        tree.mkdir(parents=True)
        for n,s in original.items(): (tree/n).write_text(s)
        subprocess.run(['patch','--batch','--fuzz=0','-p1','-i',str(BASE_PATCH)], cwd=td, check=True, capture_output=True)
        modified = {n:(tree/n).read_text() for n in names}

    s=modified['gencontelem_f2f.f']
    s=insert_once(s, '      implicit none\n', '''!     Coupon-only output trace; these locals never enter solver equations.
      integer wjdiag_valid
      real*8 wjdiag_rawclear
''')
    s=insert_once(s, '              igauss=indexf+m\n', '''              wjdiag_valid=0
              wjdiag_rawclear=0.d0
''')
    s=insert_once(s, '                clear=al(1)*xn(1)+al(2)*xn(2)+al(3)*xn(3)\n', '''                wjdiag_valid=1
                wjdiag_rawclear=clear
''')
    anchor='''              if(isol.ne.0) then
!     
!     generation of a contact spring element
'''
    addition='''!     Log the final generation decision, including mapped open points.
!     Raw gap and classifier gap differ in the static initialization path.
              if(wjdiag_valid.eq.1) then
                write(*,901) 'CCXPT_MAP',istep,iinc,icutb+1,iit,
     &            iloop,i,jj,igauss,ifaces,ifacem,isol,nmethod,
     &            int(elcon(3,1,imat)),wjdiag_rawclear,clear,
     &            springarea(1,igauss),elcon(2,1,imat),
     &            springarea(2,igauss),xn(1),xn(2),xn(3),
     &            pslavsurf(1,igauss),pslavsurf(2,igauss),
     &            pmastsurf(1,igauss),pmastsurf(2,igauss)
              else
                write(*,902) 'CCXPT_UNMAPPED',istep,iinc,
     &            icutb+1,iit,iloop,i,jj,igauss,ifaces,isol
              endif
'''
    assert s.count('  901 ')==0 and s.count('  902 ')==0
    s=insert_once(s,anchor,addition,before=True)
    # Formats are non-executable. Flush diagnostics only after the routine's work.
    assert s.rstrip().endswith('end')
    idx=s.rfind('      end')
    s=s[:idx]+'''  901 format(A,13(1X,I0),12(1X,ES25.17E3))
  902 format(A,10(1X,I0))
'''+s[idx:]
    modified['gencontelem_f2f.f']=s

    s=modified['nonlingeo.c']
    anchor='      SFREE(v);SFREE(stx);SFREE(fn);\n      \n      if((idamping==1)&&(*iexpl<=1)){SFREE(adc);SFREE(auc);}'
    assert s.count(anchor)==1
    addition=r'''
      /* Coupon-only output trace. Read the final corrected state after any
         line search, before stx is freed. No call to a mechanics routine. */
      if((*mortar==1)&&(*ithermal<2)){
        ITG wje,wjbase,wjnp,wjg,wjface,wjt,wjpair;
        double wja,wjp,wjenergy;
        for(wje=ne0;wje<*ne;wje++){
          if(ipkon[wje]<0) continue;
          if(strncmp(&lakon[8*wje],"ESPRNGC",7)!=0) continue;
          wjbase=ipkon[wje];
          wjnp=kon[wjbase-1];
          wjg=kon[wjbase+wjnp];
          wjface=kon[wjbase+wjnp+1];
          wjpair=0;
          for(wjt=0;wjt<*ntie;wjt++){
            if((wjface>=itiefac[2*wjt])&&
               (wjface<=itiefac[2*wjt+1])){wjpair=wjt+1;break;}
          }
          wja=springarea[2*(wjg-1)];
          wjp=stx[6*mi[0]*wje+3];
          wjenergy=0.;
          if(*nener==1) wjenergy=ener[2*mi[0]*(ne0+wjg-1)];
          printf("CCXPT_TRIAL %" ITGFORMAT " %" ITGFORMAT
                 " %" ITGFORMAT " %" ITGFORMAT " %" ITGFORMAT
                 " %" ITGFORMAT " %" ITGFORMAT " %" ITGFORMAT
                 " %" ITGFORMAT " %" ITGFORMAT " %" ITGFORMAT
                 " %.17e %.17e %.17e %.17e %.17e %.17e"
                 " %.17e %.17e %.17e %.17e %.17e %.17e %.17e\n",
                 *istep,iinc,icutb+1,iit,wje+1,wjg,wjface,
                 islavsurf[2*(wjface-1)],
                 (ITG)pmastsurf[6*(wjg-1)+2],wjpair,*nener,
                 stx[6*mi[0]*wje],stx[6*mi[0]*wje+1],
                 stx[6*mi[0]*wje+2],wjp,
                 stx[6*mi[0]*wje+4],stx[6*mi[0]*wje+5],
                 wja,wjenergy,pmastsurf[6*(wjg-1)+3],
                 pmastsurf[6*(wjg-1)+4],pmastsurf[6*(wjg-1)+5],
                 (double)kscale,reltime);
        }
        fflush(stdout);
      }
'''
    s=insert_once(s,anchor,addition,before=True)
    modified['nonlingeo.c']=s
    patch=''.join(''.join(difflib.unified_diff(original[n].splitlines(True),modified[n].splitlines(True),fromfile='a/CalculiX/ccx_2.23/src/'+n,tofile='b/CalculiX/ccx_2.23/src/'+n)) for n in names)
    # No original solver line is removed/replaced, including in inherited trace.
    assert not [l for l in patch.splitlines() if l.startswith('-') and not l.startswith('---')]
    (HERE/'diagnostic.patch').write_text(patch)
    d={'schema':'ccx223_contact_point_trace_preparation/v1','status':'PREPARED_NOT_BUILT_NOT_VALIDATED_COUPON_ONLY','source_archive':str(ARCHIVE.relative_to(ROOT)), 'source_archive_sha256':ARCHIVE_SHA,'inherited_patch_sha256':BASE_PATCH_SHA,'patch_sha256':sha(patch.encode()),'original_source_sha256':{n:sha(s.encode()) for n,s in original.items()},'modified_source_sha256':{n:sha(s.encode()) for n,s in modified.items()},'changes_additions_only':True,'scope':'Generator map decisions and final corrected active-spring data; no verified adjacent-iteration snapshot join or inactive force/work bound. Do not run on current joint.','joint_acceptance':False}
    (HERE/'patch-lock.json').write_text(json.dumps(d,indent=2)+'\n')
    print(json.dumps({'patch_sha256':d['patch_sha256'],'modified_files':names,'status':d['status']}))

if __name__=='__main__':main()
