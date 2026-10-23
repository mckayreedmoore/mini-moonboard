// Display-only padding, dimensions and reference person; excluded from CAD and analysis.
import * as THREE from 'three';

export const feetAndInches = mm => {
  const hundredths = Math.round(mm / 25.4 * 100);
  const feet = Math.floor(hundredths / 1200);
  const inches = Number(((hundredths % 1200) / 100).toFixed(2));
  return `${feet} ft ${inches} in`;
};

export function createCrashPadPreview(assemblyView, crashPadCompatible, updateVisibility) {
  const crashPadGroup = new THREE.Group(), crashPadMeshes = [];
  crashPadGroup.name = 'crash-pad-placement-preview'; assemblyView.add(crashPadGroup);
  const crashPadControl = document.createElement('label'); crashPadControl.hidden = !crashPadCompatible;
  const crashPadToggle = document.createElement('input'); crashPadToggle.type = 'checkbox'; crashPadToggle.id = 'show-crash-pads';
  crashPadToggle.checked = crashPadCompatible; crashPadControl.append(crashPadToggle, 'Crash pads');
  const crashPadNote = document.createElement('p'); crashPadNote.id = 'crash-pad-note'; crashPadNote.hidden = !crashPadCompatible;
  crashPadNote.textContent = 'Two 48 × 72 × 5 in pads, side by side; center seam runs front to back. Click a pad for dimensions. Placement preview; excluded from frame weight and structural checks.';
  document.querySelector('header').append(crashPadControl, crashPadNote);
  if (crashPadCompatible) {
    // Current kicker rear face is Y=-17.74375; Y=0 leaves a small gap.
    // Two portable 4 x 6 ft pads cover the same 8 x 6 ft footprint. The
    // center seam is X=0 and therefore runs front-to-back, on Z=0.
    const width = 48*25.4, depth = 72*25.4, height = 5*25.4;
    [0x315b78, 0x704660].forEach((color, index) => {
      const geometry = new THREE.BoxGeometry(width, depth, height);
      const pad = new THREE.Mesh(geometry, new THREE.MeshStandardMaterial({color, roughness: .95, metalness: 0}));
      pad.name = `crash-pad-${index+1}`; pad.position.set((index-.5)*width, depth/2, height/2);
      pad.userData.crashPad = {index: index+1, dimensions_mm: [width, depth, height],
        layup: '2 × 0.5 in PE + 3 in 44-ILD polyurethane + 2 × 0.5 in PE',
        structural: false, mass_included: false};
      pad.userData.baseEmissive = 0;
      const edge = new THREE.LineSegments(new THREE.EdgesGeometry(geometry), new THREE.LineBasicMaterial({color: 0xc3c9ce}));
      edge.raycast = () => {}; pad.add(edge); crashPadGroup.add(pad); crashPadMeshes.push(pad);
    });
  }
  crashPadGroup.visible = crashPadCompatible;
  crashPadToggle.addEventListener('change', updateVisibility);
  return {crashPadGroup, crashPadMeshes, crashPadControl, crashPadToggle, crashPadNote};
}

export function createDimensionOverlay(assemblyView) {
  const dimensions = new THREE.Group(); assemblyView.add(dimensions);
  const dimensionLabel = (text, point) => {
    const canvas = document.createElement('canvas'); canvas.width = 1024; canvas.height = 128;
    const context = canvas.getContext('2d'); context.fillStyle = '#121619dd'; context.fillRect(0, 0, 1024, 128);
    context.fillStyle = '#f5f0e6'; context.font = 'bold 64px system-ui';
    const fontSize = Math.min(64, 64 * 980 / context.measureText(text).width);
    context.font = `bold ${fontSize}px system-ui`; context.textAlign = 'center'; context.textBaseline = 'middle'; context.fillText(text, 512, 68);
    const sprite = new THREE.Sprite(new THREE.SpriteMaterial({ map: new THREE.CanvasTexture(canvas), transparent: true, depthWrite: false }));
    sprite.position.fromArray(point); sprite.scale.set(760, 95, 1); dimensions.add(sprite);
  };
  const dimensionLine = (start, end, tick, label) => {
    const material = new THREE.LineBasicMaterial({ color: 0xf0b429 });
    const line = new THREE.Line(new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(...start), new THREE.Vector3(...end)]), material); dimensions.add(line);
    [start, end].forEach(point => dimensions.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(...point).add(new THREE.Vector3(...tick)), new THREE.Vector3(...point).sub(new THREE.Vector3(...tick))]), material)));
    dimensionLabel(label, start.map((value, index) => (value + end[index]) / 2 + (index === 2 ? 85 : 0)));
  };
  // Keep dimensions synchronized with CAD, including the outside legs.
  function drawDimensions([[xmin, ymin, zmin], [xmax, ymax, zmax]]) {
    const label = (name, mm) => `${name} ${mm.toFixed(1)} mm / ${feetAndInches(mm)}`;
    dimensionLine([-xmax, ymax + 140, 20], [-xmin, ymax + 140, 20], [0, 0, 55], label('WIDTH', xmax - xmin));
    dimensionLine([-xmax - 120, ymin, 20], [-xmax - 120, ymax, 20], [0, 0, 55], label('DEPTH', ymax - ymin));
    dimensionLine([-xmax - 120, ymax + 100, zmin], [-xmax - 120, ymax + 100, zmax], [55, 0, 0], label('HEIGHT', zmax - zmin));
  }
  document.querySelector('#dimensions').addEventListener('change', event => { dimensions.visible = event.target.checked; });
  return {dimensions, drawDimensions};
}

