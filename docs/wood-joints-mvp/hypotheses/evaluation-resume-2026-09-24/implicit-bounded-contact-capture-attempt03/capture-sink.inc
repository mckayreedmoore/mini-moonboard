/*
 * Output-only, bounded capture sink for the CalculiX 2.23 face-to-face
 * penalty contact path.  This file is appended to nonlingeo.c by the
 * additions-only patch generator.  It never writes to solver arrays.
 */
#include <errno.h>
#include <math.h>
#include <stdarg.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define WJCC_VERSION 1
#ifndef WJCC_MAX_BYTES
#define WJCC_MAX_BYTES ((uint64_t)134217728)
#endif
#define WJCC_MAX_SWEEPS 64
#define WJCC_MAX_POINTS 250000
#define WJCC_KEY_CAP 524288u
#define WJCC_MAX_TIES 128
#define WJCC_MAX_STATE_DOUBLES 1000000u
#define WJCC_LINE 2048

typedef struct {
  ITG tie,pass,faceord,face,local,igauss,valid,reason,master,law,isol;
  double rawgap,classgap,area,k,initial,nx,ny,nz,sxi,seta,mxi,meta;
  double px,py,pz,kscale;
  double trialgap,pressure,energy;
  ITG trial_seen,energy_enabled,matched;
} WJCCPoint;

typedef struct {
  uint64_t faces,zero_faces,span,candidates,mapped,unmapped,generated,excluded;
  uint64_t reason[100],duplicates,law2,other_law,nonfinite;
  double raw_min,raw_max,class_min,class_max,area_min,area_max,k_min,k_max;
  double nmin[3],nmax[3];
  ITG raw_min_face,raw_min_local,raw_max_face,raw_max_local;
  ITG class_min_face,class_min_local,class_max_face,class_max_local;
  uint64_t digest;
  int initialized;
} WJCCMapStat;

typedef struct {
  uint64_t count,unjoined,wrong_law,force_rows,energy_rows,positive_gap;
  double force[3],abs_force,energy,gap_min,gap_max;
  int force_complete,energy_complete,gap_initialized;
} WJCCTrialStat;

typedef struct {
  uint64_t same,remapped,old_missing,new_missing;
  uint64_t generated_to_excluded,excluded_to_generated;
} WJCCJoinStat;

static FILE *wjcc_fp=NULL;
static int wjcc_enabled=-1,wjcc_overflow=0,wjcc_error=0,wjcc_closed=0;
static int wjcc_map_complete=0,wjcc_trial_complete=0,wjcc_pending=0;
static uint64_t wjcc_bytes=0,wjcc_generation=0,wjcc_run_faces=0;
static uint64_t wjcc_run_points=0,wjcc_run_trials=0,wjcc_run_links=0;
static ITG wjcc_step=0,wjcc_inc=0,wjcc_attempt=0,wjcc_iter=0;
static ITG wjcc_nintpoint=0,wjcc_nener=0,wjcc_ntie=0;
static ITG wjcc_expected_faces=0,wjcc_expected_ties=0;
static double wjcc_kscale=1.0;
static ITG wjcc_pass_faces[WJCC_MAX_TIES+1][3];
static ITG wjcc_latest_pass[WJCC_MAX_TIES+1];
static ITG wjcc_prev_latest[WJCC_MAX_TIES+1];
static uint64_t wjcc_pass_spans[WJCC_MAX_TIES+1][3];
static uint64_t wjcc_face_rows=0,wjcc_point_rows=0,wjcc_trial_rows=0;
static uint64_t wjcc_face_hash=1469598103934665603ULL;
static uint64_t wjcc_outcome_hash=1469598103934665603ULL;
static ITG wjcc_offset_base[3],wjcc_offset_next[3];
static int wjcc_offset_initialized[3];
static double *wjcc_state=NULL,*wjcc_corrected=NULL;
static size_t wjcc_state_n=0,wjcc_corrected_n=0;
static ITG wjcc_corr_step=0,wjcc_corr_inc=0,wjcc_corr_attempt=0,wjcc_corr_iter=0;
static uint64_t wjcc_state_token=0,wjcc_corrected_token=0;
static int wjcc_state_finite=1,wjcc_corrected_finite=1,wjcc_prev_equal=0;
static WJCCPoint *wjcc_points=NULL,*wjcc_previous=NULL;
static size_t wjcc_points_n=0,wjcc_points_cap=0,wjcc_previous_n=0;
static uint32_t *wjcc_key_table=NULL,*wjcc_gauss_index=NULL;
static size_t wjcc_gauss_n=0;
static WJCCMapStat wjcc_map[WJCC_MAX_TIES+1][3];
static WJCCTrialStat wjcc_trial[WJCC_MAX_TIES+1];
static WJCCJoinStat wjcc_join[WJCC_MAX_TIES+1];

