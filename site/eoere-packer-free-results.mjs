import {loadPackerFreeScene, PACKER_FREE_MODEL, PACKER_FREE_REVISION, PACKER_FREE_ASSETS} from './eoere-packer-free-overlay.mjs';
import {sha256} from './wood-joints-overlay.mjs';

export const PACKER_FREE_RESULTS_ASSET = Object.freeze({path:'site/eoere-packer-free-results.json',
  sha256:'5b78a854d61d0e15dd7ddf84cb7c8b70e052443c4e79571d429158e970d1b6fc'});
export const PACKER_FREE_RESULTS_STATUS = 'Packer-free standard 4×6 frame · own six-case references available; complete connections unresolved. Declared conditional vector section references: left 0.914625, right 0.872071, top 0.613288, header 0.577484. Fifteen bearing diagnostic rows remain across eight components. Actual Cg/Cdelta and complete capacity remain unqualified. No fabrication or climbing release.';
const GEOMETRY = '9510653b41d2c0c710f4eea02c9867c44367cd2909d6b3af56716c74cfd68bde';
const RECEIPT = '73b097d9bcc364748ca08f897fca38cc2bdb7869cc04586e6706afb9b9d3d527';
const PREFIX = 'docs/bolted-frame-development/owner-frame-v10/packer-free/';
const EVALUATION = '41863a95230b64a67f3b8aeffd6874fcf75cb81891b4872459d0bd7bb87f4017';
const BANK = '976ee8d8ac593f978edf03d9eda028755751fd69b540fb8a01cdd073a242bdc3';
const ANALYSIS = 'fea/generated/v10-packer-free-v1/mechanics/analysis-v2/';
const CASES = ['a12-forward','a12-left','a12-rear','k12-right','k12-rear','a1-rear'];
const COUNTS = {Hillman_axes:66,angles:24,bolt_stacks:112,occupied_parts:1125,panels:6,plywood_cleats:4,sawn_members:20,spacer_pieces:40};
const LOAD = {accessory_mass_kg:25,downward_multiplier:2,duration_factor_CD:1,horizontal_force_N:300,weight_lb:250};
const FALSE_FLAGS = ['packers_present','historical_capacity_transferred','structural_acceptance','complete_joint_qualified',
  'complete_group_qualified','top_grid_qualified','physical_force_bounds_established','fabrication_released','climbing_released',
  'purchase_authorized','physical_changes_authorized','current_alias_promoted'];
const VECTOR = {base_side_left:[0.914624720328145,'a12-rear'],base_side_right:[0.8720708111274862,'k12-rear'],
  base_rail_top:[0.613287979767963,'k12-rear'],base_header:[0.5774844308125574,'a12-rear']};
const require = (ok,message) => {if (!ok) throw new Error('Packer-free results: '+message);};
const same = (actual,expected) => actual && Object.keys(actual).length === Object.keys(expected).length &&
  Object.entries(expected).every(([key,value]) => actual[key] === value);

