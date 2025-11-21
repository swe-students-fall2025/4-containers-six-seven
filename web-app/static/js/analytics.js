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
          text: 'Spending by Category'
        }
      }
    }
  });

  const monthlyChart = new Chart(document.getElementById('monthlyChart'), {
    type: 'line',
    data: {                                                     // TEMPORARY TEST DATA FOR VIEWING
      labels: ['Jul', 'Aug', 'Sep', 'Oct', 'Nov'],
      datasets: [{
        label: 'Total Spending (USD)',
        data: [500, 700, 600, 800, 650],
        borderColor: '#0d6efd',
        fill: false
      }]
    },
    options: {
      plugins: {
        title: {
          display: true,
          text: 'Monthly Spending'
        }
      }
    }
  });
});