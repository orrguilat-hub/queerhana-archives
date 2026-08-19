function escapeHTML(str) {
  if (!str) return '';
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

async function loadEvents() {
  const [catalogRes, eventsRes] = await Promise.all([
    fetch('data/catalog.json'),
    fetch('data/events.json'),
  ]);
  const catalog = await catalogRes.json();
  const eventsData = await eventsRes.json();

  const counts = {};
  catalog.forEach(item => {
    const ev = (item.event || '').trim();
    if (ev) counts[ev] = (counts[ev] || 0) + 1;
  });

  // Every canonical event from events.json, even one with zero items right
  // now, so the finding aid stays complete -- sorted by item count like
  // EVENTS.md's own table.
  const names = Object.keys(eventsData).sort((a, b) => (counts[b] || 0) - (counts[a] || 0));

  const list = document.getElementById('events-list');
  list.innerHTML = names.map(name => {
    const count = counts[name] || 0;
    const description = (eventsData[name] && eventsData[name].description || '').trim();
    const href = `index.html?event=${encodeURIComponent(name)}#archive`;
    return `
      <article class="event-card">
        <h2><a href="${href}">${escapeHTML(name)}</a></h2>
        <div class="event-card-count">${count} item${count === 1 ? '' : 's'}</div>
        ${description ? `<p class="event-card-desc">${escapeHTML(description)}</p>` : ''}
      </article>
    `;
  }).join('');
}

loadEvents();
