import { api } from './api.js';
import { requireUser, tutorPathFromLink } from './auth.js';
import { browserZone, dateKey, shiftDay } from './dates.js';
import { mountDirectory } from './directory.js';
import { renderOverview } from './overview.js';
import { studentWeek, studentWeekLabel, renderStudentDays, calendarDate } from './student-schedule.js';
import { mountShell, setupTabs, showMessage, busy, toast, emptyState, bookingCard, confirmAction } from './ui.js';

const $ = id => document.getElementById(id);
let bookings = [], user;
const zone = browserZone();
let selectedDay = dateKey(new Date(), zone);
mountShell(); setupTabs();
const tutors = mountDirectory($('panel-tutors'), { role: 'student', zone, onCancel: cancelBooking });
document.querySelectorAll('[data-timezone]').forEach(element => { element.textContent = zone; });

function upcoming(item) { return ['active', 'pending'].includes(item.status) && new Date(item.ends_at) > new Date(); }

function render() {
    const future = bookings.filter(upcoming).sort((a, b) => new Date(a.starts_at) - new Date(b.starts_at));
    const history = bookings.filter(item => !upcoming(item)).sort((a, b) => new Date(b.starts_at) - new Date(a.starts_at));
    $('stat-upcoming').textContent = future.length;
    $('stat-completed').textContent = bookings.filter(item => item.status === 'active' && new Date(item.ends_at) <= new Date()).length;
    $('stat-cancelled').textContent = bookings.filter(item => item.status === 'cancelled').length;
    $('upcoming-list').innerHTML = future.length ? future.map(item => bookingCard(item, 'student', zone)).join('') : emptyState('Пока нет предстоящих занятий', 'Нажмите «Найти репетитора» или откройте ссылку преподавателя и выберите удобное время.');
    $('history-list').innerHTML = history.length ? history.map(item => bookingCard(item, 'student', zone)).join('') : emptyState('История пока пустая', 'Здесь будут завершённые и отменённые занятия.');
    tutors.update(bookings);
    renderOverview(bookings, 'student', zone);
    renderSchedule();
}

function renderSchedule() {
    const days = studentWeek(bookings, selectedDay, zone);
    const lessons = days.find(day => day.date === selectedDay).lessons;
    $('student-view-date').value = selectedDay;
    $('student-week-label').textContent = studentWeekLabel(days);
    $('student-week-days').innerHTML = renderStudentDays(days, selectedDay, dateKey(new Date(), zone));
    $('student-schedule-date').textContent = calendarDate(selectedDay, { weekday: 'long', year: 'numeric' });
    $('student-schedule-list').innerHTML = lessons.length ? lessons.map(item => bookingCard(item, 'student', zone)).join('')
        : emptyState('День без записей', 'Выберите другой день или запишитесь на удобное время у своего преподавателя.');
}

function selectDay(day) { selectedDay = day; renderSchedule(); }
$('student-prev-week').addEventListener('click', () => selectDay(shiftDay(selectedDay, -7)));
$('student-next-week').addEventListener('click', () => selectDay(shiftDay(selectedDay, 7)));
$('student-today').addEventListener('click', () => selectDay(dateKey(new Date(), zone)));
$('student-view-date').addEventListener('change', event => {
    if (event.target.value && event.target.validity.valid) selectDay(event.target.value);
    else event.target.value = selectedDay;
});
for (const container of [$('student-week-days'), $('workspace-overview')]) {
    container.addEventListener('click', event => {
        const day = event.target.closest('[data-student-day]');
        if (day) selectDay(day.dataset.studentDay);
    });
}
$('student-schedule-list').addEventListener('click', event => cancelBooking(event.target.closest('[data-cancel-booking]')));

async function refresh() { bookings = await api('/bookings/my'); render(); }

async function load() {
    $('page-loading').hidden = false; $('retry-load').hidden = true; showMessage($('page-message'));
    try {
        user = await requireUser('student'); if (!user) return;
        mountShell(user);
        const profile = await api('/students/me');
        $('greeting').textContent = `Здравствуйте, ${profile.name}`;
        $('profile-name').value = profile.name; $('profile-email').value = user.email;
        await refresh(); $('dashboard-content').hidden = false;
    } catch (error) { showMessage($('page-message'), error.message); $('retry-load').hidden = false; }
    finally { $('page-loading').hidden = true; }
}

$('retry-load').addEventListener('click', load);
$('refresh-bookings').addEventListener('click', async event => {
    const button = event.currentTarget; busy(button, true, 'Обновляем…');
    try { await refresh(); showMessage($('page-message')); toast('Записи обновлены'); }
    catch (error) { showMessage($('page-message'), error.message); }
    finally { busy(button, false); }
});

$('tutor-link-form').addEventListener('submit', event => {
    event.preventDefault(); showMessage($('link-message'));
    const path = tutorPathFromLink($('tutor-link').value);
    if (path) location.assign(path);
    else showMessage($('link-message'), 'Вставьте ссылку на страницу репетитора в Ёжрике. Она заканчивается на /t/номер.');
});

async function cancelBooking(button) {
    if (!button || button.disabled) return;
    if (!await confirmAction('Отменить запись?', 'Репетитор увидит отмену в кабинете. Время снова станет доступно для записи.', 'Отменить запись')) return;
    busy(button, true, 'Отменяем…');
    try { await api(`/bookings/${Number(button.dataset.cancelBooking)}/cancel`, { method: 'POST' }); toast('Запись отменена'); await refresh(); }
    catch (error) { showMessage($('page-message'), error.message); toast(error.message); }
    finally { busy(button, false); }
}
$('upcoming-list').addEventListener('click', event => cancelBooking(event.target.closest('[data-cancel-booking]')));

$('profile-form').addEventListener('submit', async event => {
    event.preventDefault(); const button = event.currentTarget.querySelector('[type="submit"]');
    if (button.disabled) return;
    showMessage($('profile-message')); busy(button, true);
    try {
        const name = $('profile-name').value.trim(); if (!name) throw new Error('Укажите имя без пустых пробелов.');
        const profile = await api('/students/me', { method: 'PATCH', data: { name } });
        $('greeting').textContent = `Здравствуйте, ${profile.name}`;
        user.name = profile.name; mountShell(user);
        showMessage($('profile-message'), 'Профиль сохранён.', 'success');
    } catch (error) { showMessage($('profile-message'), error.message); }
    finally { busy(button, false); }
});
load();
