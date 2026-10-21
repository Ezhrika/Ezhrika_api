import { dateKey, formatDate, weekDays } from './dates.js';
import { escapeHtml } from './ui.js';

// Календарь показывает записи, а не подтверждённую посещаемость.
export function studentWeek(bookings, day, zone) {
    const lessons = bookings.filter(item => ['active', 'pending'].includes(item.status))
        .sort((a, b) => new Date(a.starts_at) - new Date(b.starts_at));
    return weekDays(day).map(date => ({ date, lessons: lessons.filter(item => dateKey(item.starts_at, zone) === date) }));
}

export function calendarDate(day, options = {}) {
    return formatDate(`${day}T12:00:00Z`, 'UTC', options);
}

export function studentWeekLabel(days) {
    return `${calendarDate(days[0].date)} — ${calendarDate(days.at(-1).date)}`;
}

export function renderStudentDays(days, selected, today, openTab = false) {
    return days.map(({ date, lessons }) => {
        const label = `${calendarDate(date, { weekday: 'long' })}. Записей: ${lessons.length}${date === today ? '. Сегодня' : ''}`;
        return `<button type="button" class="student-day${lessons.length ? ' has-lessons' : ''}${date === today ? ' is-today' : ''}" data-student-day="${date}" ${openTab ? 'data-open-tab="schedule"' : `aria-pressed="${date === selected}"`} ${date === today ? 'aria-current="date"' : ''} aria-label="${escapeHtml(label)}"><span>${escapeHtml(calendarDate(date, { weekday: 'short', day: undefined, month: undefined }))}</span><strong>${Number(date.slice(-2))}</strong><small>${lessons.length || '—'}${lessons.length ? '<span> зан.</span>' : ''}</small></button>`;
    }).join('');
}
