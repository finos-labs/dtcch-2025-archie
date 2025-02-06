import { create } from "zustand";
import { timeout } from "../../utils/common";
import { AUTH_INVALID_USER_ERROR_MSG, AUTH_PASS_KEY, AUTH_USER, AUTH_WAIT_TS } from "../../constants/auth";
import { establishSession } from "../localStorage/session";
import { destroyAllStorage } from "../localStorage/connector";

const initialState = {
    enableAuthInputs: false,
    isValidUser: false,
    isAuthenticating: false,
    errorMsg: "",
    passKeyInp: ""
}
const authStore = (set, get) => ({
    ...initialState,

    udpateEnableAuthInputs: (flag) => set(() => ({ enableAuthInputs: flag })),
    updateIsValidUser: (flag) => set(() => ({ isValidUser: flag })),
    updatePassKeyInp: (value) => set(() => ({ passKeyInp: value })),

    authenticate: async () => {
        set(() => ({
            errorMsg: "",
            isAuthenticating: true
        }));

        await timeout(AUTH_WAIT_TS);

        let _isValidUser = get().isValidUser;
        let _isAuthenticating = false;
        let _errorMsg = "";

        if (get().passKeyInp === AUTH_PASS_KEY) {
            _isValidUser = true;
            establishSession(AUTH_USER);
        }
        else {
            _errorMsg = AUTH_INVALID_USER_ERROR_MSG;
            _isValidUser = false;
        }
        set(() => ({
            isValidUser: _isValidUser,
            isAuthenticating: _isAuthenticating,
            errorMsg: _errorMsg
        }));
    },
    reset: () => {
        destroyAllStorage();
        set(() => ({
            ...initialState,
            enableAuthInputs: true
        }));
    }
});

const useAuthStore = create(authStore);

export default useAuthStore;