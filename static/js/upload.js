const SESSION_TYPES = [
  ['EASY', 'Easy'], ['LONG', 'Long Run'], ['TEMPO', 'Tempo'], ['SPEED', 'Speed/Interval'], ['MP', 'Marathon Pace'], ['RACE', 'Race'],
];
let pending = null;

const upEl = id => document.getElementById(id);
const findAthleteByName = name => athletes.find(a => a.name.trim().toLowerCase() === name.trim().toLowerCase());

function onAthleteInput() {
  const name = upEl('upAthlete').value;
  const a = findAthleteByName(name);
  const hint = upEl('upAthleteHint');
  if (!name.trim()) {
    hint.textContent = '';
    upEl('upNewGroupWrap').classList.add('hidden');
  } else if (a) {
    hint.textContent = a.group_id ? `Nhóm: ${groupName(a.group_id) || a.group_id} — giáo án và tuần sẽ được đề xuất theo nhóm` : 'Học viên chưa có nhóm — bạn sẽ chọn giáo án và tuần thủ công';
    upEl('upNewGroupWrap').classList.add('hidden');
  } else {
    hint.textContent = 'Học viên mới — sẽ được tạo khi đọc file';
    upEl('upNewGroup').innerHTML = groupOptions(activeGroup && activeGroup !== '__none__' ? activeGroup : '');
    upEl('upNewGroupWrap').classList.remove('hidden');
  }
}

function planOptions(selected) {
  return '<option value="">— Không chấm —</option>' + window.PLANS_DATA.map(p =>
    `<option value="${esc(p.id)}" ${p.id === selected ? 'selected' : ''}>${esc(p.name)}</option>`).join('');
}

function weekOptions(planId, selected) {
  const plan = window.PLANS_DATA.find(p => p.id === planId);
  let html = '<option value="">— Không chọn tuần —</option>';
  if (plan) html += plan.weeks.map(w =>
    `<option value="${w.week}" ${w.week === selected ? 'selected' : ''}>T${w.week} · ${esc(w.session_type)} · ${w.total_km}km</option>`).join('');
  return html;
}

function typeOptions(selected) {
  return SESSION_TYPES.map(([v, l]) => `<option value="${v}" ${v === selected ? 'selected' : ''}>${l}</option>`).join('');
}

async function doPreview() {
  const name = upEl('upAthlete').value.trim();
  const file = upEl('upFile').files[0];
  if (!name) return showToast('Thiếu học viên', 'Chọn hoặc nhập tên học viên', 'warn');
  if (!file) return showToast('Chưa chọn file', 'Chọn file .gpx, .fit hoặc .csv', 'warn');

  const btn = upEl('upPreviewBtn');
  btn.disabled = true;
  btn.textContent = 'Đang đọc file…';
  try {
    let a = findAthleteByName(name);
    if (!a) {
      a = await api('/api/athletes', { method: 'POST', json: { name, group_id: upEl('upNewGroup').value || null } });
      await reloadData();
    }
    if (pending) await cancelPreview(true);
    const fd = new FormData();
    fd.append('athlete_id', a.id);
    fd.append('file', file);
    pending = await api('/api/uploads', { method: 'POST', form: fd });
    pending.athlete = a;
    renderPreview();
  } catch (e) {
    showToast('Không đọc được file', e.message, 'err');
  } finally {
    btn.disabled = false;
    btn.textContent = 'Đọc file';
  }
}

function renderPreview() {
  const rows = pending.items.map(it => `
    <tr data-index="${it.index}">
      <td><input type="checkbox" class="pv-use" ${it.duplicate ? '' : 'checked'} style="width:auto"></td>
      <td class="mono">${esc(it.date)}<br><span class="muted">${it.distance_km} km · ${fmtPace(it.avg_pace_sec)}${it.avg_hr ? ' · ' + it.avg_hr + ' bpm' : ''}</span>
        ${it.duplicate ? '<br><span class="tag warn">Trùng buổi đã có</span>' : ''}</td>
      <td>
        <select class="pv-plan">${planOptions(it.suggested_plan_id)}</select>
        <select class="pv-week" style="margin-top:4px">${weekOptions(it.suggested_plan_id, it.suggested_week)}</select>
        <select class="pv-type" style="margin-top:4px">${typeOptions(it.suggested_session_type)}</select>
      </td>
    </tr>`).join('');
  const warn = pending.warnings.length ? `<div class="alert">${pending.warnings.map(esc).join('<br>')}</div>` : '';
  const el = upEl('upPreview');
  el.innerHTML = `
    ${warn}
    <div class="lbl" style="margin-top:1rem">KIỂM TRA TRƯỚC KHI LƯU · ${esc(pending.athlete.name)}</div>
    <table class="tbl"><thead><tr><th></th><th>BUỔI</th><th>GIÁO ÁN · TUẦN · LOẠI</th></tr></thead><tbody>${rows}</tbody></table>
    <div class="btn-row" style="margin-top:.75rem">
      <button class="btn btn-secondary" onclick="cancelPreview()">Hủy</button>
      <button class="btn" id="upConfirmBtn" onclick="doConfirm()">Lưu & chấm điểm</button>
    </div>`;
  el.classList.remove('hidden');
  el.querySelectorAll('.pv-plan').forEach(sel => sel.addEventListener('change', () => {
    sel.closest('tr').querySelector('.pv-week').innerHTML = weekOptions(sel.value, null);
  }));
  upEl('upResult').innerHTML = '';
}

