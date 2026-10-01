/* Standalone review harness; includes the pinned sink without editing it.
 * This does not build or execute CalculiX. */
#define main packaged_sink_harness_main
#include "../implicit-bounded-contact-capture-attempt06/tests/sink_harness.c"
#undef main

int main(int argc, char **argv) {
  ITG step=1, inc=1, cutback=0, iter=1, nk=1, mt=1;
  ITG nener=1, ntie=1, nintpoint=0, kscale=1, icntrl=0;
  double vold[1]={0.0}, ttime=0.0, time=0.1;
  int advanced=argc>1 && strcmp(argv[1], "native-iteration-advance")==0;
  int collision=argc>1 && strcmp(argv[1], "temporary-collision")==0;
  char owner_path[8192];
  FILE *owner=NULL;
  if(argc>1 && strcmp(argv[1], "original-positive")==0)
    return packaged_sink_harness_main(argc, argv);
  if(collision) {
    snprintf(owner_path, sizeof(owner_path), "%s.ccxcap-part-%ld",
      getenv("CCX_CONTACT_CAPTURE_PATH"), (long)getpid());
    owner=fopen(owner_path, "wbx");
    if(!owner) return 10;
    fputs("pre-existing review-owned sentinel\n", owner);
    fclose(owner);
  }
  ccxcap_generation_begin_(&step,&inc,&cutback,&iter,&nk,&mt,vold,
    &kscale,&nener,&ntie,&nintpoint);
  face(1,1,1,101,0,0);
  ccxcap_generation_end_();
  ccxcap_corrected_(&step,&inc,&cutback,&iter,&nk,&mt,vold);
  ccxcap_trial_end_();
  /* Pinned checkconvergence.c:874 increments (*iit) before returning on
   * the normal no-convergence branch. nonlingeo calls the link afterward. */
  if(advanced) iter++;
  ccxcap_iteration_link_(&step,&inc,&cutback,&iter,&icntrl,&ttime,&time);
  printf("first_link: captured_iter=%d live_iter=%d pending=%d links=%llu error=%d\n",
    (int)wjcc_iter,(int)iter,wjcc_pending,
    (unsigned long long)wjcc_run_links,wjcc_error);
  if(!collision) {
    iter=2;
    ccxcap_generation_begin_(&step,&inc,&cutback,&iter,&nk,&mt,vold,
      &kscale,&nener,&ntie,&nintpoint);
    face(1,1,1,101,0,0);
    ccxcap_generation_end_();
    ccxcap_corrected_(&step,&inc,&cutback,&iter,&nk,&mt,vold);
    ccxcap_trial_end_();
    icntrl=1;
    ccxcap_iteration_link_(&step,&inc,&cutback,&iter,&icntrl,&ttime,&time);
  }
  ccxcap_finish_();
  if(collision) {
    owner=fopen(owner_path,"rb");
    printf("preexisting_temporary_survives=%d\n",owner!=NULL);
    if(owner) fclose(owner);
  }
  return 0;
}
