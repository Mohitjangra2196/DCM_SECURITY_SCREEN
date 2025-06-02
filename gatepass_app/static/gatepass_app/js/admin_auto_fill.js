// gatepass_app/static/gatepass_app/js/admin_auto_fill.js

// Using a self-executing anonymous function to encapsulate the code
// and ensure we wait for django.jQuery to be available.
(function() {
    function initializeAutoFill() {
        if (typeof django !== 'undefined' && typeof django.jQuery !== 'undefined') {
            const $ = django.jQuery; // Explicitly assign django.jQuery to $

            $(document).ready(function() {
                const uniqueCodeInput = $('#id_unique_code');

                const firstNameInput = $('#id_first_name');
                const lastNameInput = $('#id_last_name');
                const gradeInput = $('#id_grade');
                const desigInput = $('#id_desig');

                const fetchAndFillEmployeeData = function() {
                    const empCode = uniqueCodeInput.val();
                    if (empCode) {
                        const baseUrl = window.location.origin;
                        const apiUrl = `${baseUrl}/api/get_employee_details/${empCode}/`;

                        $.ajax({
                            url: apiUrl,
                            type: 'GET',
                            dataType: 'json',
                            success: function(response) {
                                if (response.success && response.data) {
                                    firstNameInput.val(response.data.first_name || '');
                                    lastNameInput.val(response.data.last_name || '');
                                    gradeInput.val(response.data.grade || '');
                                    desigInput.val(response.data.desig || '');
                                } else {
                                    firstNameInput.val('');
                                    lastNameInput.val('');
                                    gradeInput.val('');
                                    desigInput.val('');
                                    console.warn('Employee not found or API error:', response.message);
                                }
                            },
                            error: function(xhr, status, error) {
                                firstNameInput.val('');
                                lastNameInput.val('');
                                gradeInput.val('');
                                desigInput.val('');
                                console.error('AJAX Error:', error, xhr.responseText);
                            }
                        });
                    } else {
                        firstNameInput.val('');
                        lastNameInput.val('');
                        gradeInput.val('');
                        desigInput.val('');
                    }
                };

                uniqueCodeInput.on('change', fetchAndFillEmployeeData);

                if (uniqueCodeInput.val()) {
                    fetchAndFillEmployeeData();
                }
            });
        } else {
            // If django.jQuery is not yet defined, retry after a short delay
            console.log("django.jQuery not found yet, retrying...");
            setTimeout(initializeAutoFill, 50); // Retry after 50ms
        }
    }

    // Initial call to start the initialization process
    initializeAutoFill();

})(); // No arguments passed here, as we check for django.jQuery inside.