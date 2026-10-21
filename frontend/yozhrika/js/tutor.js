import { api } from './api.js';
import { initShell, mountShell, escapeHtml, showMessage, busy, emptyState } from './ui.js';
import { browserZone, dateKey, formatDate, formatRange, formatTime, duration } from './dates.js';

const $ = id => document.getElementById(id);
const id = Number(location.pathname.match(/^\/t\/([1-9]\d*)\/?$/)?.[1]);
let tutor, user, slots = [], selectedDay = '', selectedId = null, zone = browserZone();
$('booking-login').href = `/login?next=${encodeURIComponent(location.pathname)}`;

function applyUser() {
    const guest = !user;
    $('guest-fields').hidden = !guest; $('student-name').required = guest; $('student-email').required = guest;
    $('guest-login-note').hidden = !guest;
    $('student-account-note').hidden = user?.role !== 'student';
    if (user?.role === 'student') $('student-account-note').textContent = `Запись будет добавлена в ваш кабинет. Email: ${user.email}.`;
    $('tutor-role-note').hidden = user?.role !== 'tutor'; $('booking-form').hidden = user?.role === 'tutor';
}

function renderDays() {
    const available = slots.filter(slot => new Date(slot.starts_at) > new Date());
    const days = [...new Set(available.map(slot => dateKey(slot.starts_at, zone)))].sort();
    if (!days.includes(selectedDay)) selectedDay = days[0] || '';
    $('available-days').innerHTML = days.map(day => `<button class="available-day" type="button" data-day="${day}" aria-pressed="${day === selectedDay}" aria-label="${escapeHtml(formatDate(`${day}T12:00:00Z`, 'UTC', { weekday: 'long', year: 'numeric' }))}"><span>${escapeHtml(formatDate(`${day}T12:00:00Z`, 'UTC', { weekday: 'short', day: undefined, month: undefined }))}</span><strong>${Number(day.slice(-2))}</strong><span>${escapeHtml(formatDate(`${day}T12:00:00Z`, 'UTC', { month: 'short', day: undefined }))}</span></button>`).join('');
    $('no-slots').hidden = days.length > 0;
    if (!days.length) $('no-slots').innerHTML = emptyState('Свободного времени пока нет', 'Репетитор ещё не открыл новые часы или все места уже заняты. Загляните позже.');
    renderSlots();
}

function renderSlots() {
    const daily = slots.filter(slot => new Date(slot.starts_at) > new Date() && dateKey(slot.starts_at, zone) === selectedDay);
    if (!daily.some(slot => slot.id === selectedId)) selectedId = null;
    $('available-slots').innerHTML = daily.map(slot => `<button class="available-slot" type="button" data-slot="${slot.id}" aria-pressed="${slot.id === selectedId}" aria-label="${escapeHtml(formatRange(slot, zone))}, ${duration(slot)} минут"><strong>${escapeHtml(formatTime(slot.starts_at, zone))}</strong><span>${duration(slot)} мин.</span></button>`).join('');
    const selected = daily.find(slot => slot.id === selectedId);
    $('booking-details').hidden = !selected;
    if (selected) {
        $('selection-date').textContent = formatDate(selected.starts_at, zone, { weekday: 'long', year: 'numeric' });
        $('selection-time').textContent = `${formatRange(selected, zone)} · ${duration(selected)} мин. · ${zone}`;
    }
}

async function refresh() { slots = await api(`/tutors/${id}/slots`, { auth: false }); renderDays(); }

async function load() {
    $('page-loading').hidden = false; $('retry-load').hidden = true; showMessage($('page-message'));
    try {
        if (!Number.isSafeInteger(id) || id < 1) throw new Error('Не удалось определить репетитора. Проверьте ссылку на страницу.');
        [user, tutor, slots] = await Promise.all([initShell(), api(`/tutors/${id}`, { auth: false }), api(`/tutors/${id}/slots`, { auth: false })]);
        document.title = `${tutor.name} — запись на занятие · Ёжрика`;
        $('tutor-name').textContent = tutor.name; $('tutor-subject').textContent = tutor.subject;
        $('tutor-avatar').textContent = tutor.name.trim().split(/\s+/).slice(0, 2).map(part => part[0]).join('').toUpperCase();
        $('tutor-description').textContent = tutor.description || 'Выберите свободное время и оставьте комментарий, если хотите обсудить тему занятия заранее.';
        $('tutor-timezone').textContent = tutor.timezone;
        const zones = new Set([browserZone(), tutor.timezone, 'Europe/Moscow', 'Asia/Novosibirsk', 'UTC']);
        $('display-timezone').replaceChildren(...[...zones].filter(value => {
            try { new Intl.DateTimeFormat('ru', { timeZone: value }); return true; } catch { return false; }
        }).map(value => Object.assign(document.createElement('option'), { value, textContent: `${value}${value === browserZone() ? ' — ваш часовой пояс' : ''}` })));
        $('display-timezone').value = zone;
        applyUser(); renderDays(); $('public-content').hidden = false;
    } catch (error) { showMessage($('page-message'), error.message); $('retry-load').hidden = false; }
    finally { $('page-loading').hidden = true; }
}

