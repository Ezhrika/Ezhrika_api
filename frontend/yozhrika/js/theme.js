(() => {
    const root = document.documentElement;
    try {
        const saved = localStorage.getItem('yozhrika-theme');
        root.dataset.theme = saved === 'light' ? 'light' : 'dark';
    } catch { root.dataset.theme = 'dark'; }

    function update() {
        const dark = root.dataset.theme !== 'light';
        const background = getComputedStyle(root).getPropertyValue('--bg').trim();
        if (background) document.querySelector('meta[name="theme-color"]')?.setAttribute('content', background);
        document.querySelectorAll('[data-theme-toggle]').forEach(button => {
            button.setAttribute('aria-label', dark ? 'Включить светлую тему' : 'Включить тёмную тему');
            const label = button.querySelector('[data-theme-label]');
            if (label) label.textContent = dark ? 'Светлая тема' : 'Тёмная тема';
        });
    }
    document.addEventListener('click', event => {
        if (!event.target.closest('[data-theme-toggle]')) return;
        root.dataset.theme = root.dataset.theme === 'dark' ? 'light' : 'dark';
        try { localStorage.setItem('yozhrika-theme', root.dataset.theme); } catch { /* Тема работает без сохранения. */ }
        update();
    });
    document.addEventListener('theme-controls-ready', update);
    document.addEventListener('DOMContentLoaded', update);
})();
