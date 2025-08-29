// Main JavaScript file
document.addEventListener('DOMContentLoaded', function() {
    console.log('Quantica app loaded');
    
    // Smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth'
                });
            }
        });
    });
});

// Language Toggle Functionality
function toggleLanguageMenu() {
    const dropdown = document.getElementById('langDropdown');
    const arrow = document.querySelector('.dropdown-arrow');
    
    if (dropdown.classList.contains('show')) {
        dropdown.classList.remove('show');
        arrow.style.transform = 'rotate(0deg)';
    } else {
        dropdown.classList.add('show');
        arrow.style.transform = 'rotate(180deg)';
    }
}

// Close language dropdown when clicking outside
document.addEventListener('click', function(event) {
    const languageToggle = document.querySelector('.language-toggle');
    const dropdown = document.getElementById('langDropdown');
    
    if (languageToggle && !languageToggle.contains(event.target)) {
        dropdown.classList.remove('show');
        document.querySelector('.dropdown-arrow').style.transform = 'rotate(0deg)';
    }
});