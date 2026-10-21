import { api } from './api.js';
import { requireUser } from './auth.js';
import { mountDirectory } from './directory.js';
import { renderOverview, tutorOverviewStats } from './overview.js';
import { fillSubjects } from './subjects.js';
import { dateKey, formatDate, formatRange, duration, shiftDay, weekDays, zonedISO, browserZone, fillTimezones } from './dates.js';
import { mountShell, escapeHtml, showMessage, busy, setupTabs, emptyState, toast, confirmAction, statusBadge, bookingCard } from './ui.js';

const $ = id => document.getElementById(id);
let profile, user, slots = [], bookings = [], zone = browserZone(), selectedDay = dateKey();
mountShell(); setupTabs(); fillTimezones($('timezone-list'));
const students = mountDirectory($('panel-students'), { role: 'tutor', zone, onCancel: cancelBooking });

function futureBooking(item) { return ['active', 'pending'].includes(item.status) && new Date(item.ends_at) > new Date(); }

function render() {
    document.querySelectorAll('[data-timezone]').forEach(element => { element.textContent = zone; });
    const summary = tutorOverviewStats(bookings, zone);
    $('stat-students').textContent = summary.students;
    $('stat-today').textContent = summary.today;
    $('stat-week').textContent = summary.week;
    $('stat-week-dates').textContent = `${formatDate(`${summary.weekStart}T12:00:00Z`, 'UTC')} — ${formatDate(`${summary.weekEnd}T12:00:00Z`, 'UTC')}`;
    $('view-date').value = selectedDay;
    $('slot-date').min = dateKey(new Date(), zone);
    $('week-days').innerHTML = weekDays(selectedDay).map(day => `<button class="week-day" type="button" data-day="${day}" aria-pressed="${day === selectedDay}" aria-label="${escapeHtml(formatDate(`${day}T12:00:00Z`, 'UTC', { weekday: 'long', year: 'numeric' }))}"><span>${escapeHtml(formatDate(`${day}T12:00:00Z`, 'UTC', { weekday: 'short', day: undefined, month: undefined }))}</span><strong>${Number(day.slice(-2))}</strong></button>`).join('');
    $('schedule-date').textContent = formatDate(`${selectedDay}T12:00:00Z`, 'UTC', { year: 'numeric' });
    const daily = slots.filter(item => item.status !== 'cancelled' && dateKey(item.starts_at, zone) === selectedDay).sort((a, b) => new Date(a.starts_at) - new Date(b.starts_at));
    $('schedule-list').innerHTML = daily.length ? daily.map(slot => {
        const booking = bookings.find(item => item.slot_id === slot.id && ['active', 'pending'].includes(item.status));
        return `<article class="schedule-item"><div><strong>${escapeHtml(formatRange(slot, zone))}</strong><p class="hint">${duration(slot)} мин.${booking ? ` · ${escapeHtml(booking.student_name)}` : ''}</p></div><div class="inline-actions">${statusBadge(slot)}${slot.status === 'open' && new Date(slot.starts_at) > new Date() ? `<button class="button quiet small" data-close-slot="${slot.id}" type="button">Закрыть</button>` : ''}</div></article>`;
    }).join('') : emptyState('На этот день времени пока нет', 'Добавьте свободные часы через форму «Добавить время».');
    renderBookings();
    students.update(bookings, zone);
    renderOverview(bookings, 'tutor', zone, slots);
}

function renderBookings() {
    const filter = $('booking-filter').value;
    const shown = bookings.filter(item => filter === 'all' || (filter === 'upcoming' ? futureBooking(item) : !futureBooking(item)));
    shown.sort((a, b) => filter === 'history' ? new Date(b.starts_at) - new Date(a.starts_at) : new Date(a.starts_at) - new Date(b.starts_at));
    $('booking-list').innerHTML = shown.length ? shown.map(item => bookingCard(item, 'tutor', zone)).join('') : emptyState('Здесь пока нет записей', filter === 'upcoming' ? 'Откройте свободные часы и поделитесь своей страницей с учениками.' : 'Завершённые и отменённые занятия появятся здесь.');
}

async function refresh() {
    [slots, bookings] = await Promise.all([api('/slots/my'), api('/bookings/tutor')]);
    render();
}

async function load() {
    $('page-loading').hidden = false; $('retry-load').hidden = true; showMessage($('page-message'));
    try {
        user = await requireUser('tutor'); if (!user) return;
        mountShell(user);
        profile = await api('/tutors/me');
        try { new Intl.DateTimeFormat('ru', { timeZone: profile.timezone }); zone = profile.timezone; } catch { zone = browserZone(); }
        selectedDay = dateKey(new Date(), zone);
        $('greeting').textContent = `Здравствуйте, ${profile.name}`;
        $('profile-name').value = profile.name;
        await fillSubjects($('profile-subject'), profile.subject);
        $('profile-description').value = profile.description; $('profile-timezone').value = profile.timezone;
        $('profile-email').value = user.email; $('slot-date').value = selectedDay;
        $('share-url').value = `${location.origin}/t/${profile.id}`; $('public-page').href = `/t/${profile.id}`;
        await refresh(); $('dashboard-content').hidden = false;
    } catch (error) { showMessage($('page-message'), error.message); $('retry-load').hidden = false; }
    finally { $('page-loading').hidden = true; }
}

