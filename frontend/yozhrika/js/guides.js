import { initShell, showMessage } from './ui.js';
import { dashboardPath, tutorPathFromLink } from './auth.js';

initShell().then(user => {
    if (!user) return;
    document.querySelectorAll('[data-account-link]').forEach(link => {
        link.href = dashboardPath(user.role);
        link.textContent = 'Открыть мой кабинет ↗';
    });
    document.querySelectorAll('[data-role-link]').forEach(link => {
        if (link.dataset.roleLink !== user.role) return;
        link.href = dashboardPath(user.role);
        link.textContent = 'Открыть мой кабинет ↗';
    });
}).catch(() => { /* Справочные страницы доступны и без загрузки аккаунта. */ });

const form = document.getElementById('open-tutor-form');
if (form) {
    form.addEventListener('submit', event => {
        event.preventDefault();
        const path = tutorPathFromLink(document.getElementById('tutor-page-link').value);
        const message = document.getElementById('link-message');
        if (path) { showMessage(message); location.assign(path); }
        else showMessage(message, 'Вставьте ссылку репетитора на этом сайте. Она заканчивается на /t/номер.');
    });
}

const search = document.getElementById('help-search');
if (search) {
    const entries = [...document.querySelectorAll('.faq-item')];
    const groups = [...document.querySelectorAll('.help-group')];
    const normalize = value => value.toLocaleLowerCase('ru').replaceAll('ё', 'е').replace(/\s+/g, ' ').trim();
    search.addEventListener('input', () => {
        const words = normalize(search.value).split(' ').filter(Boolean);
        let count = 0;
        entries.forEach(entry => {
            const category = entry.closest('.help-group').querySelector('h2').textContent;
            const text = normalize(`${category} ${entry.textContent} ${entry.dataset.search || ''}`);
            const matches = words.every(word => text.includes(word));
            entry.hidden = !matches;
            entry.open = words.length > 0 && matches;
            if (matches) count++;
        });
        groups.forEach(group => { group.hidden = ![...group.querySelectorAll('.faq-item')].some(entry => !entry.hidden); });
        document.getElementById('help-no-results').hidden = count > 0;
        document.getElementById('help-result-count').textContent = words.length ? `Найдено ответов: ${count}` : '';
    });
}
