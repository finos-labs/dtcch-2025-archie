import { useEffect, useRef } from 'react';
import { RiChatNewLine } from "react-icons/ri";
import { FaArrowsUpToLine, FaArrowsDownToLine } from "react-icons/fa6";
import { PiSpeakerSimpleHighBold } from "react-icons/pi";
import { FaMale, FaFemale } from "react-icons/fa";
import { RxAvatar } from "react-icons/rx";
import '../style/ChatWindow.css';
import ChatInput from './ChatInput';
import Chat from './Chat';
import { AUDIO_OVERLAY_MODE, LOADING_OVERLAY_MODE, MALE_GENDER, NO_OVERLAY_MODE, VIDEO_OVERLAY_MODE } from '../constants/app';
import useAppStore from '../store/application/appStore';
import { resetBlobUrlStore } from '../utils/blob';

const avatars = ["man-avatar1", "man-avatar2", "man-avatar3", "woman-avatar1", "woman-avatar2", "woman-avatar3"];
const images = {};
avatars.map(avatar => {
     images[avatar] = { src: `/media/${avatar}/avatar.png`};
});
  
function ChatWindow() {
    const isSubHeaderOpen = useAppStore((state) => state.isSubHeaderOpen);
    const mediaOverlayMode = useAppStore((state) => state.mediaOverlayMode);
    const selectedQuestion = useAppStore((state) => state.selectedQuestion);
    const botToRespond = useAppStore((state) => state.botToRespond);
    const audioUrl = useAppStore((state) => state.audioUrl);
    const videoUrl = useAppStore((state) => state.videoUrl);
    const voiceList = useAppStore((state) => state.voiceList);
    const avatarList = useAppStore((state) => state.avatarList);
    const showVoiceList = useAppStore((state) => state.showVoiceList);
    const showAvatarList = useAppStore((state) => state.showAvatarList);
    const voiceId = useAppStore((state) => state.voiceId);
    const avatarId = useAppStore((state) => state.avatarId);

    const toggleIsSubHeaderOpen = useAppStore((state) => state.toggleIsSubHeaderOpen);
    const handleChatItemsUpdate = useAppStore((state) => state.handleChatItemsUpdate);
    const updateSearchText = useAppStore((state) => state.updateSearchText);
    const updateSelectedFile = useAppStore((state) => state.updateSelectedFile);
    const closeMediaOverlayContent = useAppStore((state) => state.closeMediaOverlayContent);
    const udpateShowVoiceList = useAppStore((state) => state.udpateShowVoiceList);
    const updateShowAvatarList = useAppStore((state) => state.updateShowAvatarList);
    const updateVoiceId = useAppStore((state) => state.updateVoiceId);
    const updateAvatarId = useAppStore((state) => state.updateAvatarId);    

    const fileUploadRef = useRef(null);
    const clearFields = (isNewChat) => {
        updateSearchText("");
        isNewChat && handleChatItemsUpdate([]);
        updateSelectedFile(null);
        fileUploadRef.current.value = "";
    }
    useEffect(() => {
        if (selectedQuestion === null) {
            updateSearchText("");
        }
        else {
            clearFields(true);
            updateSearchText(selectedQuestion);
        }
    }, [selectedQuestion]);
    const openVoiceList = (e) => {
        e.stopPropagation();
        udpateShowVoiceList(true);
        updateShowAvatarList(false);
    }
    const openAvatarList = (e) => {
        e.stopPropagation();
        udpateShowVoiceList(false);
        updateShowAvatarList(true);
    }
    const onSelectVoice = (voice) => {
        updateVoiceId(voice.voice_id);
        udpateShowVoiceList(false);
        resetBlobUrlStore();
    }
    const onSelectAvatar = (avatar) => {
        updateAvatarId(avatar.avatar_name);
        updateShowAvatarList(false);
        resetBlobUrlStore();
    }
    return (
        <div id="chatwindow-wrapper">
            <div id="chat-header">
                <div id="chat-header-left-wrapper">
                    {isSubHeaderOpen ?
                        <div id="slide-icon" title="Slide above">
                            <FaArrowsUpToLine
                                size={25}
                                color={"black"}
                                onClick={toggleIsSubHeaderOpen}
                            />
                        </div>
                        :
                        <div id="slide-icon" title="Slide below">
                            <FaArrowsDownToLine
                                size={25}
                                color={"black"}
                                onClick={toggleIsSubHeaderOpen}
                            />
                        </div>
                    }
                    <div id="new-chat-icon" title="Create New Chat">
                        <RiChatNewLine
                            size={25}
                            color={"black"}
                            onClick={() => !botToRespond && clearFields(true)}
                        />
                    </div>
                </div>
                <div id="chat-header-right-wrapper">
                    <div id="voice-wrapper" title="Choose voice" onClick={openVoiceList}>
                        <PiSpeakerSimpleHighBold
                            size={25}
                            color={"black"}
                            onClick={() => { }}
                        />
                        <div id="voice-options-wrapper" className={`${showVoiceList ? "active": ""}`}>
                            {voiceList.map(voice => {
                                return (
                                    <div className={`voice-option ${voice.voice_id === voiceId ? "active": ""}`} key={`Voice-${voice.voice_id}`} onClick={() => onSelectVoice(voice)}>
                                        <div className="voice-option-gender">{voice.gender === MALE_GENDER ? <FaMale size={25} />: <FaFemale size={25} />}</div>
                                        <div className="voice-option-namelang">
                                            <div className="voice-option-name">{voice.voice_id}</div>
                                            <div className="voice-option-lang">{voice.language_name}</div>
                                        </div>
                                    </div>
                                )
                            })}
                        </div>
                    </div>
                    <div id="avatar-wrapper" title="Choose avatar" onClick={openAvatarList}>
                        <RxAvatar
                            size={25}
                            color={"black"}
                            onClick={() => { }}
                        />
                        <div id="avatar-options-wrapper" className={`${showAvatarList ? "active": ""}`}>
                            {avatarList.map(avatar => {
                                return (
                                    <div className={`avatar-option ${avatar.avatar_name === avatarId ? "active": ""}`} key={`Avatar-${avatar.avatar_name}`} onClick={() => onSelectAvatar(avatar)}>
                                        <div className="avatar-option-img">
                                            <img src={images[avatar.avatar_name].src} width={20} height={30}></img>
                                        </div>
                                        <div className="avatar-option-name">{avatar.avatar_name}</div>
                                    </div>
                                )
                            })}
                        </div>
                    </div>
                </div>
            </div>
            <div id="chat-body">
                <Chat />
            </div>
            <div id="chat-footer">
                <ChatInput
                    fileUploadRef={fileUploadRef}
                    clearFields={clearFields}
                />
            </div>
            {mediaOverlayMode !== NO_OVERLAY_MODE &&
                <div id="overlay-wrapper" onClick={closeMediaOverlayContent}>
                    <div id="overlay-sub-wrapper">
                        {mediaOverlayMode === AUDIO_OVERLAY_MODE &&
                            <div id="audio-player-wrapper">
                                <audio src={audioUrl} autoPlay controls type="audio/mp3">
                                    Your browser does not support the audio element.
                                </audio>
                            </div>
                        }
                        {mediaOverlayMode === VIDEO_OVERLAY_MODE &&
                            <div id="video-player-wrapper">
                                <video width="320" height="240" autoPlay controls>
                                    <source src={videoUrl} type="video/mp4" />
                                    Your browser does not support the video tag.
                                </video>
                            </div>
                        }
                        {mediaOverlayMode === LOADING_OVERLAY_MODE &&
                            <div id="loading-player-wrapper">
                                Converting...
                            </div>
                        }
                    </div>
                </div>
            }
        </div>
    )
}

export default ChatWindow;