// MRF Waste Logger JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Auto-fill current date and time on page load
    const datetimeInput = document.getElementById('datetime');
    if (datetimeInput) {
        const now = new Date();
        // Format to local datetime string for datetime-local input
        const year = now.getFullYear();
        const month = String(now.getMonth() + 1).padStart(2, '0');
        const day = String(now.getDate()).padStart(2, '0');
        const hours = String(now.getHours()).padStart(2, '0');
        const minutes = String(now.getMinutes()).padStart(2, '0');
        
        datetimeInput.value = `${year}-${month}-${day}T${hours}:${minutes}`;
    }

    // Form validation and enhancement
    const wasteForm = document.getElementById('wasteForm');
    if (wasteForm) {
        wasteForm.addEventListener('submit', function(e) {
            // Additional client-side validation
            const vehicleNumber = document.getElementById('vehicle_number').value.trim();
            const wasteWeight = document.getElementById('waste_weight').value;
            
            // Basic vehicle number format validation
            if (vehicleNumber && !isValidVehicleNumber(vehicleNumber)) {
                e.preventDefault();
                showAlert('Please enter a valid vehicle number format (e.g., MH-01-AB-1234)', 'warning');
                return;
            }
            
            // Weight validation
            if (wasteWeight && (isNaN(wasteWeight) || parseFloat(wasteWeight) <= 0)) {
                e.preventDefault();
                showAlert('Please enter a valid positive weight value', 'warning');
                return;
            }
            
            // Save to localStorage for offline support (bonus feature)
            saveToLocalStorage();
        });
    }

    // Offline support functions
    function saveToLocalStorage() {
        if (!navigator.onLine) {
            const formData = getFormData();
            if (formData) {
                let offlineData = JSON.parse(localStorage.getItem('offlineWasteLogs') || '[]');
                offlineData.push({
                    ...formData,
                    timestamp: new Date().toISOString(),
                    synced: false
                });
                localStorage.setItem('offlineWasteLogs', JSON.stringify(offlineData));
                showAlert('Data saved locally. Will sync when online.', 'info');
            }
        }
    }

    function getFormData() {
        const form = document.getElementById('wasteForm');
        if (!form) return null;
        
        return {
            vehicle_number: form.vehicle_number.value,
            datetime: form.datetime.value,
            waste_weight: form.waste_weight.value,
            waste_type: form.waste_type.value,
            material_category: form.material_category.value,
            destination: form.destination.value
        };
    }

    // Sync offline data when online
    function syncOfflineData() {
        const offlineData = JSON.parse(localStorage.getItem('offlineWasteLogs') || '[]');
        const unsyncedData = offlineData.filter(item => !item.synced);
        
        if (unsyncedData.length > 0 && navigator.onLine) {
            // Note: In a real implementation, you would send this data to the server
            // For this application, we'll just mark as synced since we can't make fetch calls
            const updatedData = offlineData.map(item => ({
                ...item,
                synced: true
            }));
            localStorage.setItem('offlineWasteLogs', JSON.stringify(updatedData));
            showAlert(`Synced ${unsyncedData.length} offline entries`, 'success');
        }
    }

    // Check for offline data on page load
    window.addEventListener('online', syncOfflineData);
    
    // Check for existing offline data
    const offlineData = JSON.parse(localStorage.getItem('offlineWasteLogs') || '[]');
    const unsyncedCount = offlineData.filter(item => !item.synced).length;
    if (unsyncedCount > 0) {
        showAlert(`You have ${unsyncedCount} entries saved offline. They will sync when you submit the form.`, 'info');
    }

    // Utility functions
    function isValidVehicleNumber(vehicleNum) {
        // Basic validation for Indian vehicle number format
        const pattern = /^[A-Z]{2}-\d{2}-[A-Z]{1,2}-\d{4}$/;
        return pattern.test(vehicleNum.toUpperCase());
    }

    function showAlert(message, type = 'info') {
        // Create alert element
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show`;
        alertDiv.innerHTML = `
            <i data-feather="${type === 'error' ? 'alert-circle' : type === 'success' ? 'check-circle' : 'info'}"></i>
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        // Insert at top of main content
        const main = document.querySelector('main');
        if (main) {
            main.insertBefore(alertDiv, main.firstChild);
            // Re-initialize feather icons for the new alert
            feather.replace();
            
            // Auto-dismiss after 5 seconds
            setTimeout(() => {
                alertDiv.remove();
            }, 5000);
        }
    }

    // Auto-dismiss flash messages after 5 seconds
    const alerts = document.querySelectorAll('.alert:not(.alert-dismissible)');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.opacity = '0';
            setTimeout(() => alert.remove(), 300);
        }, 5000);
    });

    // Initialize tooltips if needed
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Real-time search functionality for reports
    if (document.getElementById('filterForm')) {
        initializeRealTimeSearch();
    }
});

