const STATUS_COLORS = { on_track: '#00e676', under: '#ffd740', over: '#ff9100', in_progress: '#00e5ff', no_target: '#64748b' };
const STATUS_LABELS = { on_track: 'đạt', under: 'thiếu', over: 'vượt', in_progress: 'đang diễn ra', no_target: 'không có mục tiêu' };
Chart.defaults.color = '#64748b';
Chart.defaults.borderColor = '#1e2d45';

function renderCharts() {
  const weeks = window.SUMMARY.weeks;
  const multiPlan = new Set(weeks.map(w => w.plan_id)).size > 1;
  const kmCanvas = document.getElementById('chartKm');
  if (kmCanvas && weeks.length) {
    new Chart(kmCanvas, {
      type: 'bar',
      data: {
        labels: weeks.map(w => (multiPlan ? (window.PLAN_NAMES[w.plan_id] || w.plan_id) + ' ' : '') + 'T' + w.week),
        datasets: [
          { label: 'Thực tế (km)', data: weeks.map(w => w.actual_km), backgroundColor: weeks.map(w => STATUS_COLORS[w.status]), borderRadius: 4 },
          { label: 'Mục tiêu (km)', data: weeks.map(w => w.target_km), backgroundColor: 'rgba(100,116,139,.25)', borderColor: '#64748b', borderWidth: 1, borderRadius: 4 },
        ],
      },
      options: {
        maintainAspectRatio: false,
        plugins: { tooltip: { callbacks: { afterBody: items => `Trạng thái: ${STATUS_LABELS[weeks[items[0].dataIndex].status]} · ${weeks[items[0].dataIndex].sessions} buổi` } } },
      },
    });
  }
  const hrCanvas = document.getElementById('chartHr');
  const withHr = [...window.ACTIVITIES].reverse().filter(a => a.avg_hr);
  if (hrCanvas && withHr.length) {
    new Chart(hrCanvas, {
      type: 'line',
      data: {
        labels: withHr.map(a => a.date),
        datasets: [
          { label: 'HR TB', data: withHr.map(a => a.avg_hr), borderColor: '#ff5252', backgroundColor: 'rgba(255,82,82,.1)', tension: .3, fill: true },
          { label: 'HR tối đa mục tiêu', data: withHr.map(a => a.plan_week_snapshot ? a.plan_week_snapshot.target_hr_max : null), borderColor: '#64748b', borderDash: [4, 4], pointRadius: 0, spanGaps: true },
        ],
      },
      options: { maintainAspectRatio: false },
    });
  }
}

async function deleteActivity(btn) {
  if (!confirm(`Xóa buổi tập ${btn.dataset.label}?\nThao tác này không hoàn tác được.`)) return;
  btn.disabled = true;
  try {
    await api(`/api/athletes/${encodeURIComponent(window.ATHLETE_ID)}/activities/${encodeURIComponent(btn.dataset.id)}`, { method: 'DELETE' });
    location.reload();
  } catch (e) {
    btn.disabled = false;
    showToast('Không xóa được', e.message, 'err');
  }
}

function renderMarkdown(md) {
  const lines = esc(md).split('\n');
  let html = '', inList = false;
  for (const raw of lines) {
    const line = raw.replace(/\*\*(.+?)\*\*/g, '<b>$1</b>');
    const li = line.match(/^\s*[-*]\s+(.*)/);
    if (li) { if (!inList) { html += '<ul>'; inList = true; } html += `<li>${li[1]}</li>`; continue; }
    if (inList) { html += '</ul>'; inList = false; }
    const h = line.match(/^#{1,4}\s+(.*)/);
    if (h) html += `<h4>${h[1]}</h4>`;
    else if (line.trim()) html += `<p>${line}</p>`;
  }
  return html + (inList ? '</ul>' : '');
}

async function getAIFeedback() {
  const btn = document.getElementById('aiBtn');
  const out = document.getElementById('aiOutput');
  btn.disabled = true;
  btn.textContent = 'Đang phân tích…';
  out.innerHTML = '<p class="muted">AI đang đọc các buổi tập gần nhất, có thể mất 10–60 giây…</p>';
  try {
    const res = await api(`/api/athletes/${encodeURIComponent(window.ATHLETE_ID)}/ai-feedback`, {
      method: 'POST', json: { plan_id: window.AI_PLAN_ID, plan_week: Number(document.getElementById('aiWeek').value) },
    });
    out.innerHTML = renderMarkdown(res.feedback);
  } catch (e) {
    out.innerHTML = `<div class="alert">⚠️ ${esc(e.message)}</div>`;
  } finally {
    btn.disabled = false;
    btn.textContent = '✨ Phân tích lại';
  }
}

function preselectAiWeek() {
  const sel = document.getElementById('aiWeek');
  const latest = window.ACTIVITIES.find(a => a.plan_id === window.AI_PLAN_ID && a.plan_week);
  if (sel && latest) sel.value = String(latest.plan_week);
}

document.querySelectorAll('button[data-id]').forEach(b => b.addEventListener('click', () => deleteActivity(b)));
document.getElementById('aiBtn').addEventListener('click', getAIFeedback);
preselectAiWeek();
renderCharts();
