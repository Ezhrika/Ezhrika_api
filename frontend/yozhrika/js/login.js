import { signIn, safeNext, dashboardPath } from './auth.js';
import { initShell, showMessage, busy, passwordToggle } from './ui.js';

const form = document.getElementById('login-form');
const message = document.getElementById('form-message');
const next = safeNext(new URLSearchParams(location.search).get('next'), '');
document.getElementById('register-link').href = `/register${next ? `?next=${encodeURIComponent(next)}` : ''}`;
passwordToggle();
initShell().then(user => { if (user) location.replace(next || dashboardPath(user.role)); }).catch(error => showMessage(message, error.message));

form.addEventListener('submit', async event => {
    event.preventDefault();
    const button = form.querySelector('[type="submit"]');
    if (button.disabled) return;
    showMessage(message); busy(button, true, 'Входим…');
    try {
        const user = await signIn(form.email.value.trim(), form.password.value);
        location.assign(next || dashboardPath(user.role));
    } catch (error) { showMessage(message, error.message); }
    finally { busy(button, false); }
});
