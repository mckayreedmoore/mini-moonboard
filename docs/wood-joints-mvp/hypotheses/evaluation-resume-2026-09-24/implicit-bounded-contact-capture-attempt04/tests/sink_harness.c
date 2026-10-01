#include <stdlib.h>
typedef int ITG;
#include "../capture-sink.inc"

static void face(ITG tie,ITG pass,ITG ord,ITG encoded,ITG start,ITG end){
  ITG status=1;
  ccxcap_face_(&tie,&pass,&ord,&encoded,&start,&end,&status);
}

static void point(ITG tie,ITG pass,ITG faceord,ITG encoded,ITG local,
                  ITG igauss,ITG valid,ITG reason,ITG master,ITG isol,
                  double gap,double xi,double eta){
  ITG law=2;
  double area=1.0,k=10.0,initial=0.0,nx=0.0,ny=0.0,nz=1.0;
  double mxi=0.25,meta=0.25,px=0.5,py=0.5,pz=0.0;
  ccxcap_point_(&tie,&pass,&faceord,&encoded,&local,&igauss,&valid,&reason,
    &master,&law,&isol,&gap,&gap,&area,&k,&initial,&nx,&ny,&nz,&xi,&eta,
    &mxi,&meta,&px,&py,&pz);
}

static void map_sweep(ITG generation){
  ITG tie=1,pass,ord,encoded,start,end;
  for(pass=1;pass<=2;pass++){
    ord=1;encoded=101;start=0;end=1;face(tie,pass,ord,encoded,start,end);
    ord=2;encoded=102;start=1;end=3;face(tie,pass,ord,encoded,start,end);
    point(tie,pass,1,101,1,1,1,(generation==1||pass==1)?0:2,201,
          generation==1?25:0,-0.1,0.1,0.1);
    point(tie,pass,2,102,1,2,0,1,0,0,0.0,0.2,0.2);
    point(tie,pass,2,102,2,3,1,(generation==1||pass==1)?2:0,
          generation==1?201:202,generation==1?0:25,
          generation==1?0.02:-0.1,0.3,0.3);
  }
}

static void simple_step_sweep(void){
  ITG tie=1,pass,ord,encoded,start,end;
  for(pass=1;pass<=2;pass++){
    ord=1;encoded=101;start=0;end=1;face(tie,pass,ord,encoded,start,end);
    ord=2;encoded=102;start=1;end=3;face(tie,pass,ord,encoded,start,end);
    point(tie,pass,1,101,1,1,1,0,201,25,-0.1,0.1,0.1);
    point(tie,pass,2,102,1,2,0,1,0,0,0.0,0.2,0.2);
    point(tie,pass,2,102,2,3,1,2,0,0,0.02,0.3,0.3);
  }
}

static void mixed_pass_sweep(void){
  ITG tie=1,ord=1,encoded=101,start=0,end=2;
  face(tie,1,ord,encoded,start,end);
  point(tie,1,1,101,1,1,1,0,201,25,-0.1,0.1,0.1);
  point(tie,1,1,101,2,2,1,0,201,25,-0.1,0.2,0.2);
  /* Only tie 1 has prior contact and is regenerated in optional pass 2. */
  face(tie,2,ord,encoded,start,end);
  point(tie,2,1,101,1,1,1,0,201,25,-0.1,0.1,0.1);
  point(tie,2,1,101,2,2,1,0,201,25,-0.1,0.2,0.2);
  tie=2;encoded=201;start=2;end=4;
  face(tie,1,ord,encoded,start,end);
  point(tie,1,1,201,1,3,1,0,301,25,-0.1,0.3,0.3);
  point(tie,1,1,201,2,4,1,0,301,25,-0.1,0.4,0.4);
}

