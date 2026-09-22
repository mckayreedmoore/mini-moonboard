// Owner-review barrel-nut visualization. Colors indicate layout status, never strength.

export function validateOwnerBarrelScene(data, hiddenNames) {
  const inventory = data?.inventory;
  if (data?.schema !== 'owner_barrel_layout_scene/v1' ||
      data.status !== 'complete_layout_concept_not_qualified' ||
      data.baseline !== 'compact-floor-flush-kerf-right' ||
      data.layout_clearance_approved !== false ||
      data.drilling_released !== false ||
      data.fabrication_released !== false ||
      data.structural_released !== false) {
    throw new Error('Barrel viewer release boundary changed');
  }
  if (inventory?.replaced_angle_duties !== 24 ||
      inventory.removed_structural_sds !== 144 ||
      inventory.moved_center_posts !== 2 ||
      inventory.kicker_screw_backers !== 2 ||
      inventory.derived_cut_headers !== 1 ||
      inventory.fixed_panel_kicker_screw_axes !== 66 ||
      inventory.retained_frame_bolt_axes !== 12 ||
      inventory.direct_joint_duties !== 24 ||
      inventory.barrel_nut_envelopes !== data.barrel_nut_envelopes?.length ||
      inventory.new_diagnostic_bolt_axes !== data.diagnostic_bolt_axes?.length ||
      inventory.rail_head_washer_envelopes !== 40 ||
      data.rail_head_washer_envelopes?.length !== 40 ||
      inventory.other_head_washer_envelopes !== 48 ||
      data.other_head_washer_envelopes?.length !== 48 ||
      inventory.backer_attachment_duties !== 2 ||
      inventory.backer_barrel_nut_envelopes !== 4 ||
      data.backer_barrel_nut_envelopes?.length !== 4 ||
      inventory.backer_diagnostic_bolt_axes !== 4 ||
      data.backer_diagnostic_bolt_axes?.length !== 4 ||
      inventory.backer_head_washer_envelopes !== 8 ||
      data.backer_head_washer_envelopes?.length !== 8 ||
      data.backer_attachment?.thread_engagement_verified !== false ||
      data.backer_attachment?.capacity_verified !== false ||
      Object.values(data.backer_attachment?.release_flags || {}).some(Boolean) ||
      Object.keys(data.backer_attachment?.station_dispositions || {}).length !== 2 ||
      Object.keys(data.station_dispositions || {}).length !== 24 ||
      !Array.isArray(data.cross_family_physical_clash_stations) ||
      data.cross_family_physical_clash_stations.some(station =>
        !Object.hasOwn(data.station_dispositions, station)) ||
      !data.solids?.length || !Array.isArray(data.barrel_nut_envelopes) ||
      Object.keys(data.station_dispositions).some(station =>
        !data.solids.some(row => row.source_station === station) &&
        !data.barrel_nut_envelopes.some(row => row.source_station === station)) ||
      data.solids.filter(row => row.role === 'moved_center_post').length !== 2 ||
      data.solids.filter(row => row.role === 'kicker_screw_backer').length !== 2 ||
      data.solids.filter(row => row.role === 'derived_cut_header' &&
        row.name === 'base_header/derived_outer_header_cut' && row.mesh?.triangles?.length).length !== 1 ||
      data.outer_header_cut_diagnostics?.source_member !== 'base_header' ||
      data.outer_header_cut_diagnostics?.counterbore_count !== 4 ||
      data.outer_header_cut_diagnostics?.machine_bore_count !== 4 ||
      data.outer_header_cut_diagnostics?.connected_solid_count !== 1 ||
      data.outer_header_cut_diagnostics?.cut_is_valid !== true ||
      !(data.outer_header_cut_diagnostics?.cut_volume_mm3 > 0) ||
      !(data.outer_header_cut_diagnostics.cut_volume_mm3 < data.outer_header_cut_diagnostics.uncut_volume_mm3) ||
      !Number.isFinite(data.outer_header_cut_diagnostics?.minimum_modeled_radial_edge_residual_mm) ||
      !(data.outer_header_cut_diagnostics.minimum_modeled_radial_edge_residual_mm > 0) ||
      !Number.isFinite(data.outer_header_cut_diagnostics?.counterbore_floor_residual_mm) ||
      !(data.outer_header_cut_diagnostics.counterbore_floor_residual_mm > 0) ||
      data.outer_header_cut_diagnostics?.net_section_capacity_verified !== false ||
      data.outer_header_cut_diagnostics?.disposition !== 'REVISE' ||
      data.outer_header_cut_diagnostics?.clearance_approved !== false ||
      data.rim_first_sequence?.temporary_fixed_fastener_removal_required !== true ||
      data.rim_first_sequence?.per_rim_release?.panel_screws !== 8 ||
      data.rim_first_sequence?.per_rim_release?.frame_bolts !== 2 ||
      data.rim_first_sequence?.per_rim_release?.trial_rim_joint_bolts !== 10 ||
      data.rim_first_sequence?.operational_result !== 'conditional_unverified' ||
      inventory.conditional_outer_header_recess_envelopes !== 12 ||
      data.conditional_outer_header_recess_envelopes?.length !== 12 ||
      ['recess_head', 'recess_washer', 'recess_counterbore'].some(role =>
        data.conditional_outer_header_recess_envelopes.filter(row => row.role === role).length !== 4) ||
      data.conditional_outer_header_recess_envelopes.some(row =>
        !['clip_timber_header_outer_left', 'clip_timber_header_outer_right'].includes(row.source_station)) ||
      ['clip_timber_header_outer_left', 'clip_timber_header_outer_right'].some(station =>
        ['recess_head', 'recess_washer', 'recess_counterbore'].some(role =>
          data.conditional_outer_header_recess_envelopes.filter(row =>
            row.source_station === station && row.role === role).length !== 2)) ||
      data.outer_header_recess_trial?.counterbore_depth_mm !== 6.651 ||
      data.outer_header_recess_trial?.forward_row_y_mm !== -85 ||
      data.outer_header_recess_trial?.side_rim_removal_required_for_driver !== true ||
      data.outer_header_recess_trial?.actual_rim_removal_verified !== false ||
      data.outer_header_recess_trial?.delivered_hardware_verified !== false ||
      data.outer_header_recess_trial?.structural_capacity_verified !== false) {
    throw new Error('Barrel viewer does not cover all 24 duties and fixed sources');
  }
  if (data.solids.some(row => !['moved_center_post', 'kicker_screw_backer', 'derived_cut_header'].includes(row.role)) ||
      Object.hasOwn(inventory, 'mixed_compact_block_duties')) {
    throw new Error('Barrel-only scene contains a corner-block artifact');
  }
  if (data.hidden_baseline_visual_names?.length !== 171 ||
      hiddenNames?.length !== 171 ||
      !hiddenNames.includes('base_header') ||
      data.hidden_baseline_visual_names.some((name, index) => name !== hiddenNames[index])) {
    throw new Error('Barrel viewer baseline inventory changed');
  }
  return data;
}

