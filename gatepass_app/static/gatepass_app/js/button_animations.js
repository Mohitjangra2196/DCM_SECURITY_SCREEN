document.addEventListener('DOMContentLoaded', function() {
    const markOutForms = document.querySelectorAll('form[action*="mark_out"]');
    const markInForms = document.querySelectorAll('form[action*="mark_in"]');

    function setupButtonAnimation(forms, buttonText) {
        forms.forEach(form => {
            form.addEventListener('submit', function(event) {
                const button = form.querySelector('button[type="submit"]');
                if (button) {
                    button.classList.add('loading'); // Add loading class for opacity/pointer-events
                    button.innerHTML = `Processing... <span class="loading-spinner"></span>`; // Change text and add spinner
                    // The form submission will handle the redirect, so no need to stop spinner here.
                    // It will be reset when the new page loads.
                }
            });
        });
    }

    setupButtonAnimation(markOutForms, 'Mark Out');
    setupButtonAnimation(markInForms, 'Mark In');
});