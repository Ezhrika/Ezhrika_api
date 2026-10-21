import test from 'node:test';
import assert from 'node:assert/strict';
import { dateKey, weekDays, shiftDay, zonedISO, duration } from '../frontend/yozhrika/js/dates.js';

globalThis.window = new EventTarget();
globalThis.document = { body: { dataset: {} } };
globalThis.location = new URL('http://localhost:8000');
const storage = new Map();
globalThis.sessionStorage = { getItem: key => storage.get(key) ?? null, setItem: (key, value) => storage.set(key, value), removeItem: key => storage.delete(key) };
const { safeNext, tutorPathFromLink, validatePassword } = await import('../frontend/yozhrika/js/auth.js');
const { api, setToken, getToken } = await import('../frontend/yozhrika/js/api.js');
const { escapeHtml } = await import('../frontend/yozhrika/js/ui.js');
const { bookingDirectory, filterDirectory } = await import('../frontend/yozhrika/js/directory.js');
const { tutorOverviewStats } = await import('../frontend/yozhrika/js/overview.js');
const { studentWeek } = await import('../frontend/yozhrika/js/student-schedule.js');

const directoryNow = Date.parse('2026-10-22T10:30:00Z');
const directoryBooking = (id, overrides = {}) => ({ id, tutor_id: 1, tutor_name: 'Анна', subject: 'Математика', student_id: 1, student_name: 'Иван', student_email: 'ivan@example.org', status: 'active', starts_at: '2026-10-23T10:00:00Z', ends_at: '2026-10-23T11:00:00Z', created_at: '2026-10-20T10:00:00Z', ...overrides });

test('student calendar groups and sorts active records by local week and excludes cancellations', () => {
    const lesson = (id, starts_at, status = 'active') => directoryBooking(id, { starts_at, ends_at: new Date(Date.parse(starts_at) + 3600000).toISOString(), status });
    const bookings = [
        lesson(1, '2026-10-26T03:00:00Z'), lesson(2, '2026-10-25T18:00:00Z'),
        lesson(3, '2026-10-26T18:00:00Z', 'pending'), lesson(4, '2026-10-26T04:00:00Z', 'cancelled'),
        lesson(5, '2026-10-26T05:00:00Z', 'expired'), lesson(6, '2026-10-25T16:00:00Z'),
        lesson(7, '2026-11-01T16:00:00Z'), lesson(8, '2026-11-01T18:00:00Z'),
    ];
    const local = studentWeek(bookings, '2026-10-28', 'Asia/Novosibirsk');
    assert.equal(local.length, 7);
    assert.equal(local[0].date, '2026-10-26');
    assert.equal(local.at(-1).date, '2026-11-01');
    assert.deepEqual(local[0].lessons.map(item => item.id), [2, 1]);
    assert.deepEqual(local[1].lessons.map(item => item.id), [3]);
    assert.deepEqual(local[6].lessons.map(item => item.id), [7]);
    assert.equal(local.flatMap(day => day.lessons).length, 4);
    const utc = studentWeek(bookings, '2026-10-28', 'UTC');
    assert.deepEqual(utc[0].lessons.map(item => item.id), [1, 3]);
    assert.deepEqual(utc[6].lessons.map(item => item.id), [7, 8]);
    assert.equal(studentWeek([], '2026-10-28', 'UTC').every(day => day.lessons.length === 0), true);
});

test('tutor overview counts confirmed lessons in the profile timezone and calendar week', () => {
    const lesson = (id, starts_at, status = 'active', student_id = 1) => directoryBooking(id, { starts_at, ends_at: new Date(Date.parse(starts_at) + 3600000).toISOString(), status, student_id });
    const bookings = [
        lesson(1, '2026-10-26T00:00:00Z'),
        lesson(2, '2026-10-25T16:30:00Z'),
        lesson(3, '2026-11-01T17:30:00Z'),
        lesson(4, '2026-10-26T10:00:00Z', 'pending', null),
        lesson(5, '2026-10-26T11:00:00Z', 'cancelled', 2),
        lesson(6, '2026-10-25T18:00:00Z'),
        lesson(7, '2026-10-29T10:00:00Z'),
    ];
    const now = Date.parse('2026-10-25T23:30:00Z');
    const local = tutorOverviewStats(bookings, 'Asia/Novosibirsk', now);
    assert.equal(local.students, 3);
    assert.equal(local.today, 2);
    assert.equal(local.week, 3);
    assert.equal(local.weekStart, '2026-10-26');
    assert.equal(local.weekEnd, '2026-11-01');
    const utc = tutorOverviewStats(bookings, 'UTC', now);
    assert.equal(utc.today, 2);
    assert.equal(utc.week, 2);
    assert.equal(utc.weekStart, '2026-10-19');
    assert.equal(tutorOverviewStats([], 'UTC', now).students, 0);
});