static uint64_t wjcc_fnv(const void *data,size_t n,uint64_t h){
  const unsigned char *p=(const unsigned char*)data;size_t i;
  for(i=0;i<n;i++){h^=(uint64_t)p[i];h*=1099511628211ULL;}
  return h;
}
static uint64_t wjcc_state_hash(const double *v,size_t n,int *finite){
  size_t i;uint64_t h=1469598103934665603ULL;
  for(i=0;i<n;i++){if(!isfinite(v[i]))*finite=0;h=wjcc_fnv(&v[i],sizeof(double),h);}
  return h;
}
static int wjcc_hex64(const char *s){
  size_t i;if(!s||strlen(s)!=64)return 0;
  for(i=0;i<64;i++)if(!((s[i]>='0'&&s[i]<='9')||(s[i]>='a'&&s[i]<='f')||(s[i]>='A'&&s[i]<='F')))return 0;
  return 1;
}
static const char *wjcc_env(const char *name){const char *v=getenv(name);return v?v:"UNBOUND";}
static int wjcc_parse_bounded_itg(const char *s,long minimum,long maximum,ITG *out){
  char *end=NULL;long value;const char *p;
  if(!s||!*s)return 0;
  for(p=s;*p;p++)if(*p<'0'||*p>'9')return 0;
  errno=0;value=strtol(s,&end,10);
  if(errno||end==s||*end!='\0'||value<minimum||value>maximum)return 0;
  *out=(ITG)value;return 1;
}
static void wjcc_emit(int footer,const char *fmt,...){
  char line[WJCC_LINE];int n;va_list ap;uint64_t limit=WJCC_MAX_BYTES-(footer?0:4096);
  if(!wjcc_fp||(!footer&&(wjcc_error||wjcc_overflow)))return;
  va_start(ap,fmt);n=vsnprintf(line,sizeof(line),fmt,ap);va_end(ap);
  if(n<0||(size_t)n>=sizeof(line)||wjcc_bytes+(uint64_t)n>limit){wjcc_overflow=1;return;}
  if(fwrite(line,1,(size_t)n,wjcc_fp)!=(size_t)n){wjcc_error=1;return;}
  wjcc_bytes+=(uint64_t)n;
}
static const char *wjcc_num(double x,char *b,size_t n){
  if(!isfinite(x)){snprintf(b,n,"NA");return b;}
  snprintf(b,n,"%.17g",x);return b;
}
static void wjcc_open(void){
  const char *path,*input,*includes,*source,*patch,*binary,*pairs,*faces,*ef,*et;
  int valid,roster_valid;
  if(wjcc_enabled!=-1)return;
  path=getenv("CCX_CONTACT_CAPTURE_PATH");wjcc_enabled=(path&&*path)?1:0;
  if(!wjcc_enabled)return;
  input=wjcc_env("CCX_CAPTURE_INPUT_SHA256");
  includes=wjcc_env("CCX_CAPTURE_INCLUDE_SHA256");
  source=wjcc_env("CCX_CAPTURE_SOURCE_SHA256");
  patch=wjcc_env("CCX_CAPTURE_PATCH_SHA256");
  binary=wjcc_env("CCX_CAPTURE_BINARY_SHA256");
  pairs=wjcc_env("CCX_CAPTURE_PAIR_SHA256");
  faces=wjcc_env("CCX_CAPTURE_FACE_SHA256");
  ef=getenv("CCX_CAPTURE_EXPECTED_FACES");et=getenv("CCX_CAPTURE_EXPECTED_TIES");
  roster_valid=wjcc_parse_bounded_itg(ef,1,13001,&wjcc_expected_faces)&&
    wjcc_parse_bounded_itg(et,1,WJCC_MAX_TIES,&wjcc_expected_ties);
  valid=wjcc_hex64(input)&&wjcc_hex64(includes)&&wjcc_hex64(source)&&
    wjcc_hex64(patch)&&wjcc_hex64(binary)&&wjcc_hex64(pairs)&&
    wjcc_hex64(faces)&&roster_valid;
  wjcc_fp=fopen(path,"wbx");if(!wjcc_fp){wjcc_error=1;return;}
  wjcc_emit(0,"CCXCAP\t1\n");
  wjcc_emit(0,"RUN_BEGIN\t%d\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%u\t%d\t%d\t%d\n",
    WJCC_VERSION,input,includes,source,patch,binary,pairs,faces,
    (unsigned)WJCC_MAX_BYTES,(int)wjcc_expected_ties,(int)wjcc_expected_faces,valid);
  if(!valid)wjcc_error=1;
}
static size_t wjcc_map_index(ITG tie,ITG pass){return (size_t)tie*3u+(size_t)pass;}
static uint64_t wjcc_point_hash(const WJCCPoint *p,int include_pass){
  uint64_t h=1469598103934665603ULL;
  h=wjcc_fnv(&p->tie,sizeof(p->tie),h);if(include_pass)h=wjcc_fnv(&p->pass,sizeof(p->pass),h);
  h=wjcc_fnv(&p->faceord,sizeof(p->faceord),h);h=wjcc_fnv(&p->face,sizeof(p->face),h);
  h=wjcc_fnv(&p->local,sizeof(p->local),h);
  h=wjcc_fnv(&p->sxi,sizeof(p->sxi),h);h=wjcc_fnv(&p->seta,sizeof(p->seta),h);return h;
}
static int wjcc_key_equal(const WJCCPoint *a,const WJCCPoint *b,int include_pass){
  return a->tie==b->tie&&(!include_pass||a->pass==b->pass)&&
    a->faceord==b->faceord&&a->face==b->face&&a->local==b->local&&
    memcmp(&a->sxi,&b->sxi,sizeof(double))==0&&memcmp(&a->seta,&b->seta,sizeof(double))==0;
}
static void wjcc_reset_stats(void){
  memset(wjcc_pass_faces,0,sizeof(wjcc_pass_faces));
  memset(wjcc_latest_pass,0,sizeof(wjcc_latest_pass));
  memset(wjcc_pass_spans,0,sizeof(wjcc_pass_spans));
  memset(wjcc_map,0,sizeof(wjcc_map));memset(wjcc_trial,0,sizeof(wjcc_trial));
  memset(wjcc_join,0,sizeof(wjcc_join));memset(wjcc_offset_initialized,0,sizeof(wjcc_offset_initialized));
  wjcc_face_rows=wjcc_point_rows=wjcc_trial_rows=0;
  wjcc_face_hash=wjcc_outcome_hash=1469598103934665603ULL;
}
static void wjcc_minmax(WJCCMapStat *s,WJCCPoint *p){
  if(!s->initialized){
    s->raw_min=s->raw_max=p->rawgap;s->class_min=s->class_max=p->classgap;
    s->area_min=s->area_max=p->area;s->k_min=s->k_max=p->k;
    s->raw_min_face=s->raw_max_face=s->class_min_face=s->class_max_face=p->faceord;
    s->raw_min_local=s->raw_max_local=s->class_min_local=s->class_max_local=p->local;
    s->nmin[0]=s->nmax[0]=p->nx;s->nmin[1]=s->nmax[1]=p->ny;s->nmin[2]=s->nmax[2]=p->nz;
    s->initialized=1;return;
  }
  if(p->rawgap<s->raw_min){s->raw_min=p->rawgap;s->raw_min_face=p->faceord;s->raw_min_local=p->local;}
  if(p->rawgap>s->raw_max){s->raw_max=p->rawgap;s->raw_max_face=p->faceord;s->raw_max_local=p->local;}
  if(p->classgap<s->class_min){s->class_min=p->classgap;s->class_min_face=p->faceord;s->class_min_local=p->local;}
  if(p->classgap>s->class_max){s->class_max=p->classgap;s->class_max_face=p->faceord;s->class_max_local=p->local;}
  if(p->area<s->area_min)s->area_min=p->area;if(p->area>s->area_max)s->area_max=p->area;
  if(p->k<s->k_min)s->k_min=p->k;if(p->k>s->k_max)s->k_max=p->k;
  if(p->nx<s->nmin[0])s->nmin[0]=p->nx;if(p->nx>s->nmax[0])s->nmax[0]=p->nx;
  if(p->ny<s->nmin[1])s->nmin[1]=p->ny;if(p->ny>s->nmax[1])s->nmax[1]=p->ny;
  if(p->nz<s->nmin[2])s->nmin[2]=p->nz;if(p->nz>s->nmax[2])s->nmax[2]=p->nz;
}
static int wjcc_finite_map(const WJCCPoint *p){
  return isfinite(p->rawgap)&&isfinite(p->classgap)&&isfinite(p->area)&&isfinite(p->k)&&
    isfinite(p->initial)&&isfinite(p->nx)&&isfinite(p->ny)&&isfinite(p->nz)&&
    isfinite(p->sxi)&&isfinite(p->seta)&&isfinite(p->mxi)&&isfinite(p->meta)&&
    isfinite(p->px)&&isfinite(p->py)&&isfinite(p->pz)&&isfinite(p->kscale);
}
static int wjcc_point_append(WJCCPoint *src){
  uint64_t h;size_t slot;uint32_t idx;WJCCMapStat *s;
  if(src->tie<1||src->tie>WJCC_MAX_TIES||src->pass<1||src->pass>2||src->faceord<1||src->local<1){wjcc_error=1;return 0;}
  if(wjcc_points_n>=WJCC_MAX_POINTS){wjcc_overflow=1;return 0;}
  h=wjcc_point_hash(src,1);slot=(size_t)(h&(WJCC_KEY_CAP-1));
  while((idx=wjcc_key_table[slot])!=0){
    if(wjcc_key_equal(src,&wjcc_points[idx-1],1)){
      wjcc_map[src->tie][src->pass].duplicates++;wjcc_error=1;return 0;
    }
    slot=(slot+1)&(WJCC_KEY_CAP-1);
  }
  if(wjcc_points_n==wjcc_points_cap){size_t cap=wjcc_points_cap?wjcc_points_cap*2:512;WJCCPoint *p;
    if(cap>WJCC_MAX_POINTS)cap=WJCC_MAX_POINTS;
    p=(WJCCPoint*)realloc(wjcc_points,cap*sizeof(WJCCPoint));if(!p){wjcc_error=1;return 0;}
    wjcc_points=p;wjcc_points_cap=cap;
  }
  wjcc_points[wjcc_points_n]=*src;wjcc_key_table[slot]=(uint32_t)(wjcc_points_n+1);
  wjcc_points_n++;wjcc_point_rows++;wjcc_run_points++;
  s=&wjcc_map[src->tie][src->pass];s->candidates++;
  s->digest=wjcc_fnv(&h,sizeof(h),s->digest?s->digest:1469598103934665603ULL);
  s->reason[(src->reason>=0&&src->reason<100)?src->reason:99]++;
  if(src->valid){s->mapped++;
    if(!wjcc_finite_map(src)){s->nonfinite++;wjcc_error=1;}else wjcc_minmax(s,src);
    if(src->law==2)s->law2++;else s->other_law++;
    if(src->isol!=0){
      uint32_t previous=0;
      s->generated++;
      if(wjcc_gauss_index&&src->igauss>0&&(size_t)src->igauss<wjcc_gauss_n){
        previous=wjcc_gauss_index[src->igauss];
        if(previous&&(!wjcc_key_equal(src,&wjcc_points[previous-1],0)))wjcc_error=1;
        wjcc_gauss_index[src->igauss]=(uint32_t)wjcc_points_n;
      }else wjcc_error=1;
    }
    else s->excluded++;
  }else{s->unmapped++;if(src->isol!=0)wjcc_error=1;}
  if(src->reason==99){wjcc_error=1;}
  if(src->pass>wjcc_latest_pass[src->tie])wjcc_latest_pass[src->tie]=src->pass;
  wjcc_outcome_hash=wjcc_fnv(&h,sizeof(h),wjcc_outcome_hash);
  wjcc_outcome_hash=wjcc_fnv(&src->reason,sizeof(src->reason),wjcc_outcome_hash);
  wjcc_outcome_hash=wjcc_fnv(&src->isol,sizeof(src->isol),wjcc_outcome_hash);
  return 1;
}
static void wjcc_emit_map_summaries(void){
  ITG tie,pass;char a[32],b[32],c[32],d[32],e[32],f[32],g[32],h[32],i[32],j[32];
  char k[32],l[32],m[32],n[32],o[32],p[32],q[32],r[32],s[32],t[32],u[32],v[32],w[32];
  for(tie=1;tie<=wjcc_ntie;tie++)for(pass=1;pass<=2;pass++){
    WJCCMapStat *x=&wjcc_map[tie][pass];
    if(!wjcc_pass_faces[tie][pass]&&!x->candidates)continue;
    wjcc_emit(0,
      "MAP_SUMMARY\t%llu\t%d\t%d\t%d\t%d\t%d\t%d"
      "\t%llu\t%llu\t%llu\t%llu\t%llu\t%llu\t%llu\t%llu"
      "\t%llu\t%llu\t%llu\t%llu\t%llu\t%llu\t%llu\t%llu\t%llu"
      "\t%s\t%d\t%d\t%s\t%d\t%d\t%s\t%d\t%d\t%s\t%d\t%d"
      "\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s"
      "\t%llu\t%llu\t%llu\t%016llx\t%llu\n",
      (unsigned long long)wjcc_generation,(int)wjcc_step,(int)wjcc_inc,(int)wjcc_attempt,(int)wjcc_iter,(int)tie,(int)pass,
      (unsigned long long)x->faces,(unsigned long long)x->zero_faces,(unsigned long long)x->span,
      (unsigned long long)x->candidates,(unsigned long long)x->mapped,(unsigned long long)x->unmapped,
      (unsigned long long)x->generated,(unsigned long long)x->excluded,
      (unsigned long long)x->reason[0],(unsigned long long)x->reason[1],(unsigned long long)x->reason[2],
      (unsigned long long)x->reason[3],(unsigned long long)x->reason[4],(unsigned long long)x->reason[5],
      (unsigned long long)x->reason[6],(unsigned long long)x->reason[7],(unsigned long long)x->reason[99],
      wjcc_num(x->initialized?x->raw_min:NAN,a,sizeof(a)),(int)x->raw_min_face,(int)x->raw_min_local,
      wjcc_num(x->initialized?x->raw_max:NAN,b,sizeof(b)),(int)x->raw_max_face,(int)x->raw_max_local,
      wjcc_num(x->initialized?x->class_min:NAN,c,sizeof(c)),(int)x->class_min_face,(int)x->class_min_local,
      wjcc_num(x->initialized?x->class_max:NAN,d,sizeof(d)),(int)x->class_max_face,(int)x->class_max_local,
      wjcc_num(x->initialized?x->area_min:NAN,e,sizeof(e)),wjcc_num(x->initialized?x->area_max:NAN,f,sizeof(f)),
      wjcc_num(x->initialized?x->k_min:NAN,g,sizeof(g)),wjcc_num(x->initialized?x->k_max:NAN,h,sizeof(h)),
      wjcc_num(x->initialized?x->nmin[0]:NAN,i,sizeof(i)),wjcc_num(x->initialized?x->nmax[0]:NAN,j,sizeof(j)),
      wjcc_num(x->initialized?x->nmin[1]:NAN,k,sizeof(k)),wjcc_num(x->initialized?x->nmax[1]:NAN,l,sizeof(l)),
      wjcc_num(x->initialized?x->nmin[2]:NAN,m,sizeof(m)),wjcc_num(x->initialized?x->nmax[2]:NAN,n,sizeof(n)),
      (unsigned long long)x->law2,(unsigned long long)x->other_law,(unsigned long long)x->duplicates,
      (unsigned long long)x->digest,(unsigned long long)x->nonfinite);
  }
}
static void wjcc_emit_trial_summaries(void){
  ITG tie;char fx[32],fy[32],fz[32],af[32],energy[32],gmin[32],gmax[32];
  for(tie=1;tie<=wjcc_ntie;tie++){
    WJCCTrialStat *s=&wjcc_trial[tie];uint64_t expected=0;int p;
    for(p=1;p<=2;p++)if(p==wjcc_latest_pass[tie])expected=wjcc_map[tie][p].generated;
    if(!s->count&&!expected)continue;
    wjcc_emit(0,"TRIAL_SUMMARY\t%llu\t%d\t%d\t%d\t%d\t%d\t%llu\t%llu\t%llu\t%llu\t%llu\t%llu\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%llu\t%llu\t%llu\n",
      (unsigned long long)wjcc_generation,(int)wjcc_step,(int)wjcc_inc,(int)wjcc_attempt,(int)wjcc_iter,(int)tie,
      (unsigned long long)expected,(unsigned long long)s->count,(unsigned long long)s->unjoined,
      (unsigned long long)s->wrong_law,(unsigned long long)s->force_rows,(unsigned long long)s->energy_rows,
      (s->force_complete&&s->count)?wjcc_num(s->force[0],fx,sizeof(fx)):"NA",
      (s->force_complete&&s->count)?wjcc_num(s->force[1],fy,sizeof(fy)):"NA",
      (s->force_complete&&s->count)?wjcc_num(s->force[2],fz,sizeof(fz)):"NA",
      (s->force_complete&&s->count)?wjcc_num(s->abs_force,af,sizeof(af)):"NA",
      (s->energy_complete&&s->count)?wjcc_num(s->energy,energy,sizeof(energy)):"NA",
      (s->gap_initialized)?wjcc_num(s->gap_min,gmin,sizeof(gmin)):"NA",
      (s->gap_initialized)?wjcc_num(s->gap_max,gmax,sizeof(gmax)):"NA",
      (unsigned long long)s->positive_gap,(unsigned long long)(wjcc_nener==1),
      (unsigned long long)(s->count==expected));
    if(s->count!=expected||s->unjoined)wjcc_error=1;
  }
}
static void wjcc_emit_state_joins(void){
  ITG t;for(t=1;t<=wjcc_ntie;t++){
    WJCCJoinStat *s=&wjcc_join[t];
    wjcc_emit(0,"STATE_JOIN\t%llu\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%llu\t%llu\t%llu\t%llu\t%llu\t%llu\n",
      (unsigned long long)wjcc_generation,(int)wjcc_step,(int)wjcc_inc,(int)wjcc_attempt,(int)wjcc_iter,
      (int)t,(int)wjcc_prev_equal,(int)(wjcc_corr_iter+1==wjcc_iter),
      (unsigned long long)s->same,(unsigned long long)s->remapped,(unsigned long long)s->old_missing,
      (unsigned long long)s->new_missing,(unsigned long long)s->generated_to_excluded,
      (unsigned long long)s->excluded_to_generated);
  }
}
static void wjcc_join_previous(void){
  uint32_t *table=NULL;size_t a,slot;ITG t;
  int eligible=wjcc_prev_equal&&wjcc_corr_step==wjcc_step&&wjcc_corr_inc==wjcc_inc&&
    wjcc_corr_attempt==wjcc_attempt&&(wjcc_corr_iter+1==wjcc_iter);
  if(!eligible||!wjcc_previous_n)return;
  table=(uint32_t*)calloc(WJCC_KEY_CAP,sizeof(uint32_t));if(!table){wjcc_error=1;return;}
  for(a=0;a< wjcc_points_n;a++){
    WJCCPoint *p=&wjcc_points[a];uint64_t h;uint32_t idx;
    if(p->tie<1||p->tie>wjcc_ntie||p->pass!=wjcc_latest_pass[p->tie])continue;
    p->matched=0;
    h=wjcc_point_hash(p,0);slot=(size_t)(h&(WJCC_KEY_CAP-1));
    while((idx=table[slot])!=0){
      if(wjcc_key_equal(p,&wjcc_points[idx-1],0)){wjcc_error=1;break;}
      slot=(slot+1)&(WJCC_KEY_CAP-1);
    }
    if(!table[slot])table[slot]=(uint32_t)(a+1);
  }
  for(a=0;a<wjcc_previous_n;a++){
    WJCCPoint *old=&wjcc_previous[a],*cur=NULL;uint64_t h;uint32_t idx;
    if(old->tie<1||old->tie>wjcc_ntie||old->pass!=wjcc_prev_latest[old->tie])continue;
    h=wjcc_point_hash(old,0);slot=(size_t)(h&(WJCC_KEY_CAP-1));
    while((idx=table[slot])!=0){
      if(wjcc_key_equal(old,&wjcc_points[idx-1],0)){cur=&wjcc_points[idx-1];break;}
      slot=(slot+1)&(WJCC_KEY_CAP-1);
    }
    if(!cur){wjcc_join[old->tie].old_missing++;continue;}
    cur->matched=1;
    if(old->isol!=0&&cur->isol==0)wjcc_join[old->tie].generated_to_excluded++;
    if(old->isol==0&&cur->isol!=0)wjcc_join[old->tie].excluded_to_generated++;
    if(old->valid&&cur->valid&&old->master==cur->master&&old->law==cur->law&&
       memcmp(&old->rawgap,&cur->rawgap,sizeof(double))==0&&
       memcmp(&old->classgap,&cur->classgap,sizeof(double))==0&&
       memcmp(&old->initial,&cur->initial,sizeof(double))==0&&
       memcmp(&old->mxi,&cur->mxi,sizeof(double))==0&&memcmp(&old->meta,&cur->meta,sizeof(double))==0&&
       memcmp(&old->nx,&cur->nx,sizeof(double))==0&&memcmp(&old->ny,&cur->ny,sizeof(double))==0&&
       memcmp(&old->nz,&cur->nz,sizeof(double))==0&&memcmp(&old->area,&cur->area,sizeof(double))==0&&
       memcmp(&old->k,&cur->k,sizeof(double))==0&&memcmp(&old->kscale,&cur->kscale,sizeof(double))==0)
      wjcc_join[old->tie].same++;
    else wjcc_join[old->tie].remapped++;
  }
  for(a=0;a<wjcc_points_n;a++){
    WJCCPoint *cur=&wjcc_points[a];
    if(cur->tie<1||cur->tie>wjcc_ntie||cur->pass!=wjcc_latest_pass[cur->tie])continue;
    if(!cur->matched)wjcc_join[cur->tie].new_missing++;
  }
  free(table);
  for(t=1;t<=wjcc_ntie;t++){
    if(wjcc_join[t].same+wjcc_join[t].remapped+wjcc_join[t].old_missing==0&&
       wjcc_latest_pass[t]!=0)wjcc_error=1;
  }
}

