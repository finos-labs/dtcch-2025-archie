import { useEffect, useRef } from 'react';
import { PiAtomFill, PiSpeakerSimpleHighBold } from "react-icons/pi";
import { CiFileOn } from "react-icons/ci";
import '../style/Chat.css';
import { copyToClipboard, getDateWithTime } from '../utils/common';
import { LuStar, LuCopy } from "react-icons/lu";
import { MdVideoLibrary } from "react-icons/md";
import useAppStore from '../store/application/appStore';

function Chat() {
    const chatItems = useAppStore((state) => state.chatItems);
    const botToRespond = useAppStore((state) => state.botToRespond);

    const addToQuestionFavList = useAppStore((state) => state.addToQuestionFavList);
    const openAudioMediaOverlay = useAppStore((state) => state.openAudioMediaOverlay);
    const openVideoMediaOverlay = useAppStore((state) => state.openVideoMediaOverlay);

    const messagesEndRef = useRef(null);
    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
    }
    useEffect(() => {
        scrollToBottom();
    }, [chatItems]);
    return (
        <div className="chat">
            <div className="chat-items-wrapper">
                {chatItems.map((x, ind) => {
                    return (
                        <div className={"chat-item " + (x.isBot ? "bot" : "")} key={"chatItem-" + ind} ref={ind === chatItems.length - 1 ? messagesEndRef : null}>
                            {x.isBot ?
                                (
                                    <div>
                                        <PiAtomFill
                                            size={25}
                                            color={"#0E5447"}
                                        />
                                    </div>
                                )
                                :
                                null
                            }
                            <div>
                                <div className="chat-msg">
                                    {x.type === 'complex' ?
                                        <div>
                                            <div>
                                                <div>{x.message.text}</div>
                                                {x.message.images && x.message.images.length > 0 && x.message.images.map((msgImg, msgImgInd) => {
                                                    return (
                                                        <div className="chat-msg-img-wrapper" key={`msg-img-${ind}-${msgImgInd}`}>
                                                            <div><img src={`data:image/png;base64, ${msgImg.source.data}`} alt={msgImg.source.data} /></div>
                                                        </div>
                                                    )
                                                })}
                                            </div>
                                        </div>
                                        :
                                        <div>{x.message}</div>
                                    }
                                    {x?.uploadDoc?.name &&
                                        <div className="uploaded-file" title={`File - ${x.uploadDoc.name} (Size - ${x.uploadDoc.size})`}>
                                            <div>
                                                <CiFileOn />
                                            </div>
                                            <div>
                                                {x.uploadDoc.name}
                                            </div>

                                        </div>}
                                    <div>

                                    </div>
                                </div>
                                <div className="chat-msg-ts">{getDateWithTime(x.ts)}</div>
                            </div>
                            <div className="chat-msg-icon-wrapper">
                                {!x.isBot && <div title="Add question to favorites">
                                    <LuStar
                                        size={18}
                                        color={"gray"}
                                        onClick={() => addToQuestionFavList(x.message)}
                                    />
                                </div>}
                                {<div title="Copy text">
                                    <LuCopy
                                        size={18}
                                        color={"gray"}
                                        onClick={() => copyToClipboard(x.type, x.message)}
                                    />
                                </div>}
                                <div title="Play Audio">
                                    {x.showMediaOptions && <PiSpeakerSimpleHighBold
                                        size={18}
                                        color={"gray"}
                                        onClick={() => openAudioMediaOverlay(x.type, x.message)}
                                    />}
                                </div>
                                <div title="Play Video">
                                    {x.showMediaOptions && <MdVideoLibrary
                                        size={18}
                                        color={"gray"}
                                        onClick={() => openVideoMediaOverlay(x.type, x.message)}
                                    />}
                                </div>
                            </div>
                        </div>
                    )
                })}
                {botToRespond &&
                    <div className="loading-icon">
                        <PiAtomFill
                            size={40}
                            color={"#0E5447"}
                        />
                    </div>
                }
            </div>
        </div>
    );
}

export default Chat;
