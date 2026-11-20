const PHASE_COLORS = ['#3b82f6', '#f59e0b', '#22c55e', '#a855f7', '#ef4444', '#14b8a6'];
let planChart = null;
let currentPlanId = null;

function phaseColor(n) { return PHASE_COLORS[(n - 1) % PHASE_COLORS.length]; }

function renderPlanTabs() {
  document.getElementById('planTabs').innerHTML = window.PLANS_DATA.map(p =>
    `<button class="gtab ${p.id === currentPlanId ? 'active' : ''}" onclick="selectPlan('${esc(p.id)}')">${esc(p.name)}</button>`).join('');
}

function selectPlan(id) {
  currentPlanId = id;
  const plan = window.PLANS_DATA.find(p => p.id === id);
  renderPlanTabs();
  const total = plan.weeks.reduce((s, w) => s + w.total_km, 0);
  document.getElementById('planSummary').textContent =
    `${plan.description || ''} · ${plan.total_weeks} tuần · tổng ${Math.round(total)} km · đỉnh ${Math.max(...plan.weeks.map(w => w.total_km))} km/tuần`;

  const phases = [...new Map(plan.weeks.map(w => [w.phase, w.phase_name])).entries()];
  document.getElementById('phaseLegend').innerHTML = phases.map(([n, name]) =>
    `<span class="pl-item"><span class="pl-dot" style="background:${phaseColor(n)}"></span>${esc(name)}</span>`).join('') +
    '<span class="pl-item">· mờ = giảm tải · viền đứt = taper · viền vàng = race</span>';

  document.getElementById('planWeeks').innerHTML = plan.weeks.map(w => `
    <div class="week-chip ${w.deload ? 'deload' : ''} ${w.taper ? 'taper' : ''} ${w.race_week ? 'race' : ''}"
         style="border-bottom:3px solid ${phaseColor(w.phase)}" onclick="showWeek(${w.week})">
      <div class="wc-num">T${w.week}</div><div class="wc-km">${w.total_km}km</div>
    </div>`).join('');
  document.getElementById('weekDetail').classList.add('hidden');

  if (planChart) planChart.destroy();
  planChart = new Chart(document.getElementById('planChart'), {
    type: 'bar',
    data: {
      labels: plan.weeks.map(w => 'T' + w.week),
      datasets: [
        { label: 'Km/tuần', data: plan.weeks.map(w => w.total_km), backgroundColor: plan.weeks.map(w => phaseColor(w.phase) + (w.deload ? '66' : 'cc')), borderRadius: 3 },
        { label: 'Long run', type: 'line', data: plan.weeks.map(w => w.long_run_km), borderColor: '#00e5ff', pointRadius: 2, tension: .3 },
      ],
    },
    options: {
      maintainAspectRatio: false,
      onClick: (_, els) => { if (els.length) showWeek(els[0].index + 1); },
      plugins: { legend: { labels: { color: '#64748b' } } },
      scales: { x: { ticks: { color: '#64748b' }, grid: { color: '#1e2d45' } }, y: { ticks: { color: '#64748b' }, grid: { color: '#1e2d45' } } },
    },
  });
}

function showWeek(n) {
  const plan = window.PLANS_DATA.find(p => p.id === currentPlanId);
  const w = plan.weeks[n - 1];
  document.querySelectorAll('.week-chip').forEach((el, i) => el.classList.toggle('sel', i === n - 1));
  const flags = [w.deload && 'Giảm tải', w.taper && 'Taper', w.race_week && 'Tuần race'].filter(Boolean);
  const el = document.getElementById('weekDetail');
  el.innerHTML = `<b>Tuần ${w.week}</b> · ${esc(w.phase_name)} ${flags.map(f => `<span class="tag warn">${f}</span>`).join(' ')}<br>
    Tổng ${w.total_km} km · long run ${w.long_run_km} km · trọng tâm <b>${esc(w.session_type)}</b><br>
    Pace ${fmtPace(w.target_pace_min).replace('/km', '')}–${fmtPace(w.target_pace_max)} · HR ≤ ${w.target_hr_max}
    ${w.note ? `<div class="note">${esc(w.note)}</div>` : ''}`;
  el.classList.remove('hidden');
}

if (window.PLANS_DATA.length) selectPlan(window.DEFAULT_PLAN_ID || window.PLANS_DATA[0].id);
else document.getElementById('planSummary').textContent = 'Chưa có giáo án hợp lệ trong thư mục plans/.';
