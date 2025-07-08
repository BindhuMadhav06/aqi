let charts = {};
let currentTheme = 'light';
let currentData = null;
let predictionComparisonChart = null;
let hourlyDistributionChart = null;
let radarChart = null;

// Initialize dashboard
document.addEventListener('DOMContentLoaded', function() {
    initializeEventListeners();
    initializeTheme();
    setupChartDefaults();

    // Hide loading spinner after initialization
    hideLoadingSpinner();

    // Render initial charts from embedded data
    const dataScript = document.getElementById('dashboard-data');
    if (dataScript) {
        try {
            const data = JSON.parse(dataScript.textContent);
            if (data && Object.keys(data).length > 0) {
                currentData = data;
                renderCharts(
                    data.filteredData,
                    data.radarData,
                    data.hourlyDistributions,
                    data.futurePredictions,
                    data.pollutants,
                    getCurrentPollutant()
                );
            } else {
                showError('No initial data available.');
            }
        } catch (e) {
            console.error('Error parsing dashboard data:', e);
            showError('Failed to parse initial data.');
        }
    } else {
        showError('Dashboard data not found.');
    }
});

// Event Listeners
function initializeEventListeners() {
    const themeToggle = document.getElementById('theme-toggle');
    if (themeToggle) {
        themeToggle.addEventListener('click', toggleTheme);
    }

    const citySelect = document.getElementById('city-select');
    if (citySelect) {
        citySelect.addEventListener('change', updateDashboard);
    }

    const timeRangeSelect = document.getElementById('time-range-select');
    if (timeRangeSelect) {
        timeRangeSelect.addEventListener('change', updateDashboard);
    }

    const viewButtons = document.querySelectorAll('.view-btn');
    viewButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            updateActiveView(this.dataset.view);
            updateDashboard();
        });
    });

    const pollutantButtons = document.querySelectorAll('.pollutant-btn');
    pollutantButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            updateActivePollutant(this.dataset.pollutant);
            updateDashboard();
        });
    });

    const clearErrors = document.getElementById('clear-errors');
    if (clearErrors) {
        clearErrors.addEventListener('click', function() {
            const errorPanel = document.getElementById('error-panel');
            if (errorPanel) {
                errorPanel.style.display = 'none';
            }
        });
    }
}

// Theme Management
function initializeTheme() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    setTheme(savedTheme);
}

function toggleTheme() {
    const newTheme = currentTheme === 'light' ? 'dark' : 'light';
    setTheme(newTheme);
}

function setTheme(theme) {
    currentTheme = theme;
    localStorage.setItem('theme', theme);
    const html = document.documentElement;
    const sunIcon = document.getElementById('sun-icon');
    const moonIcon = document.getElementById('moon-icon');
    
    if (theme === 'dark') {
        html.classList.add('dark');
        if (sunIcon) sunIcon.classList.remove('hidden');
        if (moonIcon) moonIcon.classList.add('hidden');
    } else {
        html.classList.remove('dark');
        if (sunIcon) sunIcon.classList.add('hidden');
        if (moonIcon) moonIcon.classList.remove('hidden');
    }
    
    updateChartThemes();
}

// Chart Setup
function setupChartDefaults() {
    Chart.defaults.font.family = 'Inter, sans-serif';
    Chart.defaults.font.size = 12;
    Chart.register(ChartZoom);
}

function getChartColors() {
    const isDark = currentTheme === 'dark';
    return {
        background: isDark ? '#1f2937' : '#ffffff',
        text: isDark ? '#f9fafb' : '#1f2937',
        grid: isDark ? '#374151' : '#e5e7eb',
        border: isDark ? '#4b5563' : '#d1d5db',
        primary: '#3b82f6',
        secondary: '#10b981',
        accent: '#f59e0b',
        danger: '#ef4444',
        warning: '#f59e0b',
        info: '#06b6d4'
    };
}