void ccxcap_generation_begin_(ITG *step,ITG *inc,ITG *icutb,ITG *iter,
  ITG *nk,ITG *mt,double *vold,double *kscale,ITG *nener,ITG *ntie,ITG *nintpoint){
  size_t n;int finite=1;
  wjcc_open();if(wjcc_enabled!=1)return;
  if(wjcc_pending){wjcc_error=1;wjcc_pending=0;}
  if(wjcc_generation>=WJCC_MAX_SWEEPS){wjcc_overflow=1;return;}
  free(wjcc_previous);wjcc_previous=wjcc_points;wjcc_previous_n=wjcc_points_n;
  memset(wjcc_prev_latest,0,sizeof(wjcc_prev_latest));
  if(wjcc_previous)for(size_t z=0;z<wjcc_previous_n;z++)
    if(wjcc_previous[z].tie>0&&wjcc_previous[z].tie<=WJCC_MAX_TIES&&
       wjcc_previous[z].pass>wjcc_prev_latest[wjcc_previous[z].tie])
      wjcc_prev_latest[wjcc_previous[z].tie]=wjcc_previous[z].pass;
  wjcc_points=NULL;wjcc_points_n=wjcc_points_cap=0;
  free(wjcc_key_table);wjcc_key_table=(uint32_t*)calloc(WJCC_KEY_CAP,sizeof(uint32_t));
  free(wjcc_gauss_index);wjcc_gauss_index=NULL;wjcc_gauss_n=0;
  if(!wjcc_key_table){wjcc_error=1;return;}
  if(*ntie<1||*ntie>WJCC_MAX_TIES||*ntie!=wjcc_expected_ties||*nintpoint<0){wjcc_error=1;return;}
  wjcc_ntie=*ntie;wjcc_nintpoint=*nintpoint;wjcc_nener=*nener;wjcc_kscale=*kscale;
  if((size_t)(*nintpoint)+1>WJCC_MAX_POINTS*4u){wjcc_error=1;return;}
  wjcc_gauss_n=(size_t)(*nintpoint)+1;
  wjcc_gauss_index=(uint32_t*)calloc(wjcc_gauss_n,sizeof(uint32_t));
  if(!wjcc_gauss_index){wjcc_error=1;return;}
  wjcc_generation++;wjcc_step=*step;wjcc_inc=*inc;wjcc_attempt=*icutb+1;wjcc_iter=*iter;
  wjcc_map_complete=wjcc_trial_complete=0;wjcc_pending=1;wjcc_reset_stats();
  n=(size_t)(*nk)*(size_t)(*mt);
  if(n>WJCC_MAX_STATE_DOUBLES){wjcc_overflow=1;return;}
  if(n!=wjcc_state_n){double *p=(double*)realloc(wjcc_state,n*sizeof(double));if(!p&&n){wjcc_error=1;return;}wjcc_state=p;wjcc_state_n=n;}
  if(n)memcpy(wjcc_state,vold,n*sizeof(double));
  wjcc_state_finite=1;wjcc_state_token=wjcc_state_hash(wjcc_state,n,&wjcc_state_finite);
  wjcc_prev_equal=0;
  if(wjcc_corrected&&n==wjcc_corrected_n&&wjcc_corr_step==*step&&wjcc_corr_inc==*inc&&wjcc_corr_attempt==*icutb+1){
    wjcc_prev_equal=(memcmp(wjcc_state,wjcc_corrected,n*sizeof(double))==0);
  }
  wjcc_emit(0,"GEN_BEGIN\t%llu\t%d\t%d\t%d\t%d\t%d\t%llu\t%zu\t%d\t%016llx\t%d\t%d\t%016llx\n",
    (unsigned long long)wjcc_generation,(int)*step,(int)*inc,(int)(*icutb+1),(int)*iter,
    (int)*nintpoint,(unsigned long long)wjcc_previous_n,n,(int)wjcc_corr_iter,
    (unsigned long long)wjcc_state_token,wjcc_state_finite,wjcc_prev_equal,
    (unsigned long long)wjcc_corrected_token);
}