async function cancelPreview(silent) {
  if (!pending) return;
  try { await api(`/api/uploads/${pending.token}`, { method: 'DELETE' }); } catch (e) { /* đã hết hạn */ }
  pending = null;
  upEl('upPreview').classList.add('hidden');
  upEl('upPreview').innerHTML = '';
  if (!silent) showToast('Đã hủy', 'File chưa được lưu', 'warn');
}

async function doConfirm() {
  const items = [...upEl('upPreview').querySelectorAll('tbody tr')]
    .filter(tr => tr.querySelector('.pv-use').checked)
    .map(tr => ({
      index: Number(tr.dataset.index),
      plan_id: tr.querySelector('.pv-plan').value || null,
      plan_week: tr.querySelector('.pv-week').value ? Number(tr.querySelector('.pv-week').value) : null,
      session_type: tr.querySelector('.pv-type').value,
    }));
  if (!items.length) return showToast('Chưa chọn buổi nào', 'Tick ít nhất một buổi để lưu', 'warn');
  upEl('upConfirmBtn').disabled = true;
  try {
    const res = await api(`/api/uploads/${pending.token}/confirm`, { method: 'POST', json: { items } });
    const athlete = pending.athlete;
    pending = null;
    upEl('upPreview').classList.add('hidden');
    upEl('upFile').value = '';
    upEl('upFileName').textContent = '';
    renderResult(res, athlete);
    await reloadData();
  } catch (e) {
    upEl('upConfirmBtn').disabled = false;
    showToast('Không lưu được', e.message, 'err');
  }
}

function renderResult(res, athlete) {
  const saved = res.saved.map(a => {
    const an = a.analysis;
    return `<div class="result-item">
      <span class="result-score">${an.badge} ${an.score ?? '—'}</span>
      <span class="mono"> ${esc(a.date)} · ${a.distance_km} km · ${fmtPace(a.avg_pace_sec)} · ${esc(a.session_type)}${a.plan_week ? ' · T' + a.plan_week : ''}</span>
      ${an.flags.length ? `<ul class="flags">${an.flags.map(f => `<li>${esc(f)}</li>`).join('')}</ul>` : ''}
      ${an.note ? `<div class="note">${esc(an.note)}</div>` : ''}
    </div>`;
  }).join('');
  const skipped = res.skipped.length ? `<div class="note">${res.skipped.length} buổi bị bỏ qua vì trùng với buổi đã có.</div>` : '';
  upEl('upResult').innerHTML = `${saved}${skipped}
    <a class="btn-sm" href="/athletes/${encodeURIComponent(athlete.id)}" style="display:inline-block;margin-top:.5rem;text-decoration:none">Xem hồ sơ ${esc(athlete.name)} →</a>`;
  showToast(res.saved.length ? `Đã lưu ${res.saved.length} buổi` : 'Không có buổi mới', res.skipped.length ? `${res.skipped.length} buổi trùng` : '', res.saved.length ? 'ok' : 'warn');
}

upEl('upAthlete').addEventListener('input', onAthleteInput);
upEl('upFile').addEventListener('change', e => { upEl('upFileName').textContent = e.target.files[0] ? e.target.files[0].name : ''; });
const dz = upEl('dropZone');
['dragenter', 'dragover'].forEach(ev => dz.addEventListener(ev, () => dz.classList.add('dragover')));
['dragleave', 'drop'].forEach(ev => dz.addEventListener(ev, () => dz.classList.remove('dragover')));
upEl('upPreviewBtn').addEventListener('click', doPreview);
