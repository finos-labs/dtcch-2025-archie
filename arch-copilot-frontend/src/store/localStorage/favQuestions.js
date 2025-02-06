import { FAV_QUESTIONS } from "../../constants/localStorage";
import { getFromStorage, setToStorage } from "./connector";

/*
    [
        {
            searchText: ""
        }
    ] 
*/

export const setQuestionFavListToStorage = (value) => setToStorage(FAV_QUESTIONS, value);

export const getQuestionFavListFromStorage = () => getFromStorage(FAV_QUESTIONS);