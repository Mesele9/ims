// Main JavaScript for Inventory Management System

// Document ready function
$(document).ready(function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl)
    });
    
    // Initialize popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'))
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl)
    });
    
    // Auto-hide alerts after 5 seconds
    setTimeout(function() {
        $('.alert').alert('close');
    }, 5000);
    
    // Dynamic form fields for line items
    if ($('#dynamic-form-container').length) {
        // Add item row
        $('#add-item-row').on('click', function() {
            const index = $('.item-row').length;
            const newRow = $('#item-row-template').html().replace(/INDEX/g, index);
            $('#items-container').append(newRow);
            initializeItemSelect();
        });
        
        // Remove item row
        $(document).on('click', '.remove-item-row', function() {
            $(this).closest('.item-row').remove();
            updateTotals();
        });
        
        // Initialize first row if empty
        if ($('.item-row').length === 0) {
            $('#add-item-row').click();
        }
    }
    
    // Item selection change handler
    function initializeItemSelect() {
        $('.item-select').on('change', function() {
            const row = $(this).closest('.item-row');
            const itemId = $(this).val();
            
            if (itemId) {
                // Fetch item details via API
                $.ajax({
                    url: `/api/items/${itemId}/`,
                    method: 'GET',
                    success: function(data) {
                        row.find('.item-uom').text(data.unit_of_measure_name);
                        row.find('.item-price').val(data.current_price);
                        row.find('.item-balance').text(data.current_balance);
                        row.find('.item-quantity').attr('max', data.current_balance);
                        updateRowTotal(row);
                    }
                });
            } else {
                row.find('.item-uom').text('');
                row.find('.item-price').val('');
                row.find('.item-balance').text('');
                updateRowTotal(row);
            }
        });
    }
    
    // Quantity or price change handler
    $(document).on('input', '.item-quantity, .item-price', function() {
        updateRowTotal($(this).closest('.item-row'));
    });
    
    // Update row total
    function updateRowTotal(row) {
        const quantity = parseFloat(row.find('.item-quantity').val()) || 0;
        const price = parseFloat(row.find('.item-price').val()) || 0;
        const total = quantity * price;
        row.find('.item-total').val(total.toFixed(2));
        updateTotals();
    }
    
    // Update grand total
    function updateTotals() {
        let grandTotal = 0;
        $('.item-total').each(function() {
            grandTotal += parseFloat($(this).val()) || 0;
        });
        $('#grand-total').text(grandTotal.toFixed(2));
    }
    
    // Initialize DataTables if present
    if ($('.datatable').length) {
        $('.datatable').DataTable({
            responsive: true,
            language: {
                search: "_INPUT_",
                searchPlaceholder: "Search...",
            }
        });
    }
    
    // Print functionality
    $('.btn-print').on('click', function() {
        window.print();
        return false;
    });
    
    // Export to CSV
    $('.btn-export-csv').on('click', function() {
        const table = $($(this).data('table'));
        const rows = table.find('tr');
        let csv = [];
        
        rows.each(function() {
            const row = [];
            $(this).find('th, td').each(function() {
                row.push('"' + $(this).text().trim().replace(/"/g, '""') + '"');
            });
            csv.push(row.join(','));
        });
        
        const csvContent = csv.join('\n');
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.setAttribute('href', url);
        link.setAttribute('download', $(this).data('filename') || 'export.csv');
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    });
    
    // File input custom display
    $('.custom-file-input').on('change', function() {
        const fileName = $(this).val().split('\\').pop();
        $(this).siblings('.custom-file-label').addClass('selected').html(fileName);
    });
    
    // Form validation
    if ($('.needs-validation').length) {
        $('.needs-validation').each(function() {
            $(this).on('submit', function(event) {
                if (!this.checkValidity()) {
                    event.preventDefault();
                    event.stopPropagation();
                }
                $(this).addClass('was-validated');
            });
        });
    }
});
