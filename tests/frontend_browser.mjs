import { spawn } from 'node:child_process';
import { mkdtemp, readFile, mkdir, writeFile, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join, resolve, basename, sep } from 'node:path';
import { setTimeout as delay } from 'node:timers/promises';
import assert from 'node:assert/strict';

// Запускается с отдельным tests/frontend_preview.py, не с рабочей БД.
const base = 'http://127.0.0.1:8765';
const profile = await mkdtemp(join(tmpdir(), 'ezhrika-browser-'));
const artifacts = resolve('tests/artifacts');
await mkdir(artifacts, { recursive: true });
const chrome = spawn(process.env.CHROME_PATH || 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe', [
    '--headless=new', '--disable-gpu', '--no-first-run', '--no-default-browser-check',
    '--disable-background-networking', '--remote-debugging-port=0', `--user-data-dir=${profile}`,
    'about:blank',
], { windowsHide: true, stdio: 'ignore' });
let launchError;
chrome.on('error', error => { launchError = error; });
let socket;

try {
    let port;
    for (let i = 0; i < 150; i++) {
        if (launchError) throw launchError;
        try { port = Number((await readFile(join(profile, 'DevToolsActivePort'), 'utf8')).split('\n')[0]); break; } catch { await delay(100); }
    }
    if (!port) throw new Error('Headless Chrome did not start.');
    const version = await (await fetch(`http://127.0.0.1:${port}/json/version`)).json();
    socket = new WebSocket(version.webSocketDebuggerUrl);
    await new Promise((resolve, reject) => { socket.addEventListener('open', resolve, { once: true }); socket.addEventListener('error', reject, { once: true }); });
    let sequence = 0;
    const pending = new Map();
    const errors = [];
    socket.addEventListener('message', event => {
        const value = JSON.parse(event.data);
        if (value.id && pending.has(value.id)) {
            const item = pending.get(value.id); pending.delete(value.id); clearTimeout(item.timeout);
            value.error ? item.reject(new Error(JSON.stringify(value.error))) : item.resolve(value.result);
        }
        if (value.method === 'Runtime.exceptionThrown') errors.push(value.params.exceptionDetails.exception?.description || value.params.exceptionDetails.text);
    });
    function call(method, params = {}, sessionId) {
        return new Promise((resolve, reject) => {
            const id = ++sequence;
            const timeout = setTimeout(() => { pending.delete(id); reject(new Error(`CDP timeout: ${method}`)); }, 15000);
            pending.set(id, { resolve, reject, timeout });
            socket.send(JSON.stringify({ id, method, params, ...(sessionId ? { sessionId } : {}) }));
        });
    }
    const { targetId } = await call('Target.createTarget', { url: 'about:blank' });
    const { sessionId } = await call('Target.attachToTarget', { targetId, flatten: true });
    const page = (method, params) => call(method, params, sessionId);
    await page('Page.enable'); await page('Runtime.enable');
    await page('Emulation.setTimezoneOverride', { timezoneId: 'Asia/Novosibirsk' });
    async function evaluate(expression) {
        const result = await page('Runtime.evaluate', { expression, awaitPromise: true, returnByValue: true, userGesture: true });
        if (result.exceptionDetails) throw new Error(result.exceptionDetails.exception?.description || result.exceptionDetails.text);
        return result.result.value;
    }
    async function waitFor(expression, label = expression) {
        for (let i = 0; i < 150; i++) { if (await evaluate(expression)) return; await delay(100); }
        throw new Error(`Timed out: ${label}\n${await evaluate('document.body.innerText')}`);
    }
    async function go(path) {
        await page('Page.navigate', { url: `${base}${path}` });
        await waitFor(`location.pathname === ${JSON.stringify(path.split('?')[0].split('#')[0])} && document.readyState === 'complete'`, `navigation ${path}`);
    }
    async function fill(id, value) { await evaluate(`document.getElementById(${JSON.stringify(id)}).value = ${JSON.stringify(value)}`); }
    async function click(selector) { await evaluate(`document.querySelector(${JSON.stringify(selector)}).click()`); }
    async function submit(id) { await evaluate(`document.getElementById(${JSON.stringify(id)}).requestSubmit()`); }
    async function searchDirectory(id, value) {
        await fill(id, value);
        await evaluate(`document.getElementById(${JSON.stringify(id)}).dispatchEvent(new Event('input', { bubbles: true }))`);
    }
    async function filterDirectory(id, value) {
        await fill(id, value);
        await evaluate(`document.getElementById(${JSON.stringify(id)}).dispatchEvent(new Event('change', { bubbles: true }))`);
    }
    async function login(email, path) {
        await go('/login'); await fill('email', email); await fill('password', 'frontend-test-only'); await submit('login-form');
        await waitFor(`location.pathname === ${JSON.stringify(path)} && !!document.getElementById('dashboard-content') && !document.getElementById('dashboard-content').hidden`);
    }
    let viewportWidth;
    async function viewport(width, height = 900) { viewportWidth = width; await page('Emulation.setDeviceMetricsOverride', { width, height, deviceScaleFactor: 1, mobile: width < 600 }); }
    async function shot(name) {
        await evaluate("window.scrollTo({ top: 0, left: 0, behavior: 'instant' })");
        await delay(120);
        const fits = await evaluate(`Math.max(document.documentElement.scrollWidth, document.body.scrollWidth) <= ${viewportWidth}`);
        if (!fits) console.log('Overflow elements:', await evaluate(`[...document.querySelectorAll('body *')].filter(element => { const rect = element.getBoundingClientRect(); return rect.width > 0 && (rect.right > ${viewportWidth} + 1 || rect.left < -1); }).slice(0, 15).map(element => ({ tag: element.tagName, class: element.className, text: element.innerText?.slice(0, 70), width: element.getBoundingClientRect().width }))`));
        assert.equal(fits, true, `Horizontal overflow: ${name}`);
        const metrics = await page('Page.getLayoutMetrics');
        const screenshot = await page('Page.captureScreenshot', { format: 'png', captureBeyondViewport: true, clip: { x: 0, y: 0, width: metrics.cssContentSize.width, height: metrics.cssContentSize.height, scale: 1 } });
        await writeFile(join(artifacts, name + '.png'), Buffer.from(screenshot.data, 'base64'));
    }
    await viewport(1440);
    await go('/'); await waitFor("!!document.querySelector('[data-theme-toggle]')");
    assert.equal(await evaluate("document.querySelector('.header-account a:last-child').textContent"), 'Регистрация');
    await shot('home-dark'); await click('[data-theme-toggle]'); await shot('home-light');
    await viewport(390, 844); await shot('home-mobile');
    await viewport(320, 844); await shot('home-small');
    await viewport(1440); await click('[data-theme-toggle]');

    const menuPaths = ['/', '/features'];
    assert.deepEqual(await evaluate("[...document.querySelectorAll('.nav a')].map(link => link.getAttribute('href'))"), menuPaths);
    for (const path of ['/features', '/tutors', '/for-tutors', '/for-students', '/help']) {
        await go(path); await waitFor("!!document.querySelector('.nav')");
        if (menuPaths.includes(path)) assert.equal(await evaluate("document.querySelector('.nav a[aria-current=page]').getAttribute('href')"), path);
        await shot(path.slice(1) + '-desktop');
        if (path === '/features') {
            await click('[data-theme-toggle]'); await shot('features-light');
            await viewport(320, 844); await shot('features-light-small');
            await viewport(1440); await click('[data-theme-toggle]');
        }
        await viewport(390, 844); await shot(path.slice(1) + '-mobile');
        assert.equal(await evaluate("getComputedStyle(document.querySelector('.nav')).display"), 'none');
        await click('.nav-toggle');
        assert.equal(await evaluate("document.querySelector('.nav-toggle').getAttribute('aria-expanded')"), 'true');
        await shot(path.slice(1) + '-menu');
        await evaluate("document.querySelector('.nav-toggle').dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true }))");
        assert.equal(await evaluate("document.querySelector('.nav-toggle').getAttribute('aria-expanded')"), 'false');
        await viewport(320, 844); await shot(path.slice(1) + '-small');
        await viewport(1101); await shot(path.slice(1) + '-tablet');
        await viewport(1440);
    }
    await fill('help-search', 'часовой пояс');
    await evaluate("document.getElementById('help-search').dispatchEvent(new Event('input', { bubbles: true }))");
    assert.ok(await evaluate("document.querySelectorAll('.faq-item:not([hidden])').length > 0"));
    assert.equal(await evaluate("document.querySelector('.faq-item:not([hidden])').open"), true);
    assert.equal(await evaluate("document.querySelector('#account .faq-item').hidden"), false);
    await fill('help-search', 'отмена');
    await evaluate("document.getElementById('help-search').dispatchEvent(new Event('input', { bubbles: true }))");
    assert.equal(await evaluate("document.querySelectorAll('#cancellation .faq-item:not([hidden])').length"), 3);
    await fill('help-search', 'несуществующийвопрос');
    await evaluate("document.getElementById('help-search').dispatchEvent(new Event('input', { bubbles: true }))");
    assert.equal(await evaluate("document.getElementById('help-no-results').hidden"), false);
    await fill('help-search', '');
    await evaluate("document.getElementById('help-search').dispatchEvent(new Event('input', { bubbles: true }))");
    assert.equal(await evaluate("document.querySelectorAll('.faq-item[hidden]').length"), 0);
    await go('/for-students'); await waitFor("!!document.querySelector('.nav')");
    await fill('tutor-page-link', 'https://example.org/t/1'); await submit('open-tutor-form');
    assert.equal(await evaluate("document.getElementById('link-message').hidden"), false);
    assert.equal(await evaluate('location.pathname'), '/for-students');
    await fill('tutor-page-link', base + '/t/1'); await submit('open-tutor-form');
    await waitFor("location.pathname === '/t/1' && !!document.getElementById('public-content') && !document.getElementById('public-content').hidden");

    await go('/tutors'); await waitFor("!document.getElementById('catalog-content').hidden");
    await searchDirectory('catalog-search', 'Анна Смирнова');
    assert.equal(await evaluate("document.querySelectorAll('#catalog-list .person-card').length"), 1);
    await searchDirectory('catalog-search', 'нет такого имени');
    assert.match(await evaluate("document.getElementById('catalog-list').innerText"), /Никого не нашли/);
    await click('[data-catalog-reset]');
    await filterDirectory('catalog-subject', 'Математика');
    assert.ok(await evaluate("document.querySelectorAll('#catalog-list .person-card').length > 0"));
    assert.equal(await evaluate("document.querySelector('[data-catalog-subject=\"Математика\"]').getAttribute('aria-pressed')"), 'true');
    await click('[data-catalog-subject=""]');
    assert.equal(await evaluate("document.getElementById('catalog-subject').value"), '');
    await filterDirectory('catalog-order', 'name-desc');
    await filterDirectory('catalog-order', 'name');
    await searchDirectory('catalog-search', 'Анна Смирнова'); await click('#catalog-list a');
    await waitFor("location.pathname === '/t/1' && !!document.getElementById('public-content') && !document.getElementById('public-content').hidden");

    await go('/t/1'); await waitFor("!document.getElementById('public-content').hidden");
    await click('[data-slot]'); await shot('booking-desktop');
    await viewport(390, 844); await shot('booking-mobile');

    const suffix = Date.now();
    await viewport(1440); await go('/register?role=tutor');
    await waitFor("!!document.getElementById('register-next')");
    await shot('register-role'); await viewport(390, 844); await shot('register-role-mobile');
    await viewport(320, 844); await shot('register-role-small'); await viewport(1440);
    await click('#register-next'); await click('#register-next');
    assert.equal(await evaluate("document.querySelector('[data-register-step=\"2\"]').hidden"), false, 'Empty details cannot advance.');
    await waitFor("!document.getElementById('subject').disabled && [...document.getElementById('subject').options].some(option => option.value === 'Математика')");
    await fill('name', 'Тестовый преподаватель'); await fill('subject', 'Математика');
    await fill('email', `tutor-${suffix}@example.org`); await fill('password', 'frontend-test-only');
    await fill('password', 'пароль123'); await click('#register-next');
    assert.equal(await evaluate("document.querySelector('[data-register-step=\"2\"]').hidden"), false);
    assert.match(await evaluate("document.getElementById('form-message').textContent"), /латинские/);
    await fill('password', 'frontend-test-only');
    await shot('register-details');
    await viewport(320, 844); await shot('register-details-small'); await viewport(1440);
    await click('[data-theme-toggle]'); await shot('register-error-light'); await click('[data-theme-toggle]');
    await click('[data-register-go="3"]');
    assert.equal(await evaluate("document.getElementById('review-email').textContent"), `tutor-${suffix}@example.org`);
    await shot('register-review'); await viewport(320, 844); await shot('register-review-small'); await viewport(1440);
    await click('[data-register-go="1"]');
    assert.equal(await evaluate("document.querySelector('[data-register-step=\"1\"]').hidden"), false);
    await click('[data-register-go="2"]'); assert.equal(await evaluate("document.getElementById('password').value"), 'frontend-test-only'); await click('[data-register-go="3"]');
    await submit('register-form');
    await waitFor("location.pathname === '/tutor/dashboard' && document.getElementById('dashboard-content') && !document.getElementById('dashboard-content').hidden");
    assert.equal(await evaluate("document.querySelector('.header-user-name').textContent"), 'Тестовый преподаватель');
    assert.equal(await evaluate("document.querySelector('[data-logout]').nextElementSibling.className"), 'header-user');
    assert.equal(await evaluate("document.querySelector('.header-avatar').childElementCount"), 0);
    assert.equal(await evaluate("document.getElementById('tab-profile').closest('.workspace-settings').getAttribute('aria-label')"), 'Настройки');
    assert.equal(await evaluate("document.getElementById('tab-overview').getAttribute('aria-selected')"), 'true');
    assert.equal(await evaluate("document.getElementById('stat-payments').textContent"), '—');
    assert.equal(await evaluate("document.querySelectorAll('.tutor-stats .stat').length"), 4);
    await shot('tutor-overview'); await viewport(390, 844); await shot('tutor-overview-mobile'); await viewport(320, 844); await shot('tutor-overview-small'); await viewport(1440);
    await viewport(1101); await shot('tutor-overview-tablet'); await viewport(1440);
    await click('[data-theme-toggle]'); await shot('tutor-overview-light'); await click('[data-theme-toggle]');
    await click('#workspace-overview [data-open-tab="homework"]');
    assert.equal(await evaluate("location.hash"), '#homework');
    assert.equal(await evaluate("document.getElementById('panel-homework').hidden"), false);
    assert.equal(await evaluate("document.getElementById('panel-overview').hidden"), true);
    assert.match(await evaluate("document.getElementById('panel-homework').innerText"), /пока недоступны/);
    await shot('tutor-homework');
    await click('[data-theme-toggle]'); await shot('tutor-homework-light'); await click('[data-theme-toggle]');
    await viewport(320, 844); await shot('tutor-homework-small'); await viewport(1440);
    await click('#tab-payments');
    assert.equal(await evaluate("location.hash"), '#payments');
    assert.equal(await evaluate("document.getElementById('panel-payments').hidden"), false);
    await shot('tutor-payments');
    await click('[data-theme-toggle]'); await shot('tutor-payments-light');
    await viewport(320, 844); await shot('tutor-payments-light-small'); await click('[data-theme-toggle]');
    await viewport(320, 844); await shot('tutor-payments-small');
    assert.equal(await evaluate("document.querySelector('.workspace-nav').getAttribute('aria-orientation')"), 'horizontal');
    assert.equal(await evaluate("document.querySelector('.workspace-nav').getBoundingClientRect().height < 70"), true);
    await evaluate("document.getElementById('tab-payments').dispatchEvent(new KeyboardEvent('keydown', { key: 'End', bubbles: true }))");
    assert.equal(await evaluate("location.hash"), '#profile');
    await waitFor("(() => { const nav = document.querySelector('.workspace-nav').getBoundingClientRect(), tab = document.getElementById('tab-profile').getBoundingClientRect(); return tab.left >= nav.left - 1 && tab.right <= nav.right + 1; })()");
    await go('/tutor/dashboard#reports');
    await waitFor("!document.getElementById('dashboard-content').hidden");
    assert.equal(await evaluate("document.getElementById('tab-reports').getAttribute('aria-selected')"), 'true');
    assert.equal(await evaluate("document.getElementById('panel-reports').hidden"), false);
    await waitFor("document.querySelector('.workspace-nav').scrollLeft > 0");
    await shot('tutor-reports-small'); await viewport(1440);
    await waitFor("document.querySelector('.workspace-nav').getAttribute('aria-orientation') === 'vertical'");
    await click('#tab-overview');
    await click('#workspace-overview [data-open-tab="schedule"]');
    assert.equal(await evaluate("document.getElementById('tab-schedule').getAttribute('aria-selected')"), 'true');
    const tutorPath = await evaluate("new URL(document.getElementById('share-url').value).pathname");
    const slotDate = await evaluate("(() => { const date = new Date(document.getElementById('slot-date').value + 'T12:00:00Z'); date.setUTCDate(date.getUTCDate() + 2); return date.toISOString().slice(0, 10); })()");
    await fill('slot-date', slotDate); await fill('slot-start', '10:00'); await fill('slot-end', '11:00');
    await submit('slot-form'); await waitFor("document.getElementById('slot-message').classList.contains('success')");
    assert.equal(await evaluate("Number(document.getElementById('overview-open-slots').textContent)"), 1);
    await shot('tutor-dashboard');
    await viewport(390, 844); await shot('tutor-dashboard-mobile'); await viewport(1440);
    await click('#tab-students');
    assert.match(await evaluate("document.getElementById('students-list').innerText"), /Ученики появятся после первой записи/);
    assert.equal(await evaluate("document.querySelectorAll('#students-list .person-card').length"), 0);
    await click('#tab-profile'); await fill('profile-description', 'Подготовка к экзаменам. <img src=x onerror="window.injected=true">');
    await submit('profile-form'); await waitFor("document.getElementById('profile-message').classList.contains('success')");
    const updatedTutorName = `Преподаватель после изменения ${suffix}`;
    await fill('profile-name', updatedTutorName); await submit('profile-form');
    await waitFor(`document.querySelector('.header-user-name').textContent === ${JSON.stringify(updatedTutorName)}`);
    await click('[data-logout]'); await waitFor("location.pathname === '/login'");

    await go('/register?role=student'); await waitFor("!!document.getElementById('register-next')");
    await click('#register-next');
    assert.equal(await evaluate("document.getElementById('subject').required"), false);
    await fill('name', 'Тестовый ученик <img src=x onerror="window.injected=true">');
    await fill('email', `student-${suffix}@example.org`); await fill('password', 'frontend-test-only');
    await click('#register-next');
    assert.equal(await evaluate("document.querySelector('#review-name img')"), null);
    await submit('register-form');
    await waitFor("location.pathname === '/student/dashboard' && document.getElementById('dashboard-content') && !document.getElementById('dashboard-content').hidden");
    assert.equal(await evaluate("document.querySelector('.header-user-name').textContent"), 'Тестовый ученик <img src=x onerror="window.injected=true">');
    assert.equal(await evaluate("!!document.querySelector('.header-user img') || window.injected === true"), false);
    assert.equal(await evaluate("document.getElementById('tab-profile').closest('.workspace-settings').getAttribute('aria-label')"), 'Настройки');
    await click('.header-user');
    await waitFor("location.hash === '#profile' && document.getElementById('tab-profile').getAttribute('aria-selected') === 'true'");
    await click('#tab-tutors');
    await click('#panel-tutors a[href="/tutors"]'); await waitFor("location.pathname === '/tutors' && !!document.getElementById('catalog-content') && !document.getElementById('catalog-content').hidden");
    await searchDirectory('catalog-search', updatedTutorName);
    assert.equal(await evaluate("document.querySelectorAll('#catalog-list .person-card').length"), 1);
    await shot('catalog-signed-in'); await viewport(390, 844); await shot('catalog-signed-in-mobile');
    await viewport(320, 844); await shot('catalog-signed-in-small'); await viewport(1440);
    await click('#catalog-list a');
    await waitFor(`location.pathname === ${JSON.stringify(tutorPath)} && !!document.getElementById('public-content') && !document.getElementById('public-content').hidden`);
    await go('/student/dashboard'); await waitFor("!document.getElementById('dashboard-content').hidden");
    await click('#tab-tutors');
    assert.match(await evaluate("document.getElementById('tutors-list').innerText"), /Здесь будут ваши репетиторы/);
    await click('#tab-overview'); await shot('student-empty');
    await go(tutorPath); await waitFor("!document.getElementById('public-content').hidden");
    assert.equal(await evaluate('window.injected === true'), false, 'Profile description must not execute HTML.');
    await click('[data-slot]'); await submit('booking-form'); await waitFor("!document.getElementById('booking-success').hidden");
    assert.match(await evaluate("document.getElementById('booking-success').innerText"), /Вы записаны/);
    await go('/student/dashboard'); await waitFor("!document.getElementById('dashboard-content').hidden");
    assert.equal(await evaluate("document.getElementById('stat-upcoming').textContent"), '1');
    assert.equal(await evaluate("document.querySelectorAll('.lesson-spotlight').length"), 1);
    await shot('student-dashboard'); await viewport(390, 844); await shot('student-mobile'); await viewport(1440);
    await click('[data-theme-toggle]'); await shot('student-overview-light'); await click('[data-theme-toggle]');
    await viewport(320, 844); await shot('student-overview-small'); await viewport(1440);
    await click('#workspace-overview [data-student-day]');
    assert.equal(await evaluate("location.hash"), '#schedule');
    await fill('student-view-date', slotDate);
    await evaluate("document.getElementById('student-view-date').dispatchEvent(new Event('change', { bubbles: true }))");
    assert.equal(await evaluate("document.querySelectorAll('#student-schedule-list .booking-item').length"), 1);
    await shot('student-schedule');
    await click('[data-theme-toggle]'); await shot('student-schedule-light');
    await viewport(320, 844); await shot('student-schedule-light-small');
    await click('[data-theme-toggle]'); await shot('student-schedule-small'); await viewport(1440);
    await click('#student-next-week');
    assert.equal(await evaluate("document.querySelectorAll('#student-schedule-list .booking-item').length"), 0);
    await click('#student-prev-week');
    assert.equal(await evaluate("document.querySelectorAll('#student-schedule-list .booking-item').length"), 1);
    await click('#student-today');
    assert.equal(await evaluate("!!document.querySelector('#student-week-days .is-today[aria-pressed=true]')"), true);
    const selectedStudentDay = await evaluate("document.getElementById('student-view-date').value");
    await fill('student-view-date', '');
    await evaluate("document.getElementById('student-view-date').dispatchEvent(new Event('change', { bubbles: true }))");
    assert.equal(await evaluate("document.getElementById('student-view-date').value"), selectedStudentDay);
    await click('#tab-overview'); await click('#workspace-overview [data-open-tab="homework"]');
    assert.equal(await evaluate("location.hash"), '#homework');
    assert.match(await evaluate("document.getElementById('panel-homework').innerText"), /пока недоступны/);
    await shot('student-homework');
    await viewport(320, 844); await go('/student/dashboard#materials');
    await waitFor("!document.getElementById('dashboard-content').hidden");
    assert.equal(await evaluate("document.getElementById('tab-materials').getAttribute('aria-selected')"), 'true');
    assert.match(await evaluate("document.getElementById('panel-materials').innerText"), /пока недоступны/);
    await shot('student-materials-small');
    await click('[data-theme-toggle]'); await shot('student-materials-light-small');
    await click('[data-theme-toggle]'); await viewport(1440); await click('#tab-overview');
    await click('#workspace-overview [data-open-tab="upcoming"]');
    assert.equal(await evaluate("document.getElementById('tab-upcoming').getAttribute('aria-selected')"), 'true');
    await shot('student-bookings-compact');
    await click('#tab-tutors');
    assert.equal(await evaluate("document.querySelectorAll('#tutors-list .person-card').length"), 1);
    await searchDirectory('tutors-search', 'математика');
    assert.equal(await evaluate("document.querySelectorAll('#tutors-list .person-card').length"), 1);
    await searchDirectory('tutors-search', 'нет такого преподавателя');
    assert.match(await evaluate("document.getElementById('tutors-list').innerText"), /Никого не нашли/);
    await click('#panel-tutors [data-directory-reset]');
    await shot('my-tutors-desktop'); await click('[data-theme-toggle]'); await shot('my-tutors-light');
    await click('[data-theme-toggle]'); await viewport(390, 844); await shot('my-tutors-mobile');
    await viewport(320, 844); await shot('my-tutors-small'); await viewport(1440);
    assert.equal(await evaluate("document.querySelector('#tutors-list .text-link').getAttribute('href')"), tutorPath);
    await click('#tutors-list .text-link');
    await waitFor(`location.pathname === ${JSON.stringify(tutorPath)} && !!document.getElementById('public-content') && !document.getElementById('public-content').hidden`);
    await go('/student/dashboard#tutors'); await waitFor("document.querySelectorAll('#tutors-list .person-card').length === 1");
    assert.equal(await evaluate("document.getElementById('tab-tutors').getAttribute('aria-selected')"), 'true');
    await click('#tutors-list [data-directory-open]');
    assert.equal(await evaluate("document.querySelectorAll('#panel-tutors [data-directory-detail] .person-bookings:first-of-type .booking-item').length"), 1);
    await shot('tutor-records'); await viewport(390, 844); await shot('tutor-records-mobile');
    await viewport(320, 844); await shot('tutor-records-small'); await viewport(1440);
    assert.equal(await evaluate("!!document.querySelector('#panel-tutors [data-cancel-booking]')"), true);
    await click('#tab-schedule'); await fill('student-view-date', slotDate);
    await evaluate("document.getElementById('student-view-date').dispatchEvent(new Event('change', { bubbles: true }))");
    await click('#student-schedule-list [data-cancel-booking]');
    await waitFor("!!document.querySelector('dialog[open]')"); await click('dialog [value="confirm"]');
    await waitFor("document.getElementById('stat-upcoming').textContent === '0'");
    assert.equal(await evaluate("document.querySelectorAll('#student-schedule-list .booking-item').length"), 0);
    await click('#tab-tutors');
    assert.match(await evaluate("document.querySelector('#panel-tutors [data-directory-detail]').innerText"), /Отменено/);
    await click('#panel-tutors [data-directory-back]');
    assert.equal(await evaluate("document.activeElement.hasAttribute('data-directory-open')"), true);
    await filterDirectory('tutors-filter', 'upcoming');
    assert.equal(await evaluate("document.querySelectorAll('#tutors-list .person-card').length"), 0);
    await click('#panel-tutors [data-directory-reset]');
    assert.equal(await evaluate("document.querySelectorAll('#tutors-list .person-card').length"), 1);
    await click('#tab-history'); assert.match(await evaluate("document.getElementById('history-list').innerText"), /Отменено/);
    await click('[data-logout]'); await waitFor("location.pathname === '/login'");

    await go(tutorPath); await waitFor("!document.getElementById('public-content').hidden");
    await click('[data-slot]'); await fill('student-name', 'Гость'); await fill('student-email', `guest-${suffix}@example.org`);
    await submit('booking-form'); await waitFor("!document.getElementById('booking-success').hidden");
    assert.match(await evaluate("document.getElementById('booking-success').innerText"), /Проверьте вашу почту/);
    const mail = await (await fetch(`${base}/__qa/mail`)).json();
    const links = mail.at(-1).split('\n').filter(line => line.startsWith('http'));
    assert.equal(links.length, 2);
    await login(`tutor-${suffix}@example.org`, '/tutor/dashboard');
    await click('#tab-students');
    assert.equal(await evaluate("document.querySelectorAll('#students-list .person-card').length"), 2);
    assert.equal(await evaluate("!!document.querySelector('#students-list img') || window.injected === true"), false, 'Student names must remain plain text.');
    await searchDirectory('students-search', `student-${suffix}@example.org`);
    assert.equal(await evaluate("document.querySelectorAll('#students-list .person-card').length"), 1);
    await click('#students-list [data-directory-open]');
    assert.match(await evaluate("document.querySelector('#panel-students [data-directory-detail]').innerText"), /Отменено/);
    await click('#panel-students [data-directory-back]');
    await searchDirectory('students-search', ''); await filterDirectory('students-filter', 'guest');
    assert.equal(await evaluate("document.querySelectorAll('#students-list .person-card').length"), 1);
    assert.match(await evaluate("document.getElementById('students-list').innerText"), /Ждёт подтверждения/);
    await click('#students-list [data-directory-open]');
    assert.match(await evaluate("document.querySelector('#panel-students [data-directory-detail]').innerText"), /не привязаны к аккаунту/);
    await shot('guest-records'); await viewport(390, 844); await shot('guest-records-mobile');
    await viewport(320, 844); await shot('guest-records-small'); await viewport(1440);
    await click('#panel-students [data-directory-back]'); await filterDirectory('students-filter', 'account');
    assert.equal(await evaluate("document.querySelectorAll('#students-list .person-card').length"), 1);
    await filterDirectory('students-filter', 'all');
    await shot('my-students-desktop'); await viewport(390, 844); await shot('my-students-mobile');
    await viewport(320, 844); await shot('my-students-small'); await viewport(1440);
    await click('[data-logout]'); await waitFor("location.pathname === '/login'");
    const confirmUrl = new URL(links[0]);
    await go(confirmUrl.pathname + confirmUrl.search); await waitFor("!!document.getElementById('action-form')");
    await shot('confirmation'); await submit('action-form'); await waitFor("document.getElementById('action-title').textContent === 'Запись подтверждена'");
    const cancelUrl = new URL(links[1]);
    await go(cancelUrl.pathname + cancelUrl.search); await waitFor("!!document.getElementById('action-form')");
    await submit('action-form'); await waitFor("document.getElementById('action-title').textContent === 'Запись отменена'");

    await login(`student-${suffix}@example.org`, '/student/dashboard');
    await click('#tab-tutors'); await click('#tutors-list .text-link');
    await waitFor(`location.pathname === ${JSON.stringify(tutorPath)} && !!document.getElementById('public-content') && !document.getElementById('public-content').hidden`);
    await click('[data-slot]'); await submit('booking-form'); await waitFor("!document.getElementById('booking-success').hidden");
    await click('[data-logout]'); await waitFor("location.pathname === '/login'");
    await login(`tutor-${suffix}@example.org`, '/tutor/dashboard'); await click('#tab-students');
    await filterDirectory('students-filter', 'upcoming');
    assert.equal(await evaluate("document.querySelectorAll('#students-list .person-card').length"), 1);
    await click('#students-list [data-directory-open]'); await click('#panel-students [data-cancel-booking]');
    await waitFor("!!document.querySelector('dialog[open]')"); await click('dialog [value="confirm"]');
    await waitFor("document.querySelectorAll('#panel-students [data-directory-detail] .badge.cancelled').length === 2");
    assert.equal(await evaluate("Number(document.getElementById('overview-open-slots').textContent)"), 0, 'Tutor cancellation closes the slot.');
    assert.equal(await evaluate("document.querySelectorAll('#panel-students [data-directory-detail] .booking-item').length"), 2);
    assert.deepEqual(errors, [], 'Unexpected browser exceptions');
    console.log('Browser checks passed: tutor catalog, search/filters, catalog-to-booking flow, header identity, profile navigation/name update, guide pages, navigation, mobile menu, help search, tutor links, registration, roles, slot creation, profile escaping, directories, student calendar/date/week navigation and cancellation, homework/materials tabs, repeat booking, cancellation by both roles, guest confirmation/cancellation, desktop/mobile layouts, both themes.');
    console.log(`Screenshots: ${artifacts}`);
    await call('Browser.close').catch(() => {});
} finally {
    socket?.close();
    chrome.kill();
    await delay(500);
    if (resolve(profile).startsWith(resolve(tmpdir()) + sep) && basename(profile).startsWith('ezhrika-browser-')) await rm(profile, { recursive: true, force: true, maxRetries: 3, retryDelay: 250 }).catch(() => {});
}
