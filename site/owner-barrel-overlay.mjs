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
      inventory.fixed_panel_kicker_screw_axes !== 66 ||
      inventory.retained_frame_bolt_axes !== 12 ||
      inventory.direct_joint_duties !== 24 ||
      inventory.barrel_nut_envelopes !== data.barrel_nut_envelopes?.length ||
      inventory.new_diagnostic_bolt_axes !== data.diagnostic_bolt_axes?.length ||
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
  if (data.solids.some(row => !['moved_center_post', 'kicker_screw_backer'].includes(row.role)) ||
      Object.hasOwn(inventory, 'mixed_compact_block_duties')) {
    throw new Error('Barrel-only scene contains a corner-block artifact');
  }
  if (data.hidden_baseline_visual_names?.length !== 170 ||
      hiddenNames?.length !== 170 ||
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
    const disposition = data.station_dispositions[row.source_station] || 'LAYOUT_TRIAL';
    const revise = /REVISE|CLASH|BLOCKED|NO_FIT/.test(disposition) ||
      clashStations.has(row.source_station);
    const color = row.role === 'moved_center_post' ? 0x38bdf8 :
      row.role === 'kicker_screw_backer' ? 0x4ade80 :
      revise ? 0xf87171 : 0xa78bfa;
    const mesh = new THREE.Mesh(meshGeometry(THREE, row.mesh), new THREE.MeshStandardMaterial({
      color, transparent: true, opacity: .82, depthWrite: false, roughness: .7,
    }));
    mesh.userData.part = {
      name: row.name,
      fabrication: {
        owner_barrel_overlay: true, kind: 'timber', category: 'timber',
        description: `${row.role.replaceAll('_', ' ')}; ${disposition}; not a cut or structural release`,
      },
    };
    mesh.userData.baseEmissive = 0;
    meshes.push(mesh);
    group.add(mesh);
  }
  for (const row of data.diagnostic_bolt_axes) {
    const mesh = cylinder(THREE, row, 0x72e5ff,
      'Diagnostic bolt path only; length, head, engagement, and drilling are not approved');
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
  };
}
