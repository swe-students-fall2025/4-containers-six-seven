document.addEventListener('DOMContentLoaded', () => {
  const tableBody = document.querySelector('#receiptTable tbody');
  const categoryFilter = document.getElementById('categoryFilter');
  const merchantSearch = document.getElementById('merchantSearch');
  const clearFilters = document.getElementById('clearFilters');

  function fetchReceipts() {
    const category = categoryFilter.value;
    const merchant = merchantSearch.value;

    fetch(`/api/receipts?category=${category}&merchant=${merchant}`)
      .then(res => res.json())
      .then(data => {
        tableBody.innerHTML = '';
        data.receipts.forEach(receipt => {
          const row = document.createElement('tr');
          row.innerHTML = `
            <td>${receipt.date}</td>
            <td>${receipt.merchant}</td>
            <td>$${receipt.amount.toFixed(2)}</td>
            <td>${receipt.category}</td>
            <td><button class="btn btn-sm btn-danger" data-id="${receipt._id}">Delete</button></td>
          `;
          tableBody.appendChild(row);
        });
      });
  }

  categoryFilter.addEventListener('change', fetchReceipts);
  merchantSearch.addEventListener('input', fetchReceipts);
  clearFilters.addEventListener('click', () => {
    categoryFilter.value = '';
    merchantSearch.value = '';
    fetchReceipts();
  });

  tableBody.addEventListener('click', (e) => {
    if (e.target.tagName === 'BUTTON') {
      const id = e.target.dataset.id;
      fetch(`/api/receipts/${id}`, { method: 'DELETE' })
        .then(() => fetchReceipts());
    }
  });

  fetchReceipts();
});