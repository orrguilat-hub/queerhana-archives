// ---------- Featured reference section: rotating preview images ----------
// One pool per card. Edit an array to add/remove images -- one image is
// picked at random from its own pool on every page load (no cycling). A
// static site has no way to read a folder's contents at runtime, so
// filenames are listed explicitly.
const FEATURED_BOOK_IMAGES = [
  'assets/book-frames/screenshot-2026-08-11-8-18-43.png',
  'assets/book-frames/screenshot-2026-08-11-8-19-20.png',
  'assets/book-frames/screenshot-2026-08-11-8-19-30.png',
  'assets/book-frames/screenshot-2026-08-11-8-19-46.png',
  'assets/book-frames/screenshot-2026-08-11-8-20-01.png',
];
const FEATURED_DOCU_IMAGES = [
  'assets/docu-frames/screenshot-2026-08-11-8-03-21.png',
  'assets/docu-frames/screenshot-2026-08-11-8-03-40.png',
  'assets/docu-frames/screenshot-2026-08-11-8-04-08.png',
  'assets/docu-frames/screenshot-2026-08-11-8-04-23.png',
  'assets/docu-frames/screenshot-2026-08-11-8-05-14.png',
  'assets/docu-frames/screenshot-2026-08-11-8-06-10.png',
  'assets/docu-frames/screenshot-2026-08-11-8-07-14.png',
  'assets/docu-frames/screenshot-2026-08-11-8-08-17.png',
  'assets/docu-frames/screenshot-2026-08-11-8-08-35.png',
  'assets/docu-frames/screenshot-2026-08-11-8-09-00.png',
  'assets/docu-frames/screenshot-2026-08-11-8-09-27.png',
  'assets/docu-frames/screenshot-2026-08-11-8-10-20.png',
  'assets/docu-frames/screenshot-2026-08-11-8-11-12.png',
  'assets/docu-frames/screenshot-2026-08-11-8-13-33.png',
  'assets/docu-frames/screenshot-2026-08-11-8-14-21.png',
  'assets/docu-frames/screenshot-2026-08-11-8-17-01.png',
];
const FEATURED_SITE_IMAGES = [
  'assets/site-frames/screenshot-2026-08-11-7-47-55.png',
  'assets/site-frames/screenshot-2026-08-11-8-23-41.png',
  'assets/site-frames/screenshot-2026-08-11-8-24-42.png',
  'assets/site-frames/screenshot-2026-08-11-8-26-52.png',
  'assets/site-frames/site-frame.png',
];
// Used only if a pool above is ever emptied out -- an existing site asset,
// never a generated placeholder.
const FEATURED_FALLBACK_IMAGE = 'assets/bones-smiley.png';

function setRandomFeaturedImage(imgId, pool) {
  const img = document.getElementById(imgId);
  if (!img) return;
  const list = pool && pool.length ? pool : [FEATURED_FALLBACK_IMAGE];
  const choice = list[Math.floor(Math.random() * list.length)];
  img.src = encodeURI(choice);
}

setRandomFeaturedImage('featured-img-book', FEATURED_BOOK_IMAGES);
setRandomFeaturedImage('featured-img-docu', FEATURED_DOCU_IMAGES);
setRandomFeaturedImage('featured-img-site', FEATURED_SITE_IMAGES);

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
  applyStateFromURL({ fromPopstate: true });
}

function matchesSearch(item, term) {
  if (!term) return true;
  const haystack = [
    item.title, item.description, item.created_year, item.credit_text
  ].filter(Boolean).join(' ').toLowerCase();
  return haystack.includes(term);
}

function parseTags(item) {
  if (!item.subject_tags) return [];
  return item.subject_tags.split(';').map(t => t.trim()).filter(Boolean);
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
    card.tabIndex = 0;
    card.setAttribute('role', 'button');
    card.setAttribute('aria-label', `View details for ${item.title}`);

    const tagClass = `tag-${item.file_type}`;
    const tagLabel = (TYPE_LABELS[item.file_type] || item.file_type).toUpperCase();
    const tags = parseTags(item);
    const tagsHTML = tags.length
      ? `<div class="card-tags">${tags.map(t => `<span class="tag-chip">${escapeHTML(t)}</span>`).join('')}</div>`
      : '';

    const thumbHTML = (item.file_type === 'pdf' && item.excerpt)
      ? `<div class="card-thumb card-thumb--text">
           <span class="card-tag ${tagClass}">${tagLabel}</span>
           <p class="excerpt">${escapeHTML(item.excerpt)}</p>
         </div>`
      : `<div class="card-thumb">
           <span class="card-tag ${tagClass}">${tagLabel}</span>
           <img src="${iaThumb(item.archive_id)}" alt="${escapeHTML(item.title)}" loading="lazy"
                onerror="this.closest('.card-thumb').classList.add('noimg'); this.remove();">
         </div>`;

    card.innerHTML = `
      ${thumbHTML}
      <div class="card-body">
        <h3 class="card-title">${escapeHTML(item.title)}</h3>
        ${item.event ? `<div class="card-event">${escapeHTML(item.event)}</div>` : ''}
        ${tagsHTML}
      </div>
    `;
    card.addEventListener('click', () => openModal(item));
    card.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); openModal(item); }
    });
    grid.appendChild(card);
  });

  const loadMoreBtn = document.getElementById('load-more');
  loadMoreBtn.hidden = items.length <= visibleCount;
}

