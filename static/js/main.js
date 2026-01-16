// DOM Ready
document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    const tooltips = document.querySelectorAll('[data-tooltip]');
    tooltips.forEach(element => {
        element.addEventListener('mouseenter', showTooltip);
        element.addEventListener('mouseleave', hideTooltip);
    });

    // File upload preview
    const fileInput = document.getElementById('image');
    const fileName = document.getElementById('file-name');
    
    if (fileInput && fileName) {
        fileInput.addEventListener('change', function(e) {
            if (this.files && this.files[0]) {
                fileName.textContent = this.files[0].name;
                
                // Preview image
                const reader = new FileReader();
                reader.onload = function(e) {
                    const preview = document.getElementById('image-preview');
                    if (preview) {
                        preview.innerHTML = `<img src="${e.target.result}" alt="Preview" style="max-width: 100%; border-radius: 10px; margin-top: 10px;">`;
                    }
                };
                reader.readAsDataURL(this.files[0]);
            }
        });
    }

    // Form validation
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const requiredFields = this.querySelectorAll('[required]');
            let isValid = true;
            
            requiredFields.forEach(field => {
                if (!field.value.trim()) {
                    isValid = false;
                    field.style.borderColor = '#ff416c';
                    
                    // Add error message
                    let errorMsg = field.nextElementSibling;
                    if (!errorMsg || !errorMsg.classList.contains('error-message')) {
                        errorMsg = document.createElement('div');
                        errorMsg.className = 'error-message';
                        errorMsg.style.color = '#ff416c';
                        errorMsg.style.fontSize = '0.9rem';
                        errorMsg.style.marginTop = '5px';
                        field.parentNode.appendChild(errorMsg);
                    }
                    errorMsg.textContent = 'This field is required';
                } else {
                    field.style.borderColor = '#e1e1e1';
                    const errorMsg = field.nextElementSibling;
                    if (errorMsg && errorMsg.classList.contains('error-message')) {
                        errorMsg.remove();
                    }
                }
            });
            
            if (!isValid) {
                e.preventDefault();
            }
        });
    });

    // Animated background particles
    createParticles();
});

// Tooltip functions
function showTooltip(e) {
    const tooltipText = this.getAttribute('data-tooltip');
    const tooltip = document.createElement('div');
    tooltip.className = 'tooltip';
    tooltip.textContent = tooltipText;
    tooltip.style.position = 'absolute';
    tooltip.style.background = 'rgba(0,0,0,0.8)';
    tooltip.style.color = 'white';
    tooltip.style.padding = '5px 10px';
    tooltip.style.borderRadius = '4px';
    tooltip.style.fontSize = '0.8rem';
    tooltip.style.zIndex = '1000';
    
    const rect = this.getBoundingClientRect();
    tooltip.style.top = (rect.top - 30) + 'px';
    tooltip.style.left = (rect.left + rect.width/2) + 'px';
    tooltip.style.transform = 'translateX(-50%)';
    
    document.body.appendChild(tooltip);
    this.tooltipElement = tooltip;
}

function hideTooltip() {
    if (this.tooltipElement) {
        this.tooltipElement.remove();
    }
}

// Create animated particles
function createParticles() {
    const container = document.querySelector('.animated-bg');
    if (!container) return;
    
    const colors = ['#FFACAC', '#E45A84', '#583C87'];
    
    for (let i = 0; i < 6; i++) {
        const particle = document.createElement('div');
        particle.className = 'particle';
        particle.style.background = colors[i % colors.length];
        particle.style.opacity = '0.3';
        container.appendChild(particle);
    }
}

// Upload area click handler
function triggerUpload() {
    document.getElementById('image').click();
}

// Close application
function closeApplication() {
    if (confirm('Are you sure you want to close the application?')) {
        // Clear local storage
        localStorage.clear();
        // Redirect to close page
        window.location.href = '/close';
    }
}