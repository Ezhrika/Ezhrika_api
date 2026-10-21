"""Общий справочник предметов для регистрации, профиля и каталога."""

SUBJECTS = (
    "Математика", "Русский язык", "Английский язык", "Физика", "Информатика",
    "Химия", "Биология", "История", "Обществознание", "География", "Литература",
    "Немецкий язык", "Французский язык", "Испанский язык", "Китайский язык",
    "Программирование", "Начальная школа", "Музыка", "Рисование",
)


def _key(value: str) -> str:
    return " ".join(value.casefold().replace("ё", "е").split())


_NAMES = {_key(subject): subject for subject in SUBJECTS}
_ALIASES = {
    "math": "Математика", "maths": "Математика", "mathematics": "Математика",
    "physics": "Физика", "english": "Английский язык", "английский": "Английский язык",
    "russian": "Русский язык", "русский": "Русский язык",
    "немецкий": "Немецкий язык", "французский": "Французский язык",
    "испанский": "Испанский язык", "китайский": "Китайский язык",
    "computer science": "Информатика", "programming": "Программирование",
}


def canonical_subject(value: str) -> str | None:
    return _NAMES.get(_key(value)) or _ALIASES.get(_key(value))


def require_subject(value: str) -> str:
    subject = canonical_subject(value)
    if subject is None:
        raise ValueError("Choose a subject from the subject list.")
    return subject


def display_subject(value: str) -> str:
    # Не меняем и не теряем старые нестандартные названия при чтении.
    return canonical_subject(value) or value
