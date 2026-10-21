import { api } from './api.js';
import { initShell, escapeHtml, showMessage, busy } from './ui.js';
import { formatDate, formatRange, browserZone } from './dates.js';

const $ = id => document.getElementById(id);
const action = document.body.dataset.action;
const token = new URLSearchParams(location.search).get('token') || new URLSearchParams(location.hash.slice(1)).get('token');
initShell().catch(() => {});
if (!token) {
    $('action-form').hidden = true;
    showMessage($('action-message'), 'В ссылке нет данных записи. Откройте полную ссылку из письма.');
}
$('action-form').addEventListener('submit', async event => {
    event.preventDefault(); const button = event.currentTarget.querySelector('[type="submit"]');
    if (button.disabled) return;
    showMessage($('action-message')); busy(button, true, action === 'confirm' ? 'Подтверждаем…' : 'Отменяем…');
    try {
        const booking = await api(`/bookings/${action === 'confirm' ? 'confirm-by-token' : 'cancel-by-token'}`, { method: 'POST', data: { token }, auth: false });
        $('action-form').hidden = true; $('action-description').hidden = true; $('action-result').hidden = false;
        $('action-title').textContent = action === 'confirm' ? 'Запись подтверждена' : 'Запись отменена';
        $('action-result').innerHTML = `<p>${escapeHtml(booking.tutor_name)} · ${escapeHtml(booking.subject)}</p><p>${escapeHtml(formatDate(booking.starts_at, browserZone(), { year: 'numeric' }))} · ${escapeHtml(formatRange(booking))}</p><p class="hint">Время: ${escapeHtml(browserZone())}.</p><div class="inline-actions" style="margin-top:24px"><a class="button secondary" href="/t/${Number(booking.tutor_id)}">${action === 'confirm' ? 'Страница репетитора' : 'Выбрать новое время'} ↗</a></div>`;
        showMessage($('action-message'), action === 'confirm' ? 'Выбранное время сохранено за вами. Сохраните письмо: в нём есть ссылка для отмены.' : 'Ваша запись отменена.', 'success');
        $('action-title').tabIndex = -1; $('action-title').focus();
    } catch (error) {
        showMessage($('action-message'), error.message);
        if ([400, 404, 409, 410, 422].includes(error.status)) $('action-form').hidden = true;
    } finally { busy(button, false); }
});
