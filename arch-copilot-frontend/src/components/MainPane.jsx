import { TbWindowMaximize } from "react-icons/tb";
import { FaStar } from "react-icons/fa";
import { PiAtomFill } from "react-icons/pi";
import { GoDot, GoDotFill } from "react-icons/go";
import '../style/MainPane.css';
import MenuDropdown from "./MenuDropdown";
import ChatWindow from "./ChatWindow";
import useAppStore from '../store/application/appStore';
import { APP_MENU, APP_NAME, MAX_SUGGESTIONS, MAX_SUGGESTIONS_PER_PAGE } from "../constants/app";

function MainPane() {
    const isSidePaneClose = useAppStore((state) => state.isSidePaneClose);
    const isSubHeaderOpen = useAppStore((state) => state.isSubHeaderOpen);
    const questionFavList = useAppStore((state) => state.questionFavList);
    const botToRespond = useAppStore((state) => state.botToRespond);
    const currentSuggestionPage = useAppStore((state) => state.currentSuggestionPage);

    const toggleIsSidePaneClose = useAppStore((state) => state.toggleIsSidePaneClose);
    const updateSelectedQuestion = useAppStore((state) => state.updateSelectedQuestion);
    const updateCurrentSuggestionPage = useAppStore((state) => state.updateCurrentSuggestionPage);

    return (
        <div id="mainpane-wrapper" className="full-vh">
            <div className="full-vh">
                <div id="mainpane-header">
                    <div id="app-name">
                        {isSidePaneClose ?
                            <div title="Show Topics History">
                                <TbWindowMaximize
                                    size={32}
                                    color={"white"}
                                    style={{ cursor: 'pointer' }}
                                    onClick={toggleIsSidePaneClose}
                                />
                            </div>
                            :
                            null
                        }
                        <span>{APP_NAME}</span>
                        {/* <PiAtomFill
                            size={26}
                        /> */}
                    </div>
                    {/* <MenuDropdown
                        menuOptions={APP_MENU}
                    /> */}

                </div>
                <div id="mainpane-subheader" className={`${isSubHeaderOpen ? 'open' : 'close'}`}>
                    <div id="mainpane-subheader-tab">
                        <div className="active">
                            <span>Questions</span>
                            <span>
                                <FaStar
                                    size={15}
                                    color={"white"}
                                />
                            </span>
                        </div>
                    </div>
                    <div id="question-suggestion-wrapper">
                        <div id="question-suggestions">
                            {questionFavList && questionFavList.slice((currentSuggestionPage * MAX_SUGGESTIONS_PER_PAGE), (currentSuggestionPage * MAX_SUGGESTIONS_PER_PAGE) + MAX_SUGGESTIONS_PER_PAGE).map((x, ind) => (
                                <div key={`question-suggestion-${ind}`} title={x.searchText} onClick={() => !botToRespond && updateSelectedQuestion(x.searchText)} >
                                    <div>{x.searchText}</div>
                                </div>
                            ))}
                        </div>
                        <div id="suggestion-carousel-controller">
                            {[...Array(MAX_SUGGESTIONS / MAX_SUGGESTIONS_PER_PAGE)].map((_, ind) =>
                                ind !== currentSuggestionPage ?
                                    (
                                        <GoDot
                                            key={ind}
                                            size={25}
                                            color={"orange"}
                                            onClick={() => updateCurrentSuggestionPage(ind)}
                                        />
                                    )
                                    :
                                    (
                                        <GoDotFill
                                            key={ind}
                                            size={25}
                                            color={"orange"}
                                            onClick={() => updateCurrentSuggestionPage(ind)}
                                        />
                                    )
                            )}
                        </div>
                    </div>
                </div>
                <div id="mainpane-chatwindow">
                   <ChatWindow />
                </div>
            </div>
        </div>
    )
}
export default MainPane;