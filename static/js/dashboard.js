// Advanced AQI Dashboard - Frontend Logic

// Global variables
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
    populateCityDropdown();

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
                    getCurrentPollutant(),
                    data.selectedCity
                );
                updateTimestamp(data.selectedCity, data.timeRange);
            } else {
                showError('No initial data available.');
                logClientError('No initial data available.');
            }
        } catch (e) {
            console.error('Error parsing dashboard data:', e);
            showError('Failed to parse initial data.');
            logClientError('Error parsing dashboard data: ' + e.message);
        }
    } else {
        showError('Dashboard data not found.');
        logClientError('Dashboard data script not found.');
    }
});

// Populate city dropdown
function populateCityDropdown() {
    fetch('/api/cities')
        .then(response => response.json())
        .then(data => {
            if (data.cities) {
                const citySelect = document.getElementById('city-select');
                citySelect.innerHTML = '';
                data.cities.forEach(city => {
                    const option = document.createElement('option');
                    option.value = city;
                    option.textContent = city;
                    if (city === getCurrentCity()) {
                        option.selected = true;
                    }
                    citySelect.appendChild(option);
                });
                logClientInfo(`Populated city dropdown with: ${data.cities}`);
            } else {
                showError('Failed to load cities.');
                logClientError('Failed to load cities: ' + JSON.stringify(data.error));
            }
        })
        .catch(error => {
            console.error('Error fetching cities:', error);
            showError('Error fetching city list.');
            logClientError('Error fetching cities: ' + error.message);
        });
}

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

function renderCharts(filteredData, radarData, hourlyDistributions, futurePredictions, pollutants, selectedPollutant, selectedCity) {
    console.log('Rendering charts with:', { filteredData, radarData, hourlyDistributions, futurePredictions, pollutants, selectedPollutant, selectedCity });
    logClientInfo(`Rendering charts for view: ${getCurrentView()} and city: ${selectedCity}`);
    currentData = { filteredData, radarData, hourlyDistributions, futurePredictions, pollutants, selectedPollutant, selectedCity };
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
                logClientError('Invalid view type: ' + viewType);
        }
    } catch (e) {
        console.error('Error rendering charts:', e);
        showError('Failed to render charts.');
        logClientError('Error rendering charts: ' + e.message);
    }
    hideLoadingSpinner();
}

function renderTimeSeriesChart(data, pollutant) {
    const canvas = document.getElementById('timeSeriesChart');
    if (!canvas || !data || data.length === 0) {
        console.warn('TimeSeriesChart: Missing canvas or data');
        showError('Cannot render Time Series Chart: Missing data or canvas.');
        logClientError('TimeSeriesChart: Missing canvas or data');
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
        logClientError('RadarChart: Missing canvas or data');
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
        logClientError('PredictionComparisonChart: Missing canvas or data');
        return;
    }

    const ctx = canvas.getContext('2d');
    const colors = getChartColors();

    const labels = Array.from({ length: Math.max(data.length, predictions.length) }, (_, i) => i + 1);
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

function renderHourlyDistributionChart(data, pollutant) {
    const canvas = document.getElementById('hourlyDistributionChart');
    if (!canvas || !data || data.length === 0) {
        console.warn('HourlyDistributionChart: Missing canvas or data');
        showError('Cannot render Hourly Distribution Chart: Missing data or canvas.');
        logClientError('HourlyDistributionChart: Missing canvas or data');
        return;
    }

    const ctx = canvas.getContext('2d');
    const colors = getChartColors();

    const labels = data.map(d => `${d.hour}:00`);
    const values = data.map(d => d.average);

    if (hourlyDistributionChart) hourlyDistributionChart.destroy();
    hourlyDistributionChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: `${pollutant} Average (μg/m³)`,
                data: values,
                backgroundColor: colors.secondary + '80',
                borderColor: colors.secondary,
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
                    grid: { color: colors.grid }
                }
            },
            plugins: {
                legend: { labels: { color: colors.text } }
            }
        }
    });
}

