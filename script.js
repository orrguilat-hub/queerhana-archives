const TYPE_LABELS = {
  pdf: 'Document',
  video: 'Video',
  image: 'Photo'
};

const PAGE_SIZE = 8;

let allItems = [];
let currentFilter = 'all';
let searchTerm = '';
let visibleCount = PAGE_SIZE;
let advFilters = { yearStart: '', yearEnd: '', event: '', location: '', credit: '' };

async function loadCatalog() {
  const res = await fetch('data/catalog.json');
  allItems = await res.json();
  document.getElementById('item-count').textContent = `${allItems.length} items catalogued`;
  render();
}

function matchesSearch(item, term) {
  if (!term) return true;
  const haystack = [
    item.title, item.description, item.created_year, item.credit_text
  ].filter(Boolean).join(' ').toLowerCase();
  return haystack.includes(term);
}

function parseYear(str) {
  if (!str) return null;
  const m = String(str).match(/\d{4}/);
  return m ? parseInt(m[0], 10) : null;
}

function matchesAdvanced(item) {
  const year = parseYear(item.created_year);
  if (advFilters.yearStart && year !== null && year < parseInt(advFilters.yearStart, 10)) return false;
  if (advFilters.yearEnd && year !== null && year > parseInt(advFilters.yearEnd, 10)) return false;
  if (advFilters.event && !(item.event || '').toLowerCase().includes(advFilters.event)) return false;
  if (advFilters.location && !(item.location || '').toLowerCase().includes(advFilters.location)) return false;
  if (advFilters.credit && !(item.credit_text || '').toLowerCase().includes(advFilters.credit)) return false;
  return true;
}

// Internet Archive URL helpers
const iaThumb    = id => `https://archive.org/services/img/${id}`;
const iaDetails  = id => `https://archive.org/details/${id}`;
const iaDownload = (id, file) => `https://archive.org/download/${id}/${encodeURIComponent(file)}`;

function getFilteredItems() {
  const term = searchTerm.trim().toLowerCase();
  return allItems
    .filter(i => currentFilter === 'all' || i.file_type === currentFilter)
    .filter(i => matchesSearch(i, term))
    .filter(matchesAdvanced);
}

function render() {
  const grid = document.getElementById('catalog-grid');
  grid.innerHTML = '';

  const items = getFilteredItems();
  const shown = items.slice(0, visibleCount);

  if (shown.length === 0) {
    grid.innerHTML = '<p class="empty-msg">No items match your search.</p>';
  }

  shown.forEach(item => {
    const card = document.createElement('article');
    card.className = 'card';

    const credit = item.credit_text ? `Credit: ${item.credit_text}` : '';
    const tagClass = `tag-${item.file_type}`;
    const tagLabel = (TYPE_LABELS[item.file_type] || item.file_type).toUpperCase();

    const thumbHTML = (item.file_type === 'pdf' && item.excerpt)
      ? `<div class="card-thumb card-thumb--text">
           <span class="card-tag ${tagClass}">${tagLabel}</span>
           <p class="excerpt">${escapeHTML(item.excerpt)}</p>
         </div>`
      : `<a class="card-thumb" href="${iaDetails(item.archive_id)}" target="_blank" rel="noopener" aria-label="View ${escapeHTML(item.title)} on the Internet Archive">
           <span class="card-tag ${tagClass}">${tagLabel}</span>
           <img src="${iaThumb(item.archive_id)}" alt="${escapeHTML(item.title)}" loading="lazy"
                onerror="this.closest('.card-thumb').classList.add('noimg'); this.remove();">
         </a>`;

    card.innerHTML = `
      ${thumbHTML}
      <div class="card-body">
        <div>
          <h3 class="card-title">${escapeHTML(item.title)}</h3>
          <p class="card-desc">${escapeHTML(item.description)}</p>
          <div class="card-meta">
            <span>${escapeHTML(item.created_year)}</span>
            ${credit ? `<span>${escapeHTML(credit)}</span>` : ''}
          </div>
        </div>
        <div class="card-footer">
          <span class="card-license">${escapeHTML(item.cc_license)}</span>
          <div class="card-actions">
            <a href="${iaDetails(item.archive_id)}" target="_blank" rel="noopener" aria-label="View ${escapeHTML(item.title)}" title="View">&#8599;</a>
            <a href="${iaDownload(item.archive_id, item.ia_file)}" target="_blank" rel="noopener" aria-label="Download ${escapeHTML(item.title)}" title="Download">&#8595;</a>
          </div>
        </div>
      </div>
    `;
    grid.appendChild(card);
  });

  const loadMoreBtn = document.getElementById('load-more');
  loadMoreBtn.hidden = items.length <= visibleCount;
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
    visibleCount = PAGE_SIZE;
    render();
  });
});

document.getElementById('search-input').addEventListener('input', (e) => {
  searchTerm = e.target.value;
  visibleCount = PAGE_SIZE;
  render();
});

document.getElementById('apply-filters').addEventListener('click', () => {
  advFilters = {
    yearStart: document.getElementById('filter-year-start').value.trim(),
    yearEnd: document.getElementById('filter-year-end').value.trim(),
    event: document.getElementById('filter-event').value.trim().toLowerCase(),
    location: document.getElementById('filter-location').value.trim().toLowerCase(),
    credit: document.getElementById('filter-credit').value.trim().toLowerCase()
  };
  visibleCount = PAGE_SIZE;
  render();
});

document.getElementById('load-more').addEventListener('click', () => {
  visibleCount += PAGE_SIZE;
  render();
});

document.getElementById('filters-toggle').addEventListener('click', () => {
  const toggle = document.getElementById('filters-toggle');
  const filters = document.getElementById('adv-filters');
  const isOpen = filters.classList.toggle('open');
  toggle.setAttribute('aria-expanded', isOpen);
});

loadCatalog();
