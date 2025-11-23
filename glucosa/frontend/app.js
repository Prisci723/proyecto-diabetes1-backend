// ============================================================================
// Configuración y Variables Globales
// ============================================================================

const API_BASE_URL = 'http://localhost:8000';
let glucoseChart = null;

// ============================================================================
// Inicialización
// ============================================================================

document.addEventListener('DOMContentLoaded', function() {
    console.log('Aplicación iniciada');
    checkAPIConnection();
    generateHistoricalReadings();
    updateUserInputs();
});

// ============================================================================
// Verificar Conexión con API
// ============================================================================

async function checkAPIConnection() {
    const statusDot = document.querySelector('.status-dot');
    const statusText = document.querySelector('.status-text');
    
    try {
        const response = await fetch(`${API_BASE_URL}/health`);
        const data = await response.json();
        
        if (data.status === 'healthy' && data.model_loaded) {
            statusDot.classList.add('connected');
            statusText.textContent = 'Conectado';
            console.log('✓ Conexión con API establecida');
        } else {
            throw new Error('Modelo no cargado');
        }
    } catch (error) {
        statusText.textContent = 'Desconectado';
        console.error('Error de conexión:', error);
        showNotification('Error de conexión con el servidor', 'error');
    }
}

// ============================================================================
// Generar Campos de Lecturas Históricas
// ============================================================================

function generateHistoricalReadings() {
    const container = document.getElementById('historicalReadings');
    const now = new Date();
    
    container.innerHTML = '';
    
    for (let i = 11; i >= 0; i--) {
        const time = new Date(now - (i * 5 * 60 * 1000)); // Cada 5 minutos atrás
        const timeStr = time.toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' });
        
        const readingDiv = document.createElement('div');
        readingDiv.className = 'reading-item';
        readingDiv.innerHTML = `
            <div class="reading-header">
                <span class="reading-time">⏰ ${timeStr}</span>
                <span class="reading-label">Hace ${i * 5} min</span>
            </div>
            <div class="reading-grid">
                <div class="reading-field">
                    <label>Glucosa (mg/dL) *</label>
                    <input type="number" 
                           class="form-control reading-glucose" 
                           data-index="${11-i}"
                           data-timestamp="${time.toISOString()}"
                           placeholder="Ej: 150" 
                           min="20" 
                           max="600"
                           required>
                </div>
                <div class="reading-field">
                    <label>Carbohidratos (g)</label>
                    <input type="number" 
                           class="form-control reading-carbs" 
                           data-index="${11-i}"
                           placeholder="0" 
                           value="0"
                           min="0">
                </div>
                <div class="reading-field">
                    <label>Insulina (U)</label>
                    <input type="number" 
                           class="form-control reading-bolus" 
                           data-index="${11-i}"
                           placeholder="0" 
                           value="0"
                           min="0" 
                           step="0.1">
                </div>
                <div class="reading-field">
                    <label>Ejercicio (min)</label>
                    <input type="number" 
                           class="form-control reading-exercise" 
                           data-index="${11-i}"
                           placeholder="0" 
                           value="0"
                           min="0">
                </div>
            </div>
        `;
        
        container.appendChild(readingDiv);
    }
}

// ============================================================================
// Generar Campos de Inputs del Usuario
// ============================================================================

function updateUserInputs() {
    const nSteps = parseInt(document.getElementById('nSteps').value);
    const container = document.getElementById('userInputsContainer');
    
    container.innerHTML = '';
    
    for (let i = 0; i < nSteps; i++) {
        const minutes = (i + 1) * 5;
        
        const inputDiv = document.createElement('div');
        inputDiv.className = 'user-input-item';
        inputDiv.innerHTML = `
            <div class="input-header">
                🕐 +${minutes} minutos
            </div>
            <div class="input-grid">
                <div class="input-field">
                    <label>Carbohidratos (g)</label>
                    <input type="number" 
                           class="form-control user-carbs" 
                           data-step="${i}"
                           placeholder="0" 
                           value="0"
                           min="0">
                </div>
                <div class="input-field">
                    <label>Insulina (U)</label>
                    <input type="number" 
                           class="form-control user-bolus" 
                           data-step="${i}"
                           placeholder="0" 
                           value="0"
                           min="0" 
                           step="0.1">
                </div>
                <div class="input-field">
                    <label>Ejercicio intensidad (0-10)</label>
                    <input type="number" 
                           class="form-control user-exercise-intensity" 
                           data-step="${i}"
                           placeholder="0" 
                           value="0"
                           min="0" 
                           max="10">
                </div>
                <div class="input-field">
                    <label>Ejercicio duración (min)</label>
                    <input type="number" 
                           class="form-control user-exercise-duration" 
                           data-step="${i}"
                           placeholder="0" 
                           value="0"
                           min="0">
                </div>
            </div>
        `;
        
        container.appendChild(inputDiv);
    }
}