function renderCharts(filteredData, radarData, hourlyDistributions, futurePredictions, pollutants, selectedPollutant) {
    console.log('Rendering charts with:', { filteredData, radarData, hourlyDistributions, futurePredictions, pollutants, selectedPollutant });
    currentData = { filteredData, radarData, hourlyDistributions, futurePredictions, pollutants, selectedPollutant };
    destroyCharts();

    const viewType = getCurrentView();
    try {
        switch(viewType) {
            case 'overview':
                renderTimeSeriesChart(filteredData, selectedPollutant);
                renderRadarChart(radarData);
                renderPredictionComparisonChart(filteredData, futurePredictions[selectedPollutant], selectedPollutant);
                break;
            case 'trends':
                renderHourlyDistributionChart(hourlyDistributions[selectedPollutant], selectedPollutant);
                renderFuturePredictionsChart(futurePredictions[selectedPollutant], selectedPollutant);
                break;
            case 'pollutants':
                renderMultiPollutantChart(filteredData);
                break;
            case 'weather':
                renderWeatherChart(filteredData);
                renderCorrelationChart(filteredData);
                break;
            default:
                showError('Invalid view type selected.');
        }
    } catch (e) {
        console.error('Error rendering charts:', e);
        showError('Failed to render charts.');
    }
    hideLoadingSpinner();
}

function renderTimeSeriesChart(data, pollutant) {
    const canvas = document.getElementById('timeSeriesChart');
    if (!canvas || !data || data.length === 0) {
        console.warn('TimeSeriesChart: Missing canvas or data');
        showError('Cannot render Time Series Chart: Missing data or canvas.');
        return;
    }

    const ctx = canvas.getContext('2d');
    const colors = getChartColors();

    const labels = data.map(d => new Date(d.datetime).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false }));
    const values = data.map(d => d[pollutant] || 0);

    if (charts.timeSeries) charts.timeSeries.destroy();
    charts.timeSeries = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: `${pollutant} (μg/m³)`,
                data: values,
                borderColor: colors.primary,
                backgroundColor: colors.primary + '20',
                fill: true,
                tension: 0.4,
                pointRadius: 2,
                pointHoverRadius: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    display: true,
                    title: { display: true, text: 'Time', color: colors.text },
                    ticks: { color: colors.text, maxTicksLimit: 10 },
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
                            return `${context.dataset.label}: ${context.parsed.y.toFixed(2)}`;
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

function renderRadarChart(data) {
    const canvas = document.getElementById('radarChart');
    if (!canvas || !data || data.length === 0) {
        console.warn('RadarChart: Missing canvas or data');
        showError('Cannot render Radar Chart: Missing data or canvas.');
        return;
    }

    const ctx = canvas.getContext('2d');
    const colors = getChartColors();

    const labels = data.map(d => d.subject);
    const values = data.map(d => d.value);

    if (radarChart) radarChart.destroy();
    radarChart = new Chart(ctx, {
        type: 'radar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Current Levels',
                data: values,
                borderColor: colors.primary,
                backgroundColor: colors.primary + '40',
                pointBackgroundColor: colors.primary,
                pointBorderColor: colors.background,
                pointHoverBackgroundColor: colors.background,
                pointHoverBorderColor: colors.primary,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                r: {
                    beginAtZero: true,
                    max: 100,
                    ticks: { color: colors.text, backdropColor: 'transparent' },
                    grid: { color: colors.grid },
                    angleLines: { color: colors.grid },
                    pointLabels: { color: colors.text }
                }
            },
            plugins: {
                legend: { labels: { color: colors.text } },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `${context.label}: ${context.parsed.r.toFixed(2)}%`;
                        }
                    }
                }
            }
        }
    });
}

