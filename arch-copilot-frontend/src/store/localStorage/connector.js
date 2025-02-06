export const setToStorage = (key, value) => {
    localStorage.setItem(key, JSON.stringify(value));
}

export const destroyStorage = (key) => {
    localStorage.removeItem(key);
}

export const destroyAllStorage = () => {
    localStorage.clear();
}

export const getFromStorage = (key) => {
    const value = localStorage.getItem(key);
    return value == null ? null : JSON.parse(value);
}

export const destroySession = () => destroyAllStorage();