function renderFuturePredictionsChart(predictions, pollutant) {
    const canvas = document.getElementById('futurePredictionsChart');
    if (!canvas || !predictions || predictions.length === 0) {
        console.warn('FuturePredictionsChart: Missing canvas or data');
        showError('Cannot render Future Predictions Chart: Missing data or canvas.');
        logClientError('FuturePredictionsChart: Missing canvas or data');
        return;
    }

    const ctx = canvas.getContext('2d');
    const colors = getChartColors();

    const labels = Array.from({ length: predictions.length }, (_, i) => `+${i+1}h`);

    if (charts.futurePredictions) charts.futurePredictions.destroy();
    charts.futurePredictions = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: `Predicted ${pollutant} (μg/m³)`,
                data: predictions,
                borderColor: colors.danger,
                backgroundColor: colors.danger + '20',
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
                    title: { display: true, text: 'Future Hours', color: colors.text },
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
                legend: { labels: { color: colors.text } }
            }
        }
    });
}

function renderMultiPollutantChart(data) {
    const canvas = document.getElementById('multiPollutantChart');
    if (!canvas || !data || data.length === 0) {
        console.warn('MultiPollutantChart: Missing canvas or data');
        showError('Cannot render Multi-Pollutant Chart: Missing data or canvas.');
        logClientError('MultiPollutantChart: Missing canvas or data');
        return;
    }

    const ctx = canvas.getContext('2d');
    const colors = getChartColors();

    const labels = data.map(d => new Date(d.datetime).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false }));
    const datasets = [
        { label: 'PM2.5', data: data.map(d => d['PM2.5'] || 0), borderColor: colors.primary, backgroundColor: colors.primary + '20' },
        { label: 'PM10', data: data.map(d => d['PM10'] || 0), borderColor: colors.secondary, backgroundColor: colors.secondary + '20' },
        { label: 'SO2', data: data.map(d => d['SO2'] || 0), borderColor: colors.accent, backgroundColor: colors.accent + '20' },
        { label: 'NO2', data: data.map(d => d['NO2'] || 0), borderColor: colors.danger, backgroundColor: colors.danger + '20' },
        { label: 'CO', data: data.map(d => d['CO'] || 0), borderColor: colors.info, backgroundColor: colors.info + '20' },
        { label: 'O3', data: data.map(d => d['O3'] || 0), borderColor: colors.warning, backgroundColor: colors.warning + '20' }
    ];

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
                legend: { labels: { color: colors.text } }
            }
        }
    });
}

function renderWeatherChart(data) {
    const canvas = document.getElementById('weatherChart');
    if (!canvas || !data || data.length === 0) {
        console.warn('WeatherChart: Missing canvas or data');
        showError('Cannot render Weather Chart: Missing data or canvas.');
        logClientError('WeatherChart: Missing canvas or data');
        return;
    }

    const ctx = canvas.getContext('2d');
    const colors = getChartColors();

    const labels = data.map(d => new Date(d.datetime).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false }));
    const datasets = [
        { label: 'Temperature (°C)', data: data.map(d => d['TEMP'] || 0), borderColor: colors.primary, yAxisID: 'y' },
        { label: 'Humidity (%)', data: data.map(d => d['HUMIDITY'] || 0), borderColor: colors.secondary, yAxisID: 'y1' },
        { label: 'Wind Speed (m/s)', data: data.map(d => d['WIND_SPEED'] || 0), borderColor: colors.accent, yAxisID: 'y2' }
    ];

    if (charts.weather) charts.weather.destroy();
    charts.weather = new Chart(ctx, {
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
                    title: { display: true, text: 'Temperature (°C)', color: colors.text },
                    ticks: { color: colors.text },
                    grid: { color: colors.grid }
                },
                y1: {
                    display: true,
                    position: 'right',
                    title: { display: true, text: 'Humidity (%)', color: colors.text },
                    ticks: { color: colors.text },
                    grid: { drawOnChartArea: false }
                },
                y2: {
                    display: true,
                    position: 'right',
                    title: { display: true, text: 'Wind Speed (m/s)', color: colors.text },
                    ticks: { color: colors.text },
                    grid: { drawOnChartArea: false }
                }
            },
            plugins: {
                legend: { labels: { color: colors.text } }
            }
        }
    });
}

