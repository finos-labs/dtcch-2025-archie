import { PiAtomFill } from "react-icons/pi";
import { FaUnlock } from "react-icons/fa6";
import "../style/AuthPage.css";
import { APP_NAME } from "../constants/app";
import useAuthStore from "../store/application/authStore";

function AuthPage() {
    const errorMsg = useAuthStore((state) => state.errorMsg);
    const isAuthenticating = useAuthStore((state) => state.isAuthenticating);

    const enableAuthInputs = useAuthStore((state) => state.enableAuthInputs);
    const updatePassKeyInp = useAuthStore((state) => state.updatePassKeyInp);
    const authenticate = useAuthStore((state) => state.authenticate);

    const onPassKeyUpdate = (e) => {
        updatePassKeyInp(e.target?.value);
    }
    const onKeyDown = (e) => {
        if (e.key === "Enter") {
            e.preventDefault();
            authenticate();
        }
    }
    return (
        <div id="auth-page-wrapper" className="full-vh">
            <div id="logo-screen-wrapper">
                <div><img src="/logo/logo_256.png"></img></div>
                <div id="app-name">{APP_NAME}</div>
            </div>

            <div id="auth-page-body" className={`${enableAuthInputs ? "show" : ""} `}>
                <input type="password" disabled={isAuthenticating} placeholder="Enter your passkey" onChange={onPassKeyUpdate} onKeyDown={onKeyDown}></input>
                <div id="auth-page-unlock" className={isAuthenticating ? "disabled" : ""} onClick={authenticate}>
                    <FaUnlock
                        size={20}
                        color={"white"}
                    />
                </div>               
            </div>
            <div id="auth-page-footer">
                {errorMsg && <div>{errorMsg}</div>}
            </div>
        </div>
    )
}
export default AuthPage;