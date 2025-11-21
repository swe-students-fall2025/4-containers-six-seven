document.addEventListener('DOMContentLoaded', () => {
  const tableBody = document.querySelector('#receiptTable tbody');
  const categoryFilter = document.getElementById('categoryFilter');
  const clearFilters = document.getElementById('clearFilters');

  function fetchReceipts() {
  const category = categoryFilter.value;

  fetch(`/api/receipts?category=${category}`)
    .then(res => res.json())
    .then(data => {
      tableBody.innerHTML = '';
      data.receipts.forEach(receipt => {
        const row = document.createElement('tr');
        row.innerHTML = `
          <td>${receipt.date}</td>
          <td>$${receipt.amount.toFixed(2)}</td>
          <td>${receipt.category}</td>
          <td><button class="btn btn-sm btn-danger" data-id="${receipt._id}">Delete</button></td>
        `;
        tableBody.appendChild(row);
      });
    });
  }

  categoryFilter.addEventListener('change', fetchReceipts);
  clearFilters.addEventListener('click', () => {
    categoryFilter.value = '';
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