function renderCorrelationChart(data) {
    const canvas = document.getElementById('correlationChart');
    if (!canvas || !data || data.length === 0) {
        console.warn('CorrelationChart: Missing canvas or data');
        showError('Cannot render Correlation Chart: Missing data or canvas.');
        logClientError('CorrelationChart: Missing canvas or data');
        return;
    }

    const ctx = canvas.getContext('2d');
    const colors = getChartColors();

    const pollutants = ['PM2.5', 'PM10', 'SO2', 'NO2', 'CO', 'O3'];
    const weatherParams = ['TEMP', 'HUMIDITY', 'WIND_SPEED'];
    const correlationData = [];

    pollutants.forEach(p => {
        weatherParams.forEach(w => {
            const xValues = data.map(d => d[p] || 0);
            const yValues = data.map(d => d[w] || 0);
            // Calculate Pearson correlation coefficient
            const n = xValues.length;
            const meanX = xValues.reduce((sum, x) => sum + x, 0) / n;
            const meanY = yValues.reduce((sum, y) => sum + y, 0) / n;
            let num = 0, denomX = 0, denomY = 0;
            for (let i = 0; i < n; i++) {
                const xDiff = xValues[i] - meanX;
                const yDiff = yValues[i] - meanY;
                num += xDiff * yDiff;
                denomX += xDiff * xDiff;
                denomY += yDiff * yDiff;
            }
            const correlation = num / Math.sqrt(denomX * denomY);
            correlationData.push({
                x: meanX,
                y: meanY,
                r: Math.min(Math.abs(correlation) * 20, 20), // Scale radius for visibility
                label: `${p} vs ${w}`
            });
        });
    });

    if (charts.correlation) charts.correlation.destroy();
    charts.correlation = new Chart(ctx, {
        type: 'scatter',
        data: {
            datasets: [{
                label: 'Correlation',
                data: correlationData,
                backgroundColor: colors.info + '80',
                borderColor: colors.info,
                pointRadius: correlationData.map(d => d.r)
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    display: true,
                    title: { display: true, text: 'Pollutant Mean (μg/m³)', color: colors.text },
                    ticks: { color: colors.text },
                    grid: { color: colors.grid }
                },
                y: {
                    display: true,
                    title: { display: true, text: 'Weather Parameter Mean', color: colors.text },
                    ticks: { color: colors.text },
                    grid: { color: colors.grid }
                }
            },
            plugins: {
                legend: { labels: { color: colors.text } },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `${context.raw.label}: r=${(context.raw.r / 20).toFixed(2)}`;
                        }
                    }
                }
            }
        }
    });
}

function destroyCharts() {
    Object.values(charts).forEach(chart => {
        if (chart) chart.destroy();
    });
    if (predictionComparisonChart) predictionComparisonChart.destroy();
    if (hourlyDistributionChart) hourlyDistributionChart.destroy();
    if (radarChart) radarChart.destroy();
    charts = {};
    predictionComparisonChart = null;
    hourlyDistributionChart = null;
    radarChart = null;
}

function updateChartThemes() {
    if (currentData) {
        renderCharts(
            currentData.filteredData,
            currentData.radarData,
            currentData.hourlyDistributions,
            currentData.futurePredictions,
            currentData.pollutants,
            currentData.selectedPollutant,
            currentData.selectedCity
        );
    }
}

function getCurrentView() {
    const activeBtn = document.querySelector('.view-btn[style*="background-color: #1d4ed8"]');
    return activeBtn ? activeBtn.dataset.view : 'overview';
}

function getCurrentPollutant() {
    const activeBtn = document.querySelector('.pollutant-btn[style*="background-color: #1d4ed8"]');
    return activeBtn ? activeBtn.dataset.pollutant : 'PM2.5'; // Default to PM2.5 if none selected
}

function getCurrentCity() {
    const citySelect = document.getElementById('city-select');
    return citySelect ? citySelect.value : 'Delhi'; // Default to Delhi if none selected
}

function getCurrentTimeRange() {
    const timeRangeSelect = document.getElementById('time-range-select');
    return timeRangeSelect ? timeRangeSelect.value : '24h'; // Default to 24h if none selected
}

function updateActiveView(view) {
    const viewButtons = document.querySelectorAll('.view-btn');
    viewButtons.forEach(btn => {
        btn.style.backgroundColor = '#3b82f6'; // Default color
    });
    const activeBtn = document.querySelector(`.view-btn[data-view="${view}"]`);
    if (activeBtn) {
        activeBtn.style.backgroundColor = '#1d4ed8'; // Active color
    }

    // Show/hide views
    const views = ['overview', 'trends', 'pollutants', 'weather'];
    views.forEach(v => {
        const viewElement = document.getElementById(`${v}-view`);
        if (viewElement) {
            viewElement.style.display = v === view ? 'block' : 'none';
        }
    });
}

