import {loadV11ResultsScene,V11_RESULTS_ASSET} from './eoere-v11-results.mjs';
import {V11_MODEL} from './eoere-v11-v9-eight-bolt-overlay.mjs';
import {sha256} from './wood-joints-overlay.mjs';

export const V11_RESULTS_V2_ASSET=Object.freeze({path:'site/eoere-v11-results-v2.json',sha256:'53ff172e2607f41eeeabf85519b88ecbaf1beb53bfcc642735e2b48a94f1eb48'});
const require=(ok,message)=>{if(!ok)throw new Error('V11 method update: '+message);};
const STANDARD='f04eeb1c3b4cb166f92befc77f1c7515d2e8b5800f0a289cb9d13702de404801';
const CRITERION='f71c425ab7aa795183329cc6782924e3f1ee8e28aa644f4ffac2fd27c0e18001';
const PREFIX='docs/bolted-frame-development/owner-frame-v11/';

export function validateV11ResultsV2(data){
  require(data.schema==='eoere_v11_viewer_results/v2'&&data.model===V11_MODEL&&data.base_results?.path===V11_RESULTS_ASSET.path&&
    data.base_results.sha256===V11_RESULTS_ASSET.sha256&&data.geometry_sha256==='befcf54de15984fcf05c5ede053d622afb249c0c2279f291ae65f06763b542a7'&&
    data.response_bank?.sha256==='482d8e5cf5eec0566a7eb637666137350cbf90f1674f909241c78a103f615963','exact own preceding results and unchanged forces required');
  require(data.standard_cg_source?.path===PREFIX+'standard-cg-comparison.json'&&data.standard_cg_source.sha256===STANDARD&&
    data.criterion_source?.path===PREFIX+'criterion-followthrough.json'&&data.criterion_source.sha256===CRITERION,'own current public method sources required');
  const c=data.standard_cg,b=data.preserved_raw_port_bounds,m=data.mixed_plane_references;
  require(c?.aggregate_directional_index===.8420030182968952&&c.aggregate_directional_flags===0&&
    c.individual_over_Cg_index===.8420030182968952&&c.individual_over_Cg_flags===0&&
    c.Fe90_net_floor_index===1.2563600548088276&&c.Fe90_net_floor_flags===5&&
    c.fixed_row_and_area_hypotheses_only===true&&c.actual_Cg_selected===false,'gross-area hypotheses and net-floor flags must remain distinct');
  require(b?.index_upper===2.2080838963062854&&b.inconclusive_flags===21&&b.conservative_inconclusive_not_new_method_failures===true&&
    b.source?.sha256==='a61f5592607b972b734b753b53971cb845a174c3b28cf1008232a5f3d1072f88','conservative raw-port history cannot become definitive method failures');
  require(m?.axes===24&&m.plywood_sawn_plane_references===96&&m.steel_wood_plane_references===192&&
    m.plywood_sawn_maximum===.4553824157450979&&m.steel_wood_maximum===.24327762351357893&&
    m.above_one===0&&m.complete_capacity_qualified===false,'plane references do not establish complete mixed capacity');
  require(data.actual_Cg_adopted===null&&data.actual_Cdelta_adopted===null&&data.complete_connection_capacity===null,'actual factors and full capacity remain unresolved');
  for(const key of['complete_joint_qualified','structural_acceptance','fabrication_released','climbing_released'])require(data[key]===false,'no qualification/release transfer: '+key);
  return data;
}

export function applyV11ResultsV2(scene,input){
  const data=validateV11ResultsV2(input),old='Fresh 92 ksi row-bound maximum 2.208084: 21 bounds across 10 interfaces remain inconclusive.';
  require(scene.design?.key===V11_MODEL&&scene.parts?.length===1109&&scene.meta?.active_results_record?.sha256===V11_RESULTS_ASSET.sha256&&
    scene.meta.status.includes(old),'the preserved own V1 presentation must supply this frame');
  const status=scene.meta.status.replace(old,
    'Standard Cg under fixed gross/equivalent-area row hypotheses: aggregate and individual/Cg maxima 0.842003, zero flags. '+
    'Fe90 net-lateral floor maximum 1.256360, five flags. Prior raw-port bound 2.208084 and 21 flags remain conservative and inconclusive.').replace(
    '24 mixed axes and complete connections remain unresolved.',
    'Current 24 mixed axes have zero plane references above one; full mixed capacities and complete connections remain unresolved.');
  const parts=scene.parts.map(part=>part.fabrication?.unsupported_mixed_capacity?{...part,fabrication:{...part.fabrication,
    analysis_reference:'Mixed-media axis: current conditional plane references are recorded separately. Full mixed/group/axial/couple capacity remains unsupported; no complete joint pass is assigned.'}}:part);
  return {...scene,parts,meta:{...scene.meta,status,active_method_update:V11_RESULTS_V2_ASSET,standard_cg:data.standard_cg,
    preserved_raw_port_bounds:data.preserved_raw_port_bounds,mixed_plane_references:data.mixed_plane_references,
    portable_sources:{...scene.meta.portable_sources,standard_cg:data.standard_cg_source,criterion_followthrough:data.criterion_source}}};
}

export async function loadV11ResultsSceneV2(THREE,options,previousLoader=loadV11ResultsScene){
  const response=await fetch(new URL('eoere-v11-results-v2.json',import.meta.url));require(response.ok,'current method update unavailable');
  const raw=await response.arrayBuffer();require(await sha256(raw)===V11_RESULTS_V2_ASSET.sha256,'current method update bytes changed');
  const data=validateV11ResultsV2(JSON.parse(new TextDecoder().decode(raw)));
  return applyV11ResultsV2(await previousLoader(THREE,options),data);
}