export function createReferencePerson(scene, meshes) {
  // +X is climber-left after the display-only face reflection. At floor
  // level Y=250 is in front of the lower climbing face; the bracing is on
  // the opposite, support-side normal. Do not infer front/back from a
  // global Y sign because the board is sloped.
  const person = new THREE.Group(), personMeshes = []; person.position.set(1710, 250, 0); scene.add(person);
  const personPart = { name: 'McKay', fabrication: { dimensions_mm: [450, 300, 1727.2], dimensions_imperial: [17.72, 11.81, 68.00], description: 'an absolutely staggering 5\'8\" reference person; display-only and excluded from CAD, cut lists, stability, and FEA' } };
  const addPersonPart = (geometry, position, rotation = [0, 0, 0]) => {
    const mesh = new THREE.Mesh(geometry, new THREE.MeshStandardMaterial({ color: 0x607d8b, roughness: .85 }));
    mesh.position.fromArray(position); mesh.rotation.fromArray(rotation); mesh.userData.part = personPart; meshes.push(mesh); personMeshes.push(mesh); person.add(mesh);
  };
  // Simplified 1727.2 mm / 5 ft 8 in mannequin: visual scale reference only.
  addPersonPart(new THREE.CylinderGeometry(82, 105, 720, 12), [0, 0, 1125], [Math.PI / 2, 0, 0]);
  addPersonPart(new THREE.SphereGeometry(90, 16, 12), [0, 0, 1637.2]);
  [-95, 95].forEach(x => addPersonPart(new THREE.CylinderGeometry(48, 55, 740, 10), [x, 0, 370], [Math.PI / 2, 0, 0]));
  [-150, 150].forEach(x => addPersonPart(new THREE.CylinderGeometry(36, 42, 590, 10), [x, 0, 1110], [Math.PI / 2, 0, 0]));
  const personMaterial = new THREE.LineBasicMaterial({ color: 0x87ceeb });
  person.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(-250, 0, 0), new THREE.Vector3(-250, 0, 1727.2)]), personMaterial));
  [[-305, 0, 0], [-195, 0, 0], [-305, 0, 1727.2], [-195, 0, 1727.2]].forEach((point, index, points) => { if (index % 2 === 0) person.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(...point), new THREE.Vector3(...points[index + 1])]), personMaterial)); });
  const personCanvas = document.createElement('canvas'); personCanvas.width = 1024; personCanvas.height = 128;
  const personContext = personCanvas.getContext('2d'); personContext.fillStyle = '#121619dd'; personContext.fillRect(0, 0, 1024, 128); personContext.fillStyle = '#f5f0e6'; personContext.font = 'bold 58px system-ui'; personContext.textAlign = 'center'; personContext.textBaseline = 'middle'; personContext.fillText("MCKAY — 5'8\" / 1727.2 mm", 512, 68);
  const personLabel = new THREE.Sprite(new THREE.SpriteMaterial({ map: new THREE.CanvasTexture(personCanvas), transparent: true, depthWrite: false })); personLabel.position.set(-250, 0, 1815); personLabel.scale.set(700, 88, 1); person.add(personLabel);
  document.querySelector('#person').addEventListener('change', event => { person.visible = event.target.checked; });
  return {person, personMeshes, personPart};
}
