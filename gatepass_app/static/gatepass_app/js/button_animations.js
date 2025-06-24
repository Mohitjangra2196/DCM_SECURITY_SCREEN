document.addEventListener('DOMContentLoaded', function() {
    // Select all forms related to 'mark_out' actions
    const markOutForms = document.querySelectorAll('form[action*="mark_out"]');
    // Select all forms related to 'mark_in' actions
    const markInForms = document.querySelectorAll('form[action*="mark_in"]');
    // Select the refresh button by its ID
    const refreshPageButton = document.getElementById('refreshPageButton');

    /**
     * Sets up a submission animation for the specified forms.
     * When a form is submitted, its submit button will show a loading state.
     * @param {NodeList} forms - A NodeList of form elements.
     * @param {string} buttonText - The original text of the button (not used currently, but kept for context if needed).
     */
    function setupButtonAnimation(forms, buttonText) {
        forms.forEach(form => {
            form.addEventListener('submit', function(event) {
                const button = form.querySelector('button[type="submit"]');
                if (button) {
                    // Add 'loading' class to reduce opacity and disable pointer events (via CSS)
                    button.classList.add('loading');
                    // Change button text and add a loading spinner
                    button.innerHTML = `Processing... <span class="loading-spinner"></span>`;
                    // The page will typically redirect after form submission,
                    // so the spinner's state will be reset on the new page load.
                }
            });
        });
    }

    // Apply the submission animation to mark_out and mark_in forms
    setupButtonAnimation(markOutForms, 'Mark Out');
    setupButtonAnimation(markInForms, 'Mark In');

    // Add functionality for the Refresh button
    if (refreshPageButton) { // Check if the button exists on the page
        refreshPageButton.addEventListener('click', function() {
            // When the refresh button is clicked, reload the entire page
            location.reload();
        });
    }
});
