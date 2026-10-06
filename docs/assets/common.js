/**
 * AMEVA Ecosystem - Unified Common Client Script (shared/common.js)
 * High-Clarity Enterprise Open-Source Standard (SSOT v3.1)
 * 
 * Features:
 * 1. Desktop Sidebar Edge Tab (< / >) Collapse Handle
 * 2. Mobile Responsive Top Header Hamburger Drawer (<= 960px)
 * 3. Collapsible Category Section Accordions
 * 4. Automatic Code Block Copy Tooltips
 * 5. Active Link Highlighting
 */

document.addEventListener('DOMContentLoaded', () => {
    const header = document.querySelector('header');
    const container = document.querySelector('.container');
    const sidebar = document.querySelector('.sidebar');

    if (!sidebar) return;

    // ── 1. Desktop Sidebar Edge Tab (< / > Toggle Handle) ─────────────────────
    let tabBtn = document.getElementById('sidebar-toggle-tab');
    if (!tabBtn) {
        tabBtn = document.createElement('div');
        tabBtn.id = 'sidebar-toggle-tab';
        tabBtn.className = 'sidebar-toggle-tab';
        tabBtn.setAttribute('title', '사이드바 접기/펼치기 (Toggle Sidebar)');
        tabBtn.setAttribute('aria-label', 'Toggle Sidebar');
        tabBtn.innerHTML = '‹';
        sidebar.appendChild(tabBtn);
    }

    function updateDesktopSidebar(collapsed) {
        if (collapsed) {
            sidebar.classList.add('desktop-collapsed');
            if (container) container.classList.add('sidebar-collapsed');
            tabBtn.classList.add('collapsed-tab');
            tabBtn.innerHTML = '›';
            document.body.appendChild(tabBtn); // Move to body for fixed left positioning
        } else {
            sidebar.classList.remove('desktop-collapsed');
            if (container) container.classList.remove('sidebar-collapsed');
            tabBtn.classList.remove('collapsed-tab');
            tabBtn.innerHTML = '‹';
            sidebar.appendChild(tabBtn); // Restore inside sidebar
        }
    }

    // Restore saved state
    const isSavedCollapsed = localStorage.getItem('ameva_desktop_sidebar_collapsed') === 'true';
    if (window.innerWidth > 960 && isSavedCollapsed) {
        updateDesktopSidebar(true);
    }

    tabBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        const willCollapse = !sidebar.classList.contains('desktop-collapsed');
        updateDesktopSidebar(willCollapse);
        localStorage.setItem('ameva_desktop_sidebar_collapsed', willCollapse ? 'true' : 'false');
    });

    // ── 2. Mobile Header Hamburger Button (Active <= 960px) ───────────────────
    if (header) {
        let toggleBtn = header.querySelector('.menu-toggle-btn');
        if (!toggleBtn) {
            toggleBtn = document.createElement('button');
            toggleBtn.className = 'menu-toggle-btn';
            toggleBtn.setAttribute('aria-label', 'Toggle Navigation Menu');
            toggleBtn.innerHTML = `
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round">
                    <line x1="3" y1="6" x2="21" y2="6"></line>
                    <line x1="3" y1="12" x2="21" y2="12"></line>
                    <line x1="3" y1="18" x2="21" y2="18"></line>
                </svg>
                <span class="menu-toggle-label">Menu</span>
            `;
            
            const controls = header.querySelector('.header-controls');
            if (controls) {
                controls.insertBefore(toggleBtn, controls.firstChild);
            } else {
                header.appendChild(toggleBtn);
            }
        }

        toggleBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            const isOpen = sidebar.classList.toggle('mobile-open');
            toggleBtn.classList.toggle('active', isOpen);
            toggleBtn.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
        });

        // Close mobile drawer on link click
        sidebar.querySelectorAll('a').forEach(link => {
            link.addEventListener('click', () => {
                if (window.innerWidth <= 960) {
                    sidebar.classList.remove('mobile-open');
                    toggleBtn.classList.remove('active');
                }
            });
        });
    }

    // ── 3. Collapsible Sidebar Section Accordions ─────────────────────────────
    const headers = sidebar.querySelectorAll('h3');
    headers.forEach(h3 => {
        const ul = h3.nextElementSibling;
        if (!ul || ul.tagName !== 'UL') return;

        h3.classList.add('collapsible-header');

        if (!h3.querySelector('.accordion-icon')) {
            const icon = document.createElement('span');
            icon.className = 'accordion-icon';
            icon.textContent = '▾';
            h3.appendChild(icon);
        }

        h3.addEventListener('click', () => {
            const isCollapsed = ul.classList.toggle('collapsed');
            h3.classList.toggle('collapsed', isCollapsed);
            const icon = h3.querySelector('.accordion-icon');
            if (icon) {
                icon.textContent = isCollapsed ? '▸' : '▾';
            }
        });
    });

    // ── 4. Setup Copy Buttons on all <pre><code> blocks ───────────────────────
    document.querySelectorAll('pre').forEach((pre) => {
        if (pre.querySelector('.copy-code-btn')) return;

        const btn = document.createElement('button');
        btn.className = 'copy-code-btn';
        btn.setAttribute('aria-label', 'Copy code');
        btn.textContent = 'Copy';

        btn.addEventListener('click', async () => {
            const codeBlock = pre.querySelector('code') || pre;
            const textToCopy = codeBlock.innerText.trim();
            try {
                await navigator.clipboard.writeText(textToCopy);
                btn.textContent = 'Copied!';
                btn.style.backgroundColor = '#16a34a';
                btn.style.color = '#ffffff';

                setTimeout(() => {
                    btn.textContent = 'Copy';
                    btn.style.backgroundColor = '';
                    btn.style.color = '';
                }, 2000);
            } catch (err) {
                console.error('Failed to copy: ', err);
            }
        });

        pre.appendChild(btn);
    });

    // ── 5. Auto-highlight Active Link in Sidebar ───────────────────────────────
    const currentPath = window.location.pathname;
    document.querySelectorAll('.sidebar a').forEach(link => {
        const href = link.getAttribute('href');
        if (!href) return;
        
        if (href === currentPath || currentPath.endsWith(href) || (href === './' && currentPath.endsWith('/'))) {
            link.classList.add('active');
            const parentUl = link.closest('ul');
            if (parentUl) {
                parentUl.classList.remove('collapsed');
                const prevH3 = parentUl.previousElementSibling;
                if (prevH3 && prevH3.tagName === 'H3') {
                    prevH3.classList.remove('collapsed');
                    const icon = prevH3.querySelector('.accordion-icon');
                    if (icon) icon.textContent = '▾';
                }
            }
        }
    });
});
