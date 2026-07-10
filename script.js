const TYPE_LABELS = {
  pdf: 'Text / Flyer',
  video: 'Video',
  image: 'Photo'
};

let allItems = [];
let currentFilter = 'all';
let searchTerm = '';

async function loadCatalog() {
  const res = await fetch('data/catalog.json');
  allItems = await res.json();
  render();
}

function matchesSearch(item, term) {
  if (!term) return true;
  const haystack = [
    item.title, item.description, item.created_year, item.credit_text
  ].filter(Boolean).join(' ').toLowerCase();
  return haystack.includes(term);
}

// Internet Archive URL helpers
const iaThumb    = id => `https://archive.org/services/img/${id}`;
const iaDetails  = id => `https://archive.org/details/${id}`;
const iaDownload = (id, file) => `https://archive.org/download/${id}/${encodeURIComponent(file)}`;

function render() {
  const grid = document.getElementById('catalog-grid');
  grid.innerHTML = '';

  const term = searchTerm.trim().toLowerCase();

  const items = allItems
    .filter(i => currentFilter === 'all' || i.file_type === currentFilter)
    .filter(i => matchesSearch(i, term));

  if (items.length === 0) {
    grid.innerHTML = '<p style="font-family: var(--font-mono);">No items match your search.</p>';
    return;
  }

  items.forEach(item => {
    const card = document.createElement('article');
    card.className = 'card';

    const credit = item.credit_text ? `Credit: ${item.credit_text}` : '';

    card.innerHTML = `
      <a class="card-thumb" href="${iaDetails(item.archive_id)}" target="_blank" rel="noopener" aria-label="View ${escapeHTML(item.title)} on the Internet Archive">
        <img src="${iaThumb(item.archive_id)}" alt="${escapeHTML(item.title)}" loading="lazy"
             onerror="this.closest('.card-thumb').classList.add('noimg'); this.remove();">
      </a>
      <span class="card-type">${TYPE_LABELS[item.file_type] || item.file_type}</span>
      <h2 class="card-title">${escapeHTML(item.title)}</h2>
      <p class="card-desc">${escapeHTML(item.description)}</p>
      <div class="card-meta">
        <span>${escapeHTML(item.created_year)}</span>
        ${credit ? `<span>${escapeHTML(credit)}</span>` : ''}
      </div>
      <span class="card-license">${escapeHTML(item.cc_license)}</span>
      <div class="card-links">
        <a class="card-link" href="${iaDetails(item.archive_id)}" target="_blank" rel="noopener">View&nbsp;↗</a>
        <a class="card-link card-link--alt" href="${iaDownload(item.archive_id, item.ia_file)}" target="_blank" rel="noopener">Download&nbsp;↓</a>
      </div>
    `;
    grid.appendChild(card);
  });
}

function escapeHTML(str) {
  if (!str) return '';
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

document.querySelectorAll('.filter-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelector('.filter-btn.active').classList.remove('active');
    btn.classList.add('active');
    currentFilter = btn.dataset.filter;
    render();
  });
});

document.getElementById('search-input').addEventListener('input', (e) => {
  searchTerm = e.target.value;
  render();
});

loadCatalog();
