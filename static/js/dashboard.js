let groups = window.GROUPS_DATA;
let athletes = window.ATHLETES_DATA;
let activeGroup = '';
const planName = id => (window.PLANS_DATA.find(p => p.id === id) || {}).name || id || '—';
const groupName = id => (groups.find(g => g.id === id) || {}).name;

function groupOptions(selected, emptyLabel = '— Không có nhóm —') {
  return `<option value="">${esc(emptyLabel)}</option>` + groups.map(g =>
    `<option value="${esc(g.id)}" ${g.id === selected ? 'selected' : ''}>${esc(g.name)}</option>`).join('');
}

function renderGroups() {
  const el = document.getElementById('groupList');
  if (!groups.length) {
    el.innerHTML = '<div class="empty">Chưa có nhóm. Tạo nhóm để app tự tính tuần giáo án khi upload.</div>';
  } else {
    el.innerHTML = groups.map(g => `
      <div class="group-card">
        <div class="gc-info">
          <div class="gc-name">${esc(g.name)}</div>
          <div class="gc-meta">${esc(planName(g.plan_id))}${g.start_date ? ' · bắt đầu ' + esc(g.start_date) : ' · chưa có ngày bắt đầu'}</div>
        </div>
        <div class="gc-count">${g.athlete_count} HV</div>
        <button class="btn-sm" onclick="openGroupModal('${esc(g.id)}')">Sửa</button>
      </div>`).join('');
  }
  document.getElementById('navGroups').textContent = groups.length;
  renderFilter();
}

function renderFilter() {
  const tabs = [{ id: '', name: 'Tất cả' }, ...groups, { id: '__none__', name: 'Chưa có nhóm' }];
  document.getElementById('groupFilter').innerHTML = tabs.map(t =>
    `<button class="gtab ${t.id === activeGroup ? 'active' : ''}" onclick="filterAthletes('${esc(t.id)}')">${esc(t.name)}</button>`).join('');
}

function filterAthletes(groupId) {
  activeGroup = groupId;
  renderFilter();
  renderAthletes();
}

function renderAthletes() {
  const list = athletes.filter(a =>
    !activeGroup || (activeGroup === '__none__' ? !a.group_id : a.group_id === activeGroup));
  const el = document.getElementById('athleteList_');
  if (!list.length) {
    el.innerHTML = '<div class="empty">Chưa có học viên nào ở đây.</div>';
  } else {
    el.innerHTML = list.map(a => `
      <a class="athlete-card" href="/athletes/${encodeURIComponent(a.id)}">
        <div class="avatar">${esc(a.name.trim().split(/\s+/).pop()[0] || '?')}</div>
        <div class="athlete-info">
          <div class="athlete-name">${esc(a.name)} ${a.group_id ? `<span class="tag">${esc(groupName(a.group_id) || a.group_id)}</span>` : '<span class="tag muted">không nhóm</span>'}</div>
          <div class="athlete-meta">${a.activity_count} buổi${a.last_activity ? ' · gần nhất ' + esc(a.last_activity) : ''}</div>
        </div>
        <div class="athlete-km">${a.total_km} km</div>
        <button class="btn-sm" onclick="event.preventDefault(); openMoveModal('${esc(a.id)}')">Đổi nhóm</button>
      </a>`).join('');
  }
  document.getElementById('navAthletes').textContent = athletes.length;
  document.getElementById('athleteList').innerHTML = athletes.map(a => `<option value="${esc(a.name)}">`).join('');
  if (window.onAthletesChanged) window.onAthletesChanged();
}

async function reloadData() {
  [groups, athletes] = await Promise.all([api('/api/groups'), api('/api/athletes')]);
  renderGroups();
  renderAthletes();
}

function openGroupModal(id) {
  const g = groups.find(x => x.id === id);
  document.getElementById('groupModalTitle').textContent = g ? '✏️ Sửa nhóm' : '👥 Tạo nhóm mới';
  document.getElementById('gId').value = g ? g.id : '';
  document.getElementById('gName').value = g ? g.name : '';
  document.getElementById('gPlan').value = g ? g.plan_id : window.DEFAULT_PLAN_ID;
  document.getElementById('gStart').value = g && g.start_date ? g.start_date : '';
  document.getElementById('gNotes').value = g ? g.notes : '';
  openModal('groupModal');
  document.getElementById('gName').focus();
}

async function saveGroup() {
  const id = document.getElementById('gId').value;
  const body = {
    name: document.getElementById('gName').value,
    plan_id: document.getElementById('gPlan').value,
    start_date: document.getElementById('gStart').value || null,
    notes: document.getElementById('gNotes').value,
  };
  try {
    if (id) await api(`/api/groups/${encodeURIComponent(id)}`, { method: 'PATCH', json: body });
    else await api('/api/groups', { method: 'POST', json: body });
    closeModal('groupModal');
    showToast(id ? 'Đã cập nhật nhóm' : 'Đã tạo nhóm', body.name);
    await reloadData();
  } catch (e) { showToast('Không lưu được nhóm', e.message, 'err'); }
}

function openAthleteModal() {
  document.getElementById('aName').value = '';
  document.getElementById('aGroup').innerHTML = groupOptions(activeGroup && activeGroup !== '__none__' ? activeGroup : '');
  openModal('athleteModal');
  document.getElementById('aName').focus();
}

async function createAthlete() {
  const body = { name: document.getElementById('aName').value, group_id: document.getElementById('aGroup').value || null };
  try {
    const a = await api('/api/athletes', { method: 'POST', json: body });
    closeModal('athleteModal');
    showToast('Đã thêm học viên', a.name);
    await reloadData();
  } catch (e) { showToast('Không thêm được học viên', e.message, 'err'); }
}

function openMoveModal(id) {
  const a = athletes.find(x => x.id === id);
  document.getElementById('mAthlete').value = id;
  document.getElementById('moveTitle').textContent = `Chuyển nhóm: ${a.name}`;
  document.getElementById('mGroup').innerHTML = groupOptions(a.group_id);
  openModal('moveModal');
}

async function moveAthlete() {
  const id = document.getElementById('mAthlete').value;
  try {
    await api(`/api/athletes/${encodeURIComponent(id)}`, { method: 'PATCH', json: { group_id: document.getElementById('mGroup').value || null } });
    closeModal('moveModal');
    showToast('Đã chuyển nhóm', 'Các buổi tập cũ giữ nguyên kết quả chấm');
    await reloadData();
  } catch (e) { showToast('Không chuyển được nhóm', e.message, 'err'); }
}

renderGroups();
renderAthletes();
