#include <stdlib.h>
#include <stdio.h>
typedef int ITG;

#ifdef WJCC_TEST_IO_FAILURE
static int test_io_failure_mode=0;
static int test_flush_calls=0;
static int test_flush(FILE *stream){
  int status=fflush(stream);test_flush_calls++;
  if((test_io_failure_mode==1&&test_flush_calls==1)||
     (test_io_failure_mode==2&&test_flush_calls==3))return EOF;
  return status;
}
static int test_close(FILE *stream){
  int status=fclose(stream);
  if(test_io_failure_mode==3)return EOF;
  return status;
}
#define WJCC_FFLUSH test_flush
#define WJCC_FCLOSE test_close
#endif

#include "../capture-sink.inc"

static void face_with_status(ITG tie,ITG pass,ITG ord,ITG encoded,ITG start,ITG end,ITG status){
  ccxcap_face_(&tie,&pass,&ord,&encoded,&start,&end,&status);
}

static void face(ITG tie,ITG pass,ITG ord,ITG encoded,ITG start,ITG end){
  face_with_status(tie,pass,ord,encoded,start,end,1);
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

static void mixed_pass_sweep(int pass2_mismatch_kind){
  ITG tie=1,ord=1,encoded=101,start=0,end=2;
  ITG pass2_face=encoded,pass2_start=start,pass2_end=end,pass2_status=1;
  face(tie,1,ord,encoded,start,end);
  point(tie,1,1,101,1,1,1,0,201,25,-0.1,0.1,0.1);
  point(tie,1,1,101,2,2,1,0,201,25,-0.1,0.2,0.2);
  /* Only tie 1 has prior contact and is regenerated in optional pass 2. */
  if(pass2_mismatch_kind==1)pass2_face=999;
  if(pass2_mismatch_kind==2){pass2_start+=10;pass2_end+=10;}
  if(pass2_mismatch_kind==3)pass2_status=0;
  face_with_status(tie,2,ord,pass2_face,pass2_start,pass2_end,pass2_status);
  point(tie,2,1,101,1,1,1,0,201,25,-0.1,0.1,0.1);
  point(tie,2,1,101,2,2,1,0,201,25,-0.1,0.2,0.2);
  tie=2;encoded=201;start=2;end=4;
  face(tie,1,ord,encoded,start,end);
  point(tie,1,1,201,1,3,1,0,301,25,-0.1,0.3,0.3);
  point(tie,1,1,201,2,4,1,0,301,25,-0.1,0.4,0.4);
}

static void candidate_cap_sweep(ITG count){
  ITG tie=1,pass=1,ord=1,encoded=101,start=0,end=count,index;
  double gap=0.1;
  face(tie,pass,ord,encoded,start,end);
  for(index=1;index<=count;index++)
    point(tie,pass,ord,encoded,index,index,1,2,0,0,gap,0.1,0.1);
}

int main(int argc,char **argv){
  ITG step=1,inc=1,cutback=0,iter=1,nk=3,mt=1,nener=1,ntie=1,nintpoint=3;
  ITG tie=1,face_encoded=101,igen,loop,ord,status=1;
  ITG element=12,igauss,trial_tie=1,energy_enabled=1,icntrl,kscale=1;
  double vold[3]={0.0,0.0,0.0},ttime=0.0,time=0.1;
  double gap=-0.1,t1=0.0,t2=0.0,pressure=1.0,s1=0.0,s2=0.0;
  double area=1.0,energy=0.05,nx=0.0,ny=0.0,nz=1.0;
#ifdef WJCC_TEST_IO_FAILURE
  if(argc>1&&strcmp(argv[1],"fail-gen-flush")==0)test_io_failure_mode=1;
  if(argc>1&&strcmp(argv[1],"fail-footer-flush")==0)test_io_failure_mode=2;
  if(argc>1&&strcmp(argv[1],"fail-close")==0)test_io_failure_mode=3;
#endif
  if(argc>1&&strcmp(argv[1],"candidate-cap-boundary")==0){
    nintpoint=250000;ntie=1;
    ccxcap_generation_begin_(&step,&inc,&cutback,&iter,&nk,&mt,vold,&kscale,
                             &nener,&ntie,&nintpoint);
    candidate_cap_sweep(nintpoint);
    ccxcap_generation_end_();
    ccxcap_corrected_(&step,&inc,&cutback,&iter,&nk,&mt,vold);
    ccxcap_trial_end_();
    icntrl=1;ccxcap_iteration_link_(&step,&inc,&cutback,&iter,&icntrl,&ttime,&time);
    ccxcap_finish_();
    return 0;
  }
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
  if(argc>1&&(strcmp(argv[1],"mixed-pass2")==0||
      strcmp(argv[1],"bad-pass2-identity")==0||
      strcmp(argv[1],"bad-pass2-offset")==0||
      strcmp(argv[1],"bad-pass2-status")==0)){
    int pass2_mismatch_kind=strcmp(argv[1],"bad-pass2-identity")==0?1:
      strcmp(argv[1],"bad-pass2-offset")==0?2:
      strcmp(argv[1],"bad-pass2-status")==0?3:0;
    ntie=2;nintpoint=4;
    ccxcap_generation_begin_(&step,&inc,&cutback,&iter,&nk,&mt,vold,&kscale,
                             &nener,&ntie,&nintpoint);
    mixed_pass_sweep(pass2_mismatch_kind);
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
