document.addEventListener("DOMContentLoaded", async () => {
  // Check authentication on page load
  const user = await checkAuthStatus();
  if (!user) {
    redirectToLogin("/history");
    return;
  }

  const tableBody = document.querySelector("#receiptTable tbody");
  const categoryFilter = document.getElementById("categoryFilter");
  const clearFilters = document.getElementById("clearFilters");

  // Fetch categories and populate dropdown
  function loadCategories() {
    fetch("/api/receipts/categories", {
      credentials: "include",
    })
      .then((res) => {
        if (res.status === 401) {
          handleUnauthorized("/history");
          return null;
        }
        return res.json();
      })
      .then((data) => {
        if (!data) return; // Handled by redirect
        // Clear existing options except "All Categories"
        categoryFilter.innerHTML = '<option value="">All Categories</option>';
        // Add categories from API
        data.categories.forEach((category) => {
          const option = document.createElement("option");
          option.value = category;
          option.textContent = category;
          categoryFilter.appendChild(option);
        });
      })
      .catch((error) => {
        console.error("Error loading categories:", error);
      });
  }

  function fetchReceipts() {
    const category = categoryFilter.value;
    const url = category
      ? `/api/receipts?category=${encodeURIComponent(category)}`
      : "/api/receipts";

    fetch(url, {
      credentials: "include",
    })
      .then((res) => {
        if (res.status === 401) {
          handleUnauthorized("/history");
          return null;
        }
        return res.json();
      })
      .then((data) => {
        if (!data) return; // Handled by redirect
        tableBody.innerHTML = "";
        if (data.receipts && data.receipts.length > 0) {
          data.receipts.forEach((receipt) => {
            const row = document.createElement("tr");
            const date = receipt.date || "N/A";
            const merchant = receipt.merchant || "N/A";
            const total = receipt.total
              ? `$${receipt.total.toFixed(2)}`
              : "$0.00";
            const category = receipt.category || "Uncategorized";
            row.innerHTML = `
              <td>${date}</td>
              <td>${merchant}</td>
              <td>${total}</td>
              <td>${category}</td>
              <td><button class="btn btn-sm btn-danger" data-id="${receipt._id}">Delete</button></td>
            `;
            tableBody.appendChild(row);
          });
        } else {
          const row = document.createElement("tr");
          row.innerHTML =
            '<td colspan="5" class="text-center">No receipts found</td>';
          tableBody.appendChild(row);
        }
      })
      .catch((error) => {
        console.error("Error fetching receipts:", error);
        tableBody.innerHTML =
          '<tr><td colspan="5" class="text-center text-danger">Error loading receipts</td></tr>';
      });
  }

  categoryFilter.addEventListener("change", fetchReceipts);
  clearFilters.addEventListener("click", () => {
    categoryFilter.value = "";
    fetchReceipts();
  });

  tableBody.addEventListener("click", (e) => {
    if (e.target.tagName === "BUTTON") {
      const id = e.target.dataset.id;
      fetch(`/api/receipts/${id}`, {
        method: "DELETE",
        credentials: "include",
      })
        .then((res) => {
          if (res.status === 401) {
            handleUnauthorized("/history");
            return;
          }
          fetchReceipts();
        })
        .catch((error) => {
          console.error("Delete error:", error);
        });
    }
  });

  // Load categories and receipts on page load
  loadCategories();
  fetchReceipts();
});