// ============================================================================
// Cargar Datos de Ejemplo
// ============================================================================

function loadSampleData() {
    // Datos de ejemplo realistas
    const sampleGlucose = [150, 145, 142, 138, 135, 140, 145, 150, 155, 160, 165, 170];
    
    const glucoseInputs = document.querySelectorAll('.reading-glucose');
    glucoseInputs.forEach((input, index) => {
        input.value = sampleGlucose[index];
    });
    
    // Simular una comida hace 30 minutos
    const carbsInputs = document.querySelectorAll('.reading-carbs');
    carbsInputs[6].value = 45;  // Hace 30 minutos
    
    const bolusInputs = document.querySelectorAll('.reading-bolus');
    bolusInputs[6].value = 5.0;  // Hace 30 minutos
    
    showNotification('Datos de ejemplo cargados correctamente', 'success');
}

// ============================================================================
// Recolectar Datos del Formulario
// ============================================================================

function collectHistoricalData() {
    const historicalData = [];
    const glucoseInputs = document.querySelectorAll('.reading-glucose');
    
    for (let i = 0; i < 12; i++) {
        const glucoseInput = glucoseInputs[i];
        const glucose = parseFloat(glucoseInput.value);
        
        if (!glucose || glucose < 20 || glucose > 600) {
            throw new Error(`Glucosa inválida en lectura ${i + 1}. Debe estar entre 20-600 mg/dL.`);
        }
        
        const timestamp = glucoseInput.dataset.timestamp;
        const carbs = parseFloat(document.querySelectorAll('.reading-carbs')[i].value) || 0;
        const bolus = parseFloat(document.querySelectorAll('.reading-bolus')[i].value) || 0;
        const exercise = parseFloat(document.querySelectorAll('.reading-exercise')[i].value) || 0;
        
        historicalData.push({
            timestamp: timestamp,
            glucose: glucose,
            carbs: carbs,
            bolus: bolus,
            exercise_intensity: exercise > 0 ? 5 : 0,  // Intensidad moderada si hay ejercicio
            exercise_duration: exercise
        });
    }
    
    return historicalData;
}

function collectUserInputs() {
    const nSteps = parseInt(document.getElementById('nSteps').value);
    const userInputs = [];
    
    for (let i = 0; i < nSteps; i++) {
        const carbs = parseFloat(document.querySelectorAll('.user-carbs')[i].value) || 0;
        const bolus = parseFloat(document.querySelectorAll('.user-bolus')[i].value) || 0;
        const exerciseIntensity = parseFloat(document.querySelectorAll('.user-exercise-intensity')[i].value) || 0;
        const exerciseDuration = parseFloat(document.querySelectorAll('.user-exercise-duration')[i].value) || 0;
        
        userInputs.push({
            carbs: carbs,
            bolus: bolus,
            exercise_intensity: exerciseIntensity,
            exercise_duration: exerciseDuration
        });
    }
    
    return userInputs;
}

// ============================================================================
// Hacer Predicción
// ============================================================================

