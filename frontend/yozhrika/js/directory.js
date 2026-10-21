import { browserZone, formatDate, formatRange } from './dates.js';
import { escapeHtml, emptyState, bookingCard } from './ui.js';

const normalize = value => String(value ?? '').toLocaleLowerCase('ru').replaceAll('ё', 'е').trim();
const byStart = (a, b) => new Date(a.starts_at) - new Date(b.starts_at);

// Контакты получаем только из собственных записей. Гостя не связываем с аккаунтом по email.
export function bookingDirectory(bookings, role, now = Date.now()) {
    const groups = new Map();
    for (const booking of bookings) {
        const guest = role === 'tutor' && booking.student_id == null;
        const key = role === 'student' ? `tutor:${booking.tutor_id}` : guest
            ? `guest:${normalize(booking.student_email) || booking.id}` : `student:${booking.student_id}`;
        if (!groups.has(key)) groups.set(key, { key, guest, bookings: [] });
        groups.get(key).bookings.push(booking);
    }
    return [...groups.values()].map(group => {
        const latest = [...group.bookings].sort((a, b) => new Date(b.created_at) - new Date(a.created_at) || b.id - a.id)[0];
        const upcoming = group.bookings.filter(item => ['active', 'pending'].includes(item.status) && new Date(item.ends_at).getTime() > now).sort(byStart);
        const history = group.bookings.filter(item => !upcoming.includes(item)).sort((a, b) => byStart(b, a));
        return {
            ...group, upcoming, history, next: upcoming[0] || null,
            name: role === 'tutor' ? latest.student_name : latest.tutor_name,
            email: role === 'tutor' ? latest.student_email : '',
            subject: role === 'student' ? latest.subject : '',
            tutorId: latest.tutor_id,
            past: history.filter(item => item.status === 'active' && new Date(item.ends_at).getTime() <= now).length,
            cancelled: group.bookings.filter(item => item.status === 'cancelled').length,
        };
    }).sort((a, b) => {
        if (a.next && b.next) return byStart(a.next, b.next) || a.name.localeCompare(b.name, 'ru');
        if (a.next || b.next) return a.next ? -1 : 1;
        return a.name.localeCompare(b.name, 'ru');
    });
}

export function filterDirectory(entries, query = '', kind = 'all') {
    const words = normalize(query).split(/\s+/).filter(Boolean);
    return entries.filter(entry => {
        if (kind === 'upcoming' && !entry.next) return false;
        if (kind === 'guest' && !entry.guest) return false;
        if (kind === 'account' && entry.guest) return false;
        const text = normalize(`${entry.name} ${entry.email} ${entry.subject}`);
        return words.every(word => text.includes(word));
    });
}