void ccxcap_face_(ITG *tie,ITG *pass,ITG *ordinal,ITG *face,ITG *start,ITG *end,ITG *status){
  ITG span=*end-*start;uint64_t h;
  if(wjcc_enabled!=1)return;
  if(*tie<1||*tie>wjcc_ntie||*pass<1||*pass>2||*ordinal<1||span<0||*status<0||*status>1){wjcc_error=1;return;}
  if(!wjcc_offset_initialized[*pass]){wjcc_offset_initialized[*pass]=1;wjcc_offset_base[*pass]=*start;wjcc_offset_next[*pass]=*start;}
  if(*start!=wjcc_offset_next[*pass])wjcc_error=1;
  wjcc_offset_next[*pass]=*end;
  wjcc_pass_faces[*tie][*pass]++;wjcc_pass_spans[*tie][*pass]+=(uint64_t)span;
  wjcc_map[*tie][*pass].faces++;wjcc_map[*tie][*pass].span+=(uint64_t)span;
  if(span==0)wjcc_map[*tie][*pass].zero_faces++;
  wjcc_face_rows++;wjcc_run_faces++;
  h=wjcc_fnv(tie,sizeof(*tie),wjcc_face_hash);h=wjcc_fnv(pass,sizeof(*pass),h);
  h=wjcc_fnv(ordinal,sizeof(*ordinal),h);h=wjcc_fnv(face,sizeof(*face),h);
  h=wjcc_fnv(start,sizeof(*start),h);h=wjcc_fnv(end,sizeof(*end),h);h=wjcc_fnv(status,sizeof(*status),h);wjcc_face_hash=h;
  wjcc_emit(0,"FACE\t%llu\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\n",
    (unsigned long long)wjcc_generation,(int)*tie,(int)*pass,(int)*ordinal,(int)*face,
    (int)*start,(int)*end,(int)span,(int)*status);
}