async function makePrediction() {
    try {
        // Mostrar estado de carga
        showLoadingState();
        
        // Recolectar datos
        const historicalData = collectHistoricalData();
        const userInputs = collectUserInputs();
        const nSteps = parseInt(document.getElementById('nSteps').value);
        
        console.log('Enviando datos:', { historicalData, userInputs, nSteps });
        
        // Hacer request a la API
        const response = await fetch(`${API_BASE_URL}/predict`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                historical_data: historicalData,
                user_inputs: userInputs,
                n_steps: nSteps
            })
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Error en la predicción');
        }
        
        const result = await response.json();
        console.log('Resultado:', result);
        
        // Mostrar resultados
        displayResults(result);
        showNotification('Predicción completada exitosamente', 'success');
        
    } catch (error) {
        console.error('Error:', error);
        hideLoadingState();
        showNotification(error.message, 'error');
    }
}

// ============================================================================
// Mostrar/Ocultar Estados
// ============================================================================

function showLoadingState() {
    document.getElementById('loadingState').style.display = 'flex';
    document.getElementById('emptyState').style.display = 'none';
    document.getElementById('resultsContent').style.display = 'none';
}

function hideLoadingState() {
    document.getElementById('loadingState').style.display = 'none';
    document.getElementById('emptyState').style.display = 'flex';
}

// ============================================================================
// Mostrar Resultados
// ============================================================================

function displayResults(result) {
    document.getElementById('loadingState').style.display = 'none';
    document.getElementById('emptyState').style.display = 'none';
    document.getElementById('resultsContent').style.display = 'block';
    
    // Summary cards
    displaySummaryCards(result.summary);
    
    // Alerts
    displayAlerts(result.alerts);
    
    // Chart
    displayChart(result.predictions, result.timestamps);
    
    // Table
    displayPredictionsTable(result.predictions, result.timestamps);
    
    // Stats
    displayStats(result.summary);
}

function displaySummaryCards(summary) {
    document.getElementById('currentGlucose').textContent = summary.current_glucose;
    document.getElementById('finalGlucose').textContent = summary.final_glucose;
    
    const change = summary.change;
    const changeElement = document.getElementById('glucoseChange');
    changeElement.textContent = change > 0 ? `+${change}` : change;
    changeElement.style.color = change > 0 ? '#f59e0b' : '#10b981';
    
    const trendElement = document.getElementById('trend');
    trendElement.textContent = summary.trend === 'ascendente' ? '↗️ Subiendo' : '↘️ Bajando';
    trendElement.style.color = summary.trend === 'ascendente' ? '#f59e0b' : '#10b981';
}

function displayAlerts(alerts) {
    const container = document.getElementById('alertsContainer');
    container.innerHTML = '';
    
    if (alerts.length === 0) {
        const noAlerts = document.createElement('div');
        noAlerts.className = 'alert alert-success';
        noAlerts.innerHTML = `
            <span class="alert-icon">✅</span>
            <div class="alert-content">
                <div class="alert-title">Todo bien</div>
                <div class="alert-message">No se detectaron alertas críticas en el horizonte de predicción.</div>
            </div>
        `;
        container.appendChild(noAlerts);
        return;
    }
    
    alerts.forEach(alert => {
        const alertDiv = document.createElement('div');
        const alertClass = alert.severity === 'CRÍTICO' ? 'alert-critical' : 'alert-warning';
        const icon = alert.type === 'HIPOGLUCEMIA' ? '⚠️' : '📈';
        
        alertDiv.className = `alert ${alertClass}`;
        alertDiv.innerHTML = `
            <span class="alert-icon">${icon}</span>
            <div class="alert-content">
                <div class="alert-title">${alert.type} - ${alert.time}</div>
                <div class="alert-message">${alert.message}</div>
            </div>
        `;
        
        container.appendChild(alertDiv);
    });
}