// Real-time search and filter functionality
function initializeRealTimeSearch() {
    const searchInputs = document.querySelectorAll('#filterForm input[type="text"], #filterForm input[type="number"], #filterForm select');
    const tableRows = document.querySelectorAll('.table tbody tr');
    
    // Add event listeners for real-time filtering
    searchInputs.forEach(input => {
        input.addEventListener('input', debounce(filterTableRows, 300));
        if (input.type === 'select-one') {
            input.addEventListener('change', filterTableRows);
        }
    });
    
    function filterTableRows() {
        const filters = {
            vehicleNumber: document.getElementById('vehicle_number')?.value.toLowerCase() || '',
            panchayath: document.getElementById('panchayath')?.value.toLowerCase() || '',
            weightMin: parseFloat(document.getElementById('weight_min')?.value) || 0,
            weightMax: parseFloat(document.getElementById('weight_max')?.value) || Infinity,
            wasteType: document.getElementById('waste_type')?.value || '',
            materialCategory: document.getElementById('material_category')?.value || '',
            destination: document.getElementById('destination')?.value || ''
        };
        
        let visibleCount = 0;
        
        tableRows.forEach(row => {
            const cells = row.querySelectorAll('td');
            if (cells.length === 0) return;
            
            const vehicleNumber = cells[0]?.textContent.toLowerCase() || '';
            const weight = parseFloat(cells[2]?.textContent) || 0;
            const wasteType = cells[3]?.querySelector('.badge')?.textContent.trim() || '';
            const materialCategory = cells[4]?.textContent.trim() || '';
            const destination = cells[5]?.querySelector('.badge')?.textContent.trim() || '';
            const panchayath = cells[6]?.textContent.toLowerCase() || '';
            
            const matches = (
                vehicleNumber.includes(filters.vehicleNumber) &&
                panchayath.includes(filters.panchayath) &&
                weight >= filters.weightMin &&
                weight <= filters.weightMax &&
                (filters.wasteType === '' || wasteType === filters.wasteType) &&
                (filters.materialCategory === '' || materialCategory === filters.materialCategory) &&
                (filters.destination === '' || destination === filters.destination)
            );
            
            if (matches) {
                row.style.display = '';
                visibleCount++;
            } else {
                row.style.display = 'none';
            }
        });
        
        // Update visible count
        const countElement = document.querySelector('.text-muted');
        if (countElement) {
            const totalCount = tableRows.length;
            countElement.textContent = `Showing ${visibleCount} of ${totalCount} records`;
        }
    }
    
    // Quick filter buttons
    addQuickFilterButtons();
}

function addQuickFilterButtons() {
    const filterForm = document.getElementById('filterForm');
    if (!filterForm) return;
    
    const quickFiltersDiv = document.createElement('div');
    quickFiltersDiv.className = 'row mb-3';
    quickFiltersDiv.innerHTML = `
        <div class="col-12">
            <label class="form-label">Quick Filters:</label>
            <div class="btn-group" role="group">
                <button type="button" class="btn btn-outline-primary btn-sm quick-filter" data-filter="today">Today</button>
                <button type="button" class="btn btn-outline-primary btn-sm quick-filter" data-filter="week">This Week</button>
                <button type="button" class="btn btn-outline-primary btn-sm quick-filter" data-filter="month">This Month</button>
                <button type="button" class="btn btn-outline-success btn-sm quick-filter" data-filter="recycler">Recycler Only</button>
                <button type="button" class="btn btn-outline-info btn-sm quick-filter" data-filter="heavy">Heavy Loads (>1000kg)</button>
            </div>
        </div>
    `;
    
    // Insert before the first row of form fields
    const firstRow = filterForm.querySelector('.row');
    firstRow.parentNode.insertBefore(quickFiltersDiv, firstRow);
    
    // Add event listeners for quick filters
    document.querySelectorAll('.quick-filter').forEach(button => {
        button.addEventListener('click', function() {
            const filterType = this.getAttribute('data-filter');
            applyQuickFilter(filterType);
            
            // Update button states
            document.querySelectorAll('.quick-filter').forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');
        });
    });
}

function applyQuickFilter(filterType) {
    const today = new Date();
    const dateFromInput = document.getElementById('date_from');
    const dateToInput = document.getElementById('date_to');
    const destinationSelect = document.getElementById('destination');
    const weightMinInput = document.getElementById('weight_min');
    
    // Clear existing filters
    document.getElementById('filterForm').reset();
    
    switch (filterType) {
        case 'today':
            const todayStr = today.toISOString().split('T')[0];
            dateFromInput.value = todayStr;
            dateToInput.value = todayStr;
            break;
            
        case 'week':
            const weekStart = new Date(today.setDate(today.getDate() - today.getDay()));
            const weekEnd = new Date(today.setDate(today.getDate() - today.getDay() + 6));
            dateFromInput.value = weekStart.toISOString().split('T')[0];
            dateToInput.value = weekEnd.toISOString().split('T')[0];
            break;
            
        case 'month':
            const monthStart = new Date(today.getFullYear(), today.getMonth(), 1);
            const monthEnd = new Date(today.getFullYear(), today.getMonth() + 1, 0);
            dateFromInput.value = monthStart.toISOString().split('T')[0];
            dateToInput.value = monthEnd.toISOString().split('T')[0];
            break;
            
        case 'recycler':
            destinationSelect.value = 'Recycler';
            break;
            
        case 'heavy':
            weightMinInput.value = '1000';
            break;
    }
    
    // Trigger filtering
    if (typeof filterTableRows === 'function') {
        filterTableRows();
    }
}

// Debounce function for performance
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}
