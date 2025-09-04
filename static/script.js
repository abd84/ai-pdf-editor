document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('pdfForm');
    const submitBtn = document.getElementById('submitBtn');
    const progressSection = document.getElementById('progressSection');
    const promptTextarea = document.getElementById('prompt');
    const exampleButtons = document.querySelectorAll('.example-btn');

    // Handle example button clicks
    exampleButtons.forEach(button => {
        button.addEventListener('click', function() {
            const example = this.getAttribute('data-example');
            promptTextarea.value = example;
            promptTextarea.focus();
        });
    });

    // Handle form submission
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const formData = new FormData(form);
        const file = formData.get('file');
        const prompt = formData.get('prompt');

        // Validate inputs
        if (!file || file.size === 0) {
            alert('Please select a PDF file.');
            return;
        }

        if (!prompt.trim()) {
            alert('Please enter a prompt describing your desired changes.');
            return;
        }

        // Check file size (50MB limit)
        const maxSize = 50 * 1024 * 1024; // 50MB in bytes
        if (file.size > maxSize) {
            alert('File size exceeds 50MB limit. Please select a smaller file.');
            return;
        }

        // Check file type
        if (!file.name.toLowerCase().endsWith('.pdf')) {
            alert('Please select a PDF file.');
            return;
        }

        // Show progress and disable submit button
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Processing...';
        progressSection.style.display = 'block';
        form.style.display = 'none';

        try {
            const response = await fetch('/api/edit-pdf', {
                method: 'POST',
                body: formData
            });

            if (response.ok) {
                // Get the filename from response headers or use default
                const contentDisposition = response.headers.get('Content-Disposition');
                let filename = 'edited_document.pdf';
                
                if (contentDisposition) {
                    const filenameMatch = contentDisposition.match(/filename=(.+)/);
                    if (filenameMatch) {
                        filename = filenameMatch[1].replace(/"/g, '');
                    }
                }

                // Create blob and download link
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = filename;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);

                // Show success message
                showAlert('success', 'PDF processed successfully! Your download should start automatically.');
                
            } else {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'An error occurred while processing the PDF.');
            }

        } catch (error) {
            console.error('Error:', error);
            showAlert('error', error.message || 'An unexpected error occurred. Please try again.');
        } finally {
            // Reset form state
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<i class="fas fa-magic me-2"></i>Process PDF';
            progressSection.style.display = 'none';
            form.style.display = 'block';
        }
    });

    // File input change handler
    document.getElementById('pdfFile').addEventListener('change', function(e) {
        const file = e.target.files[0];
        if (file) {
            // Validate file type
            if (!file.name.toLowerCase().endsWith('.pdf')) {
                alert('Please select a PDF file.');
                this.value = '';
                return;
            }

            // Validate file size
            const maxSize = 50 * 1024 * 1024; // 50MB
            if (file.size > maxSize) {
                alert('File size exceeds 50MB limit. Please select a smaller file.');
                this.value = '';
                return;
            }

            // Update form text to show selected file
            const formText = this.parentElement.querySelector('.form-text');
            formText.textContent = `Selected: ${file.name} (${formatFileSize(file.size)})`;
        }
    });

    function formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    function showAlert(type, message) {
        // Remove existing alerts
        const existingAlerts = document.querySelectorAll('.alert');
        existingAlerts.forEach(alert => alert.remove());

        // Create new alert
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type === 'success' ? 'success' : 'danger'} alert-dismissible fade show`;
        alertDiv.innerHTML = `
            <i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-triangle'} me-2"></i>
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        // Insert alert before the form
        const container = document.querySelector('.container .row .col-lg-8');
        const card = container.querySelector('.card');
        container.insertBefore(alertDiv, card);

        // Auto-dismiss success alerts after 5 seconds
        if (type === 'success') {
            setTimeout(() => {
                if (alertDiv.parentElement) {
                    alertDiv.remove();
                }
            }, 5000);
        }
    }

    // Add some nice animations
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, observerOptions);

    // Observe elements for animation
    document.querySelectorAll('.feature-box, .accordion-item').forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(20px)';
        el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        observer.observe(el);
    });
});