function renderPredictionComparisonChart(data, predictions, pollutant) {
    const canvas = document.getElementById('predictionComparisonChart');
    if (!canvas || !data || !predictions || data.length === 0 || predictions.length === 0) {
        console.warn('PredictionComparisonChart: Missing canvas or data');
        showError('Cannot render Prediction Comparison Chart: Missing data or canvas.');
        return;
    }

    const ctx = canvas.getContext('2d');
    const colors = getChartColors();

    const labels = Array.from({ length: data.length }, (_, i) => i + 1);
    const actual = data.map(d => d[pollutant] || 0);

    if (predictionComparisonChart) predictionComparisonChart.destroy();
    predictionComparisonChart = new Chart(ctx, {
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
                    tension: 0.1,
                    pointRadius: 3,
                    pointHoverRadius: 5
                },
                {
                    label: 'Predicted',
                    data: predictions,
                    borderColor: colors.danger,
                    backgroundColor: colors.danger + '20',
                    fill: false,
                    tension: 0.1,
                    pointRadius: 3,
                    pointHoverRadius: 5
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                intersect: false,
                mode: 'index'
            },
            scales: {
                x: {
                    display: true,
                    title: { 
                        display: true, 
                        text: 'Hours', 
                        color: colors.text,
                        font: { size: 12, weight: 'bold' }
                    },
                    ticks: { color: colors.text, maxTicksLimit: 10 },
                    grid: { color: colors.grid, drawBorder: false }
                },
                y: {
                    display: true,
                    title: { 
                        display: true, 
                        text: `${pollutant} Concentration (μg/m³)`, 
                        color: colors.text,
                        font: { size: 12, weight: 'bold' }
                    },
                    ticks: { 
                        color: colors.text,
                        callback: function(value) {
                            return value.toFixed(1);
                        }
                    },
                    grid: { color: colors.grid, drawBorder: false }
                }
            },
            plugins: {
                legend: { 
                    labels: { 
                        color: colors.text,
                        usePointStyle: true,
                        padding: 20
                    },
                    position: 'top'
                },
                tooltip: {
                    backgroundColor: colors.background,
                    titleColor: colors.text,
                    bodyColor: colors.text,
                    borderColor: colors.grid,
                    borderWidth: 1,
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
        showError('Cannot render Hourly Distribution Chart: Missing data or canvas.');
        return;
    }

    const ctx = canvas.getContext('2d');
    const colors = getChartColors();

    const labels = hourlyData.map(d => `${d.hour}:00`);
    const averages = hourlyData.map(d => d.average);

    if (hourlyDistributionChart) hourlyDistributionChart.destroy();
    hourlyDistributionChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: `Hourly ${pollutant} Average`,
                data: averages,
                backgroundColor: colors.primary + '80',
                borderColor: colors.primary,
                borderWidth: 1,
                borderRadius: 4,
                borderSkipped: false
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                intersect: false,
                mode: 'index'
            },
            scales: {
                x: {
                    display: true,
                    title: { 
                        display: true, 
                        text: 'Hour of Day', 
                        color: colors.text,
                        font: { size: 12, weight: 'bold' }
                    },
                    ticks: { color: colors.text, maxRotation: 45 },
                    grid: { color: colors.grid, drawBorder: false }
                },
                y: {
                    display: true,
                    title: { 
                        display: true, 
                        text: `${pollutant} (μg/m³)`, 
                        color: colors.text,
                        font: { size: 12, weight: 'bold' }
                    },
                    ticks: { 
                        color: colors.text,
                        callback: function(value) {
                            return value.toFixed(1);
                        }
                    },
                    grid: { color: colors.grid, drawBorder: false },
                    beginAtZero: true
                }
            },
            plugins: {
                legend: { 
                    labels: { 
                        color: colors.text,
                        usePointStyle: true,
                        padding: 20
                    },
                    position: 'top'
                },
                tooltip: {
                    backgroundColor: colors.background,
                    titleColor: colors.text,
                    bodyColor: colors.text,
                    borderColor: colors.grid,
                    borderWidth: 1,
                    callbacks: {
                        label: function(context) {
                            return `${context.dataset.label}: ${context.parsed.y.toFixed(2)} μg/m³`;
                        }
                    }
                }
            }
        }
    });
}