void ccxcap_point_(ITG *tie,ITG *pass,ITG *faceord,ITG *face,ITG *local,
  ITG *igauss,ITG *valid,ITG *reason,ITG *master,ITG *law,ITG *isol,
  double *raw,double *classgap,double *area,double *penalty,double *initial,
  double *nx,double *ny,double *nz,double *sxi,double *seta,double *mxi,
  double *meta,double *px,double *py,double *pz){
  WJCCPoint p;memset(&p,0,sizeof(p));
  if(wjcc_enabled!=1)return;
  p.tie=*tie;p.pass=*pass;p.faceord=*faceord;p.face=*face;p.local=*local;p.igauss=*igauss;
  p.valid=*valid;p.reason=*reason;p.master=*master;p.law=*law;p.isol=*isol;
  p.rawgap=*raw;p.classgap=*classgap;p.area=*area;p.k=*penalty;p.initial=*initial;
  p.nx=*nx;p.ny=*ny;p.nz=*nz;p.sxi=*sxi;p.seta=*seta;p.mxi=*mxi;p.meta=*meta;
  p.px=*px;p.py=*py;p.pz=*pz;p.kscale=wjcc_kscale;
  wjcc_point_append(&p);
}

void ccxcap_generation_end_(void){
  ITG t,p;uint64_t totalspan=0;ITG totalfaces=0;
  if(wjcc_enabled!=1||!wjcc_pending)return;
  for(p=1;p<=2;p++)if(wjcc_offset_initialized[p]){
    uint64_t span=0;ITG faces=0;
    for(t=1;t<=wjcc_ntie;t++){span+=wjcc_pass_spans[t][p];faces+=wjcc_pass_faces[t][p];}
    totalspan+=span;totalfaces+=faces;
    if(span!=(uint64_t)wjcc_nintpoint||
       (uint64_t)(wjcc_offset_next[p]-wjcc_offset_base[p])!=span||
       faces!=wjcc_expected_faces)wjcc_error=1;
  }
  if(!wjcc_offset_initialized[1]||
     !wjcc_offset_initialized[2]||
     (totalfaces==0&&wjcc_expected_faces!=0))wjcc_error=1;
  for(t=1;t<=wjcc_ntie;t++)for(p=1;p<=2;p++)
    if(wjcc_map[t][p].candidates!=wjcc_pass_spans[t][p])wjcc_error=1;
  wjcc_join_previous();wjcc_emit_map_summaries();wjcc_emit_state_joins();
  wjcc_map_complete=(totalfaces>0||wjcc_nintpoint==0)&&!wjcc_error&&!wjcc_overflow;
  wjcc_emit(0,"GEN_END\t%llu\t%llu\t%llu\t%llu\t%d\t%d\t%016llx\t%016llx\t%d\n",
    (unsigned long long)wjcc_generation,(unsigned long long)wjcc_face_rows,
    (unsigned long long)wjcc_point_rows,(unsigned long long)wjcc_nintpoint,
    (int)totalfaces,(int)totalspan,(unsigned long long)wjcc_face_hash,
    (unsigned long long)wjcc_outcome_hash,wjcc_map_complete);
  fflush(wjcc_fp);
}

