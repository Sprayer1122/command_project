// Global variables
let allTestcases = [];

// DOM elements
const clusteredTableContainer = document.getElementById('clusteredTableContainer');
const detailsView = document.getElementById('detailsView');
const loadingSpinner = document.getElementById('loadingSpinner');
const noDataMessage = document.getElementById('noDataMessage');

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    loadClustered();
});

// Load data from API
async function loadClustered() {
    showLoading(true);
    try {
        const res = await fetch('/api/clustered');
        const data = await res.json();
        if (res.ok && data.summary) {
            updateStatsFromSummary(data.summary);
            renderSummaryTable(data.summary);
            noDataMessage.style.display = data.summary.length === 0 ? 'block' : 'none';
        } else {
            noDataMessage.style.display = 'block';
        }
    } catch (e) {
        noDataMessage.style.display = 'block';
    } finally {
        showLoading(false);
    }
}

// Update statistics
function updateStatsFromSummary(summary) {
    document.getElementById('totalCases').textContent = summary.reduce((acc, row) => acc + row.total_failures, 0);
    document.getElementById('filteredCases').textContent = summary.reduce((acc, row) => acc + row.unique_failures, 0);
    document.getElementById('generatedOn').textContent = new Date().toLocaleString();
}

// Render the main summary table
function renderSummaryTable(summary) {
    let html = `<table class="summary-table">
        <thead>
            <tr>
                <th>S.No</th>
                <th>Failing Command</th>
                <th>Unique Failures</th>
            </tr>
        </thead>
        <tbody>`;
    summary.forEach((row, idx) => {
        html += `<tr data-cmd="${encodeURIComponent(row.failing_command)}" class="summary-row">
            <td>${row.sno}</td>
            <td>
                <button class="expand-btn" aria-label="Expand" data-idx="${idx}">+</button>
                <span>${row.failing_command}</span>
            </td>
            <td>${row.unique_failures} (${row.total_failures})</td>
        </tr>
        <tr class="expand-row" style="display:none;"><td colspan="3"><div class="expand-content"></div></td></tr>`;
    });
    html += `</tbody></table>`;
    clusteredTableContainer.innerHTML = html;

    // Add expand/collapse listeners
    document.querySelectorAll('.expand-btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            const idx = parseInt(this.getAttribute('data-idx'));
            toggleExpand(idx, summary[idx]);
        });
    });
}

// Toggle expand/collapse for a summary row
function toggleExpand(idx, row) {
    const allExpandRows = document.querySelectorAll('.expand-row');
    const expandRow = allExpandRows[idx];
    const expandContent = expandRow.querySelector('.expand-content');
    if (expandRow.style.display === 'none') {
        // Collapse all others
        allExpandRows.forEach(r => r.style.display = 'none');
        document.querySelectorAll('.expand-btn').forEach(b => b.textContent = '+');
        // Expand this
        expandRow.style.display = '';
        document.querySelectorAll('.expand-btn')[idx].textContent = '-';
        renderTagTable(expandContent, row);
    } else {
        expandRow.style.display = 'none';
        document.querySelectorAll('.expand-btn')[idx].textContent = '+';
    }
}

// Render the tag sub-table for a command
function renderTagTable(container, row) {
    let html = `<table class="tag-table">
        <thead><tr><th>Tag</th><th>Error Message</th><th>Count</th></tr></thead><tbody>`;
    row.tags.forEach(tagRow => {
        html += `<tr>
            <td>${tagRow.tag}</td>
            <td>${tagRow.error_message}</td>
            <td><a class="count-link" href="/testcases?command=${encodeURIComponent(row.failing_command)}&tag=${encodeURIComponent(tagRow.tag)}" target="_blank">${tagRow.count}</a></td>
        </tr>`;
    });
    html += `</tbody></table>`;
    container.innerHTML = html;
}

// Show the details view for a command+tag
async function showDetailsView(command, tag) {
    detailsView.style.display = 'block';
    detailsView.innerHTML = '<div>Loading...</div>';
    try {
        const res = await fetch(`/api/clustered/details?command=${command}&tag=${tag}`);
        const data = await res.json();
        if (res.ok) {
            let html = `<button class="close-details" onclick="hideDetailsView()">&times;</button>`;
            html += `<h2>${data.command} / ${data.tag}</h2>`;
            html += `<div style="margin-bottom:10px;color:#888;">${data.error_message}</div>`;
            html += `<ul>`;
            data.testcases.forEach(tc => {
                html += `<li>${tc}</li>`;
            });
            html += `</ul>`;
            detailsView.innerHTML = html;
            window.scrollTo({top: detailsView.offsetTop - 30, behavior: 'smooth'});
        } else {
            detailsView.innerHTML = '<div style="color:red;">Not found</div>';
        }
    } catch (e) {
        detailsView.innerHTML = '<div style="color:red;">Error loading details</div>';
    }
}
window.hideDetailsView = function() {
    detailsView.style.display = 'none';
}

// Show loading spinner
function showLoading(show) {
    loadingSpinner.style.display = show ? 'block' : 'none';
    if (show) {
        clusteredTableContainer.innerHTML = '';
        detailsView.style.display = 'none';
        noDataMessage.style.display = 'none';
    }
} 