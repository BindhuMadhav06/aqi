// Chart creation functions for AQI Dashboard

function createTimeSeriesChart(ctx, data, pollutant) {
    const colors = getChartColors();
    const plotData = data.plotData[pollutant];
    
    return new Chart(ctx, {
        type: 'line',
        data: {
            labels: plotData.labels || plotData.actual.map((_, i) => new Date(Date.now() + i * 3600000).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false })),
            datasets: [
                {
                    label: `${pollutant} Actual (μg/m³)`,
                    data: plotData.actual,
                    borderColor: colors.primary,
                    backgroundColor: colors.primary + '20',
                    fill: true,
                    tension: 0.4,
                    pointRadius: 2,
                    pointHoverRadius: 4
                },
                {
                    label: `${pollutant} Predicted (μg/m³)`,
                    data: Array(plotData.actual.length).fill(null).concat(plotData.predicted),
                    borderColor: colors.danger,
                    backgroundColor: colors.danger + '20',
                    fill: true,
                    tension: 0.4,
                    pointRadius: 2,
                    pointHoverRadius: 4
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    title: { display: true, text: 'Time', color: colors.text },
                    ticks: { color: colors.text, maxTicksLimit: 10 },
                    grid: { color: colors.grid }
                },
                y: {
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
                    zoom: { wheel: { enabled: true }, pinch: { enabled: true }, mode: 'xy' },
                    pan: { enabled: true, mode: 'xy' }
                }
            }
        }
    });
}

function createRadarChart(ctx, radarData) {
    const colors = getChartColors();
    
    return new Chart(ctx, {
        type: 'radar',
        data: {
            labels: radarData.map(d => d.subject),
            datasets: [{
                label: 'Pollutant Levels',
                data: radarData.map(d => d.value),
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

function createHourlyDistributionChart(ctx, hourlyData, pollutant) {
    const colors = getChartColors();
    
    return new Chart(ctx, {
        type: 'bar',
        data: {
            labels: hourlyData.map(d => `${d.hour}:00`),
            datasets: [{
                label: `${pollutant} Average (μg/m³)`,
                data: hourlyData.map(d => d.average),
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
                    title: { display: true, text: 'Hour of Day', color: colors.text },
                    ticks: { color: colors.text },
                    grid: { color: colors.grid }
                },
                y: {
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

function createFuturePredictionsChart(ctx, predictions, pollutant) {
    const colors = getChartColors();
    
    return new Chart(ctx, {
        type: 'line',
        data: {
            labels: Array.from({ length: predictions.length }, (_, i) => `+${i+1}h`),
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
                    title: { display: true, text: 'Future Hours', color: colors.text },
                    ticks: { color: colors.text, maxTicksLimit: 12 },
                    grid: { color: colors.grid }
                },
                y: {
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

function createMultiPollutantChart(ctx, plotData, pollutants) {
    const colors = getChartColors();
    
    const labels = plotData[pollutants[0]]?.labels || plotData[pollutants[0]]?.actual.map((_, i) => new Date(Date.now() + i * 3600000).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false }));
    const datasets = pollutants.map(pollutant => ({
        label: pollutant,
        data: plotData[pollutant]?.actual || [],
        borderColor: colors[pollutant === 'PM2.5' ? 'primary' : pollutant === 'PM10' ? 'secondary' : pollutant === 'SO2' ? 'accent' : pollutant === 'NO2' ? 'danger' : pollutant === 'CO' ? 'info' : 'warning'],
        backgroundColor: colors[pollutant === 'PM2.5' ? 'primary' : pollutant === 'PM10' ? 'secondary' : pollutant === 'SO2' ? 'accent' : pollutant === 'NO2' ? 'danger' : pollutant === 'CO' ? 'info' : 'warning'] + '20',
        fill: true
    }));

    return new Chart(ctx, {
        type: 'line',
        data: { labels, datasets },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    title: { display: true, text: 'Time', color: colors.text },
                    ticks: { color: colors.text, maxTicksLimit: 10 },
                    grid: { color: colors.grid }
                },
                y: {
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

function createWeatherChart(ctx, weatherData) {
    const colors = getChartColors();
    
    const labels = weatherData.map(d => new Date(d.datetime || Date.now()).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false }));
    const datasets = [
        { label: 'Temperature (°C)', data: weatherData.map(d => d.temperature || 0), borderColor: colors.primary, yAxisID: 'y' },
        { label: 'Humidity (%)', data: weatherData.map(d => d.humidity || 0), borderColor: colors.secondary, yAxisID: 'y1' },
        { label: 'Wind Speed (m/s)', data: weatherData.map(d => d.windSpeed || 0), borderColor: colors.accent, yAxisID: 'y2' }
    ];

    return new Chart(ctx, {
        type: 'line',
        data: { labels, datasets },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    title: { display: true, text: 'Time', color: colors.text },
                    ticks: { color: colors.text, maxTicksLimit: 10 },
                    grid: { color: colors.grid }
                },
                y: {
                    title: { display: true, text: 'Temperature (°C)', color: colors.text },
                    ticks: { color: colors.text },
                    grid: { color: colors.grid }
                },
                y1: {
                    position: 'right',
                    title: { display: true, text: 'Humidity (%)', color: colors.text },
                    ticks: { color: colors.text },
                    grid: { drawOnChartArea: false }
                },
                y2: {
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

function createCorrelationChart(ctx, correlationData, pollutant) {
    const colors = getChartColors();
    
    const scatterData = correlationData.map(d => ({ x: d.temperature, y: d[pollutant.toLowerCase()] || d.pm25 }));
    const regression = calculateLinearRegression(scatterData);
    const regressionLine = scatterData.map(d => ({ x: d.x, y: regression.slope * d.x + regression.intercept }));

    return new Chart(ctx, {
        type: 'scatter',
        data: {
            datasets: [
                {
                    label: 'Data Points',
                    data: scatterData,
                    backgroundColor: colors.info + '80',
                    borderColor: colors.info,
                    pointRadius: 5
                },
                {
                    label: 'Regression Line',
                    data: regressionLine,
                    type: 'line',
                    borderColor: colors.danger,
                    borderWidth: 2,
                    fill: false,
                    pointRadius: 0
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    title: { display: true, text: 'Temperature (°C)', color: colors.text },
                    ticks: { color: colors.text },
                    grid: { color: colors.grid }
                },
                y: {
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

function calculateLinearRegression(data) {
    const n = data.length;
    let sumX = 0, sumY = 0, sumXY = 0, sumXX = 0;
    
    data.forEach(point => {
        sumX += point.x;
        sumY += point.y;
        sumXY += point.x * point.y;
        sumXX += point.x * point.x;
    });

    const slope = (n * sumXY - sumX * sumY) / (n * sumXX - sumX * sumX);
    const intercept = (sumY - slope * sumX) / n;
    
    return { slope, intercept };
}