// ---------- Item detail modal ----------
let lastFocusedEl = null;
let openItemId = null;
let modalPushed = false; // true when the open modal's URL entry was pushed by us (safe to history.back() to close)

function openModal(item, opts = {}) {
  openItemId = String(item.id);
  const tagLabel = (TYPE_LABELS[item.file_type] || item.file_type).toUpperCase();
  const tagClass = `tag-${item.file_type}`;

  const thumbEl = document.getElementById('modal-thumb');
  const tagBadge = `<span class="card-tag ${tagClass}">${tagLabel}</span>`;
  if (item.file_type === 'pdf' && item.excerpt) {
    thumbEl.className = 'modal-thumb';
    thumbEl.innerHTML = `${tagBadge}<p class="excerpt">${escapeHTML(item.excerpt)}</p>`;
  } else {
    thumbEl.className = 'modal-thumb';
    thumbEl.innerHTML = tagBadge;
    const img = document.createElement('img');
    img.alt = item.title || '';
    img.src = iaThumb(item.archive_id);
    img.addEventListener('error', () => {
      thumbEl.classList.add('noimg');
      img.remove();
    });
    thumbEl.appendChild(img);

    // The thumbnail above is IA's small services/img preview -- swap it for
    // the actual full-resolution original once that's loaded, so the modal
    // never permanently shows a lower-res image than the real file. Only
    // for file_type 'image': video/pdf originals aren't renderable as <img>,
    // and their download link already points at the real file.
    if (item.file_type === 'image' && item.ia_file) {
      img.classList.add('modal-thumb-loading');
      const fullRes = new Image();
      fullRes.onload = () => {
        img.src = fullRes.src;
        img.classList.remove('modal-thumb-loading');
      };
      fullRes.onerror = () => {
        img.classList.remove('modal-thumb-loading');
      };
      fullRes.src = iaDownload(item.archive_id, item.ia_file);
    }
  }

  document.getElementById('modal-title').textContent = item.title || '';

  const fields = [
    ['Event', item.event],
    ['Location', item.location],
    ['Date', item.created_year],
    ['Credit', item.credit_text],
    ['Rights holder', item.rights_owner],
    ['License', item.cc_license],
  ].filter(([, v]) => v);
  document.getElementById('modal-fields').innerHTML = fields
    .map(([k, v]) => `<dt>${escapeHTML(k)}</dt><dd>${escapeHTML(v)}</dd>`).join('');

  const tags = parseTags(item);
  document.getElementById('modal-tags').innerHTML = tags
    .map(t => `<span class="tag-chip">${escapeHTML(t)}</span>`).join('');

  // Observational description stays collapsed by default -- fact fields
  // above (event/location/date/credit) are the archivist's own information;
  // this is model-generated visual description, not a claim the archive
  // is making about who's in the frame. Reset to collapsed on every open.
  const descEl = document.getElementById('modal-desc');
  const descToggle = document.getElementById('modal-desc-toggle');
  descEl.textContent = item.description || '';
  descEl.hidden = true;
  descToggle.setAttribute('aria-expanded', 'false');
  descToggle.setAttribute('aria-label', 'Show description');
  descToggle.hidden = !item.description;

  document.getElementById('modal-actions').innerHTML = `
    <a href="${iaDetails(item.archive_id)}" target="_blank" rel="noopener" aria-label="View ${escapeHTML(item.title)} on the Internet Archive" title="View">&#8599;</a>
    <a href="${iaDownload(item.archive_id, item.ia_file)}" target="_blank" rel="noopener" aria-label="Download ${escapeHTML(item.title)}" title="Download">&#8595;</a>
  `;

  lastFocusedEl = document.activeElement;
  const modal = document.getElementById('item-modal');
  modal.hidden = false;
  document.body.style.overflow = 'hidden';
  document.getElementById('modal-close').focus();

  if (!opts.fromPopstate) {
    modalPushed = pushURL();
  }
}

function closeModal(opts = {}) {
  const modal = document.getElementById('item-modal');
  if (modal.hidden) return;
  modal.hidden = true;
  document.body.style.overflow = '';
  if (lastFocusedEl) lastFocusedEl.focus();
  openItemId = null;

  if (!opts.fromPopstate) {
    if (modalPushed) {
      history.back(); // triggers popstate, which closes for real without pushing again
    } else {
      pushURL(); // nothing of ours to go back to (e.g. arrived via a direct item link)
    }
  }
  modalPushed = false;
}

