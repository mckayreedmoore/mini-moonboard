"""Executable CalculiX sign/stiffness check before using unilateral supports."""
import re
import subprocess
from pathlib import Path


def main():
    directory=Path("fea/generated/connection")
    directory.mkdir(parents=True,exist_ok=True)
    for force in (-100.,100.):
        job=directory/("spring_pull" if force<0 else "spring_push")
        job.with_suffix(".inp").write_text(f"""*NODE,NSET=N
1,0.,0.,0.
2,0.,0.,10000.
*ELEMENT,TYPE=SPRINGA,ELSET=HEAD
1,1,2
*ELEMENT,TYPE=SPRINGA,ELSET=BACK
2,1,2
*SPRING,ELSET=HEAD,NONLINEAR
0.,-100.
0.,0.
100000.,100.
*SPRING,ELSET=BACK,NONLINEAR
-1000000.,-100.
0.,0.
0.,100.
*BOUNDARY
1,1,2
2,1,3
*STEP,NLGEOM,INC=100
*STATIC
0.1,1.,1.e-6,0.2
*CLOAD
1,3,{force:.1f}
*NODE PRINT,NSET=N
U
*END STEP
""")
        run=subprocess.run(["ccx","-i",job.name],cwd=directory,capture_output=True,text=True,check=False)
        job.with_suffix(".log").write_text(run.stdout+run.stderr)
        if run.returncode or "*ERROR" in run.stdout.upper():
            raise RuntimeError(run.stdout[-3000:])
        rows=re.findall(r"^\s*1\s+([-+\d.E]+)\s+([-+\d.E]+)\s+([-+\d.E]+)\s*$",job.with_suffix(".dat").read_text(),re.MULTILINE)
        actual=float(rows[-1][2])
        expected=force/(1000 if force<0 else 10000)
        if abs(actual-expected)>1e-8:
            raise ValueError((actual,expected))
        print(job.name,actual,"mm: PASS")


if __name__=="__main__":
    main()
