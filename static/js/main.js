const navToggle = document.querySelector("[data-nav-toggle]");
const navMenu = document.querySelector("[data-nav-menu]");

const closeMenu = () => {
    if (!navToggle || !navMenu) {
        return;
    }

    navMenu.classList.remove("is-open");
    navToggle.setAttribute("aria-expanded", "false");
    document.body.classList.remove("menu-open");
};

if (navToggle && navMenu) {
    navToggle.addEventListener("click", () => {
        const isOpen = navMenu.classList.toggle("is-open");
        navToggle.setAttribute("aria-expanded", String(isOpen));
        document.body.classList.toggle("menu-open", isOpen);
    });

    navMenu.querySelectorAll("a").forEach((link) => {
        link.addEventListener("click", closeMenu);
    });

    window.addEventListener("resize", () => {
        if (window.innerWidth > 1024) {
            closeMenu();
        }
    });
}

// Universal Collapsible Sidebar Drawer for Candidates and Companies (Tablets & Mobiles)
document.addEventListener('DOMContentLoaded', function() {
    const sidebar = document.querySelector('.candidate-sidebar');
    const header = document.querySelector('.candidate-topbar-main');
    
    if (sidebar && header) {
        // Create the hamburger toggle button
        const toggleBtn = document.createElement('button');
        toggleBtn.type = 'button';
        toggleBtn.className = 'sidebar-toggle-hamburger';
        toggleBtn.setAttribute('aria-label', 'Toggle sidebar navigation');
        toggleBtn.innerHTML = `
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <line x1="3" y1="12" x2="21" y2="12"></line>
                <line x1="3" y1="6" x2="21" y2="6"></line>
                <line x1="3" y1="18" x2="21" y2="18"></line>
            </svg>
        `;
        
        // Insert toggle at the start of header
        header.insertBefore(toggleBtn, header.firstChild);
        
        // Create the overlay element if it doesn't exist
        let overlay = document.querySelector('.sidebar-overlay');
        if (!overlay) {
            overlay = document.createElement('div');
            overlay.className = 'sidebar-overlay';
            document.body.appendChild(overlay);
        }
        
        // Click events
        toggleBtn.addEventListener('click', function() {
            document.body.classList.toggle('sidebar-open');
        });
        
        overlay.addEventListener('click', function() {
            document.body.classList.remove('sidebar-open');
        });
        
        // Close sidebar when clicking links inside it
        sidebar.querySelectorAll('a').forEach(link => {
            link.addEventListener('click', function() {
                document.body.classList.remove('sidebar-open');
            });
        });
    }
});
