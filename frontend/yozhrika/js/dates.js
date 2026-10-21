export function browserZone() { return Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC'; }

function parts(value, zone) {
    const options = { timeZone: zone, year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', hourCycle: 'h23' };
    return Object.fromEntries(new Intl.DateTimeFormat('en-GB', options).formatToParts(new Date(value)).map(part => [part.type, part.value]));
}

export function dateKey(value = new Date(), zone = browserZone()) {
    const p = parts(value, zone);
    return `${p.year}-${p.month}-${p.day}`;
}

export function formatDate(value, zone = browserZone(), options = {}) {
    return new Intl.DateTimeFormat('ru-RU', { timeZone: zone, day: 'numeric', month: 'long', ...options }).format(new Date(value));
}

export function formatTime(value, zone = browserZone()) {
    return new Intl.DateTimeFormat('ru-RU', { timeZone: zone, hour: '2-digit', minute: '2-digit', hourCycle: 'h23' }).format(new Date(value));
}

export function formatRange(slot, zone = browserZone()) { return `${formatTime(slot.starts_at, zone)}–${formatTime(slot.ends_at, zone)}`; }
export function duration(slot) { return Math.round((new Date(slot.ends_at) - new Date(slot.starts_at)) / 60000); }

export function shiftDay(key, count) {
    const date = new Date(`${key}T12:00:00Z`);
    date.setUTCDate(date.getUTCDate() + count);
    return date.toISOString().slice(0, 10);
}

export function weekDays(key) {
    const day = new Date(`${key}T12:00:00Z`).getUTCDay();
    const monday = shiftDay(key, -(day === 0 ? 6 : day - 1));
    return Array.from({ length: 7 }, (_, i) => shiftDay(monday, i));
}

// Преобразование введённого местного времени в UTC без зависимости от пояса браузера.
export function zonedISO(date, time, zone) {
    if (!/^\d{4}-\d{2}-\d{2}$/.test(date) || !/^\d{2}:\d{2}$/.test(time)) throw new Error('Укажите дату и время занятия.');
    const target = `${date}T${time}`;
    const wallTime = Date.parse(`${target}:00Z`);
    if (!Number.isFinite(wallTime) || new Date(wallTime).toISOString().slice(0, 16) !== target) throw new Error('Проверьте дату и время занятия.');
    let guess = wallTime;
    const localStamp = stamp => { const p = parts(stamp, zone); return `${p.year}-${p.month}-${p.day}T${p.hour}:${p.minute}`; };
    for (let i = 0; i < 4; i++) {
        const actual = Date.parse(`${localStamp(guess)}:00Z`);
        guess += wallTime - actual;
    }
    if (localStamp(guess) !== target) throw new Error('Это время отсутствует из-за перевода часов. Выберите другое время.');
    for (const offset of [-3600000, -1800000, 1800000, 3600000]) {
        if (localStamp(guess + offset) === target) throw new Error('Это время повторяется из-за перевода часов. Выберите другое время.');
    }
    return new Date(guess).toISOString();
}

export function fillTimezones(list, selected = browserZone()) {
    const values = new Set([selected, browserZone(), 'UTC', 'Europe/Moscow', 'Asia/Novosibirsk']);
    if (Intl.supportedValuesOf) Intl.supportedValuesOf('timeZone').forEach(zone => values.add(zone));
    list.replaceChildren(...[...values].sort().map(value => Object.assign(document.createElement('option'), { value })));
}
