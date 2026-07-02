// Executive Reliability Dashboard — client interactions (vanilla, no deps).

// Tab switching
function exShowTab(name, btn) {
  document.querySelectorAll('.exec-dash .ex-panel').forEach(function (p) {
    p.classList.toggle('hidden', p.getAttribute('data-panel') !== name);
  });
  document.querySelectorAll('.exec-dash .ex-tab').forEach(function (t) {
    t.classList.remove('active');
  });
  if (btn) btn.classList.add('active');
}

// Refresh Snapshot — placeholder (no backend). Later: re-fetch snapshot API.
function exRefreshSnapshot(btn) {
  if (!btn) return;
  var original = btn.textContent;
  btn.classList.add('loading');
  btn.textContent = '⟳ Refreshing…';
  setTimeout(function () {
    btn.classList.remove('loading');
    btn.textContent = original;
    // TODO: replace with fetch('/api/executive/snapshot') and re-render.
  }, 900);
}

// Period switch — fetches the dashboard fragment and swaps it in place,
// so changing the period never triggers a full page reload.
async function exLoadPeriod(period, pushHistory) {
  var current = document.querySelector('.exec-dash');
  if (!current) return;
  var activeTab = document.querySelector('.exec-dash .ex-tab.active');
  var activeTabName = activeTab ? activeTab.getAttribute('data-tab') : 'overview';
  // Only mark the select as loading — no full-dash dimming
  current.classList.add('ex-loading');
  try {
    var res = await fetch('/dashboard/executive/fragment?period=' + encodeURIComponent(period));
    if (!res.ok) throw new Error('fragment fetch failed');
    var html = await res.text();
    var wrap = document.createElement('div');
    wrap.innerHTML = html;
    var next = wrap.querySelector('.exec-dash');
    if (!next) throw new Error('fragment missing .exec-dash');
    current.replaceWith(next);
    var nextBtn = next.querySelector('.ex-tab[data-tab="' + activeTabName + '"]');
    exShowTab(activeTabName, nextBtn);
    if (pushHistory !== false) {
      var url = new URL(window.location.href);
      url.searchParams.set('period', period);
      window.history.pushState({ period: period }, '', url);
    }
  } catch (e) {
    // Fallback: normal navigation if the fragment endpoint is unreachable.
    window.location.href = '/dashboard/executive?period=' + encodeURIComponent(period);
  }
}

function exChangePeriod(period) {
  exLoadPeriod(period, true);
}

window.addEventListener('popstate', function (e) {
  var period = (e.state && e.state.period) || new URL(window.location.href).searchParams.get('period') || '';
  exLoadPeriod(period, false);
});

// Expose for inline handlers
window.exShowTab = exShowTab;
window.exRefreshSnapshot = exRefreshSnapshot;
window.exChangePeriod = exChangePeriod;
