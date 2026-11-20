function fmtPace(sec) {
  if (!sec || sec <= 0) return '—';
  const m = Math.floor(sec / 60), s = Math.round(sec % 60);
  return `${m}:${String(s).padStart(2, '0')}/km`;
}

function esc(v) {
  return String(v ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}

let toastTimer = null;
function showToast(title, body = '', type = 'ok') {
  const el = document.getElementById('toast');
  el.className = `toast ${type}`;
  el.innerHTML = `<div class="toast-title">${esc(title)}</div><div class="toast-body">${esc(body)}</div>`;
  requestAnimationFrame(() => el.classList.add('show'));
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => el.classList.remove('show'), 4500);
}

async function api(path, { method = 'GET', json, form } = {}) {
  const opts = { method, headers: {} };
  if (json !== undefined) {
    opts.headers['Content-Type'] = 'application/json';
    opts.body = JSON.stringify(json);
  } else if (form) {
    opts.body = form;
  }
  let res;
  try {
    res = await fetch(path, opts);
  } catch (e) {
    throw new Error('Không kết nối được tới app');
  }
  let data = null;
  try { data = await res.json(); } catch (e) { /* non-JSON */ }
  if (!res.ok) throw new Error((data && data.error) || `Lỗi ${res.status}`);
  return data;
}

function openModal(id) { document.getElementById(id).classList.add('open'); }
function closeModal(id) { document.getElementById(id).classList.remove('open'); }
