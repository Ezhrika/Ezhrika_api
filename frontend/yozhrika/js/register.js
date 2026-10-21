import { api } from './api.js';
import { signIn, safeNext, dashboardPath, validatePassword } from './auth.js';
import { browserZone } from './dates.js';
import { fillSubjects } from './subjects.js';
import { initShell, showMessage, busy, passwordToggle } from './ui.js';

const form = document.getElementById('register-form');
const message = document.getElementById('form-message');
const params = new URLSearchParams(location.search);
const next = safeNext(params.get('next'), '');
const initialRole = params.get('role') === 'student' || next.startsWith('/t/') ? 'student' : 'tutor';
form.querySelector(`[name="role"][value="${initialRole}"]`).checked = true;
document.getElementById('login-link').href = `/login${next ? `?next=${encodeURIComponent(next)}` : ''}`;
function updateRole() {
    const tutor = form.elements.role.value === 'tutor';
    document.getElementById('subject-field').hidden = !tutor;
    form.subject.required = tutor;
    document.getElementById('registration-role-note').textContent = tutor ? 'Кабинет репетитора: расскажите немного о себе.' : 'Кабинет ученика: как к вам обращаться?';
}
form.querySelectorAll('[name="role"]').forEach(input => input.addEventListener('change', updateRole));
updateRole(); passwordToggle();
fillSubjects(form.subject).catch(() => showMessage(message, 'Не удалось загрузить список предметов. Обновите страницу и попробуйте снова.'));
initShell().then(user => { if (user) location.replace(next || dashboardPath(user.role)); }).catch(error => showMessage(message, error.message));

let step = 1;
const titles = ['Сначала познакомимся', 'Немного о вас', 'Всё верно?'];
function showStep(value) {
    step = value; showMessage(message);
    document.querySelectorAll('[data-register-step]').forEach(panel => { panel.hidden = Number(panel.dataset.registerStep) !== step; });
    document.querySelectorAll('[data-progress]').forEach(item => {
        if (Number(item.dataset.progress) === step) item.setAttribute('aria-current', 'step');
        else item.removeAttribute('aria-current');
        item.classList.toggle('done', Number(item.dataset.progress) < step);
    });
    document.getElementById('register-title').textContent = titles[step - 1];
    document.getElementById('register-back').hidden = step === 1;
    document.getElementById('register-next').hidden = step === 3;
    form.querySelector('[type="submit"]').hidden = step !== 3;
    if (step === 2) form.elements.name.focus();
    else (step === 3 ? form.querySelector('[type="submit"]') : form.querySelector('[name="role"]:checked')).focus();
}
function validDetails() {
    for (const input of [form.elements.name, ...(form.elements.role.value === 'tutor' ? [form.subject] : []), form.email, form.password]) {
        if (!input.checkValidity()) { showStep(2); input.reportValidity(); return false; }
    }
    try {
        if (!form.elements.name.value.trim() || (form.elements.role.value === 'tutor' && !form.subject.value.trim())) throw new Error('Укажите имя и предмет без пустых пробелов.');
        validatePassword(form.password.value); return true;
    } catch (error) { showStep(2); showMessage(message, error.message); return false; }
}
function openReview() {
    if (!validDetails()) return;
    document.getElementById('review-role').textContent = form.elements.role.value === 'tutor' ? 'Репетитор' : 'Ученик';
    for (const id of ['name', 'subject', 'email']) document.getElementById(`review-${id}`).textContent = form.elements[id].value.trim();
    document.getElementById('review-subject-row').hidden = form.elements.role.value !== 'tutor';
    showStep(3);
}
function advance() {
    if (step === 1) showStep(2);
    else openReview();
}
document.querySelectorAll('[data-register-go]').forEach(button => button.addEventListener('click', () => {
    const target = Number(button.dataset.registerGo);
    if (target === 3) openReview();
    else showStep(target);
}));
function lockSteps(value) {
    document.querySelectorAll('[data-register-go], #register-back, #register-next').forEach(button => { button.disabled = value; });
}
document.getElementById('register-next').addEventListener('click', advance);
document.getElementById('register-back').addEventListener('click', () => showStep(step - 1));

form.addEventListener('submit', async event => {
    event.preventDefault();
    if (step !== 3) { advance(); return; }
    if (!validDetails()) return;
    const button = form.querySelector('[type="submit"]');
    if (button.disabled) return;
    showMessage(message); busy(button, true, 'Создаём аккаунт…'); lockSteps(true);
    let created = false;
    try {
        validatePassword(form.password.value);
        const data = { email: form.email.value.trim(), password: form.password.value, name: form.elements.name.value.trim(), role: form.elements.role.value, subject: form.subject.value.trim() };
        if (!data.name || (data.role === 'tutor' && !data.subject)) throw new Error('Укажите имя и предмет без пустых пробелов.');
        await api('/auth/register', { method: 'POST', data, auth: false });
        created = true;
        const user = await signIn(data.email, data.password);
        if (user.role === 'tutor') {
            try { await api('/tutors/me', { method: 'PATCH', data: { timezone: browserZone() } }); } catch { /* Часовой пояс можно изменить в профиле. */ }
        }
        location.assign(next || dashboardPath(user.role));
    } catch (error) {
        if (created) {
            showMessage(message, 'Аккаунт создан, но автоматический вход не удался. Перейдите по ссылке «Войти» ниже и используйте указанные данные.');
            button.hidden = true;
            document.getElementById('register-back').hidden = true;
        } else { showStep(2); showMessage(message, error.message); }
    } finally { busy(button, false); if (!created) lockSteps(false); }
});
