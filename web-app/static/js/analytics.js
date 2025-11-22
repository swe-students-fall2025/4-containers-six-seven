document.addEventListener("DOMContentLoaded", async () => {
  // Check authentication on page load
  const user = await checkAuthStatus();
  if (!user) {
    redirectToLogin("/analytics");
    return;
  }

  // Color palette for category chart
  const colors = [
    "#0d6efd",
    "#6610f2",
    "#198754",
    "#ffc107",
    "#dc3545",
    "#0dcaf0",
    "#fd7e14",
    "#6f42c1",
    "#20c997",
    "#e83e8c",
    "#6c757d",
  ];

  // Initialize charts with empty data
  const categoryChart = new Chart(document.getElementById("categoryChart"), {
    type: "pie",
    data: {
      labels: [],
      datasets: [
        {
          data: [],
          backgroundColor: colors,
        },
      ],
    },
    options: {
      plugins: {
        title: {
          display: true,
          text: "Spending by Category",
        },
      },
    },
  });

  const monthlyChart = new Chart(document.getElementById("monthlyChart"), {
    type: "line",
    data: {
      labels: [],
      datasets: [
        {
          label: "Total Spending (USD)",
          data: [],
          borderColor: "#0d6efd",
          fill: false,
        },
      ],
    },
    options: {
      plugins: {
        title: {
          display: true,
          text: "Spending Over Time",
        },
      },
    },
  });

  // Fetch analytics data from API
  fetch("/api/receipts/analytics", {
    credentials: "include",
  })
    .then((res) => {
      if (res.status === 401) {
        handleUnauthorized("/analytics");
        return null;
      }
      return res.json();
    })
    .then((data) => {
      if (!data) return; // Handled by redirect
      // Update category chart
      if (
        data.category_totals &&
        Object.keys(data.category_totals).length > 0
      ) {
        const categoryLabels = Object.keys(data.category_totals);
        const categoryValues = Object.values(data.category_totals);

        categoryChart.data.labels = categoryLabels;
        categoryChart.data.datasets[0].data = categoryValues;
        categoryChart.data.datasets[0].backgroundColor = colors.slice(
          0,
          categoryLabels.length
        );
        categoryChart.update();
      } else {
        categoryChart.data.labels = ["No Data"];
        categoryChart.data.datasets[0].data = [1];
        categoryChart.update();
      }

      // Update monthly chart
      if (data.monthly_totals && Object.keys(data.monthly_totals).length > 0) {
        // Sort months chronologically
        const sortedMonths = Object.keys(data.monthly_totals).sort();
        const monthLabels = sortedMonths.map((month) => {
          // Convert "2025-01" to "Jan 2025"
          const [year, monthNum] = month.split("-");
          const monthNames = [
            "Jan",
            "Feb",
            "Mar",
            "Apr",
            "May",
            "Jun",
            "Jul",
            "Aug",
            "Sep",
            "Oct",
            "Nov",
            "Dec",
          ];
          return `${monthNames[parseInt(monthNum) - 1]} ${year}`;
        });
        const monthValues = sortedMonths.map(
          (month) => data.monthly_totals[month]
        );

        monthlyChart.data.labels = monthLabels;
        monthlyChart.data.datasets[0].data = monthValues;
        monthlyChart.update();
      } else {
        monthlyChart.data.labels = ["No Data"];
        monthlyChart.data.datasets[0].data = [0];
        monthlyChart.update();
      }
    })
    .catch((error) => {
      console.error("Error fetching analytics:", error);
      // Show error state on charts
      categoryChart.data.labels = ["Error Loading Data"];
      categoryChart.data.datasets[0].data = [1];
      categoryChart.update();

      monthlyChart.data.labels = ["Error Loading Data"];
      monthlyChart.data.datasets[0].data = [0];
      monthlyChart.update();
    });
});
