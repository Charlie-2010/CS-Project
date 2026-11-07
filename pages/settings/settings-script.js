document.addEventListener('DOMContentLoaded', () => {
    // Theme selection logic
    const themeButtons = document.querySelectorAll('.segmented-control .segment-btn');
    themeButtons.forEach(button => {
        button.addEventListener('click', () => {
            themeButtons.forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');
            showUnsavedChanges();
        });
    });

    // Color palette selection logic
    const colorDots = document.querySelectorAll('.color-palette .color-dot');
    colorDots.forEach(dot => {
        dot.addEventListener('click', () => {
            colorDots.forEach(d => d.classList.remove('active'));
            dot.classList.add('active');

            // Map colors dynamically if variable handling is needed
            const selectedColor = dot.getAttribute('data-color');
            showUnsavedChanges();
        });
    });

    // Sidebar Toggle
    const sidebar = document.getElementById('sidebar');
    const sidebarToggle = document.getElementById('sidebar-toggle');
    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', (e) => {
            e.stopPropagation();
            sidebar.classList.toggle('expanded');
        });

        document.addEventListener('click', (event) => {
            const isClickInsideSidebar = sidebar.contains(event.target);
            if (!isClickInsideSidebar && sidebar.classList.contains('expanded')) {
                sidebar.classList.remove('expanded');
            }
        });
    }

    // Dropdowns and checkbox toggle change listeners
    const controls = document.querySelectorAll('.dropdown-control, .switch input');
    controls.forEach(control => {
        control.addEventListener('change', () => {
            showUnsavedChanges();
        });
    });

    // Footer actions
    const saveBtn = document.getElementById('save-btn');
    const resetBtn = document.getElementById('reset-btn');
    const statusText = document.getElementById('status-text');
    const statusDot = document.querySelector('.status-dot');

    saveBtn.addEventListener('click', () => {
        statusText.textContent = 'All changes saved';
        statusDot.style.backgroundColor = '#10b981';
        statusDot.style.boxShadow = '0 0 8px #10b981';
    });

    resetBtn.addEventListener('click', () => {
        // Reset defaults
        document.getElementById('task-reminders').checked = true;
        document.getElementById('weekly-summary').checked = true;
        document.getElementById('achievement-alerts').checked = false;
        document.getElementById('compact-mode').checked = false;
        document.getElementById('require-password').checked = false;
        document.getElementById('biometric-login').checked = true;

        themeButtons.forEach(btn => btn.classList.remove('active'));
        themeButtons[0].classList.add('active'); // Dark

        colorDots.forEach(d => d.classList.remove('active'));
        colorDots[0].classList.add('active'); // Cyan

        statusText.textContent = 'All changes saved';
        statusDot.style.backgroundColor = '#10b981';
        statusDot.style.boxShadow = '0 0 8px #10b981';
    });

    function showUnsavedChanges() {
        statusText.textContent = 'Unsaved changes...';
        statusDot.style.backgroundColor = '#ff9800';
        statusDot.style.boxShadow = '0 0 8px #ff9800';
    }
});