function updateActivePollutant(pollutant) {
    const pollutantButtons = document.querySelectorAll('.pollutant-btn');
    pollutantButtons.forEach(btn => {
        btn.style.backgroundColor = '#3b82f6'; // Default color
    });
    const activeBtn = document.querySelector(`.pollutant-btn[data-pollutant="${pollutant}"]`);
    if (activeBtn) {
        activeBtn.style.backgroundColor = '#1d4ed8'; // Active color
    }
}

function updateDashboard() {
    const city = getCurrentCity();
    const timeRange = getCurrentTimeRange();
    const viewType = getCurrentView();
    const pollutant = getCurrentPollutant();

    showLoadingSpinner();
    fetch(`/api/dashboard?city=${encodeURIComponent(city)}&timeRange=${timeRange}`)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                showError(`Error fetching data: ${data.error.message}`);
                logClientError(`Error fetching dashboard data: ${JSON.stringify(data.error)}`);
                hideLoadingSpinner();
                return;
            }

            currentData = {
                filteredData: data.filteredData,
                radarData: data.radarData,
                hourlyDistributions: data.hourlyDistributions,
                futurePredictions: data.futurePredictions,
                pollutants: data.pollutants,
                selectedPollutant: pollutant,
                selectedCity: data.selectedCity
            };

            renderCharts(
                data.filteredData,
                data.radarData,
                data.hourlyDistributions,
                data.futurePredictions,
                data.pollutants,
                pollutant,
                data.selectedCity
            );
            updateTimestamp(data.selectedCity, timeRange, data.timestamp);
            logClientInfo(`Dashboard updated for city: ${data.selectedCity}, timeRange: ${timeRange}`);
            hideLoadingSpinner();
        })
        .catch(error => {
            console.error('Error updating dashboard:', error);
            showError('Failed to update dashboard.');
            logClientError('Error updating dashboard: ' + error.message);
            hideLoadingSpinner();
        });
}

function updateTimestamp(city, timeRange, timestamp) {
    const lastUpdatedElement = document.getElementById('last-updated');
    if (lastUpdatedElement) {
        const formattedTimestamp = timestamp || new Date().toISOString().replace('T', ' ').substring(0, 19);
        lastUpdatedElement.textContent = `Last updated: ${formattedTimestamp} | Showing data for ${city} (${timeRange})`;
    }
}

function showLoadingSpinner() {
    // Implement loading spinner if needed (e.g., add a spinner element to the DOM)
    console.log('Showing loading spinner');
}

function hideLoadingSpinner() {
    // Implement hiding spinner if needed
    console.log('Hiding loading spinner');
}

// Populate city dropdown
function populateCityDropdown() {
    fetch('/api/cities')
        .then(response => response.json())
        .then(data => {
            if (data.cities) {
                const citySelect = document.getElementById('city-select');
                citySelect.innerHTML = '';
                data.cities.forEach(city => {
                    const option = document.createElement('option');
                    option.value = city;
                    option.textContent = city;
                    if (city === getCurrentCity()) {
                        option.selected = true;
                    }
                    citySelect.appendChild(option);
                });
                logClientInfo(`Populated city dropdown with: ${data.cities}`);
            } else {
                showError('Failed to load cities.');
                logClientError('Failed to load cities: ' + JSON.stringify(data.error));
            }
        })
        .catch(error => {
            console.error('Error fetching cities:', error);
            showError('Error fetching city list.');
            logClientError('Error fetching cities: ' + error.message);
        });
}

function showError(message) {
    const errorPanel = document.getElementById('error-panel');
    if (errorPanel) {
        errorPanel.innerHTML = `
            <p>Error: ${message}</p>
            <button id="clear-errors" class="mt-2 px-4 py-2 bg-red-500 text-white rounded-md">Clear</button>
        `;
        errorPanel.style.display = 'block';
        const clearErrors = document.getElementById('clear-errors');
        if (clearErrors) {
            clearErrors.addEventListener('click', () => {
                errorPanel.style.display = 'none';
            });
        }
    } else {
        console.warn('Error panel not found');
    }
}

function logClientInfo(message) {
    fetch('/api/log', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ level: 'info', message })
    }).catch(error => console.error('Error logging info:', error));
}

function logClientError(message) {
    fetch('/api/log', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ level: 'error', message })
    }).catch(error => console.error('Error logging error:', error));
}