function renderFuturePredictionsChart(predictions, pollutant) {
    const canvas = document.getElementById('futurePredictionsChart');
    if (!canvas || !predictions || predictions.length === 0) {
        console.warn('FuturePredictionsChart: Missing canvas or data');
        showError('Cannot render Future Predictions Chart: Missing data or canvas.');
        return;
    }

    const ctx = canvas.getContext('2d');
    const colors = getChartColors();

    const labels = Array.from({ length: predictions.length }, (_, i) => `${i + 1}:00`);

    if (charts.futurePredictions) charts.futurePredictions.destroy();
    charts.futurePredictions = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: `Predicted ${pollutant}`,
                data: predictions,
                borderColor: colors.accent,
                backgroundColor: colors.accent + '20',
                fill: true,
                tension: 0.4,
                pointRadius: 3,
                pointHoverRadius: 5,
                borderDash: [5, 5]
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    display: true,
                    title: { display: true, text: 'Hour', color: colors.text },
                    ticks: { color: colors.text, maxTicksLimit: 12 },
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
                            return `Predicted ${pollutant}: ${context.parsed.y.toFixed(2)} μg/m³`;
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

function renderMultiPollutantChart(data) {
    const canvas = document.getElementById('multiPollutantChart');
    if (!canvas || !data || data.length === 0) {
        console.warn('MultiPollutantChart: Missing canvas or data');
        showError('Cannot render Multi-Pollutant Chart: Missing data or canvas.');
        return;
    }

    const ctx = canvas.getContext('2d');
    const colors = getChartColors();

    const labels = data.map(d => new Date(d.datetime).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false }));
    const pollutants = ['PM2.5', 'PM10', 'SO2', 'NO2', 'CO', 'O3'];
    const chartColors = [colors.primary, colors.secondary, colors.accent, colors.danger, colors.warning, colors.info];

    const datasets = pollutants.map((pollutant, index) => ({
        label: pollutant,
        data: data.map(d => d[pollutant] || 0),
        borderColor: chartColors[index],
        backgroundColor: chartColors[index] + '20',
        fill: false,
        tension: 0.4,
        pointRadius: 1,
        pointHoverRadius: 3
    }));

    if (charts.multiPollutant) charts.multiPollutant.destroy();
    charts.multiPollutant = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    display: true,
                    title: { display: true, text: 'Time', color: colors.text },
                    ticks: { color: colors.text, maxTicksLimit: 10 },
                    grid: { color: colors.grid }
                },
                y: {
                    display: true,
                    title: { display: true, text: 'Concentration (μg/m³)', color: colors.text },
                    ticks: { color: colors.text },
                    grid: { color: colors.grid }
                }
            },
            plugins: {
                legend: { labels: { color: colors.text } },
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

function renderWeatherChart(data) {
    const canvas = document.getElementById('weatherChart');
    if (!canvas || !data || data.length === 0) {
        console.warn('WeatherChart: Missing canvas or data');
        showError('Cannot render Weather Chart: Missing data or canvas.');
        return;
    }

    const ctx = canvas.getContext('2d');
    const colors = getChartColors();

    const labels = data.map(d => new Date(d.datetime).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false }));

    if (charts.weather) charts.weather.destroy();
    charts.weather = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Temperature (°C)',
                    data: data.map(d => d.TEMP || 0),
                    borderColor: colors.danger,
                    backgroundColor: colors.danger + '20',
                    yAxisID: 'y',
                    fill: false,
                    tension: 0.4
                },
                {
                    label: 'Humidity (%)',
                    data: data.map(d => d.HUMIDITY || 0),
                    borderColor: colors.info,
                    backgroundColor: colors.info + '20',
                    yAxisID: 'y1',
                    fill: false,
                    tension: 0.4
                },
                {
                    label: 'Wind Speed (m/s)',
                    data: data.map(d => d.WIND_SPEED || 0),
                    borderColor: colors.secondary,
                    backgroundColor: colors.secondary + '20',
                    yAxisID: 'y2',
                    fill: false,
                    tension: 0.4
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    display: true,
                    title: { display: true, text: 'Time', color: colors.text },
                    ticks: { color: colors.text, maxTicksLimit: 10 },
                    grid: { color: colors.grid }
                },
                y: {
                    type: 'linear',
                    display: true,
                    position: 'left',
                    title: { display: true, text: 'Temperature (°C)', color: colors.text },
                    ticks: { color: colors.text },
                    grid: { color: colors.grid }
                },
                y1: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    title: { display: true, text: 'Humidity (%)', color: colors.text },
                    ticks: { color: colors.text },
                    grid: { drawOnChartArea: false }
                },
                y2: {
                    type: 'linear',
                    display: false,
                    position: 'right'
                }
            },
            plugins: {
                legend: { labels: { color: colors.text } },
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

function renderCorrelationChart(data) {
    const canvas = document.getElementById('correlationChart');
    if (!canvas || !data || data.length === 0) {
        console.warn('CorrelationChart: Missing canvas or data');
        showError('Cannot render Correlation Chart: Missing data or canvas.');
        return;
    }

    const ctx = canvas.getContext('2d');
    const colors = getChartColors();

    const scatterData = data.map(d => ({
        x: d.TEMP || 0,
        y: d['PM2.5'] || 0
    }));

    const regression = calculateLinearRegression(scatterData);
    const regressionLine = scatterData.map(d => ({
        x: d.x,
        y: regression.slope * d.x + regression.intercept
    }));

    if (charts.correlation) charts.correlation.destroy();
    charts.correlation = new Chart(ctx, {
        type: 'scatter',
        data: {
            datasets: [
                {
                    label: 'Data Points',
                    data: scatterData,
                    backgroundColor: colors.primary,
                    pointRadius: 3,
                    pointHoverRadius: 5
                },
                {
                    label: 'Regression Line',
                    data: regressionLine,
                    type: 'line',
                    borderColor: colors.secondary,
                    backgroundColor: colors.secondary + '20',
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
                    title: { display: true, text: 'Temperature (°C)', color: colors.text },
                    ticks: { color: colors.text },
                    grid: { color: colors.grid }
                },
                y: {
                    display: true,
                    title: { display: true, text: 'PM2.5 (μg/m³)', color: colors.text },
                    ticks: { color: colors.text },
                    grid: { color: colors.grid }
                }
            },
            plugins: {
                legend: { labels: { color: colors.text } },
                tooltip: {
                    callbacks: {
                        labelPointStyle(context) {
                            return { pointStyle: 'circle', rotation: 0 };
                        }
                    }
                }
            }
        }
    });
}

function calculateLinearRegression(data) {
    const n = data.length;
    if (n === 0) return { slope: 0, intercept: 0 };

    const sumX = data.reduce((sum, point) => sum + point.x, 0);
    const sumY = data.reduce((sum, point) => sum + point.y, 0);
    const sumXY = data.reduce((sum, point) => sum + point.x * point.y, 0);
    const sumX2 = data.reduce((sum, point) => sum + point.x * point.x, 0);

    const slope = (n * sumXY - sumX * sumY) / (n * sumX2 - sumX * sumX);
    const intercept = (sumY - slope * sumX) / n;

    return { slope, intercept };
}

function updateChartsForCity(cityData) {
    const selectedPollutant = getCurrentPollutant();
    if (predictionComparisonChart && cityData.filteredData && cityData.futurePredictions[selectedPollutant]) {
        predictionComparisonChart.data.datasets[0].data = cityData.filteredData.map(d => d[selectedPollutant] || 0);
        predictionComparisonChart.data.datasets[1].data = cityData.futurePredictions[selectedPollutant];
        predictionComparisonChart.data.labels = Array.from({ length: cityData.filteredData.length }, (_, i) => i + 1);
        predictionComparisonChart.update('none');
    }

    if (hourlyDistributionChart && cityData.hourlyDistributions[selectedPollutant]) {
        hourlyDistributionChart.data.labels = cityData.hourlyDistributions[selectedPollutant].map(d => `${d.hour}:00`);
        hourlyDistributionChart.data.datasets[0].data = cityData.hourlyDistributions[selectedPollutant].map(d => d.average);
        hourlyDistributionChart.update('none');
    }

    if (radarChart && cityData.radarData) {
        radarChart.data.labels = cityData.radarData.map(d => d.subject);
        radarChart.data.datasets[0].data = cityData.radarData.map(d => d.value);
        radarChart.update('none');
    }
}

function destroyCharts() {
    Object.values(charts).forEach(chart => chart?.destroy?.());
    if (predictionComparisonChart) {
        predictionComparisonChart.destroy();
        predictionComparisonChart = null;
    }
    if (hourlyDistributionChart) {
        hourlyDistributionChart.destroy();
        hourlyDistributionChart = null;
    }
    if (radarChart) {
        radarChart.destroy();
        radarChart = null;
    }
    charts = {};
}

window.addEventListener('resize', function() {
    if (predictionComparisonChart) predictionComparisonChart.resize();
    if (hourlyDistributionChart) hourlyDistributionChart.resize();
    if (radarChart) radarChart.resize();
});

function updateActiveView(view) {
    const views = document.querySelectorAll('.view-btn');
    views.forEach(btn => btn.classList.remove('active', 'bg-blue-500', 'text-white'));
    const activeBtn = document.querySelector(`.view-btn[data-view="${view}"]`);
    if (activeBtn) {
        activeBtn.classList.add('active', 'bg-blue-500', 'text-white');
    }
}

function getCurrentView() {
    const activeBtn = document.querySelector('.view-btn.active');
    return activeBtn ? activeBtn.dataset.view : 'overview';
}

function updateActivePollutant(pollutant) {
    const buttons = document.querySelectorAll('.pollutant-btn');
    buttons.forEach(btn => btn.classList.remove('active', 'bg-blue-500', 'text-white'));
    const activeBtn = document.querySelector(`.pollutant-btn[data-pollutant="${pollutant}"]`);
    if (activeBtn) {
        activeBtn.classList.add('active', 'bg-blue-500', 'text-white');
    }
}

function getCurrentPollutant() {
    const activeBtn = document.querySelector('.pollutant-btn.active');
    return activeBtn ? activeBtn.dataset.pollutant : 'PM2.5';
}

function updateDashboard() {
    const citySelect = document.getElementById('city-select');
    const timeRangeSelect = document.getElementById('time-range-select');
    const selectedCity = citySelect ? citySelect.value : 'Delhi';
    const selectedTimeRange = timeRangeSelect ? timeRangeSelect.value : '24h';
    const selectedPollutant = getCurrentPollutant();
    const viewType = getCurrentView();

    showLoadingSpinner();

    fetch(`/api/dashboard?city=${selectedCity}&timeRange=${selectedTimeRange}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            if (data.error) {
                showError(data.error.message);
            } else {
                currentData = data;
                renderCharts(
                    data.filteredData,
                    data.radarData,
                    data.hourlyDistributions,
                    data.futurePredictions,
                    data.pollutants,
                    selectedPollutant
                );
                updateChartsForCity(data);
                document.getElementById('last-updated').textContent = `Last Updated: ${new Date().toLocaleString()} for ${selectedCity}`;
            }
        })
        .catch(error => {
            console.error('Error fetching dashboard data:', error);
            showError('Failed to load data. Please try again later.');
        })
        .finally(() => {
            hideLoadingSpinner();
        });
}

function updateChartThemes() {
    const colors = getChartColors();
    Object.values(charts).forEach(chart => {
        if (chart) {
            chart.options.scales.x.ticks.color = colors.text;
            chart.options.scales.y.ticks.color = colors.text;
            chart.options.scales.x.grid.color = colors.grid;
            chart.options.scales.y.grid.color = colors.grid;
            chart.options.plugins.legend.labels.color = colors.text;
            if (chart.options.scales.r) {
                chart.options.scales.r.ticks.color = colors.text;
                chart.options.scales.r.grid.color = colors.grid;
                chart.options.scales.r.angleLines.color = colors.grid;
                chart.options.scales.r.pointLabels.color = colors.text;
            }
            chart.update();
        }
    });
}

function showLoadingSpinner() {
    const loading = document.getElementById('loading');
    if (loading) {
        loading.style.opacity = '1';
        loading.style.display = 'flex';
    }
}

function hideLoadingSpinner() {
    const loading = document.getElementById('loading');
    if (loading) {
        loading.style.opacity = '0';
        setTimeout(() => {
            loading.style.display = 'none';
        }, 500);
    }
}

function showError(message) {
    const errorPanel = document.getElementById('error-panel');
    if (errorPanel) {
        errorPanel.textContent = message;
        errorPanel.style.display = 'block';
    }
}