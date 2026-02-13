/**
 * Statistics Page JavaScript
 * Handles data visualization and export functionality
 */

/**
 * Initialize the statistics page
 */
function initStats() {
    console.log('Statistics page initialized');
    
    setupExportButtons();
    setupTableEnhancements();
    highlightBestDay();
}

/**
 * Setup export button functionality
 */
function setupExportButtons() {
    const exportButtons = document.querySelectorAll('.export-btn');
    
    exportButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            // Add visual feedback
            this.style.transform = 'scale(0.95)';
            setTimeout(() => {
                this.style.transform = '';
            }, 150);
        });
    });
}

/**
 * Enhance table with interactive features
 */
function setupTableEnhancements() {
    const table = document.querySelector('table');
    if (!table) return;
    
    // Add sorting capability (optional enhancement)
    const headers = table.querySelectorAll('th');
    let sortDirection = {};
    
    headers.forEach((header, index) => {
        header.style.cursor = 'pointer';
        header.title = 'Klicken zum Sortieren';
        
        header.addEventListener('click', () => {
            sortTable(index, header);
        });
        
        sortDirection[index] = 'asc';
    });
}

/**
 * Sort table by column
 * @param {number} columnIndex - Index of column to sort by
 * @param {HTMLElement} header - Header element that was clicked
 */
function sortTable(columnIndex, header) {
    const table = header.closest('table');
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    
    // Determine sort direction
    const currentDirection = header.dataset.sortDirection || 'asc';
    const newDirection = currentDirection === 'asc' ? 'desc' : 'asc';
    
    // Remove sort indicators from all headers
    table.querySelectorAll('th').forEach(th => {
        th.textContent = th.textContent.replace(' ↑', '').replace(' ↓', '');
        delete th.dataset.sortDirection;
    });
    
    // Add sort indicator to current header
    header.dataset.sortDirection = newDirection;
    header.textContent += newDirection === 'asc' ? ' ↑' : ' ↓';
    
    // Sort rows
    rows.sort((a, b) => {
        const aValue = a.cells[columnIndex].textContent.trim();
        const bValue = b.cells[columnIndex].textContent.trim();
        
        // Try to parse as numbers
        const aNum = parseFloat(aValue);
        const bNum = parseFloat(bValue);
        
        if (!isNaN(aNum) && !isNaN(bNum)) {
            return newDirection === 'asc' ? aNum - bNum : bNum - aNum;
        }
        
        // Sort as strings
        return newDirection === 'asc' 
            ? aValue.localeCompare(bValue, 'de')
            : bValue.localeCompare(aValue, 'de');
    });
    
    // Re-append sorted rows
    rows.forEach(row => tbody.appendChild(row));
}

/**
 * Highlight the day with most participants
 */
function highlightBestDay() {
    const tbody = document.querySelector('tbody');
    if (!tbody) return;
    
    const rows = tbody.querySelectorAll('tr');
    let maxTotal = 0;
    let bestRow = null;
    
    rows.forEach(row => {
        const totalCell = row.cells[3]; // Total column
        const total = parseInt(totalCell.textContent);
        
        if (total > maxTotal) {
            maxTotal = total;
            bestRow = row;
        }
    });
    
    if (bestRow && maxTotal > 0) {
        bestRow.style.background = 'rgba(220, 38, 38, 0.2)';
        bestRow.style.borderLeft = '4px solid #dc2626';
    }
}

/**
 * Calculate and display statistics summary
 */
function calculateSummary() {
    const tbody = document.querySelector('tbody');
    if (!tbody) return;
    
    const rows = tbody.querySelectorAll('tr');
    let totalRegistrations = 0;
    let totalGuests = 0;
    let totalParticipants = 0;
    let daysCount = rows.length;
    
    rows.forEach(row => {
        totalRegistrations += parseInt(row.cells[1].textContent) || 0;
        totalGuests += parseInt(row.cells[2].textContent) || 0;
        totalParticipants += parseInt(row.cells[3].textContent) || 0;
    });
    
    return {
        totalRegistrations,
        totalGuests,
        totalParticipants,
        daysCount,
        avgPerDay: daysCount > 0 ? (totalParticipants / daysCount).toFixed(1) : 0
    };
}

/**
 * Format date to German format
 * @param {string} dateString - Date string to format
 * @returns {string} Formatted date
 */
function formatDateGerman(dateString) {
    const date = new Date(dateString);
    const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
    return date.toLocaleDateString('de-DE', options);
}

/**
 * Export table data as JSON (for future enhancements)
 * @returns {Array} Table data as array of objects
 */
function exportTableData() {
    const table = document.querySelector('table');
    if (!table) return [];
    
    const headers = Array.from(table.querySelectorAll('th')).map(th => th.textContent.trim());
    const rows = Array.from(table.querySelectorAll('tbody tr'));
    
    return rows.map(row => {
        const cells = Array.from(row.cells);
        const rowData = {};
        
        cells.forEach((cell, index) => {
            rowData[headers[index]] = cell.textContent.trim();
        });
        
        return rowData;
    });
}

/**
 * Print statistics (opens print dialog)
 */
function printStats() {
    window.print();
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initStats);
} else {
    initStats();
}

// Add print media styles
const printStyles = `
    @media print {
        body {
            background: white;
            color: black;
        }
        .container {
            box-shadow: none;
            border: none;
        }
        .button-group {
            display: none;
        }
        table {
            page-break-inside: avoid;
        }
    }
`;

const styleSheet = document.createElement('style');
styleSheet.textContent = printStyles;
document.head.appendChild(styleSheet);

// Export functions for potential use
window.printStats = printStats;
window.exportTableData = exportTableData;
