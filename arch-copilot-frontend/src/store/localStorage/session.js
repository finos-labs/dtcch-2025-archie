import { SESSION, SESSION_VALIDITY } from "../../constants/localStorage";
import { generateUUID } from "../../utils/common";
import { getFromStorage, setToStorage } from "./connector";

export const resetSessionStoreState = (user_name) => ({
    'ts': new Date().getTime(),
    'session_id': generateUUID(),
    'user_id': user_name
});

export const getSession = () => getFromStorage(SESSION);

export const setSession = (obj) => setToStorage(SESSION, obj);

export const establishSession = (user_name) => setSession(resetSessionStoreState(user_name));

export const isSessionValid = () => {
    const session = getSession();
    if (session === null || session.ts === null || session.session_id === null || session.user_id === null)
        return false;
    
    const currentTs = new Date().getTime();
    if (((currentTs - session.ts) / 1000) > SESSION_VALIDITY || session.session_id.length <= 0)
        return false;

    return true;
}

export const getSessionObject = (key) => isSessionValid() ?  getSession()[key]: null;

export const getSessionId = () => getSessionObject('session_id');

export const getUserId = () => getSessionObject('user_id');