export function mountDirectory(root, { role, zone = browserZone(), onCancel }) {
    const tutor = role === 'tutor';
    let entries = [], selectedKey = null, lastTrigger = null;
    const list = root.querySelector('[data-directory-list]');
    const search = root.querySelector('[data-directory-search]');
    const filter = root.querySelector('[data-directory-filter]');
    const count = root.querySelector('[data-directory-count]');
    const detail = root.querySelector('[data-directory-detail]');
    const overview = root.querySelector('[data-directory-overview]');
    const noun = tutor ? 'учеников' : 'репетиторов';
    const formatNext = entry => entry.next
        ? `${formatDate(entry.next.starts_at, zone, { year: 'numeric' })} · ${formatRange(entry.next, zone)}` : 'Пока нет предстоящих записей';
    const metrics = entry => `<dl class="person-metrics"><div><dt>Предстоит</dt><dd>${entry.upcoming.length}</dd></div><div><dt>Прошло</dt><dd>${entry.past}</dd></div><div><dt>Отменено</dt><dd>${entry.cancelled}</dd></div></dl>`;
    const label = entry => tutor ? (entry.guest ? 'Гостевые записи' : 'Аккаунт ученика') : entry.subject;

    function renderList() {
        const shown = filterDirectory(entries, search.value, filter.value);
        count.textContent = `Показано ${noun}: ${shown.length} из ${entries.length}`;
        if (!shown.length) {
            list.innerHTML = entries.length
                ? `${emptyState('Никого не нашли', 'Попробуйте другое имя или сбросьте поиск и фильтр.')}<button class="button secondary directory-reset" type="button" data-directory-reset>Сбросить поиск и фильтр</button>`
                : emptyState(tutor ? 'Ученики появятся после первой записи' : 'Здесь будут ваши репетиторы', tutor
                    ? 'Откройте свободное время и отправьте ученикам ссылку на свою страницу.'
                    : 'Нажмите «Найти нового репетитора» или откройте ссылку преподавателя и запишитесь из своего аккаунта.');
            return;
        }
        list.innerHTML = shown.map(entry => `<article class="card person-card"><div class="person-heading"><span class="person-avatar" aria-hidden="true">${escapeHtml(entry.name.trim().split(/\s+/).slice(0, 2).map(word => [...word][0]).join(''))}</span><div><h3>${escapeHtml(entry.name)}</h3><p class="hint">${escapeHtml(label(entry))}</p></div></div>${entry.email ? `<p class="person-email">${escapeHtml(entry.email)}</p>` : ''}${metrics(entry)}<div class="person-next"><span class="hint">Ближайшая запись</span><p>${escapeHtml(formatNext(entry))}</p>${entry.next?.status === 'pending' ? '<span class="badge pending">Ждёт подтверждения</span>' : ''}</div><div class="person-actions"><button class="button secondary" type="button" data-directory-open="${escapeHtml(entry.key)}" aria-label="${escapeHtml(`Записи: ${entry.name}`)}">Смотреть записи</button>${tutor ? '' : `<a class="text-link" href="/t/${Number(entry.tutorId)}">Записаться ещё ↗</a>`}</div></article>`).join('');
    }

    function renderDetail() {
        const entry = entries.find(item => item.key === selectedKey);
        overview.hidden = !!entry; detail.hidden = !entry;
        if (!entry) { detail.replaceChildren(); return; }
        detail.innerHTML = `<button class="button quiet small" type="button" data-directory-back>← ${tutor ? 'Все ученики' : 'Все репетиторы'}</button><div class="person-detail-heading"><div><p class="eyebrow">${escapeHtml(label(entry))}</p><h3 tabindex="-1" data-directory-title>${escapeHtml(entry.name)}</h3>${entry.email ? `<p class="person-email">${escapeHtml(entry.email)}</p>` : ''}</div>${tutor ? '' : `<a class="button" href="/t/${Number(entry.tutorId)}">Записаться ещё ↗</a>`}</div>${entry.guest ? '<p class="hint">Гостевые записи объединены по email, указанному при записи. Они не привязаны к аккаунту ученика.</p>' : ''}${metrics(entry)}<p class="hint">Время: ${escapeHtml(zone)}. «Прошло» — записи, время которых закончилось; посещаемость не отмечается.</p><section class="person-bookings"><h4>Предстоящие записи</h4><div class="booking-list">${entry.upcoming.length ? entry.upcoming.map(item => bookingCard(item, role, zone)).join('') : emptyState('Предстоящих записей нет', tutor ? 'Ученик сможет выбрать время на вашей странице записи.' : 'Откройте страницу репетитора, чтобы выбрать новое время.')}</div></section><section class="person-bookings"><h4>История записей</h4><div class="booking-list">${entry.history.length ? entry.history.map(item => bookingCard(item, role, zone)).join('') : emptyState('История пока пустая', 'Здесь появятся прошедшие, отменённые и неподтверждённые записи.')}</div></section>`;
    }

    search.addEventListener('input', renderList);
    filter.addEventListener('change', renderList);
    root.addEventListener('click', event => {
        const open = event.target.closest('[data-directory-open]');
        if (open) { lastTrigger = open.dataset.directoryOpen; selectedKey = lastTrigger; renderDetail(); detail.querySelector('[data-directory-title]').focus(); }
        if (event.target.closest('[data-directory-back]')) {
            selectedKey = null; renderDetail();
            [...list.querySelectorAll('[data-directory-open]')].find(button => button.dataset.directoryOpen === lastTrigger)?.focus();
        }
        if (event.target.closest('[data-directory-reset]')) { search.value = ''; filter.value = 'all'; renderList(); search.focus(); }
        const cancel = event.target.closest('[data-cancel-booking]');
        if (cancel && !cancel.disabled) onCancel(cancel);
    });

    return {
        update(bookings, newZone = zone) {
            zone = newZone;
            const focused = detail.contains(document.activeElement) ? document.activeElement : null;
            entries = bookingDirectory(bookings, role); renderList(); renderDetail();
            if (focused) detail.querySelector('[data-directory-title]')?.focus();
        },
    };
}
