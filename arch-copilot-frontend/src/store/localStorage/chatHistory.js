import { CHAT_HISTORY } from "../../constants/localStorage";
import { getFromStorage, setToStorage } from "./connector";

/* 
     [
        {
            date: "mm/dd/yyyy",
            topics: [
                {
                    topicId: "",
                    topic: "",
                    chatItem: []
                }
            ]
        }
    ] 
*/

export const getChatHistoryFromStorage = () => getFromStorage(CHAT_HISTORY);

export const setChatHistoryToStorage = (value) => setToStorage(CHAT_HISTORY, value);