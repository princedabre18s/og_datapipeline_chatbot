// script.js

function showToast(message, type = 'info') {
    Toastify({
        text: message,
        duration: 5000,
        gravity: 'top',
        position: 'right',
        style: { 
            background: type === 'success' ? '#88C057' : type === 'error' ? '#BF616A' : '#3B4252', 
            color: '#ECEFF4',
            borderRadius: '8px',
            boxShadow: '0 5px 15px rgba(0, 0, 0, 0.3)'
        },
    }).showToast();
}

function appendLog(log) {
    const logContainer = document.getElementById('log-container');
    if (!logContainer) return;
    const logEntry = document.createElement('div');
    logEntry.className = 'log-entry';
    logEntry.style.opacity = '0';
    let logClass = log.includes('[ERROR]') ? 'log-error' : log.includes('[WARNING]') ? 'log-warning' : 'log-info';
    logEntry.innerHTML = `<span class="timestamp">${log.split(' - ')[0]}</span> <span class="${logClass}">${log.split(' - ').slice(1).join(' - ')}</span>`;
    logContainer.appendChild(logEntry);
    setTimeout(() => {
        logEntry.style.transition = 'opacity 0.5s';
        logEntry.style.opacity = '1';
    }, 10);
    logContainer.scrollTop = logContainer.scrollHeight;
}

function clearLogs() {
    const logContainer = document.getElementById('log-container');
    if (logContainer) logContainer.innerHTML = `<div class="log-entry">[INFO] ${new Date().toISOString().replace('T', ' ').substring(0, 19)} - Logs cleared.</div>`;
}

function showLoader(show) {
    document.getElementById('loader').style.display = show ? 'flex' : 'none';
}

function checkConnection() {
    fetch('/grand-total')
        .then(response => response.json())
        .then(data => {
            document.getElementById('status-indicator').className = 'status-online';
            document.getElementById('connection-status').textContent = 'Online';
            appendLog(`[INFO] ${new Date().toISOString().replace('T', ' ').substring(0, 19)} - Connected to server.`);
        })
        .catch(() => {
            document.getElementById('status-indicator').className = 'status-offline';
            document.getElementById('connection-status').textContent = 'Offline';
            appendLog(`[ERROR] ${new Date().toISOString().replace('T', ' ').substring(0, 19)} - Server offline.`);
        });
}

// Upload handling with live status updates
document.getElementById('upload-form')?.addEventListener('submit', async function(e) {
    e.preventDefault();
    const fileInput = document.getElementById('file');
    const dateInput = document.getElementById('date');
    const uploadBtn = document.getElementById('upload-btn');
    const statusSteps = {
        upload: document.getElementById('step-upload'),
        process: document.getElementById('step-process'),
        db: document.getElementById('step-db'),
        report: document.getElementById('step-report')
    };
    const statusMessage = document.getElementById('status-message');
    const resultSummary = document.getElementById('result-summary');

    if (!fileInput.files.length || !dateInput.value) {
        showToast('Please select a file and date.', 'error');
        return;
    }

    // Reset UI
    uploadBtn.disabled = true;
    resultSummary.classList.add('d-none');
    statusMessage.classList.add('d-none');
    Object.values(statusSteps).forEach(step => {
        step.classList.remove('active', 'completed');
        step.style.opacity = '0.5';
    });

    const formData = new FormData();
    formData.append('file', fileInput.files[0]);
    formData.append('date', dateInput.value);

    try {
        // Step 1: Uploading File
        statusSteps.upload.classList.add('active');
        statusSteps.upload.style.opacity = '1';
        appendLog(`[INFO] ${new Date().toISOString().replace('T', ' ').substring(0, 19)} - Starting file upload...`);

        const response = await fetch('/process', { method: 'POST', body: formData });
        statusSteps.upload.classList.remove('active');
        statusSteps.upload.classList.add('completed');

        // Step 2: Processing Data
        statusSteps.process.classList.add('active');
        statusSteps.process.style.opacity = '1';
        appendLog(`[INFO] ${new Date().toISOString().replace('T', ' ').substring(0, 19)} - Processing data...`);

        const data = await response.json();
        statusSteps.process.classList.remove('active');
        statusSteps.process.classList.add('completed');

        if (data.error) throw new Error(data.error);

        // Step 3: Updating Database
        statusSteps.db.classList.add('active');
        statusSteps.db.style.opacity = '1';
        appendLog(`[INFO] ${new Date().toISOString().replace('T', ' ').substring(0, 19)} - Updating database...`);
        await new Promise(resolve => setTimeout(resolve, 500)); // Simulate DB update
        statusSteps.db.classList.remove('active');
        statusSteps.db.classList.add('completed');

        // Step 4: Generating Report
        statusSteps.report.classList.add('active');
        statusSteps.report.style.opacity = '1';
        appendLog(`[INFO] ${new Date().toISOString().replace('T', ' ').substring(0, 19)} - Generating report...`);
        await new Promise(resolve => setTimeout(resolve, 500)); // Simulate report generation
        statusSteps.report.classList.remove('active');
        statusSteps.report.classList.add('completed');

        // Show Results
        document.getElementById('result-date').textContent = data.results.date;
        document.getElementById('result-records').textContent = data.results.total_records.toLocaleString();
        document.getElementById('result-new').textContent = data.results.new_records.toLocaleString();
        document.getElementById('result-updated').textContent = data.results.updated_records.toLocaleString();
        document.getElementById('result-daily-sales').textContent = data.results.daily_total_sales.toLocaleString();
        document.getElementById('result-daily-purchases').textContent = data.results.daily_total_purchases.toLocaleString();
        resultSummary.classList.remove('d-none');

        const downloadBtn = document.getElementById('download-btn');
        downloadBtn.disabled = false;
        downloadBtn.onclick = () => window.location.href = `/download/${data.results.file_name}`;

        // Success Message
        statusMessage.textContent = 'Processing Completed Successfully!';
        statusMessage.classList.remove('d-none');
        statusMessage.classList.add('success');

        data.logs.forEach(appendLog);
        showToast('Data processed successfully!', 'success');
    } catch (error) {
        // Error Handling
        Object.values(statusSteps).forEach(step => {
            if (step.classList.contains('active')) {
                step.classList.remove('active');
                step.style.opacity = '0.5';
            }
        });
        statusMessage.textContent = `Error: ${error.message}`;
        statusMessage.classList.remove('d-none');
        statusMessage.classList.add('error');
        appendLog(`[ERROR] ${new Date().toISOString().replace('T', ' ').substring(0, 19)} - ${error.message}`);
        showToast(`Error: ${error.message}`, 'error');
    } finally {
        uploadBtn.disabled = false;
    }
});

