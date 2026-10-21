import { api, getToken, setToken, clearToken } from './api.js';

let userPromise;

export function dashboardPath(role) { return role === 'tutor' ? '/tutor/dashboard' : '/student/dashboard'; }

export function safeNext(value, fallback = '/') {
    if (!value || !value.startsWith('/') || value.startsWith('//')) return fallback;
    try {
        const url = new URL(value, location.origin);
        return url.origin === location.origin && /^\/(?:t\/[1-9]\d*|(?:tutor|student)\/dashboard)$/.test(url.pathname) ? url.pathname : fallback;
    } catch { return fallback; }
}

export function tutorPathFromLink(value) {
    try {
        const url = new URL(value.trim(), location.origin);
        return url.origin === location.origin && /^\/t\/[1-9]\d*\/?$/.test(url.pathname) ? url.pathname.replace(/\/$/, '') : '';
    } catch { return ''; }
}

export async function currentUser() {
    if (!getToken()) return null;
    if (!userPromise) userPromise = api('/users/me').catch(error => {
        userPromise = null;
        if (error.status === 401) return null;
        throw error;
    });
    return userPromise;
}

export async function requireUser(role) {
    const user = await currentUser();
    if (!user) { location.replace(`/login?next=${encodeURIComponent(location.pathname)}`); return null; }
    if (user.role !== role) { location.replace(dashboardPath(user.role)); return null; }
    return user;
}

export async function signIn(email, password) {
    const result = await api('/auth/login', { method: 'POST', data: { email, password }, auth: false });
    setToken(result.access_token);
    userPromise = null;
    return currentUser();
}

export function signOut() { clearToken(); userPromise = null; location.assign('/login'); }

export function validatePassword(password) {
    if (!/^[!-~]{8,72}$/.test(password)) {
        throw new Error('Пароль: 8–72 символа, латинские буквы, цифры и знаки без пробелов.');
    }
}

window.addEventListener('session-expired', () => {
    userPromise = null;
    if (document.body.dataset.private) location.replace(`/login?next=${encodeURIComponent(location.pathname)}`);
});