$('retry-load').addEventListener('click', load);
$('display-timezone').addEventListener('change', event => { zone = event.target.value; selectedDay = ''; renderDays(); });
$('available-days').addEventListener('click', event => {
    const button = event.target.closest('[data-day]'); if (!button) return;
    selectedDay = button.dataset.day; selectedId = null; renderDays();
    $('available-days').querySelector(`[data-day="${selectedDay}"]`)?.focus({ preventScroll: true });
});
$('available-slots').addEventListener('click', event => {
    const button = event.target.closest('[data-slot]'); if (!button) return;
    selectedId = Number(button.dataset.slot); showMessage($('booking-message')); renderSlots();
    $('available-slots').querySelector(`[data-slot="${selectedId}"]`)?.focus({ preventScroll: true });
});
$('refresh-slots').addEventListener('click', async event => {
    const button = event.currentTarget; busy(button, true, 'Обновляем…'); showMessage($('booking-message'));
    try { await refresh(); } catch (error) { showMessage($('booking-message'), error.message); }
    finally { busy(button, false); }
});

$('booking-form').addEventListener('submit', async event => {
    event.preventDefault(); const button = $('book-button');
    if (button.disabled) return;
    showMessage($('booking-message')); busy(button, true, 'Записываем…');
    try {
        if (!selectedId) throw new Error('Сначала выберите свободное время.');
        const data = { slot_id: selectedId, question: $('question').value.trim() };
        if (!user) {
            data.student_name = $('student-name').value.trim(); data.student_email = $('student-email').value.trim();
            if (!data.student_name) throw new Error('Укажите имя без пустых пробелов.');
        }
        const booking = await api('/bookings', { method: 'POST', data });
        $('booking-picker').hidden = true; $('booking-success').hidden = false;
        const pending = booking.status === 'pending';
        $('booking-success').innerHTML = `<div class="action-mark" aria-hidden="true">✓</div><h2>${pending ? 'Проверьте вашу почту' : 'Вы записаны на занятие'}</h2><p>${escapeHtml(formatDate(booking.starts_at, zone, { year: 'numeric' }))} · ${escapeHtml(formatRange(booking, zone))}</p><p class="hint">${pending ? `Отправили письмо на ${escapeHtml(booking.student_email)}. Подтвердите запись по ссылке до указанного в письме времени. Без подтверждения бронь будет снята.` : 'Занятие появилось в вашем кабинете. Там можно посмотреть детали и отменить запись.'}</p><div class="inline-actions">${pending ? `<a class="button secondary" href="/cancel#token=${encodeURIComponent(booking.cancel_token)}">Отменить эту запись</a>` : '<a class="button" href="/student/dashboard">Перейти к занятиям</a>'}<button id="choose-again" class="button quiet" type="button">Вернуться к расписанию</button></div>`;
        $('booking-success').focus();
        $('choose-again').addEventListener('click', async event => {
            const returnButton = event.currentTarget; busy(returnButton, true, 'Обновляем…');
            try {
                selectedId = null; await refresh(); $('question').value = '';
                $('booking-picker').hidden = false; $('booking-success').hidden = true;
            } catch (error) { showMessage($('booking-message'), error.message); }
            finally { busy(returnButton, false); }
        });
    } catch (error) {
        showMessage($('booking-message'), error.message);
        if (error.status === 409) { selectedId = null; try { await refresh(); } catch { /* Сообщение о конфликте остаётся на экране. */ } }
        if (error.status === 401) { user = null; applyUser(); mountShell(); }
    } finally { busy(button, false); }
});
load();