function toggleDescription() {
  const descEl = document.getElementById('modal-desc');
  const toggle = document.getElementById('modal-desc-toggle');
  const nowShown = descEl.hidden; // about to become the new state
  descEl.hidden = !nowShown;
  toggle.setAttribute('aria-expanded', String(nowShown));
  toggle.setAttribute('aria-label', nowShown ? 'Hide description' : 'Show description');
}
const modalDescToggleEl = document.getElementById('modal-desc-toggle');
modalDescToggleEl.addEventListener('click', toggleDescription);
// Native <button> already activates on Enter/Space via the browser's own
// default action on the click event above -- this handler is redundant in
// every real browser, kept only as explicit belt-and-suspenders since it
// costs nothing and makes the behavior independently verifiable.
modalDescToggleEl.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' || e.key === ' ' || e.key === 'Spacebar') {
    e.preventDefault();
    toggleDescription();
  }
});

document.getElementById('modal-close').addEventListener('click', () => closeModal());
document.getElementById('item-modal').addEventListener('click', (e) => {
  if (e.target.id === 'item-modal') closeModal();
});
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') closeModal();
});

function escapeHTML(str) {
  if (!str) return '';
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

// ---------- URL state: deep links + shareable filters ----------
// One layer, used for two things: opening a specific item's modal directly
// (?item=<id>, back/forward navigates the modal open/closed), and restoring
// search/filter state from a shared link. Filter changes use replaceState
// (typing shouldn't spam browser history); only modal open/close pushes a
// new history entry.
function paramsFromState() {
  const params = new URLSearchParams();
  if (searchTerm) params.set('search', searchTerm);
  if (currentFilter && currentFilter !== 'all') params.set('type', currentFilter);
  if (advFilters.yearStart) params.set('yearStart', advFilters.yearStart);
  if (advFilters.yearEnd) params.set('yearEnd', advFilters.yearEnd);
  if (advFilters.event) params.set('event', advFilters.event);
  if (advFilters.location) params.set('location', advFilters.location);
  if (advFilters.credit) params.set('credit', advFilters.credit);
  if (openItemId) params.set('item', openItemId);
  return params;
}

function urlForState() {
  const qs = paramsFromState().toString();
  return location.pathname + (qs ? '?' + qs : '') + location.hash;
}

function currentFullURL() {
  return location.pathname + location.search + location.hash;
}

function replaceURL() {
  const url = urlForState();
  if (url !== currentFullURL()) history.replaceState(null, '', url);
}

function pushURL() {
  const url = urlForState();
  if (url === currentFullURL()) return false;
  history.pushState(null, '', url);
  return true;
}

function applyStateFromURL(opts = {}) {
  const params = new URLSearchParams(location.search);
  searchTerm = params.get('search') || '';
  currentFilter = params.get('type') || 'all';
  advFilters = {
    yearStart: params.get('yearStart') || '',
    yearEnd: params.get('yearEnd') || '',
    event: (params.get('event') || '').toLowerCase(),
    location: (params.get('location') || '').toLowerCase(),
    credit: (params.get('credit') || '').toLowerCase(),
  };

  document.getElementById('search-input').value = searchTerm;
  document.getElementById('filter-year-start').value = advFilters.yearStart;
  document.getElementById('filter-year-end').value = advFilters.yearEnd;
  document.getElementById('filter-event').value = params.get('event') || '';
  document.getElementById('filter-location').value = params.get('location') || '';
  document.getElementById('filter-credit').value = params.get('credit') || '';
  document.querySelectorAll('.filter-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.filter === currentFilter);
  });

  visibleCount = PAGE_SIZE;
  render();

  const itemId = params.get('item');
  const item = itemId ? allItems.find(i => String(i.id) === itemId) : null;
  if (item) {
    openModal(item, { fromPopstate: true });
  } else {
    closeModal({ fromPopstate: true });
  }
}

window.addEventListener('popstate', () => applyStateFromURL({ fromPopstate: true }));

document.querySelectorAll('.filter-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelector('.filter-btn.active').classList.remove('active');
    btn.classList.add('active');
    currentFilter = btn.dataset.filter;
    visibleCount = PAGE_SIZE;
    render();
    replaceURL();
  });
});

document.getElementById('search-input').addEventListener('input', (e) => {
  searchTerm = e.target.value;
  visibleCount = PAGE_SIZE;
  render();
  replaceURL();
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
  replaceURL();
});

document.getElementById('load-more').addEventListener('click', () => {
  visibleCount += PAGE_SIZE;
  render();
});

document.getElementById('filters-toggle').addEventListener('click', () => {
  const toggle = document.getElementById('filters-toggle');
  const filters = document.getElementById('collapsible-filters');
  const isOpen = filters.classList.toggle('open');
  toggle.setAttribute('aria-expanded', isOpen);
});

loadCatalog();