export function validatePackerFreeResults(data) {
  require(data.schema === 'eoere_packer_free_viewer_results/v1' && data.model === PACKER_FREE_MODEL && data.geometry_revision === PACKER_FREE_REVISION &&
    data.geometry_sha256 === GEOMETRY && data.geometry_receipt?.path === PREFIX+'geometry-receipt.json' && data.geometry_receipt.sha256 === RECEIPT &&
    data.geometry_provenance?.path === 'site/eoere-packer-free-provenance.json' && data.geometry_provenance.sha256 === PACKER_FREE_ASSETS.provenanceSha256 &&
    same(data.counts,COUNTS), 'own physical geometry and unchanged inventory required');
  require(data.sources?.evaluation?.path === PREFIX+'evaluation.json' && data.sources.evaluation.sha256 === EVALUATION &&
    data.sources.response_bank?.path === PREFIX+'response-bank.json' && data.sources.response_bank.sha256 === BANK &&
    data.analysis_geometry?.path === ANALYSIS+'geometry/geometry.json' &&
    data.analysis_geometry.sha256 === 'f187592684eab07c0c17cbf8e835452cb5ebf431510ce8aa8ffe38940807da21', 'own assessment/bank/analysis bindings required');
  require(same(data.load_contract,LOAD) && data.admission_gate_N === 1e-5 && data.all_six_cases_and_both_replays_admitted === true &&
    Array.isArray(data.cases) && data.cases.length === 6 && new Set(data.cases.map(row => row.case_id)).size === 6 &&
    CASES.every(id => data.cases.some(row => row.case_id === id)), 'six cases and unchanged load/admission contract required');
  const hashes = [];
  for (const row of data.cases) {
    require(row.both_independent_replays_admitted === true && Number.isFinite(row.gradient_inf_N) && row.gradient_inf_N >= 0 &&
      row.gradient_inf_N <= 1e-5, 'finite admitted residual and both independent replays required');
    for (const [key,file] of [['field','field.json'],['independent_replay','independent-replay.json'],['independent_plywood_replay','independent-replay-plywood.json']]) {
      require(row[key]?.path === ANALYSIS+'four-hosts/'+row.case_id+'/'+file && /^[a-f0-9]{64}$/.test(row[key].sha256 || ''), 'own case/field/replay join required');
      hashes.push(row[key].sha256);
    }
  }
  require(new Set(hashes).size === 18 && data.maximum_gradient_inf_N === 8.79750916604749e-6 &&
    data.maximum_gradient_inf_N === Math.max(...data.cases.map(row => row.gradient_inf_N)), 'distinct fields/replays and own maximum required');
  require(data.declared_vector_references && Object.keys(data.declared_vector_references).length === 4, 'four conditional member references required');
  for (const [component,[index,caseId]] of Object.entries(VECTOR)) {
    const row = data.declared_vector_references[component];
    require(row?.component === component && row.case_id === caseId && row.index === index &&
      row.metric === 'maximum_shear_torsion_reference_upper', 'own declared conditional vector reference differs: '+component);
  }
  require(data.bearing_diagnostic_case_rows === 15 && data.bearing_diagnostic_components === 8 && data.actual_Cg_adopted === null &&
    data.actual_Cdelta_adopted === null && data.complete_connection_capacity === null && data.geometry_only === false &&
    data.matched_results_pending === false && data.current_response_computed === true && data.current_own_response_bank_recorded === true &&
    data.status === PACKER_FREE_RESULTS_STATUS, 'available references and unresolved complete capacity required');
  for (const key of FALSE_FLAGS) require(data[key] === false, 'qualification/release boundary: '+key);
  return data;
}

export function applyPackerFreeResults(scene,input) {
  const data = validatePackerFreeResults(input);
  require(scene.design?.key === PACKER_FREE_MODEL && scene.parts?.length === 1125 && scene.meta?.geometry_sha256 === GEOMETRY &&
    scene.meta.layout_sha256 === RECEIPT && scene.meta.provenance_sha256 === PACKER_FREE_ASSETS.provenanceSha256 &&
    scene.meta.matched_results_pending === true && scene.meta.current_own_response_bank_recorded === false,
  'the unchanged geometry-only loader must supply this frame');
  const parts = scene.parts.map(part => part.fabrication?.description ? {...part,fabrication:{...part.fabrication,
    description:part.fabrication.description.replace('Matched geometry-specific results pending.',
      'Own six-case conditional references recorded; complete connections unresolved.')}} : part);
  return {...scene,parts,design:{...scene.design,documents:[...scene.design.documents,
    {label:'Own six-case conditional assessment',path:data.sources.evaluation.path}]},
    meta:{...scene.meta,status:data.status,geometry_only:false,matched_results_pending:false,current_response_computed:true,
      current_own_response_bank_recorded:true,active_results_record:PACKER_FREE_RESULTS_ASSET,
      load_contract:data.load_contract,case_rows:data.cases,maximum_gradient_inf_N:data.maximum_gradient_inf_N,
      declared_vector_references:data.declared_vector_references,diagnostic_case_rows:15,diagnostic_components:8,
      actual_Cg_adopted:null,actual_Cdelta_adopted:null,complete_connection_capacity:null,
      ...Object.fromEntries(FALSE_FLAGS.map(key => [key,false])),
      portable_sources:{...scene.meta.portable_sources,...data.sources}}};
}

export async function loadPackerFreeResultsScene(THREE,options,geometryLoader = loadPackerFreeScene) {
  const response = await fetch(new URL('eoere-packer-free-results.json',import.meta.url));
  require(response.ok,'own results presentation unavailable');
  const raw = await response.arrayBuffer();
  require(await sha256(raw) === PACKER_FREE_RESULTS_ASSET.sha256,'own results presentation bytes changed');
  const data = validatePackerFreeResults(JSON.parse(new TextDecoder().decode(raw)));
  return applyPackerFreeResults(await geometryLoader(THREE,options),data);
}
