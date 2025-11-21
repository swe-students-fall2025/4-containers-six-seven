document.addEventListener('DOMContentLoaded', () => {
  const categoryChart = new Chart(document.getElementById('categoryChart'), {
    type: 'pie',
    data: {                                            // TEMPORARY TEST DATA FOR VIEWING
      labels: ['Food', 'Transport', 'Office', 'Travel'],
      datasets: [{
        data: [300, 150, 100, 200],
        backgroundColor: ['#0d6efd', '#6610f2', '#198754', '#ffc107']
      }]
    },
    options: {
      plugins: {
        title: {
          display: true,
          text: 'Expenses by Category'
        }
      }
    }
  });

  const monthlyChart = new Chart(document.getElementById('monthlyChart'), {
    type: 'line',
    data: {                                                     // TEMPORARY TEST DATA FOR VIEWING
      labels: ['Jul', 'Aug', 'Sep', 'Oct', 'Nov'],
      datasets: [{
        label: 'Total Expenses',
        data: [500, 700, 600, 800, 650],
        borderColor: '#0d6efd',
        fill: false
      }]
    },
    options: {
      plugins: {
        title: {
          display: true,
          text: 'Monthly Spending Trend'
        }
      }
    }
  });

  const sellerChart = new Chart(document.getElementById('sellerChart'), {
    type: 'bar',
    data: {                                                     // TEMPORARY TEST DATA FOR VIEWING
      labels: ['Amazon', 'Uber', 'Staples', 'Delta'],
      datasets: [{
        label: 'Amount Spent ($)',
        data: [220, 180, 90, 300],
        backgroundColor: '#198754'
      }]
    },
    options: {
      plugins: {
        title: {
          display: true,
          text: 'Top Sellers'
        }
      }
    }
  });
});