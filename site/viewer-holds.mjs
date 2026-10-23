// Approximate hold display, setup controls and shareable problem highlights.
import * as THREE from 'three';
import {createHoldMesh} from './hold-geometry.js';

export function createHoldControls({assemblyView, camera, controls, updateVisibility, clearSelectedHolds}) {
  const holdGroup = new THREE.Group(), holdMeshes = [];
  assemblyView.add(holdGroup);
  const holdSetup = new URLSearchParams(location.search).get('setup') === '2020' ? '2020' : '2025';
  const holdCount = holdSetup === '2020' ? 130 : 138;
  const holdControls = document.createElement('section'); holdControls.id = 'hold-controls';
  holdControls.setAttribute('aria-label', 'Mini MoonBoard holds');
  holdControls.innerHTML = '<label>Hold setup <select id="hold-setup"><option value="2025">Mini MoonBoard 2025</option><option value="2020">Mini MoonBoard 2020</option></select></label><label><input id="show-holds" type="checkbox" checked disabled /> Show holds</label><p id="hold-status" role="status">Loading approximate holds…</p><button id="hold-front" type="button" disabled>View holds from front</button><details id="problem-tools"><summary>Problem highlights</summary><fieldset id="problem-controls" disabled><legend>Problem highlights</legend><label><input id="problem-edit" type="checkbox" /> Edit problem · click holds to mark</label><label>Mark as <select id="problem-role"><option value="s">Start</option><option value="h">Hand</option><option value="f">Foot</option><option value="t">Finish</option><option value="erase">Erase</option></select></label><label>Hold <select id="problem-position" aria-label="Hold grid position"></select></label><button id="problem-apply" type="button" disabled>Apply mark</button><p id="problem-legend"><span style="color:#4ade80">S · Start</span><span style="color:#60a5fa">H · Hand</span><span style="color:#facc15">F · Foot</span><span style="color:#f472b6">T · Finish</span></p><p id="problem-status" role="status">No holds marked.</p><button id="problem-clear" type="button">Clear</button> <button id="problem-share" type="button">Copy problem link</button><input id="problem-link" aria-label="Problem link; select and copy" readonly hidden /></fieldset></details>';
  document.querySelector('#overlay').parentElement.before(holdControls);
  const holdToggle = document.querySelector('#show-holds'), holdStatus = document.querySelector('#hold-status');
  const holdSetupSelect = document.querySelector('#hold-setup'); holdSetupSelect.value = holdSetup;
  // History restores the outgoing selection after pageshow; match this page's catalog.
  addEventListener('pageshow', () => setTimeout(() => { holdSetupSelect.value = holdSetup; }, 0));
  holdSetupSelect.addEventListener('change', () => {
    const url = new URL(location.href); url.searchParams.set('setup', holdSetupSelect.value); url.searchParams.delete('problem'); location.assign(url);
  });
  const holdFront = document.querySelector('#hold-front');
  const holdFamilies = {original: 'Original School', 'school-f': 'School Set F', wood: holdSetup === '2020' ? 'Wood A/B/C' : 'Wood B/C', foot: 'Kicker foothold'};
  holdToggle.checked = new URLSearchParams(location.search).get('holds') !== 'off';
  holdToggle.addEventListener('change', () => {
    updateVisibility();
    if (!holdToggle.checked) clearSelectedHolds();
    const url = new URL(location.href);
    if (holdToggle.checked) url.searchParams.delete('holds'); else url.searchParams.set('holds', 'off');
    history.replaceState(null, '', url);
  });
  holdFront.addEventListener('click', () => {
    // Fit the board beside the controls on desktop, or below them on phones.
    const header = document.querySelector('header').getBoundingClientRect();
    const narrow = innerWidth < header.width + 400;
    const available = Math.min(innerWidth - (narrow ? 0 : header.width), innerHeight - (narrow ? header.height : 0));
    const span = 2900 * innerHeight / Math.max(available, 180);
    const distance = span * camera.zoom / (2 * Math.tan(camera.fov * Math.PI / 360));
    const angle = Math.PI * 40 / 180;
    controls.target.set(0, -245, 1090);
    if (narrow) controls.target.addScaledVector(new THREE.Vector3(0, Math.sin(angle), Math.cos(angle)), span * header.height / (2 * innerHeight));
    else controls.target.x += span * header.width / (2 * innerHeight);
    camera.position.copy(controls.target).add(new THREE.Vector3(0, distance * Math.cos(angle), -distance * Math.sin(angle)));
    camera.clearViewOffset(); controls.update();
  });
  const problemControls = document.querySelector('#problem-controls');
  const problemEdit = document.querySelector('#problem-edit'), problemRole = document.querySelector('#problem-role');
  const problemStatus = document.querySelector('#problem-status'), problemLink = document.querySelector('#problem-link');
  const problemMarks = new Map();
  const problemRoles = {s: {label: 'Start', color: '#4ade80'}, h: {label: 'Hand', color: '#60a5fa'},
    f: {label: 'Foot', color: '#facc15'}, t: {label: 'Finish', color: '#f472b6'}};
  function updateProblem(writeUrl = true) {
    for (const mesh of holdMeshes) {
      const role = problemMarks.get(mesh.userData.hold.position);
      let marker = mesh.userData.problemMarker;
      if (role && !marker) {
        const radius = Math.hypot(mesh.userData.hold.width, mesh.userData.hold.height) / 2 + 9;
        marker = new THREE.Mesh(new THREE.RingGeometry(radius, radius + 7, 48),
          new THREE.MeshBasicMaterial({side: THREE.DoubleSide}));
        marker.position.z = 2;
        marker.raycast = () => {}; // Markers never intercept hold inspection.
        mesh.add(marker); mesh.userData.problemMarker = marker;
      }
      if (marker) { marker.visible = Boolean(role); if (role) marker.material.color.set(problemRoles[role].color); }
    }
    const entries = [...problemMarks].sort(([a], [b]) => a.localeCompare(b, undefined, {numeric: true}));
    problemStatus.textContent = entries.length ? entries.map(([position, role]) => `${position} ${problemRoles[role].label}`).join(' · ') : 'No holds marked.';
    if (writeUrl) {
      const url = new URL(location.href);
      if (entries.length) url.searchParams.set('problem', `${holdSetup}:${entries.map(([position, role]) => `${position}.${role}`).join(',')}`);
      else url.searchParams.delete('problem');
      history.replaceState(null, '', url);
    }
    problemLink.hidden = true;
  }
  function markProblem(position) {
    if (problemRole.value === 'erase') problemMarks.delete(position);
    else problemMarks.set(position, problemRole.value);
    updateProblem();
  }
  problemEdit.addEventListener('change', () => { document.querySelector('#problem-apply').disabled = !problemEdit.checked; });
  document.querySelector('#problem-apply').addEventListener('click', () => {
    if (problemEdit.checked) markProblem(document.querySelector('#problem-position').value);
  });
  function loadProblem(positions) {
    const encoded = new URLSearchParams(location.search).get('problem');
    if (!encoded) return;
    document.querySelector('#problem-tools').open = true;
    const entries = encoded.startsWith(`${holdSetup}:`) && encoded.length <= 2000 ? encoded.slice(5).split(',') : [];
    const seen = new Set();
    const valid = entries.length > 0 && entries.every(entry => {
      const match = /^([A-K](?:[1-9]|1[0-2])|KICK(?:[1-9]|10))\.([shft])$/.exec(entry);
      if (!match || !positions.has(match[1]) || seen.has(match[1])) return false;
      seen.add(match[1]); return true;
    });
    if (valid) for (const entry of entries) { const [position, role] = entry.split('.'); problemMarks.set(position, role); }
    updateProblem();
    if (!valid) problemStatus.textContent = 'Invalid or different-setup problem link ignored. No holds marked.';
  }
  document.querySelector('#problem-clear').addEventListener('click', () => { problemMarks.clear(); updateProblem(); });
  document.querySelector('#problem-share').addEventListener('click', async () => {
    const url = new URL(location.href); url.searchParams.set('setup', holdSetup); url.searchParams.delete('holds');
    try {
      if (!navigator.clipboard?.writeText) throw new Error('Clipboard unavailable');
      await navigator.clipboard.writeText(url.href); problemStatus.textContent = 'Problem link copied.';
    } catch {
      problemLink.value = url.href; problemLink.hidden = false; problemLink.focus(); problemLink.select();
      problemStatus.textContent = 'Copy the selected problem link.';
    }
  });
  async function loadHolds({mainFaceHeight, kickerHoldHeight, rowStations}) {
    try {
      const response = await fetch(`mini-${holdSetup}-holds.json`);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const catalog = await response.json();
      const positions = new Set();
      if (!Array.isArray(catalog.holds) || catalog.holds.length !== holdCount) throw new Error('Incomplete hold catalog');
      for (const hold of catalog.holds) {
        if (!/^(?:[A-K](?:[1-9]|1[0-2])|KICK(?:[1-9]|10))$/.test(hold.position) || positions.has(hold.position) ||
            !holdFamilies[hold.family] || !['edge', 'pinch', 'sloper', 'jug', 'wedge', 'triangle', 'crescent', 'tapered-pinch', 'fin', 'waisted', 'soft-lobed'].includes(hold.shape) ||
            ![hold.width, hold.height, hold.depth].every(value => Number.isFinite(value) && value > 0 && value < 400) || !Number.isFinite(hold.rotation)) {
          throw new Error('Invalid hold catalog');
        }
        positions.add(hold.position);
      }
      const angle = Math.PI * 40 / 180;
      for (const hold of catalog.holds) {
        const mesh = createHoldMesh(hold), kicker = hold.position.startsWith('KICK');
        const right = new THREE.Vector3(-1, 0, 0);
        const up = kicker ? new THREE.Vector3(0, 0, 1) : new THREE.Vector3(0, Math.sin(angle), Math.cos(angle));
        const normal = new THREE.Vector3().crossVectors(right, up);
        mesh.quaternion.setFromRotationMatrix(new THREE.Matrix4().makeBasis(right, up, normal));
        mesh.rotateZ(-hold.rotation * Math.PI / 180);
        if (kicker) mesh.position.set(1219.2 - (100 + 248.56 * (Number(hold.position.slice(4)) - 1)), -18, kickerHoldHeight);
        else {
          const station = rowStations[Number(hold.position.slice(1)) - 1];
          mesh.position.set(1019.2 - (hold.position.charCodeAt(0) - 65) * 200,
            -18 + station * Math.sin(angle), mainFaceHeight + station * Math.cos(angle));
        }
        mesh.position.addScaledVector(normal, .5);
        mesh.userData.hold = hold;
        holdMeshes.push(mesh); holdGroup.add(mesh);
      }
      const positionSelect = document.querySelector('#problem-position');
      [...positions].sort((a, b) => a.localeCompare(b, undefined, {numeric: true})).forEach(position => positionSelect.add(new Option(position, position)));
      loadProblem(positions);
      holdStatus.textContent = `${holdCount} loose approximations · yellow Originals, ${holdSetup === '2020' ? 'wood A/B/C' : 'blue Set F, wood B/C'}. Shapes, sizes and rotations are estimates. Click a hold to inspect.`;
      holdToggle.disabled = false; holdFront.disabled = false;
      updateVisibility();
    } catch (error) {
      for (const mesh of holdMeshes) { mesh.geometry.dispose(); mesh.material.dispose(); }
      holdMeshes.length = 0; holdGroup.clear();
      holdStatus.textContent = `Holds unavailable: ${error.message}. Reload to retry.`;
      holdToggle.disabled = true; holdFront.disabled = true;
    }
  }
  return {holdGroup, holdMeshes, holdSetup, holdCount, holdControls, holdToggle, holdStatus, holdFront, holdFamilies, problemControls, problemEdit, problemMarks, markProblem, loadHolds};
}
