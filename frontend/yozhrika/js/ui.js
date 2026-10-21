import { currentUser, dashboardPath, signOut } from './auth.js';
import { formatDate, formatRange, browserZone } from './dates.js';

export function escapeHtml(value) { return String(value ?? '').replace(/[&<>"']/g, char => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[char]); }

export function mountShell(user = null) {
    const header = document.querySelector('[data-header]');
    if (header) {
        header.innerHTML = `<div class="header-inner"><a class="brand" href="/" aria-label="Ёжрика — на главную"><img class="brand-image" src="/assets/yozhrika_files/logo.png" width="1926" height="816" alt="Ёжрика"></a>
            <button class="nav-toggle" type="button" aria-expanded="false" aria-controls="site-navigation"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 6h16M4 12h16M4 18h16"/></svg>Меню</button>
            <nav id="site-navigation" class="nav" aria-label="Основная навигация">${[['/', 'Главная'], ['/features', 'Возможности']].map(([href, label]) => `<a href="${href}" ${location.pathname === href ? 'aria-current="page"' : ''}>${label}</a>`).join('')}${user ? `<a href="${dashboardPath(user.role)}" ${location.pathname.includes('/dashboard') ? 'aria-current="page"' : ''}>Мой кабинет</a>` : ''}</nav>
            <div class="header-actions"><button class="theme-toggle" type="button" data-theme-toggle aria-label="Переключить тему"><span data-theme-label>Светлая тема</span><svg class="sun" viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="4"/><path d="M12 2v2m0 16v2M2 12h2m16 0h2M5 5l1.5 1.5m11 11L19 19M5 19l1.5-1.5m11-11L19 5"/></svg><svg class="moon" viewBox="0 0 24 24" aria-hidden="true"><path d="M20 14a8.5 8.5 0 0 1-10-10A8.5 8.5 0 1 0 20 14Z"/></svg></button><div class="header-account">${user ? `<button type="button" class="header-login" data-logout>Выйти</button><a class="header-user" href="${dashboardPath(user.role)}#profile" aria-label="${escapeHtml(`Профиль: ${user.name || 'Мой профиль'}`)}" title="${escapeHtml(user.name || 'Мой профиль')}"><span class="header-user-name">${escapeHtml(user.name || 'Мой профиль')}</span><span class="header-avatar" aria-hidden="true"></span></a>` : document.body.dataset.private ? '' : '<a class="header-login" href="/login">Войти</a><a class="header-register" href="/register">Регистрация</a>'}</div></div></div>`;
        header.querySelector('[data-logout]')?.addEventListener('click', signOut);
        header.removeAttribute('data-menu-open');
        const toggle = header.querySelector('.nav-toggle');
        toggle.addEventListener('click', () => {
            const open = toggle.getAttribute('aria-expanded') !== 'true';
            toggle.setAttribute('aria-expanded', String(open)); header.toggleAttribute('data-menu-open', open);
        });
        header.onkeydown = event => {
            if (event.key === 'Escape' && header.hasAttribute('data-menu-open')) {
                header.removeAttribute('data-menu-open'); toggle.setAttribute('aria-expanded', 'false'); toggle.focus();
            }
        };
    }
    const footer = document.querySelector('[data-footer]');
    if (footer) footer.innerHTML = `<div class="wrap footer-inner"><a href="/" class="footer-brand">Ёжрика</a><span>Время для занятий · ${new Date().getFullYear()}</span><div class="footer-links"><a href="/features">Возможности</a><a href="/help">Помощь</a></div></div>`;
    document.dispatchEvent(new Event('theme-controls-ready'));
}

export async function initShell() { mountShell(); const user = await currentUser(); mountShell(user); return user; }

export function showMessage(element, message = '', kind = 'error') {
    element.className = `message ${kind}`;
    element.textContent = message;
    element.hidden = !message;
    element.setAttribute('role', kind === 'error' ? 'alert' : 'status');
}

export function busy(button, value, label = 'Сохраняем…') {
    if (value) { button.dataset.originalText = button.textContent; button.textContent = label; }
    else if (button.dataset.originalText) button.textContent = button.dataset.originalText;
    button.disabled = value;
}

export function toast(text) {
    let container = document.querySelector('.toasts');
    if (!container) { container = document.createElement('div'); container.className = 'toasts'; container.setAttribute('role', 'status'); container.setAttribute('aria-live', 'polite'); document.body.append(container); }
    const item = document.createElement('div'); item.className = 'toast'; item.textContent = text; container.append(item);
    setTimeout(() => item.remove(), 5500);
}

export function emptyState(title, description) { return `<div class="empty"><h3>${escapeHtml(title)}</h3><p>${escapeHtml(description)}</p></div>`; }

export function setupTabs() {
    const tabs = [...document.querySelectorAll('[role="tab"]')];
    const navigation = document.querySelector('.workspace-nav');
    const compact = window.matchMedia('(max-width: 850px)');
    const scrollHint = navigation ? document.createElement('p') : null;
    if (scrollHint) {
        scrollHint.className = 'workspace-scroll-hint';
        scrollHint.hidden = true;
        scrollHint.innerHTML = '<span aria-hidden="true">↔</span> Ещё разделы — прокрутите меню';
        navigation.after(scrollHint);
    }
    function syncNavigation() {
        if (!navigation) return;
        navigation.setAttribute('aria-orientation', compact.matches ? 'horizontal' : 'vertical');
        scrollHint.hidden = !compact.matches || navigation.scrollWidth <= navigation.clientWidth + 1;
        const selected = navigation.querySelector('[aria-selected="true"]');
        if (!compact.matches || !selected || !navigation.clientWidth) return;
        const frame = navigation.getBoundingClientRect(), item = selected.getBoundingClientRect();
        if (item.left < frame.left) navigation.scrollLeft += item.left - frame.left;
        else if (item.right > frame.right) navigation.scrollLeft += item.right - frame.right;
    }
    if (navigation) {
        new ResizeObserver(syncNavigation).observe(navigation);
        compact.addEventListener('change', syncNavigation);
    }
    function activate(tab) {
        tabs.forEach(item => {
            const selected = item === tab;
            item.setAttribute('aria-selected', String(selected)); item.tabIndex = selected ? 0 : -1;
            document.getElementById(item.getAttribute('aria-controls')).hidden = !selected;
        });
        history.replaceState(null, '', `#${tab.dataset.tab}`);
        syncNavigation();
    }
    tabs.forEach((tab, index) => {
        tab.addEventListener('click', () => activate(tab));
        tab.addEventListener('keydown', event => {
            let next;
            if (event.key === 'ArrowRight' || event.key === 'ArrowDown') next = tabs[(index + 1) % tabs.length];
            if (event.key === 'ArrowLeft' || event.key === 'ArrowUp') next = tabs[(index - 1 + tabs.length) % tabs.length];
            if (event.key === 'Home') next = tabs[0];
            if (event.key === 'End') next = tabs.at(-1);
            if (next) { event.preventDefault(); activate(next); next.focus(); }
        });
    });
    const initial = tabs.find(tab => `#${tab.dataset.tab}` === location.hash) || tabs[0];
    if (initial) activate(initial);
    document.addEventListener('click', event => {
        const trigger = event.target.closest('[data-open-tab]');
        const target = trigger && tabs.find(tab => tab.dataset.tab === trigger.dataset.openTab);
        if (target) { activate(target); target.focus(); }
    });
    window.addEventListener('hashchange', () => {
        const selected = tabs.find(tab => `#${tab.dataset.tab}` === location.hash);
        if (selected) activate(selected);
    });
}

export function confirmAction(title, description, label = 'Подтвердить') {
    return new Promise(resolve => {
        const dialog = document.createElement('dialog');
        dialog.innerHTML = `<form method="dialog"><h2 id="confirm-title"></h2><p></p><div class="dialog-actions"><button class="button secondary" value="cancel" autofocus>Вернуться</button><button class="button" value="confirm"></button></div></form>`;
        dialog.querySelector('h2').textContent = title; dialog.querySelector('p').textContent = description;
        dialog.querySelector('[value="confirm"]').textContent = label;
        dialog.setAttribute('aria-labelledby', 'confirm-title'); document.body.append(dialog);
        dialog.addEventListener('close', () => { resolve(dialog.returnValue === 'confirm'); dialog.remove(); }, { once: true });
        dialog.showModal();
    });
}

export function passwordToggle() {
    document.querySelectorAll('[data-password-toggle]').forEach(button => button.addEventListener('click', () => {
        const input = document.getElementById(button.dataset.passwordToggle);
        const visible = input.type === 'password'; input.type = visible ? 'text' : 'password';
        button.textContent = visible ? 'Скрыть' : 'Показать'; button.setAttribute('aria-pressed', String(visible));
    }));
}

export function statusBadge(item) {
    let status = item.status;
    if (['active', 'booked', 'open'].includes(status) && new Date(item.ends_at) < new Date()) status = 'past';
    const labels = { active: 'Подтверждено', booked: 'Занято', open: 'Свободно', pending: 'Ждёт подтверждения', cancelled: 'Отменено', expired: 'Не подтверждено', past: 'Завершено' };
    return `<span class="badge ${escapeHtml(status)}">${escapeHtml(labels[status] || status)}</span>`;
}

export function bookingCard(booking, role, zone = browserZone()) {
    const upcoming = new Date(booking.starts_at) > new Date() && ['active', 'pending'].includes(booking.status);
    const title = role === 'tutor' ? booking.student_name : booking.tutor_name;
    return `<article class="booking-item"><div class="booking-top"><div><h3>${escapeHtml(title)}</h3><p class="hint">${escapeHtml(booking.subject)}${role === 'tutor' && !booking.student_id ? ' · Гостевая запись' : ''}</p></div>${statusBadge(booking)}</div>
        <p class="booking-time">${escapeHtml(formatDate(booking.starts_at, zone, { weekday: 'short', year: 'numeric' }))} · ${escapeHtml(formatRange(booking, zone))}</p>
        ${role === 'tutor' ? `<p class="hint">${escapeHtml(booking.student_email)}</p>` : ''}
        ${booking.question ? `<p class="booking-question">${escapeHtml(booking.question)}</p>` : ''}
        <div class="booking-bottom"><span class="hint">${escapeHtml(zone)}</span>${upcoming ? `<button class="button quiet small" type="button" data-cancel-booking="${Number(booking.id)}">Отменить занятие</button>` : ''}</div></article>`;
}