$('retry-load').addEventListener('click', load);
$('week-days').addEventListener('click', event => { const button = event.target.closest('[data-day]'); if (button) { selectedDay = button.dataset.day; render(); } });
$('view-date').addEventListener('change', event => { if (event.target.value) { selectedDay = event.target.value; render(); } });
$('prev-week').addEventListener('click', () => { selectedDay = shiftDay(selectedDay, -7); render(); });
$('next-week').addEventListener('click', () => { selectedDay = shiftDay(selectedDay, 7); render(); });
$('booking-filter').addEventListener('change', renderBookings);
async function refreshFromButton(event) {
    const button = event.currentTarget; busy(button, true, 'Обновляем…');
    try { await refresh(); showMessage($('page-message')); toast('Расписание обновлено'); }
    catch (error) { showMessage($('page-message'), error.message); }
    finally { busy(button, false); }
}
$('refresh-schedule').addEventListener('click', refreshFromButton);
$('refresh-students').addEventListener('click', refreshFromButton);

$('slot-form').addEventListener('submit', async event => {
    event.preventDefault(); const form = event.currentTarget, button = form.querySelector('[type="submit"]');
    if (button.disabled) return;
    showMessage($('slot-message')); busy(button, true, 'Открываем время…');
    let saved = false;
    try {
        const starts_at = zonedISO(form.elements.date.value, form.start.value, zone);
        const ends_at = zonedISO(form.elements.date.value, form.end.value, zone);
        if (new Date(starts_at) <= new Date()) throw new Error('Начало занятия должно быть в будущем.');
        if (new Date(ends_at) <= new Date(starts_at)) throw new Error('Окончание должно быть позже начала в тот же день.');
        await api('/slots', { method: 'POST', data: { starts_at, ends_at } }); saved = true;
        selectedDay = form.elements.date.value;
        await refresh(); showMessage($('slot-message'), 'Время открыто. Теперь ученики могут на него записаться.', 'success');
    } catch (error) { showMessage($('slot-message'), saved ? 'Время сохранено, но расписание не обновилось. Нажмите «Обновить».' : error.message); }
    finally { busy(button, false); }
});

$('schedule-list').addEventListener('click', async event => {
    const button = event.target.closest('[data-close-slot]'); if (!button || button.disabled) return;
    if (!await confirmAction('Закрыть это время?', 'Оно перестанет отображаться на странице записи. История прошлых записей сохранится.', 'Закрыть время')) return;
    busy(button, true, 'Закрываем…');
    try { await api(`/slots/${Number(button.dataset.closeSlot)}`, { method: 'DELETE' }); toast('Время закрыто'); await refresh(); }
    catch (error) { showMessage($('page-message'), error.message); toast(error.message); }
    finally { busy(button, false); }
});

async function cancelBooking(button) {
    if (!button || button.disabled) return;
    if (!await confirmAction('Отменить занятие?', 'Ученик получит уведомление. Это время закроется для новых записей.', 'Отменить занятие')) return;
    busy(button, true, 'Отменяем…');
    try { await api(`/bookings/${Number(button.dataset.cancelBooking)}/cancel-by-tutor`, { method: 'POST' }); toast('Занятие отменено, время закрыто'); await refresh(); }
    catch (error) { showMessage($('page-message'), error.message); toast(error.message); }
    finally { busy(button, false); }
}
$('booking-list').addEventListener('click', event => cancelBooking(event.target.closest('[data-cancel-booking]')));

$('profile-form').addEventListener('submit', async event => {
    event.preventDefault(); const button = event.currentTarget.querySelector('[type="submit"]');
    if (button.disabled) return;
    showMessage($('profile-message')); busy(button, true);
    try {
        const data = { name: $('profile-name').value.trim(), subject: $('profile-subject').value.trim(), description: $('profile-description').value.trim(), timezone: $('profile-timezone').value.trim() };
        if (!data.name || !data.subject) throw new Error('Укажите имя и предмет без пустых пробелов.');
        try { new Intl.DateTimeFormat('ru', { timeZone: data.timezone }); } catch { throw new Error('Выберите действующий часовой пояс из списка.'); }
        profile = await api('/tutors/me', { method: 'PATCH', data }); zone = profile.timezone;
        $('greeting').textContent = `Здравствуйте, ${profile.name}`; render();
        user.name = profile.name; mountShell(user);
        showMessage($('profile-message'), 'Профиль сохранён.', 'success');
    } catch (error) { showMessage($('profile-message'), error.message); }
    finally { busy(button, false); }
});

$('copy-link').addEventListener('click', async () => {
    try { await navigator.clipboard.writeText($('share-url').value); toast('Ссылка скопирована'); }
    catch { $('share-url').focus(); $('share-url').select(); toast('Ссылка выделена. Скопируйте её через меню браузера.'); }
});
load();
