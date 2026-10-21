import { dateKey, formatDate, formatRange, weekDays } from './dates.js';
import { escapeHtml, emptyState, statusBadge } from './ui.js';
import { bookingDirectory } from './directory.js';
import { renderStudentOverview } from './student-overview.js';

export function tutorOverviewStats(bookings, zone, now = Date.now()) {
    const today = dateKey(now, zone);
    const days = weekDays(today);
    const active = bookings.filter(item => item.status === 'active');
    return {
        students: bookingDirectory(bookings, 'tutor', now).length,
        today: active.filter(item => dateKey(item.starts_at, zone) === today).length,
        week: active.filter(item => { const day = dateKey(item.starts_at, zone); return day >= days[0] && day <= days[6]; }).length,
        weekStart: days[0], weekEnd: days[6],
    };
}

export function renderOverview(bookings, role, zone, slots = []) {
    if (role === 'student') return renderStudentOverview(bookings, zone);
    const tutor = role === 'tutor';
    const upcoming = bookings.filter(item => ['active', 'pending'].includes(item.status) && new Date(item.ends_at) > new Date()).sort((a, b) => new Date(a.starts_at) - new Date(b.starts_at));
    const next = upcoming[0];
    const today = dateKey(new Date(), zone);
    const sameDay = upcoming.filter(item => dateKey(item.starts_at, zone) === today);
    const name = booking => tutor ? booking.student_name : booking.tutor_name;
    const root = document.getElementById('workspace-overview');
    document.getElementById('overview-date').textContent = formatDate(new Date(), zone, { weekday: 'long', year: 'numeric' });
    const nextContent = next ? `<div class="lesson-spotlight"><div class="lesson-date"><strong>${escapeHtml(formatDate(next.starts_at, zone, { day: 'numeric', month: undefined }))}</strong><span>${escapeHtml(formatDate(next.starts_at, zone, { day: undefined, month: 'short' }))}</span></div><div><p class="eyebrow">Ближайшая запись</p><h3>${escapeHtml(name(next))}</h3><p>${escapeHtml(next.subject)} · ${escapeHtml(formatRange(next, zone))}</p><p class="hint">${escapeHtml(formatDate(next.starts_at, zone, { weekday: 'long', year: 'numeric' }))}</p></div>${statusBadge(next)}</div><button class="text-action" type="button" data-open-tab="${tutor ? 'bookings' : 'upcoming'}">Открыть записи ↗</button>`
        : `<div class="overview-welcome"><span class="orbit-mark" aria-hidden="true">◷</span><h3>${tutor ? 'Место для новых занятий' : 'Ваше следующее занятие — впереди'}</h3><p>${tutor ? 'Откройте время в расписании и отправьте ученикам свою ссылку.' : 'Выберите преподавателя, посмотрите свободные часы и запишитесь.'}</p>${tutor ? '<button class="button" type="button" data-open-tab="schedule">Открыть время ↗</button>' : '<a class="button" href="/tutors">Найти репетитора ↗</a>'}</div>`;
    const activity = upcoming.slice(0, 4).map(item => `<li><span class="agenda-time">${escapeHtml(formatRange(item, zone))}<small>${escapeHtml(formatDate(item.starts_at, zone))}</small></span><span class="agenda-person">${escapeHtml(name(item))}<small>${escapeHtml(item.subject)}</small></span>${statusBadge(item)}</li>`).join('');
    const homework = tutor ? `<section class="workspace-panel overview-homework"><div class="section-heading"><h2><svg class="heading-icon" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><use href="/assets/yozhrika_files/workspace-icons.svg#homework"></use></svg>Домашние задания</h2><span class="availability-label">Скоро</span></div><p class="hint">Здесь будут задания учеников и работы, ожидающие проверки. Раздел пока готовится.</p><button class="text-action" type="button" data-open-tab="homework">Открыть раздел →</button></section>` : '';
    root.innerHTML = `<div class="overview-grid"><div class="overview-column"><section class="workspace-panel overview-feature"><div class="section-heading"><h2>На очереди</h2><span class="hint">${escapeHtml(zone)}</span></div>${nextContent}</section><section class="workspace-panel overview-agenda"><div class="section-heading"><div><h2>Ближайшие занятия</h2><p class="hint">${sameDay.length ? `Сегодня записей: ${sameDay.length}` : 'Сегодня предстоящих записей нет'}</p></div><button class="text-action" type="button" data-open-tab="${tutor ? 'bookings' : 'upcoming'}">Все записи →</button></div>${activity ? `<ul class="agenda-list">${activity}</ul>` : emptyState('Пока тихо', 'Когда появятся новые записи, они будут здесь.')}</section>${homework}</div><aside class="overview-column"><section class="workspace-panel quick-panel"><p class="eyebrow">Под рукой</p><h2>${tutor ? 'Рабочие инструменты' : 'Для ваших занятий'}</h2>${tutor ? '<button type="button" data-open-tab="schedule"><span>Открыть свободное время</span><span aria-hidden="true">＋</span></button><button type="button" data-open-tab="students"><span>Посмотреть учеников</span><span aria-hidden="true">→</span></button><button type="button" data-open-tab="profile"><span>Ссылка для учеников</span><span aria-hidden="true">↗</span></button>' : '<a href="/tutors"><span>Найти преподавателя</span><span aria-hidden="true">↗</span></a><button type="button" data-open-tab="tutors"><span>Мои репетиторы</span><span aria-hidden="true">→</span></button><button type="button" data-open-tab="history"><span>История занятий</span><span aria-hidden="true">→</span></button>'}</section><section class="workspace-note"><span class="note-number" ${tutor ? 'id="overview-open-slots"' : ''}>${tutor ? String(slots.filter(slot => slot.status === 'open' && new Date(slot.starts_at) > new Date()).length).padStart(2, '0') : String(new Set(bookings.map(item => item.tutor_id)).size).padStart(2, '0')}</span><h2>${tutor ? 'Свободных интервалов' : 'Знакомых преподавателей'}</h2><p>${tutor ? 'На вашу страницу можно записаться по ссылке. Время ученики увидят в выбранном часовом поясе.' : 'После записи преподаватель остаётся в вашем списке. Вернуться к его расписанию можно в любой момент.'}</p><button class="text-action" type="button" data-open-tab="${tutor ? 'profile' : 'tutors'}">${tutor ? 'Моя страница записи' : 'Открыть список'} ↗</button></section></aside></div>`;
}