function meshGeometry(THREE, source) {
  const positions = [];
  for (const triangle of source.triangles) {
    for (const index of triangle) positions.push(...source.vertices_mm[index]);
  }
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
  geometry.computeVertexNormals();
  return geometry;
}

function cylinder(THREE, row, color, description) {
  const mesh = new THREE.Mesh(
    new THREE.CylinderGeometry(row.diameter_mm / 2, row.diameter_mm / 2, row.length_mm, 12),
    new THREE.MeshStandardMaterial({color, transparent: true, opacity: .8, depthWrite: false, depthTest: false}),
  );
  const direction = new THREE.Vector3(...row.axis).normalize();
  mesh.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), direction);
  mesh.position.fromArray(row.start_mm).addScaledVector(direction, row.length_mm / 2);
  mesh.userData.part = {
    name: row.name,
    fabrication: {
      owner_barrel_overlay: true, kind: 'bolt', category: 'bolts',
      description,
    },
  };
  mesh.userData.baseEmissive = 0;
  mesh.renderOrder = 10;
  return mesh;
}

export function renderOwnerBarrelScene(THREE, data, group, meshes) {
  const clashStations = new Set(data.cross_family_physical_clash_stations);
  for (const row of data.solids) {
    const derivedHeader = row.role === 'derived_cut_header';
    const disposition = data.station_dispositions[row.source_station] || 'LAYOUT_TRIAL';
    const revise = /REVISE|CLASH|BLOCKED|NO_FIT/.test(disposition) ||
      clashStations.has(row.source_station);
    const color = derivedHeader ? 0xb68152 : row.role === 'moved_center_post' ? 0x38bdf8 :
      row.role === 'kicker_screw_backer' ? 0x4ade80 :
      revise ? 0xf87171 : 0xa78bfa;
    const mesh = new THREE.Mesh(meshGeometry(THREE, row.mesh), new THREE.MeshStandardMaterial({
      color, transparent: !derivedHeader, opacity: derivedHeader ? 1 : .82,
      depthWrite: derivedHeader, roughness: .7,
    }));
    mesh.userData.part = {
      name: row.name,
      fabrication: {
        owner_barrel_overlay: true, kind: 'timber', category: 'timber',
        description: derivedHeader ?
          'Derived outer-header trial cut: four shallow counterbores and machine bores shown in wood. Single connected nominal solid; net-section capacity and drilling unverified.' :
          `${row.role.replaceAll('_', ' ')}; ${disposition}; not a cut or structural release`,
      },
    };
    mesh.userData.baseEmissive = 0;
    meshes.push(mesh);
    group.add(mesh);
  }
  for (const row of data.diagnostic_bolt_axes) {
    const mesh = cylinder(THREE, row, 0x72e5ff,
      'Provisional bolt path; modeled length and head are shown, but delivered fit, engagement, and drilling are not approved');
    meshes.push(mesh);
    group.add(mesh);
  }
  for (const row of data.backer_diagnostic_bolt_axes) {
    const mesh = cylinder(THREE, row, 0x72e5ff,
      'New kicker-backer/header attachment trial; thread, capacity, and drilling unverified');
    meshes.push(mesh);
    group.add(mesh);
  }
  for (const row of [...data.rail_head_washer_envelopes, ...data.other_head_washer_envelopes,
                     ...data.backer_head_washer_envelopes,
                     ...data.backer_barrel_nut_envelopes]) {
    const barrel = row.role === 'backer_barrel';
    const washer = row.role.endsWith('washer');
    const mesh = new THREE.Mesh(meshGeometry(THREE, row.mesh), new THREE.MeshStandardMaterial({
      color: barrel ? 0xf87171 : washer ? 0xffd166 : 0xff8c42,
      transparent: true, opacity: .88, depthWrite: false, depthTest: false,
    }));
    mesh.userData.part = {
      name: row.name,
      fabrication: {
        owner_barrel_overlay: true, kind: 'bolt', category: 'bolts',
        description: `${row.role.replaceAll('_', ' ')}; nominal barrel concept only. Delivered fit, tool access, strength and drilling are unverified`,
      },
    };
    mesh.userData.baseEmissive = 0;
    mesh.renderOrder = 11;
    meshes.push(mesh);
    group.add(mesh);
  }
  for (const row of data.conditional_outer_header_recess_envelopes) {
    const counterbore = row.role === 'recess_counterbore';
    const color = counterbore ? 0xff5dc8 : row.role === 'recess_washer' ? 0xffd166 : 0xff8c42;
    const mesh = new THREE.Mesh(meshGeometry(THREE, row.mesh), new THREE.MeshStandardMaterial({
      color, transparent: true, opacity: counterbore ? .38 : .95,
      depthWrite: false, depthTest: false, wireframe: counterbore,
    }));
    mesh.userData.part = {
      name: row.name,
      fabrication: {
        owner_barrel_overlay: true, kind: 'bolt', category: 'bolts',
        description: `${row.role.replaceAll('_', ' ')}; conditional outer-header trial only. Rim must be removed for driver access; removal sequence, actual hardware, wood capacity and drilling are unverified`,
      },
    };
    mesh.userData.baseEmissive = 0;
    mesh.renderOrder = 11;
    meshes.push(mesh);
    group.add(mesh);
  }
  for (const row of data.barrel_nut_envelopes) {
    const disposition = data.station_dispositions[row.source_station];
    const revise = /REVISE|CLASH|BLOCKED|NO_FIT/.test(disposition) ||
      clashStations.has(row.source_station);
    const mesh = new THREE.Mesh(meshGeometry(THREE, row.mesh), new THREE.MeshStandardMaterial({
      color: revise ? 0xf87171 : 0xfacc15, transparent: true, opacity: .85,
      depthWrite: false, depthTest: false,
    }));
    mesh.userData.part = {
      name: row.name,
      fabrication: {
        owner_barrel_overlay: true, kind: 'bolt', category: 'bolts',
        description: `${disposition}; provisional barrel-nut envelope; factory end-to-thread-axis, engagement, and capacity unverified`,
      },
    };
    mesh.userData.baseEmissive = 0;
    mesh.renderOrder = 10;
    meshes.push(mesh);
    group.add(mesh);
  }
  return {
    woodSolids: data.solids.length,
    boltAxes: data.diagnostic_bolt_axes.length,
    barrelNutEnvelopes: data.barrel_nut_envelopes.length,
    conditionalRecessEnvelopes: data.conditional_outer_header_recess_envelopes.length,
    railHeadWasherEnvelopes: data.rail_head_washer_envelopes.length,
    otherHeadWasherEnvelopes: data.other_head_washer_envelopes.length,
    backerAttachmentBarrels: data.backer_barrel_nut_envelopes.length,
  };
}
