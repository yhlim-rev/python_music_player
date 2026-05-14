// ==========================================================================
// DECOUPLED DAY & NIGHT CACHE TRACKING PREFERENCE ENVIRONMENT CONTROL
// ==========================================================================
document.addEventListener("DOMContentLoaded", () => {
    const themeToggle = document.getElementById('theme-toggle');
    const savedUserTheme = localStorage.getItem('studio-theme');

    // Run system check immediately on element compile to lock layout setups
    if (savedUserTheme === 'dark' || (!savedUserTheme && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
        document.body.classList.add('dark-mode');
        themeToggle.checked = true;
    } else {
        document.body.classList.remove('dark-mode');
        themeToggle.checked = false;
    }

    // Intercept user toggle changes to dynamically rewrite local storage logs
    themeToggle.addEventListener('change', () => {
        if (themeToggle.checked) {
            document.body.classList.add('dark-mode');
            localStorage.setItem('studio-theme', 'dark');
        } else {
            document.body.classList.remove('dark-mode');
            localStorage.setItem('studio-theme', 'light');
        }
    });
});