test('student accounts and guest bookings remain separate even with the same email', () => {
    const entries = bookingDirectory([
        directoryBooking(1),
        directoryBooking(2, { student_id: null, student_email: 'IVAN@example.org' }),
        directoryBooking(3, { student_id: null }),
        directoryBooking(4, { student_id: 2 }),
    ], 'tutor', directoryNow);
    assert.equal(entries.length, 3);
    assert.equal(entries.find(entry => entry.guest).bookings.length, 2);
    assert.equal(entries.find(entry => entry.key === 'student:1').bookings.length, 1);
});

test('directory distinguishes upcoming, past, cancelled and expired bookings', () => {
    const entries = bookingDirectory([
        directoryBooking(1, { starts_at: '2026-10-22T10:00:00Z', ends_at: '2026-10-22T11:00:00Z' }),
        directoryBooking(2, { starts_at: '2026-10-21T10:00:00Z', ends_at: '2026-10-21T11:00:00Z' }),
        directoryBooking(3, { status: 'cancelled' }),
        directoryBooking(4, { status: 'expired' }),
        directoryBooking(5, { status: 'pending' }),
        directoryBooking(6, { ends_at: '2026-10-22T10:30:00Z', starts_at: '2026-10-22T09:30:00Z' }),
    ], 'tutor', directoryNow);
    const [entry] = entries;
    assert.deepEqual(entry.upcoming.map(item => item.id), [1, 5]);
    assert.equal(entry.next.id, 1);
    assert.equal(entry.past, 2);
    assert.equal(entry.cancelled, 1);
    assert.equal(entry.history.length, 4);
});

test('tutor grouping uses profile IDs and keeps cancelled-only contacts', () => {
    const entries = bookingDirectory([
        directoryBooking(1, { tutor_id: 2, status: 'cancelled' }),
        directoryBooking(2, { tutor_id: 1 }),
        directoryBooking(3, { tutor_id: 1 }),
    ], 'student', directoryNow);
    assert.deepEqual(entries.map(entry => entry.tutorId), [1, 2]);
    assert.equal(entries[0].bookings.length, 2);
    assert.equal(entries[1].next, null);
    assert.equal(entries[0].email, '');
    assert.equal(filterDirectory(entries, '', 'upcoming').length, 1);
});

test('directory supports combined search and account/guest filters', () => {
    const entries = bookingDirectory([
        directoryBooking(1, { student_name: 'Артём', student_id: null }),
        directoryBooking(2, { student_name: 'Артём' }),
    ], 'tutor', directoryNow);
    assert.equal(filterDirectory(entries, 'АРТЕМ example.org', 'guest').length, 1);
    assert.equal(filterDirectory(entries, '', 'account').length, 1);
    assert.equal(filterDirectory(entries, 'нет такого').length, 0);
    assert.equal(filterDirectory(bookingDirectory([directoryBooking(1)], 'student', directoryNow), 'математика').length, 1);
    assert.deepEqual(bookingDirectory([], 'tutor', directoryNow), []);
});

test('date grouping uses the selected timezone, including midnight', () => {
    assert.equal(dateKey('2026-10-22T20:00:00Z', 'Asia/Novosibirsk'), '2026-10-23');
    assert.equal(dateKey('2026-10-22T20:00:00Z', 'UTC'), '2026-10-22');
    assert.equal(shiftDay('2026-12-31', 1), '2027-01-01');
    assert.deepEqual(weekDays('2026-10-25'), ['2026-10-19', '2026-10-20', '2026-10-21', '2026-10-22', '2026-10-23', '2026-10-24', '2026-10-25']);
});

