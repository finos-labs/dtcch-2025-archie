import { useEffect, useState } from 'react';
import { SESSION_VALID_INTERVAL_TS } from '../constants/auth';
import useAuthStore from '../store/application/authStore';
import { isSessionValid } from '../store/localStorage/session';
import '../style/App.css';
import AuthPage from './AuthPage';
import Homepage from './HomePage';
import useAppStore from '../store/application/appStore';
import { timeout } from '../utils/common';

function App() {
  const isValidUser = useAuthStore((state) => state.isValidUser);
  
  const udpateEnableAuthInputs = useAuthStore((state) => state.udpateEnableAuthInputs);
  const updateIsValidUser = useAuthStore((state) => state.updateIsValidUser);
  const udpateShowVoiceList = useAppStore((state) => state.udpateShowVoiceList);
  const updateShowAvatarList = useAppStore((state) => state.updateShowAvatarList);

  useEffect(() => {
   init();   
  }, []);

  const init = async () => {
    await timeout(3000);
    udpateEnableAuthInputs(true);
    updateIsValidUser(isSessionValid());
    setInterval(() => updateIsValidUser(isSessionValid()), SESSION_VALID_INTERVAL_TS);
  }
  const onRootClick = () => {
    udpateShowVoiceList(false);
    updateShowAvatarList(false);
  }
  return (
    <div onClick={onRootClick}>
        {isValidUser ?
          <Homepage />
          :
          <AuthPage/>
        }
    </div>
  )
}

export default App