static WJCCPoint *wjcc_find_point(ITG igauss,ITG tie,ITG face){
  uint32_t ix;if(igauss<=0||(size_t)igauss>=wjcc_gauss_n||tie<=0||tie>WJCC_MAX_TIES)return NULL;
  ix=wjcc_gauss_index?wjcc_gauss_index[igauss]:0;
  if(!ix||ix>wjcc_points_n)return NULL;
  if(wjcc_points[ix-1].tie!=tie||wjcc_points[ix-1].face!=face)return NULL;
  return &wjcc_points[ix-1];
}
void ccxcap_trial_(ITG *element,ITG *igauss,ITG *face,ITG *tie,ITG *energy_enabled,
  double *gap,double *t1,double *t2,double *pressure,double *s1,double *s2,
  double *area,double *energy,double *nx,double *ny,double *nz,double *kscale,double *reltime){
  WJCCPoint *p=wjcc_find_point(*igauss,*tie,*face);WJCCTrialStat *s;
  double fx,fy,fz;int finite_force;
  (void)element;(void)t1;(void)t2;(void)s1;(void)s2;(void)reltime;
  if(wjcc_enabled!=1)return;
  if(*tie<1||*tie>WJCC_MAX_TIES){wjcc_error=1;return;}
  s=&wjcc_trial[*tie];s->count++;wjcc_trial_rows++;wjcc_run_trials++;
  if(!s->gap_initialized){s->gap_min=s->gap_max=*gap;s->gap_initialized=1;}
  if(isfinite(*gap)){if(*gap<s->gap_min)s->gap_min=*gap;if(*gap>s->gap_max)s->gap_max=*gap;if(*gap>0.)s->positive_gap++;}else wjcc_error=1;
  if(!p){s->unjoined++;s->force_complete=0;s->energy_complete=0;return;}
  if(p->trial_seen){wjcc_error=1;s->force_complete=0;s->energy_complete=0;return;}
  p->trial_seen=1;p->trialgap=*gap;p->pressure=*pressure;p->energy=*energy;p->energy_enabled=*energy_enabled;
  finite_force=isfinite(*area)&&isfinite(*pressure)&&isfinite(*nx)&&isfinite(*ny)&&isfinite(*nz)&&isfinite(*kscale)&&*kscale!=0.;
  if(p->law!=2||!finite_force){s->wrong_law++;s->force_complete=0;s->energy_complete=0;return;}
  fx=-(*area)*(*pressure)*(*nx);fy=-(*area)*(*pressure)*(*ny);fz=-(*area)*(*pressure)*(*nz);
  if(!isfinite(fx)||!isfinite(fy)||!isfinite(fz)){s->force_complete=0;wjcc_error=1;return;}
  s->force[0]+=fx;s->force[1]+=fy;s->force[2]+=fz;
  s->abs_force+=sqrt(fx*fx+fy*fy+fz*fz);s->force_rows++;
  if(*energy_enabled==1&&isfinite(*energy)){s->energy+=*energy;s->energy_rows++;}
  else s->energy_complete=0;
}
void ccxcap_trial_end_(void){
  ITG t;if(wjcc_enabled!=1)return;
  for(t=1;t<=wjcc_ntie;t++){
    WJCCTrialStat *s=&wjcc_trial[t];s->force_complete=(s->unjoined==0&&s->wrong_law==0&&s->force_rows==s->count);
    s->energy_complete=(s->unjoined==0&&s->wrong_law==0&&s->energy_rows==s->count&&wjcc_nener==1);
  }
  wjcc_emit_trial_summaries();wjcc_trial_complete=!wjcc_error&&!wjcc_overflow;
}

