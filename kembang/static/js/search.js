document.addEventListener('DOMContentLoaded', function () {
  const input = document.querySelector('.ledger-search-input');
  if (!input) return;

  const rows = document.querySelectorAll('[data-search]');
  const tableWrapper = document.querySelector('.table-wrapper') || document.querySelector('.mixed-card-container');
  const mobileWrapper = document.querySelector('.mobile-table');

  let noResultDesktop = null;
  let noResultMobile = null;

  function showNoResult(wrapper, existing, query) {
    if (!wrapper) return existing;
    if (!existing) {
      existing = document.createElement('div');
      existing.className = 'empty-row';
      wrapper.appendChild(existing);
    }
    existing.innerHTML = '<i class="fa-solid fa-magnifying-glass"></i>Tidak ada hasil untuk "' + query + '"';
    existing.style.display = 'block';
    return existing;
  }

  function hideNoResult(existing) {
    if (existing) existing.style.display = 'none';
  }

  input.addEventListener('input', function () {
    const query = input.value.trim().toLowerCase();
    let anyVisible = false;

    rows.forEach(function (row) {
      const haystack = (row.getAttribute('data-search') || '').toLowerCase();
      const match = haystack.includes(query);
      row.style.display = match ? '' : 'none';
      if (match) anyVisible = true;
    });

    if (query === '' || anyVisible) {
      hideNoResult(noResultDesktop);
      hideNoResult(noResultMobile);
    } else {
      noResultDesktop = showNoResult(tableWrapper, noResultDesktop, query);
      noResultMobile = showNoResult(mobileWrapper, noResultMobile, query);
    }
  });
});