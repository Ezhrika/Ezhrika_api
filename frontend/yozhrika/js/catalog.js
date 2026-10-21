import { api } from './api.js';
import { getSubjects } from './subjects.js';
import { initShell, escapeHtml, emptyState, showMessage } from './ui.js';

const $ = id => document.getElementById(id);
const normalize = value => String(value ?? '').toLocaleLowerCase('ru').replaceAll('ё', 'е').trim();
let profiles = [], subjects = [];

initShell().catch(() => { /* Поиск по публичным профилям доступен без входа. */ });

function render() {
    const words = normalize($('catalog-search').value).split(/\s+/).filter(Boolean);
    const subject = $('catalog-subject').value;
    const shown = profiles.filter(profile => (!subject || profile.subject.trim() === subject)
        && words.every(word => normalize(`${profile.name} ${profile.subject} ${profile.description}`).includes(word)));
    if ($('catalog-order').value === 'name-desc') shown.reverse();
    const quickSubjects = subjects.filter(value => profiles.some(profile => profile.subject.trim() === value)).slice(0, 6);
    $('catalog-subjects').innerHTML = [{ value: '', label: 'Все предметы' }, ...quickSubjects.map(value => ({ value, label: value }))].map(item => `<button type="button" data-catalog-subject="${escapeHtml(item.value)}" aria-pressed="${subject === item.value}">${escapeHtml(item.label)}</button>`).join('');
    $('catalog-count').textContent = `Найдено репетиторов: ${shown.length} из ${profiles.length}`;
    if (!shown.length) {
        $('catalog-list').innerHTML = profiles.length
            ? `${emptyState('Никого не нашли', 'Попробуйте другой запрос или выберите все предметы.')}<button class="button secondary directory-reset" type="button" data-catalog-reset>Сбросить поиск и фильтр</button>`
            : emptyState('Профилей пока нет', 'Репетиторы ещё не зарегистрировались. Если у вас есть ссылка преподавателя, откройте её напрямую.');
        return;
    }
    $('catalog-list').innerHTML = shown.map(profile => `<article class="card person-card catalog-card"><div class="person-heading"><span class="person-avatar" aria-hidden="true">${escapeHtml(profile.name.trim().split(/\s+/).slice(0, 2).map(word => [...word][0]).join(''))}</span><div><h2>${escapeHtml(profile.name)}</h2><span class="catalog-subject">${escapeHtml(profile.subject)}</span></div></div><p class="catalog-description">${escapeHtml(profile.description || 'Познакомьтесь с преподавателем на его странице и выберите время для первого занятия.')}</p><div class="person-actions"><a class="button secondary" href="/t/${Number(profile.id)}" aria-label="${escapeHtml(`Профиль и расписание: ${profile.name}`)}"><span>Профиль и расписание</span><span aria-hidden="true">↗</span></a></div></article>`).join('');
}

async function load() {
    $('catalog-loading').hidden = false; $('catalog-retry').hidden = true; showMessage($('catalog-message'));
    try {
        [profiles, subjects] = await Promise.all([api('/tutors', { auth: false }), getSubjects()]);
        profiles.sort((a, b) => a.name.localeCompare(b.name, 'ru') || a.id - b.id);
        const selected = $('catalog-subject').value;
        // В фильтре остаются доступными и старые профили с нестандартным предметом.
        subjects = [...new Set([...subjects, ...profiles.map(profile => profile.subject.trim()).filter(Boolean)])].sort((a, b) => a.localeCompare(b, 'ru'));
        $('catalog-subject').replaceChildren(new Option('Все предметы', ''), ...subjects.map(subject => new Option(subject, subject)));
        if (subjects.includes(selected)) $('catalog-subject').value = selected;
        render(); $('catalog-content').hidden = false;
    } catch (error) { showMessage($('catalog-message'), error.message); $('catalog-retry').hidden = false; }
    finally { $('catalog-loading').hidden = true; }
}

$('catalog-form').addEventListener('submit', event => { event.preventDefault(); render(); });
$('catalog-search').addEventListener('input', render);
$('catalog-subject').addEventListener('change', render);
$('catalog-order').addEventListener('change', render);
$('catalog-retry').addEventListener('click', load);
document.getElementById('main').addEventListener('click', event => {
    if (event.target.closest('[data-catalog-reset]')) { $('catalog-search').value = ''; $('catalog-subject').value = ''; render(); $('catalog-search').focus(); }
    const topic = event.target.closest('[data-catalog-subject]');
    if (topic) { $('catalog-subject').value = topic.dataset.catalogSubject; render(); [...$('catalog-subjects').querySelectorAll('button')].find(button => button.dataset.catalogSubject === topic.dataset.catalogSubject)?.focus(); }
});
load();
