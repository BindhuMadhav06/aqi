function renderPredictionComparisonChart(actual, predicted, pollutant) {
    const canvas = document.getElementById('timeSeriesChart');
    if (!canvas || !actual || !predicted || actual.length === 0 || predicted.length === 0) {
        console.warn('PredictionComparisonChart: Missing canvas or data');
        return;
    }

    const ctx = canvas.getContext('2d');
    const colors = {
        background: currentTheme === 'dark' ? '#1f2937' : '#ffffff',
        text: currentTheme === 'dark' ? '#f9fafb' : '#1f2937',
        grid: currentTheme === 'dark' ? '#374151' : '#e5e7eb',
        primary: '#3b82f6',
        danger: '#ef4444'
    };

    const labels = Array.from({ length: actual.length }, (_, i) => i + 1);

    new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Actual',
                    data: actual,
                    borderColor: colors.primary,
                    backgroundColor: colors.primary + '20',
                    fill: false,
                    tension: 0.1
                },
                {
                    label: 'Predicted',
                    data: predicted,
                    borderColor: colors.danger,
                    backgroundColor: colors.danger + '20',
                    fill: false,
                    tension: 0.1
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    display: true,
                    title: { display: true, text: 'Time Steps', color: colors.text },
                    ticks: { color: colors.text },
                    grid: { color: colors.grid }
                },
                y: {
                    display: true,
                    title: { display: true, text: `${pollutant} (μg/m³)`, color: colors.text },
                    ticks: { color: colors.text },
                    grid: { color: colors.grid }
                }
            },
            plugins: {
                legend: { labels: { color: colors.text } },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `${context.dataset.label}: ${context.parsed.y.toFixed(2)} μg/m³`;
                        }
                    }
                },
                zoom: {
                    zoom: {
                        wheel: { enabled: true },
                        pinch: { enabled: true },
                        mode: 'xy'
                    },
                    pan: {
                        enabled: true,
                        mode: 'xy'
                    }
                }
            }
        }
    });
}

function renderHourlyDistributionChart(hourlyData, pollutant) {
    const canvas = document.getElementById('hourlyDistributionChart');
    if (!canvas || !hourlyData || hourlyData.length === 0) {
        console.warn('HourlyDistributionChart: Missing canvas or data');
        return;
    }

    const ctx = canvas.getContext('2d');
    const colors = {
        background: currentTheme === 'dark' ? '#1f2937' : '#ffffff',
        text: currentTheme === 'dark' ? '#f9fafb' : '#1f2937',
        grid: currentTheme === 'dark' ? '#374151' : '#e5e7eb',
        primary: '#3498db'
    };

    const labels = hourlyData.map(d => `${d.hour}:00`);
    const averages = hourlyData.map(d => d.average);

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: `Hourly ${pollutant} Average`,
                data: averages,
                backgroundColor: colors.primary + '80',
                borderColor: colors.primary,
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    display: true,
                    title: { display: true, text: 'Hour of Day', color: colors.text },
                    ticks: { color: colors.text },
                    grid: { color: colors.grid }
                },
                y: {
                    display: true,
                    title: { display: true, text: `${pollutant} (μg/m³)`, color: colors.text },
                    ticks: { color: colors.text },
                    grid: { color: colors.grid },
                    beginAtZero: true
                }
            },
            plugins: {
                legend: { labels: { color: colors.text } }
            }
        }
    });
}
function renderTrendLineChart(data, pollutant) {
    const canvas = document.getElementById('trendLineChart');
    if (!canvas || !data || data.length === 0) {
        console.warn('TrendLineChart: Missing canvas or data');
        return;
    }

    const ctx = canvas.getContext('2d');
    const colors = {
        background: currentTheme === 'dark' ? '#1f2937' : '#ffffff',
        text: currentTheme === 'dark' ? '#f9fafb' : '#1f2937',
        grid: currentTheme === 'dark' ? '#374151' : '#e5e7eb',
        line: '#10b981'
    };

    const labels = data.map(d => d.timestamp);
    const values = data.map(d => d[pollutant]);

    new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: `${pollutant} Trend`,
                data: values,
                borderColor: colors.line,
                backgroundColor: colors.line + '20',
                fill: true,
                tension: 0.3
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    type: 'time',
                    time: {
                        parser: 'YYYY-MM-DD HH:mm:ss',
                        tooltipFormat: 'MMM D, h:mm A',
                        unit: 'hour'
                    },
                    title: { display: true, text: 'Time', color: colors.text },
                    ticks: { color: colors.text },
                    grid: { color: colors.grid }
                },
                y: {
                    beginAtZero: true,
                    title: { display: true, text: `${pollutant} (μg/m³)`, color: colors.text },
                    ticks: { color: colors.text },
                    grid: { color: colors.grid }
                }
            },
            plugins: {
                legend: { labels: { color: colors.text } }
            }
        }
    });
}