int main(int argc,char **argv){
  ITG step=1,inc=1,cutback=0,iter=1,nk=3,mt=1,nener=1,ntie=1,nintpoint=3;
  ITG tie=1,face_encoded=101,igen,loop,ord,status=1;
  ITG element=12,igauss,trial_tie=1,energy_enabled=1,icntrl,kscale=1;
  double vold[3]={0.0,0.0,0.0},ttime=0.0,time=0.1;
  double gap=-0.1,t1=0.0,t2=0.0,pressure=1.0,s1=0.0,s2=0.0;
  double area=1.0,energy=0.05,nx=0.0,ny=0.0,nz=1.0;
  if(argc>1&&(!strcmp(argv[1],"invalid-zero")||!strcmp(argv[1],"invalid-extra"))){
    ntie=strcmp(argv[1],"invalid-zero")==0?0:2;
    ccxcap_generation_begin_(&step,&inc,&cutback,&iter,&nk,&mt,vold,&kscale,
                             &nener,&ntie,&nintpoint);
    face(tie,1,1,101,0,1);
    ccxcap_generation_end_();
    ccxcap_finish_();
    return 0;
  }
  if(argc>1&&strcmp(argv[1],"two-step")==0){
    for(loop=1;loop<=2;loop++){
      step=loop;inc=1;iter=1;vold[0]=(double)step;
      ccxcap_generation_begin_(&step,&inc,&cutback,&iter,&nk,&mt,vold,&kscale,
                               &nener,&ntie,&nintpoint);
      simple_step_sweep();
      ccxcap_generation_end_();
      ccxcap_corrected_(&step,&inc,&cutback,&iter,&nk,&mt,vold);
      igauss=1;face_encoded=101;icntrl=1;
      ccxcap_trial_(&element,&igauss,&face_encoded,&trial_tie,&energy_enabled,
        &gap,&t1,&t2,&pressure,&s1,&s2,&area,&energy,&nx,&ny,&nz,&kscale,&time);
      ccxcap_trial_end_();
      ccxcap_iteration_link_(&step,&inc,&cutback,&iter,&icntrl,&ttime,&time);
    }
    ccxcap_finish_();
    return 0;
  }
  if(argc>1&&strcmp(argv[1],"mixed-pass2")==0){
    ntie=2;nintpoint=4;
    ccxcap_generation_begin_(&step,&inc,&cutback,&iter,&nk,&mt,vold,&kscale,
                             &nener,&ntie,&nintpoint);
    mixed_pass_sweep();
    ccxcap_generation_end_();
    ccxcap_corrected_(&step,&inc,&cutback,&iter,&nk,&mt,vold);
    for(trial_tie=1;trial_tie<=2;trial_tie++){
      ITG first=(trial_tie==1)?1:3,last=first+1;
      face_encoded=(trial_tie==1)?101:201;
      for(igauss=first;igauss<=last;igauss++)
        ccxcap_trial_(&element,&igauss,&face_encoded,&trial_tie,&energy_enabled,
          &gap,&t1,&t2,&pressure,&s1,&s2,&area,&energy,&nx,&ny,&nz,&kscale,&time);
    }
    ccxcap_trial_end_();
    icntrl=1;ccxcap_iteration_link_(&step,&inc,&cutback,&iter,&icntrl,&ttime,&time);
    ccxcap_finish_();
    return 0;
  }
  if(argc>1&&argv[1][0]=='c'){
    /* Cap control: valid zero-span face rows exceed a test-only small cap. */
    ntie=1;nintpoint=0;iter=1;
    ccxcap_generation_begin_(&step,&inc,&cutback,&iter,&nk,&mt,vold,&kscale,
                             &nener,&ntie,&nintpoint);
    for(loop=1;loop<=2;loop++)for(ord=1;ord<=200;ord++)
      face(tie,loop,ord,1000+ord,0,0);
    ccxcap_generation_end_();
    ccxcap_finish_();
    return 0;
  }
  if(argc>1&&argv[1][0]=='u'){
    ccxcap_generation_begin_(&step,&inc,&cutback,&iter,&nk,&mt,vold,&kscale,
                             &nener,&ntie,&nintpoint);
    face(tie,1,1,101,0,1);
    point(tie,1,1,101,1,1,0,99,0,1,-0.1,0.1,0.1);
    ccxcap_generation_end_();
    ccxcap_finish_();
    return 0;
  }
  if(argc>1&&argv[1][0]=='d'){
    ccxcap_generation_begin_(&step,&inc,&cutback,&iter,&nk,&mt,vold,&kscale,
                             &nener,&ntie,&nintpoint);
    face(tie,1,1,101,0,2);
    point(tie,1,1,101,1,1,1,0,201,25,-0.1,0.1,0.1);
    point(tie,1,1,101,1,1,1,0,201,25,-0.1,0.1,0.1);
    ccxcap_generation_end_();
    ccxcap_finish_();
    return 0;
  }
  if(argc>1&&argv[1][0]=='m'){
    ccxcap_generation_begin_(&step,&inc,&cutback,&iter,&nk,&mt,vold,&kscale,
                             &nener,&ntie,&nintpoint);
    face(tie,1,1,101,0,1);face(tie,1,2,102,1,3);
    point(tie,1,1,101,1,1,1,0,201,25,-0.1,0.1,0.1);
    point(tie,1,2,102,1,2,0,1,0,0,0.0,0.2,0.2);
    ccxcap_generation_end_();
    ccxcap_finish_();
    return 0;
  }
  if(argc>1&&argv[1][0]=='n'){
    nener=0;energy_enabled=0;
  }
  if(argc>1&&argv[1][0]=='s'){
    ccxcap_generation_begin_(&step,&inc,&cutback,&iter,&nk,&mt,vold,&kscale,
                             &nener,&ntie,&nintpoint);
    map_sweep(1);
    ccxcap_generation_end_();
    ccxcap_corrected_(&step,&inc,&cutback,&iter,&nk,&mt,vold);
    igauss=1;face_encoded=101;icntrl=1;
    ccxcap_trial_(&element,&igauss,&face_encoded,&trial_tie,&energy_enabled,
      &gap,&t1,&t2,&pressure,&s1,&s2,&area,&energy,&nx,&ny,&nz,&kscale,&time);
    ccxcap_trial_end_();
    ccxcap_iteration_link_(&step,&inc,&cutback,&iter,&icntrl,&ttime,&time);
    /* Simulate the shared Fortran generation-end hook reached by the next
       uninstrumented pre-loop seed scan after the sink has been enabled. */
    ccxcap_generation_end_();
    ccxcap_finish_();
    return 0;
  }
  for(igen=1;igen<=2;igen++){
    if(igen==2){iter=2;}
    ccxcap_generation_begin_(&step,&inc,&cutback,&iter,&nk,&mt,vold,&kscale,
                             &nener,&ntie,&nintpoint);
    map_sweep(igen);
    ccxcap_generation_end_();
    ccxcap_corrected_(&step,&inc,&cutback,&iter,&nk,&mt,vold);
    igauss=(igen==1)?1:3;face_encoded=(igen==1)?101:102;
    ccxcap_trial_(&element,&igauss,&face_encoded,&trial_tie,&energy_enabled,
      &gap,&t1,&t2,&pressure,&s1,&s2,&area,&energy,&nx,&ny,&nz,&kscale,&time);
    ccxcap_trial_end_();
    icntrl=(igen==1)?0:1;
    ccxcap_iteration_link_(&step,&inc,&cutback,&iter,&icntrl,&ttime,&time);
  }
  ccxcap_finish_();
  return 0;
}
