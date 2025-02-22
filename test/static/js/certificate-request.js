class CertificateRequest {
    constructor() {
        this.form = document.getElementById('certificate-request-form');
        this.submitButton = this.form.querySelector('button[type="submit"]');
        this.setupValidation();
    }

    setupValidation() {
        this.form.addEventListener('submit', async (e) => {
            e.preventDefault();
            if (this.validateForm()) {
                const formData = new FormData(this.form);
                await this.submitRequest(formData);
            }
        });
    }

    validateForm() {
        const requiredFields = this.form.querySelectorAll('[required]');
        let isValid = true;

        requiredFields.forEach(field => {
            if (!field.value.trim()) {
                this.showError(field, 'This field is required');
                isValid = false;
            } else {
                this.clearError(field);
            }
        });

        // Validate completion date
        const completionDate = new Date(this.form.querySelector('#completion_date').value);
        if (completionDate > new Date()) {
            this.showError(this.form.querySelector('#completion_date'), 'Completion date cannot be in the future');
            isValid = false;
        }

        return isValid;
    }

    showError(field, message) {
        const errorDiv = field.parentElement.querySelector('.error-message') || 
                        document.createElement('div');
        errorDiv.className = 'error-message text-red-500 text-sm mt-1';
        errorDiv.textContent = message;
        if (!field.parentElement.querySelector('.error-message')) {
            field.parentElement.appendChild(errorDiv);
        }
    }

    clearError(field) {
        const errorDiv = field.parentElement.querySelector('.error-message');
        if (errorDiv) {
            errorDiv.remove();
        }
    }

    async submitRequest(formData) {
        this.submitButton.disabled = true;
        try {
            const response = await fetch(this.form.action, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': getCookie('csrftoken')
                }
            });

            if (!response.ok) {
                throw new Error('Request failed');
            }

            window.location.href = '/dashboard/';
        } catch (error) {
            console.error('Error:', error);
            this.showError(this.form, 'Failed to submit request. Please try again.');
        } finally {
            this.submitButton.disabled = false;
        }
    }
}