function displayChart(predictions, timestamps) {
    const ctx = document.getElementById('glucoseChart').getContext('2d');
    
    // Destruir gráfico anterior si existe
    if (glucoseChart) {
        glucoseChart.destroy();
    }
    
    // Formatear timestamps para el eje X
    const labels = timestamps.map(ts => {
        const date = new Date(ts);
        return date.toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' });
    });
    
    glucoseChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Predicción de Glucosa',
                data: predictions,
                borderColor: '#3b82f6',
                backgroundColor: 'rgba(59, 130, 246, 0.1)',
                borderWidth: 3,
                fill: true,
                tension: 0.4,
                pointRadius: 4,
                pointHoverRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    labels: {
                        color: '#cbd5e1',
                        font: {
                            size: 12
                        }
                    }
                },
                tooltip: {
                    backgroundColor: '#1e293b',
                    titleColor: '#f1f5f9',
                    bodyColor: '#cbd5e1',
                    borderColor: '#334155',
                    borderWidth: 1,
                    padding: 12,
                    displayColors: false,
                    callbacks: {
                        label: function(context) {
                            return `Glucosa: ${context.parsed.y.toFixed(1)} mg/dL`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: false,
                    grid: {
                        color: '#334155'
                    },
                    ticks: {
                        color: '#cbd5e1'
                    },
                    title: {
                        display: true,
                        text: 'Glucosa (mg/dL)',
                        color: '#cbd5e1'
                    }
                },
                x: {
                    grid: {
                        color: '#334155'
                    },
                    ticks: {
                        color: '#cbd5e1',
                        maxRotation: 45,
                        minRotation: 45
                    }
                }
            },
            annotation: {
                annotations: [
                    {
                        type: 'line',
                        yMin: 70,
                        yMax: 70,
                        borderColor: '#ef4444',
                        borderWidth: 2,
                        borderDash: [5, 5],
                        label: {
                            content: 'Hipoglucemia',
                            enabled: true,
                            position: 'end'
                        }
                    },
                    {
                        type: 'line',
                        yMin: 180,
                        yMax: 180,
                        borderColor: '#f59e0b',
                        borderWidth: 2,
                        borderDash: [5, 5],
                        label: {
                            content: 'Hiperglucemia',
                            enabled: true,
                            position: 'end'
                        }
                    }
                ]
            }
        }
    });
}

function displayPredictionsTable(predictions, timestamps) {
    const tbody = document.getElementById('predictionsTableBody');
    tbody.innerHTML = '';
    
    predictions.forEach((pred, index) => {
        const time = new Date(timestamps[index]);
        const timeStr = time.toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' });
        const minutes = (index + 1) * 5;
        
        let status = 'normal';
        let statusText = 'Normal';
        
        if (pred < 70) {
            status = 'critical';
            statusText = 'Hipoglucemia';
        } else if (pred < 80) {
            status = 'low';
            statusText = 'Bajo';
        } else if (pred > 180) {
            status = 'high';
            statusText = 'Alto';
        } else if (pred > 250) {
            status = 'critical';
            statusText = 'Hiperglucemia';
        }
        
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${timeStr} (+${minutes} min)</td>
            <td><strong>${pred.toFixed(1)}</strong> mg/dL</td>
            <td><span class="status-badge ${status}">${statusText}</span></td>
        `;
        
        tbody.appendChild(row);
    });
}

function displayStats(summary) {
    document.getElementById('minGlucose').textContent = `${summary.min_glucose} mg/dL`;
    document.getElementById('maxGlucose').textContent = `${summary.max_glucose} mg/dL`;
    document.getElementById('avgGlucose').textContent = `${summary.avg_glucose} mg/dL`;
    document.getElementById('timeInRange').textContent = `${summary.time_in_range.toFixed(1)}%`;
}

// ============================================================================
// Notificaciones
// ============================================================================

function showNotification(message, type = 'info') {
    // Simple console notification (puedes mejorar esto con una librería de toast)
    const emoji = type === 'success' ? '✅' : type === 'error' ? '❌' : 'ℹ️';
    console.log(`${emoji} ${message}`);
    
    // Puedes agregar aquí una librería de notificaciones como toastr o sweetalert
    if (type === 'error') {
        alert(`Error: ${message}`);
    }
}

// ============================================================================
// Utilidades
// ============================================================================

function formatTime(date) {
    return date.toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' });
}

function getGlucoseStatus(glucose) {
    if (glucose < 70) return 'critical';
    if (glucose < 80) return 'low';
    if (glucose > 180) return 'high';
    if (glucose > 250) return 'critical';
    return 'normal';
}