// Data Preview
function loadDataPreview() {
    const tableBody = document.getElementById('data-table-body');
    if (!tableBody) return;

    showLoader(true);
    fetch('/preview')
        .then(response => response.json())
        .then(data => {
            tableBody.innerHTML = '';
            if (data.warning) {
                tableBody.innerHTML = `<tr><td colspan="10" class="text-center">${data.warning}</td></tr>`;
                showToast(data.warning, 'warning');
            } else {
                data.data.forEach((row, index) => {
                    const tr = document.createElement('tr');
                    tr.style.opacity = '0';
                    tr.innerHTML = `
                        <td>${row.brand}</td>
                        <td>${row.category}</td>
                        <td>${row.size}</td>
                        <td>${row.mrp.toFixed(2)}</td>
                        <td>${row.color}</td>
                        <td>${row.sales_qty}</td>
                        <td>${row.purchase_qty}</td>
                        <td>${row.week}</td>
                        <td>${row.month}</td>
                        <td>${new Date(row.created_at).toLocaleString()}</td>
                    `;
                    tableBody.appendChild(tr);
                    setTimeout(() => {
                        tr.style.transition = 'opacity 0.5s';
                        tr.style.opacity = '1';
                    }, index * 30);
                });

                const animateNumber = (id, value) => {
                    let start = 0;
                    const element = document.getElementById(id);
                    const timer = setInterval(() => {
                        start += Math.ceil(value / 20);
                        element.textContent = start.toLocaleString();
                        if (start >= value) {
                            element.textContent = value.toLocaleString();
                            clearInterval(timer);
                        }
                    }, 50);
                };

                animateNumber('metric-total-records', data.metrics.total_records);
                animateNumber('metric-unique-brands', data.metrics.unique_brands);
                animateNumber('metric-unique-categories', data.metrics.unique_categories);
                const ratio = data.metrics.neon_total_purchases > 0 
                    ? ((data.metrics.neon_total_sales / data.metrics.neon_total_purchases) * 100).toFixed(1) 
                    : 0;
                document.getElementById('metric-ratio').textContent = `${ratio}%`;
            }
            data.logs.forEach(appendLog);
            showLoader(false);
        })
        .catch(error => {
            tableBody.innerHTML = `<tr><td colspan="10" class="text-center">Error loading data</td></tr>`;
            appendLog(`[ERROR] ${new Date().toISOString().replace('T', ' ').substring(0, 19)} - Failed to load preview: ${error.message}`);
            showToast('Failed to load preview.', 'error');
            showLoader(false);
        });
}

