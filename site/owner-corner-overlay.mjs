// Complete owner-layout visualization. Colors describe review status, not strength.

export function validateOwnerCornerScene(data, hiddenNames) {
  const count = data?.inventory;
  const expected = {
    replaced_angle_duties: 24,
    removed_structural_sds: 144,
    corner_blocks: 24,
    moved_center_posts: 2,
    kicker_screw_backers: 2,
    new_diagnostic_bolt_axes: 92,
    fixed_panel_kicker_screw_axes: 66,
    retained_frame_bolt_axes: 12,
  };
  if (data?.schema !== 'owner_corner_layout_scene/v1' ||
      data.status !== 'complete_layout_concept_not_qualified' ||
      data.baseline !== 'compact-floor-flush-kerf-right' ||
      data.layout_clearance_approved !== false ||
      data.drilling_released !== false ||
      data.fabrication_released !== false ||
      data.structural_released !== false ||
      Object.entries(expected).some(([key, value]) => count?.[key] !== value) ||
      data.solids?.length !== 28 || data.diagnostic_bolt_axes?.length !== 92 ||
      data.hidden_baseline_visual_names?.length !== 170 ||
      hiddenNames?.length !== 170 ||
      data.hidden_baseline_visual_names.some((name, index) => name !== hiddenNames[index])) {
    throw new Error('Owner corner scene inventory or release boundary changed');
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

export function renderOwnerCornerScene(THREE, data, group, meshes) {
  const diagnostics = data.assembly_diagnostics;
  const family = diagnostics.station_family;
  const local = diagnostics.local_dispositions;
  for (const row of data.solids) {
    const revise = row.role === 'corner_block' && local[family[row.source_station]]?.startsWith('REVISE');
    const color = row.role === 'moved_center_post' ? 0x38bdf8 :
      row.role === 'kicker_screw_backer' ? 0x4ade80 : revise ? 0xf87171 : 0xf0b429;
    const mesh = new THREE.Mesh(meshGeometry(THREE, row.mesh), new THREE.MeshStandardMaterial({
      color, transparent: true, opacity: .82, depthWrite: false, roughness: .7,
    }));
    mesh.userData.part = {
      name: row.name,
      fabrication: {
        owner_corner_overlay: true, kind: 'timber', category: 'timber',
        description: `${row.role.replaceAll('_', ' ')}; ${revise ? 'known REVISE geometry' : 'layout trial'}; not a cut or structural release`,
      },
    };
    mesh.userData.baseEmissive = 0;
    meshes.push(mesh);
    group.add(mesh);
  }
  for (const row of data.diagnostic_bolt_axes) {
    const geometry = new THREE.CylinderGeometry(row.diameter_mm / 2, row.diameter_mm / 2, row.length_mm, 12);
    const mesh = new THREE.Mesh(geometry, new THREE.MeshStandardMaterial({
      color: 0x72e5ff, transparent: true, opacity: .7, depthWrite: false,
    }));
    const direction = new THREE.Vector3(...row.axis);
    mesh.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), direction);
    mesh.position.fromArray(row.start_mm).addScaledVector(direction, row.length_mm / 2);
    mesh.userData.part = {
      name: `${row.name} diagnostic bolt path`,
      fabrication: {
        owner_corner_overlay: true, kind: 'bolt', category: 'bolts',
        connection_name: row.name,
        description: 'Diagnostic bore axis only; bolt length, head, nut, washer and drill size are not selected',
      },
    };
    mesh.userData.baseEmissive = 0;
    meshes.push(mesh);
    group.add(mesh);
  }
  return {woodSolids: data.solids.length, boltAxes: data.diagnostic_bolt_axes.length};
}
