import { api } from './api.js';

let subjectList;
export function getSubjects() {
    if (!subjectList) subjectList = api('/tutors/subjects', { auth: false }).catch(error => { subjectList = null; throw error; });
    return subjectList;
}

export async function fillSubjects(select, current = '') {
    const subjects = await getSubjects();
    select.replaceChildren(new Option('Выберите предмет', ''), ...subjects.map(subject => new Option(subject, subject)));
    if (current && !subjects.includes(current)) select.add(new Option(`${current} — выбран ранее`, current));
    select.value = current;
    select.disabled = false;
}
