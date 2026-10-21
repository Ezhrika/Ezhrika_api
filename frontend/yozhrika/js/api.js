const TOKEN_KEY = 'yozhrika-access-token';

export function getToken() {
    try { return sessionStorage.getItem(TOKEN_KEY); } catch { return null; }
}

export function setToken(token) {
    try { sessionStorage.setItem(TOKEN_KEY, token); }
    catch { throw new Error('Не удалось сохранить вход. Разрешите хранение данных сайта в настройках браузера.'); }
}

export function clearToken() {
    try { sessionStorage.removeItem(TOKEN_KEY); } catch { /* Уже вышли из аккаунта. */ }
}

const messages = {
    'Choose a subject from the subject list.': 'Выберите предмет из списка.',
    'Invalid email or password.': 'Неверный email или пароль.',
    'A user with this email already exists.': 'Аккаунт с таким email уже существует. Войдите в него.',
    'Could not validate credentials': 'Время входа истекло. Войдите в аккаунт ещё раз.',
    'Not authenticated': 'Войдите в аккаунт, чтобы продолжить.',
    'Slot overlaps with an existing slot for this tutor.': 'Это время пересекается с другим слотом. Выберите другой интервал.',
    'Slot is already booked or not available.': 'Это время уже заняли. Выберите другой свободный слот.',
    'Cannot book a slot in the past.': 'Это занятие уже началось. Выберите другое время.',
    'Slot not found.': 'Этот слот больше недоступен. Обновите расписание.',
    'Tutor not found.': 'Страница репетитора не найдена. Проверьте ссылку.',
    'Confirmation link has expired.': 'Срок подтверждения истёк. Откройте страницу репетитора и запишитесь заново.',
    'Invalid confirmation token.': 'Ссылка подтверждения недействительна. Откройте полную ссылку из письма.',
    'Invalid cancellation token.': 'Ссылка отмены недействительна. Откройте полную ссылку из письма.',
    'Guest booking not found.': 'Запись по этой ссылке не найдена.',
    'Booking cannot be confirmed.': 'Эту запись уже отменили или срок подтверждения истёк.',
    'Booking is no longer active.': 'Эта запись уже отменена или больше не действует.',
    'Cannot delete a booked slot. Please cancel the booking instead.': 'На это время уже есть запись. Сначала отмените занятие в разделе «Записи».',
    'Tutors cannot book lessons.': 'Запись на занятия доступна из аккаунта ученика или без входа.',
};

export class ApiError extends Error {
    constructor(message, status) { super(message); this.name = 'ApiError'; this.status = status; }
}

function errorMessage(payload, status) {
    if (Array.isArray(payload?.detail)) {
        const labels = { email: 'Email', password: 'Пароль', name: 'Имя', subject: 'Предмет', timezone: 'Часовой пояс', starts_at: 'Начало', ends_at: 'Окончание', student_email: 'Email', student_name: 'Имя', question: 'Комментарий' };
        return [...new Set(payload.detail.map(error => {
            const field = error.loc?.at(-1);
            if (field === 'password') return 'Пароль: 8–72 символа, латинские буквы, цифры и знаки без пробелов.';
            if (field === 'timezone') return 'Укажите действующий часовой пояс, например Asia/Novosibirsk.';
            if (field === 'subject' || error.msg?.includes('Choose a subject')) return 'Выберите предмет из списка.';
            if (error.msg?.includes('Slot start time')) return 'Начало занятия должно быть в будущем.';
            if (error.msg?.includes('Slot end time')) return 'Окончание занятия должно быть позже начала.';
            return `${labels[field] || 'Данные формы'}: проверьте значение и допустимую длину.`;
        }))].join(' ');
    }
    if (messages[payload?.detail]) return messages[payload.detail];
    if (status === 401) return 'Войдите в аккаунт ещё раз.';
    if (status === 403) return 'У вашего аккаунта нет доступа к этому действию.';
    if (status === 404) return 'Запрошенные данные не найдены. Обновите страницу.';
    if (status === 409) return 'Данные уже изменились. Обновите страницу и повторите действие.';
    if (status === 429) return 'Слишком много запросов. Подождите немного и попробуйте снова.';
    return 'Не удалось выполнить запрос. Попробуйте ещё раз немного позже.';
}

export async function api(path, { method = 'GET', data, auth = true } = {}) {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 15000);
    const headers = { Accept: 'application/json' };
    if (data !== undefined) headers['Content-Type'] = 'application/json';
    const token = auth ? getToken() : null;
    if (token) headers.Authorization = `Bearer ${token}`;
    try {
        const response = await fetch(`/api/v1${path}`, {
            method, headers, signal: controller.signal, credentials: 'same-origin',
            body: data === undefined ? undefined : JSON.stringify(data),
        });
        const payload = response.status === 204 ? null : await response.json().catch(() => null);
        if (!response.ok) {
            if (response.status === 401 && token) {
                clearToken();
                window.dispatchEvent(new Event('session-expired'));
            }
            throw new ApiError(errorMessage(payload, response.status), response.status);
        }
        if (response.status !== 204 && payload === null) throw new Error('Сервер вернул неожиданный ответ. Обновите страницу.');
        return payload;
    } catch (error) {
        if (error.name === 'AbortError') throw new Error('Сервер отвечает слишком долго. Проверьте соединение и попробуйте снова.');
        if (error instanceof TypeError) throw new Error('Не удалось связаться с сервером. Проверьте соединение и попробуйте снова.');
        throw error;
    } finally { clearTimeout(timeout); }
}