void ccxcap_corrected_(ITG *step,ITG *inc,ITG *icutb,ITG *iter,ITG *nk,ITG *mt,double *vold){
  size_t n=(size_t)(*nk)*(size_t)(*mt);
  if(wjcc_enabled!=1)return;
  if(n>WJCC_MAX_STATE_DOUBLES){wjcc_overflow=1;return;}
  if(n!=wjcc_corrected_n){double *p=(double*)realloc(wjcc_corrected,n*sizeof(double));if(!p&&n){wjcc_error=1;return;}wjcc_corrected=p;wjcc_corrected_n=n;}
  if(n)memcpy(wjcc_corrected,vold,n*sizeof(double));
  wjcc_corrected_finite=1;wjcc_corrected_token=wjcc_state_hash(wjcc_corrected,n,&wjcc_corrected_finite);
  wjcc_corr_step=*step;wjcc_corr_inc=*inc;wjcc_corr_attempt=*icutb+1;wjcc_corr_iter=*iter;
  wjcc_emit(0,"STATE_CORRECTED\t%llu\t%d\t%d\t%d\t%d\t%016llx\t%d\n",
    (unsigned long long)wjcc_generation,(int)*step,(int)*inc,(int)(*icutb+1),(int)*iter,
    (unsigned long long)wjcc_corrected_token,wjcc_corrected_finite);
}

