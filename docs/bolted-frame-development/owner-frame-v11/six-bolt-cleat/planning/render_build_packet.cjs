// Run with Bun and an existing Playwright installation; no CAD or structural evaluation.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const {pathToFileURL}=require('node:url'),{spawnSync}=require('node:child_process');
const here=__dirname,root=process.cwd();
const sha=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const ref=p=>({path:path.relative(root,p),sha256:sha(p)});
const esc=s=>String(s).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;');
const csv=p=>{const r=spawnSync('python3',['-c','import csv,json,sys; print(json.dumps(list(csv.DictReader(open(sys.argv[1])))))',p],{encoding:'utf8'});if(r.status!==0)throw new Error(r.stderr);return JSON.parse(r.stdout);};
(async()=>{
 if(!globalThis.Bun?.markdown?.html||!process.argv[2])throw new Error('Use: bun render_build_packet.cjs /path/to/node_modules/playwright');
 const guide=path.join(here,'build-guide.md'),parts=path.join(here,'part-reference-sheets.html');
 const original=fs.readFileSync(parts,'utf8'),body=original.match(/<body>([\s\S]*)<\/body>/)[1].replace(/<footer>[\s\S]*?<\/footer>/,'');
 const meta=JSON.parse(original.match(/<script type="application\/json" id="part-reference-metadata">([\s\S]*?)<\/script>/)[1]);
 const styles=[...original.matchAll(/<style>([\s\S]*?)<\/style>/g)].map(x=>x[1]).join('\n');
 const repo='https://github.com/mckayreedmoore/mini-moonboard/blob/master/'+path.relative(root,here).replaceAll(path.sep,'/')+'/';
 const links=html=>html.replace(/href="([^"]+)"/g,(all,url)=>url.startsWith('#')?all:'href="'+esc(new URL(url.replaceAll('&amp;','&'),repo).href)+'"');
 let content=links(Bun.markdown.html(fs.readFileSync(guide,'utf8')));
 const stockPath=path.resolve(here,'../../shorter-bolts/build-package/geometry-packet/stock-allocation.csv');
 const stock=csv(stockPath);if(stock.length!==13)throw new Error('Expected13stock boards');
 content+='<section class="part"><h1>Board allocation</h1><p>Twenty timber pieces on thirteen boards. Allowances retain 25.4 mm trim at each end and 3.175 mm kerf per member. Listed finished grain envelopes are layout references, not automatic square-blank lengths or a saw-cut order.</p><table><thead><tr><th>Board</th><th>Stock / feet</th><th>Assigned members</th><th>Finished grain envelopes (mm)</th><th>Remaining nominal stock (mm)</th></tr></thead><tbody>'+stock.map(r=>'<tr><td>'+esc(r.board_id)+'</td><td>'+esc(r.nominal_stock)+' / '+esc(r.nominal_length_ft)+'</td><td>'+esc(r.member_ids.replaceAll(';',', '))+'</td><td>'+esc(r.CURRENT_finished_grain_envelopes_mm_json)+'</td><td>'+Number(r.remaining_nominal_length_mm).toFixed(1)+'</td></tr>').join('')+'</tbody></table></section>';
 const axisPath=path.join(here,'hardware-axis-crosswalk.csv'),axes=csv(axisPath);if(axes.length!==102)throw new Error('Expected102bolt axes');
 content+='<section class="part"><h1>Bolt installation schedule</h1><p>One bolt, one matching nut and two specified washers per axis; zero spacers. All bolts retain the Grade 5 partial-thread basis. Special 6/6½-inch rows require the profile check in the guide. Foot and ordinary washer families have different thickness windows.</p><table><thead><tr><th>Axis</th><th>Thread × nominal length (in)</th><th>Bolt SKU / type</th><th>Nut SKU</th><th>Both washers (mm thickness)</th><th>Head / nut faces</th></tr></thead><tbody>'+axes.map(r=>{const half=Number(r.bolt_nominal_diameter_mm)>10,foot=/^rail_(front|rear)_bolt_/.test(r.axis_id),wash=half?'15025:2.85–3.175':foot?'15023:1.6256–2.032':'15023:2.35–2.6416';return '<tr><td>'+esc(r.axis_id)+'</td><td>'+esc(r.nominal_thread)+' × '+(Number(r.nominal_underhead_length_mm)/25.4).toFixed(2)+'</td><td>'+esc(r.bolt_sku||'Special partial-thread HCS')+'</td><td>'+esc(r.nut_sku)+'</td><td>'+wash+'</td><td>'+esc(r.head_faces)+' / '+esc(r.nut_faces)+'</td></tr>';}).join('')+'</tbody></table></section>';
 content+='<hr><h1 id="part-sheets">Dimensioned part references</h1>'+links(body);
 const openings=path.join(here,'panel-opening-layout.csv');
 if(fs.existsSync(openings)){
  const rows=csv(openings);if(rows.length!==274)throw new Error('Expected142T-nut+132LED openings');
  content+='<section class="part"><h1>Hold and LED opening schedule</h1><p>Front/climbing-face measurements; retain each panel’s TOP/DOWN or BOTTOM/UP datum. These274 openings are separate from the66 panel/kicker attachment screws. The current panel widths and fixed world-grid centers govern.</p>';
  for(const panel of [...new Set(rows.map(r=>r.panel))]){
   const group=rows.filter(r=>r.panel===panel),fields=['label','kind','diameter_mm','from_left_mm','from_datum_edge_mm','layout_note'];
   content+='<h2>'+esc(panel)+'</h2><p>'+esc(group[0].current_panel_width_mm)+' × '+esc(group[0].current_panel_height_mm)+' mm; datum '+esc(group[0].datum_edge)+' / '+esc(group[0].measurement_direction)+'. Offsets are from the front-view left and the stated datum edge.</p><table><thead><tr>'+fields.map(k=>'<th>'+esc(k.replaceAll('_',' '))+'</th>').join('')+'</tr></thead><tbody>'+group.map(r=>'<tr>'+fields.map(k=>'<td>'+esc(k==='layout_note'&&r[k]?'Existing G2 +5 mm move':r[k])+'</td>').join('')+'</tr>').join('')+'</tbody></table>';
  }
  content+='</section>';
 }
 const html=path.join(here,'build-packet.html'),pdf=path.join(here,'build-packet.pdf');
 const extra='@media print{body{font-size:11px}table{font-size:10px}h1,h2,h3{break-after:avoid}thead{display:table-header-group}.part{break-before:page}a{color:inherit;text-decoration:none}}';
 fs.writeFileSync(html,'<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Fixed 102-bolt Mini MoonBoard build packet</title><style>'+styles+extra+'</style></head><body>'+content+'</body></html>');
 const {chromium}=require(process.argv[2]),browser=await chromium.launch({headless:true,args:['--no-sandbox']});
 let browserVersion;
 try{
  browserVersion=browser.version();const page=await browser.newPage({viewport:{width:1100,height:900}});
  await page.goto(pathToFileURL(html).href,{waitUntil:'networkidle'});
  const payload=await page.pdf({path:pdf,preferCSSPageSize:true,printBackground:true,displayHeaderFooter:true,headerTemplate:'<div></div>',footerTemplate:'<div style="font:8px Arial;width:100%;text-align:center">Fixed 102-bolt design · dimensions govern · <span class="pageNumber"></span> / <span class="totalPages"></span></div>'});
  const pages=(payload.toString('latin1').match(/\/Type\s*\/Page\b/g)||[]).length;if(pages<31)throw new Error('Incomplete PDF page census');
  await page.screenshot({path:'/tmp/mini-moonboard-build-guide.png'});
  for(const id of ['lumber_leg_left','base_post_outer_left','base_side_left','main_lower_right'])await page.locator('#'+id).screenshot({path:'/tmp/mini-moonboard-'+id+'.png'});
  const inputs=[guide,parts,__filename,stockPath,axisPath,...['cut-list.csv','screw-layout.csv','service-passage-layout.csv','produce_part_reference_sheets.py','produce_panel_opening_layout.py'].map(p=>path.join(here,p))];if(fs.existsSync(openings))inputs.push(openings);
  const artifacts=[html,pdf];
  fs.writeFileSync(path.join(here,'build-packet-manifest.json'),JSON.stringify({schema:'fixed102_build_packet/v1',revision:'v11-six-bolt-cleat-v1',source_files:inputs.map(ref),part_reference_metadata:meta,artifacts:artifacts.map(p=>({...ref(p),bytes:fs.statSync(p).size})),PDF_pages:pages,renderer:{Bun:Bun.version,Playwright:require(path.join(process.argv[2],'package.json')).version,Chromium:browserVersion},counts:{part_cards:30,timbers:20,cleat_leaves:4,face_panels_and_kickers:6,stock_boards:13,bolt_axes:102,receiver_references:136,panel_screw_axes:66,timber_service_bores:32,hold_openings:142,LED_openings:132},geometry_hardware_or_structural_results_changed:false,actual_observations_supplied:false,structural_acceptance:false},null,2)+'\n');
  console.log(JSON.stringify({html:ref(html),pdf:ref(pdf),pages,bytes:payload.length}));
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