test('slot creation converts the tutor timezone to UTC', () => {
    assert.equal(zonedISO('2026-10-24', '10:00', 'Asia/Novosibirsk'), '2026-10-24T03:00:00.000Z');
    assert.equal(zonedISO('2026-10-24', '10:00', 'Europe/Moscow'), '2026-10-24T07:00:00.000Z');
    assert.equal(duration({ starts_at: '2026-10-24T03:00:00Z', ends_at: '2026-10-24T04:30:00Z' }), 90);
});

test('invalid dates and ambiguous daylight saving times are rejected', () => {
    assert.throws(() => zonedISO('2026-02-30', '10:00', 'UTC'));
    assert.throws(() => zonedISO('2026-03-29', '02:30', 'Europe/Berlin'), /отсутствует/);
    assert.throws(() => zonedISO('2026-10-25', '02:30', 'Europe/Berlin'), /повторяется/);
});

test('login return URLs cannot navigate to another site', () => {
    assert.equal(safeNext('/t/12'), '/t/12');
    assert.equal(safeNext('/tutor/dashboard'), '/tutor/dashboard');
    for (const value of ['https://example.org', '//example.org', '/\\example.org/t/12', '/api/v1/users', 'javascript:alert(1)']) assert.equal(safeNext(value), '/');
});

test('new passwords allow printable Latin keyboard characters only', () => {
    validatePassword('a'.repeat(72)); validatePassword('Abc123!@#$');
    assert.throws(() => validatePassword('a'.repeat(73)));
    assert.throws(() => validatePassword('я'.repeat(37)));
    assert.throws(() => validatePassword('short'));
    assert.throws(() => validatePassword('😀'.repeat(4)));
    assert.throws(() => validatePassword('пароль123'));
    assert.throws(() => validatePassword('Abc 12345'));
    assert.throws(() => validatePassword('Abc12345\n'));
});

test('tutor links open only a tutor page on the current site', () => {
    assert.equal(tutorPathFromLink('http://localhost:8000/t/12'), '/t/12');
    assert.equal(tutorPathFromLink(' /t/12/ '), '/t/12');
    assert.equal(tutorPathFromLink('/t/12?from=message#schedule'), '/t/12');
    for (const value of ['', '/t/0', '/t/abc', '/t/12/edit', '/login', 'https://example.org/t/12', '//example.org/t/12', 'javascript:alert(1)']) {
        assert.equal(tutorPathFromLink(value), '', value);
    }
});

test('names and comments are escaped before inserting into markup', () => {
    assert.equal(escapeHtml('<img src=x onerror="alert(1)">'), '&lt;img src=x onerror=&quot;alert(1)&quot;&gt;');
    assert.equal(escapeHtml("O'Brien & friends"), 'O&#39;Brien &amp; friends');
});

test('API sends JSON and a bearer token only for authenticated requests', async () => {
    const originalFetch = globalThis.fetch;
    setToken('test-token');
    globalThis.fetch = async (url, options) => {
        assert.equal(url, '/api/v1/slots'); assert.equal(options.headers.Authorization, 'Bearer test-token');
        assert.equal(options.body, '{"starts_at":"value"}');
        return new Response('{"id":1}', { status: 201, headers: { 'Content-Type': 'application/json' } });
    };
    try { assert.deepEqual(await api('/slots', { method: 'POST', data: { starts_at: 'value' } }), { id: 1 }); }
    finally { globalThis.fetch = originalFetch; }
});

test('an expired login is cleared and reported in Russian', async () => {
    const originalFetch = globalThis.fetch;
    setToken('expired');
    globalThis.fetch = async () => new Response('{"detail":"Could not validate credentials"}', { status: 401 });
    try { await assert.rejects(api('/users/me'), /Время входа истекло/); assert.equal(getToken(), null); }
    finally { globalThis.fetch = originalFetch; }
});

test('booking conflicts and no-content responses are handled', async () => {
    const originalFetch = globalThis.fetch;
    globalThis.fetch = async () => new Response('{"detail":"Slot is already booked or not available."}', { status: 409 });
    try {
        await assert.rejects(api('/bookings', { method: 'POST', data: { slot_id: 1 } }), /Это время уже заняли/);
        globalThis.fetch = async () => new Response(null, { status: 204 });
        assert.equal(await api('/slots/1', { method: 'DELETE' }), null);
    } finally { globalThis.fetch = originalFetch; }
});