void ccxcap_iteration_link_(ITG *step,ITG *inc,ITG *icutb,ITG *iter,ITG *icntrl,double *ttime,double *time){
  int identity=wjcc_pending&&wjcc_step==*step&&wjcc_inc==*inc&&wjcc_iter==*iter;
  int accepted=((*icntrl!=0)&&(*icutb==0));
  if(wjcc_enabled!=1||!identity)return;
  wjcc_emit(0,"ITERATION_LINK\t%llu\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%.17g\t%016llx\t%d\t%d\n",
    (unsigned long long)wjcc_generation,(int)*step,(int)*inc,(int)wjcc_attempt,
    (int)*iter,(int)(*icutb+1),(int)*icntrl,accepted?1:0,*ttime+*time,
    (unsigned long long)wjcc_corrected_token,wjcc_map_complete,wjcc_trial_complete);
  wjcc_run_links++;wjcc_pending=0;
}
void ccxcap_missing_pair_(void){if(wjcc_enabled==1)wjcc_error=1;}
void ccxcap_finish_(void){
  if(wjcc_closed||wjcc_enabled!=1)return;
  wjcc_emit(1,"RUN_END\t%llu\t%llu\t%llu\t%llu\t%llu\t%llu\t%d\t%d\t%d\n",
    (unsigned long long)wjcc_generation,(unsigned long long)wjcc_run_faces,
    (unsigned long long)wjcc_run_points,(unsigned long long)wjcc_run_trials,
    (unsigned long long)wjcc_run_links,(unsigned long long)wjcc_bytes,
    wjcc_overflow,wjcc_error,(!wjcc_overflow&&!wjcc_error&&!wjcc_pending));
  if(wjcc_fp){fflush(wjcc_fp);fclose(wjcc_fp);wjcc_fp=NULL;}wjcc_closed=1;
  free(wjcc_points);free(wjcc_previous);free(wjcc_key_table);free(wjcc_gauss_index);
  free(wjcc_state);free(wjcc_corrected);
  wjcc_points=wjcc_previous=NULL;wjcc_key_table=wjcc_gauss_index=NULL;
  wjcc_state=wjcc_corrected=NULL;
  wjcc_points_n=wjcc_points_cap=wjcc_previous_n=0;
  wjcc_state_n=0;wjcc_corrected_n=0;wjcc_gauss_n=0;
  wjcc_enabled=0;
}