// Visualizations
function loadVisualizations(startDate = null, endDate = null) {
    showLoader(true);
    const requestOptions = startDate && endDate ? {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ start_date: startDate, end_date: endDate })
    } : { method: 'GET' };

    fetch('/visualizations', requestOptions)
        .then(response => response.json())
        .then(data => {
            if (data.warning) {
                showToast(data.warning, 'warning');
                ['brand-chart', 'category-chart', 'monthly-chart', 'weekly-chart'].forEach(id => {
                    document.getElementById(id).innerHTML = '<p class="text-center">No data available</p>';
                });
            } else {
                const animateChart = (id, chartData) => {
                    const chartDiv = document.getElementById(id);
                    chartDiv.style.opacity = '0';
                    Plotly.newPlot(id, chartData.data, chartData.layout, { responsive: true });
                    setTimeout(() => {
                        chartDiv.style.transition = 'opacity 1s';
                        chartDiv.style.opacity = '1';
                    }, 100);
                };

                if (data.visualizations.brand) animateChart('brand-chart', JSON.parse(data.visualizations.brand));
                if (data.visualizations.category) animateChart('category-chart', JSON.parse(data.visualizations.category));
                if (data.visualizations.monthly) animateChart('monthly-chart', JSON.parse(data.visualizations.monthly));
                if (data.visualizations.weekly) animateChart('weekly-chart', JSON.parse(data.visualizations.weekly));
            }
            data.logs.forEach(appendLog);
            showLoader(false);
        })
        .catch(error => {
            appendLog(`[ERROR] ${new Date().toISOString().replace('T', ' ').substring(0, 19)} - Failed to load visualizations: ${error.message}`);
            showToast('Failed to load visualizations.', 'error');
            showLoader(false);
        });
}

// Export Data
function exportData() {
    fetch('/preview')
        .then(response => response.json())
        .then(data => {
            if (data.warning) {
                showToast(data.warning, 'warning');
                return;
            }
            const csv = Papa.unparse(data.data);
            const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
            const link = document.createElement('a');
            link.href = URL.createObjectURL(blob);
            link.download = 'inventory_data.csv';
            link.click();
            showToast('Data exported successfully!', 'success');
        })
        .catch(error => {
            showToast('Failed to export data.', 'error');
            appendLog(`[ERROR] ${new Date().toISOString().replace('T', ' ').substring(0, 19)} - Export failed: ${error.message}`);
        });
}

// Theme Toggle
document.getElementById('theme-toggle').addEventListener('click', () => {
    document.body.classList.toggle('light-theme');
    const icon = document.getElementById('theme-toggle').querySelector('i');
    icon.classList.toggle('fa-moon');
    icon.classList.toggle('fa-sun');
    localStorage.setItem('theme', document.body.classList.contains('light-theme') ? 'light' : 'dark');
});

// Navigation
function showSection(sectionId) {
    document.querySelectorAll('.section').forEach(section => {
        section.classList.remove('active');
        section.style.opacity = '0';
    });
    const targetSection = document.getElementById(sectionId);
    targetSection.classList.add('active');
    setTimeout(() => {
        targetSection.style.transition = 'opacity 0.5s';
        targetSection.style.opacity = '1';
    }, 10);

    if (sectionId === 'data-preview') loadDataPreview();
    else if (sectionId === 'visualizations') loadVisualizations();
}

document.querySelectorAll('.nav-link').forEach(link => {
    link.addEventListener('click', function(e) {
        e.preventDefault();
        document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
        this.classList.add('active');
        showSection(this.getAttribute('data-section'));
    });
});

// Event Listeners
document.getElementById('clear-logs')?.addEventListener('click', clearLogs);
document.getElementById('refresh-preview')?.addEventListener('click', () => {
    loadDataPreview();
    showToast('Data refreshed!', 'success');
});
document.getElementById('date-filter-form')?.addEventListener('submit', function(e) {
    e.preventDefault();
    const startDate = document.getElementById('start-date').value;
    const endDate = document.getElementById('end-date').value;
    if (startDate && endDate) {
        loadVisualizations(startDate, endDate);
        showToast('Filters applied!', 'success');
    } else {
        showToast('Select both dates.', 'warning');
    }
});
document.getElementById('export-data')?.addEventListener('click', exportData);

// Initial Setup
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.section').forEach(section => section.style.opacity = '0');
    showSection('upload');
    checkConnection();
    setInterval(checkConnection, 30000);
    appendLog(`[INFO] ${new Date().toISOString().replace('T', ' ').substring(0, 19)} - System ready.`);

    // Load theme from localStorage
    if (localStorage.getItem('theme') === 'light') {
        document.body.classList.add('light-theme');
        document.getElementById('theme-toggle').querySelector('i').classList.replace('fa-moon', 'fa-sun');
    }
});