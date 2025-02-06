import { create } from "zustand";
import { getChatHistoryFromStorage } from "../localStorage/chatHistory";
import { buildS3GetUrl, generateUUID, getCurrentDate, getCurrentTs, getPeriod, timeout } from "../../utils/common";
import { AUDIO_OVERLAY_MODE, COMPLEX, ERROR_BOT_RESPONSE, LOADING_OVERLAY_MODE, MAX_SUGGESTIONS, NO_OVERLAY_MODE, SIMPLE, VIDEO_OVERLAY_MODE } from "../../constants/app";
import { getQuestionFavListFromStorage } from "../localStorage/favQuestions";
import { getFromBlobUrlStore, pushToBlobUrlStore } from "../../utils/blob";
import { getAllAvatarsApi, getAllVoicesApi, getAudioUrlForText, getFilePathApi, getResponseForQuestionApi, getVideoUrlForText, uploadFileToS3Api } from "../../utils/request";
import { destroyAllStorage } from "../localStorage/connector";

const initialState = {
    isSidePaneClose: false,
    isSubHeaderOpen: false,
    botToRespond: false,     
    currentSuggestionPage: 0,
    mediaOverlayMode: NO_OVERLAY_MODE,
    audioUrl: "",
    videoUrl: "",
    voiceId: "",
    avatarId: "",
    voiceList: [],
    avatarList: [],
    showVoiceList: false,
    showAvatarList: false,
    searchText: "",
    selectedFile: null,
    selectedTopic: null,
    selectedQuestion: null,
    topicHistoryList: [],
    questionFavList: [],   
    chatItems: []
};

const appStore = (set, get) => ({
    ...initialState,

    toggleIsSidePaneClose: () => set((state) => ({ isSidePaneClose: !state.isSidePaneClose })),
    toggleIsSubHeaderOpen: () => set((state) => ({ isSubHeaderOpen: !state.isSubHeaderOpen })),
    updateBotToResponse: (flag) => set(() => ({ botToRespond: flag })),
    updateCurrentSuggestionPage: (value) => set(() => ({ currentSuggestionPage: value })),
    updateMediaOverlayMode: (value) => set(() => ({ mediaOverlayMode: value })),
    updateAudioUrl: (value) => set(() => ({ audioUrl: value })),
    updateVideoUrl: (value) => set(() => ({ videoUrl: value })),
    updateVoiceId: (value) => set(() => ({ voiceId: value })),
    updateAvatarId: (value) => set(() => ({ avatarId: value })),
    udpateShowVoiceList: (value) => set(() => ({ showVoiceList: value })),
    updateShowAvatarList: (value) => set(() => ({ showAvatarList: value })),
    updateSearchText: (value) => set(() => ({ searchText: value })),
    updateSelectedFile: (value) => set(() => ({ selectedFile: value })),
    updateSelectedTopic: (value) => set(() => ({ selectedTopic: value })),
    updateSelectedQuestion: (value) => set(() => ({ selectedQuestion: value })),
    updateTopicHistoryList: (value) => set(() => ({ topicHistoryList: value })),
    updateQuestionFavList: (value) => set(() => ({ questionFavList: value })),    
    updateChatItems: () => set(() => ({ chatItems: value })),

    syncTopicHistoryListFromStorage: () => {
        const chatHistoryFromStorage = getChatHistoryFromStorage();
        if (chatHistoryFromStorage && chatHistoryFromStorage.length > 0) {
            // Property period update
            let _topicHistoryList = chatHistoryFromStorage.map(chatHistory => {
                return {
                    ...chatHistory,
                    period: getPeriod(chatHistory.date)
                }
            });
            if (_topicHistoryList.findIndex(x => x.period === 'Today') === -1) {
                _topicHistoryList = [{
                    period: "Today",
                    date: getCurrentDate(),
                    topics: []
                }, ..._topicHistoryList];
            }
            set(() => ({
                topicHistoryList: _topicHistoryList
            }));
        }
    },
    syncQuestionFavListFromStorage: () => {
        let _questionFavList = [...new Array(MAX_SUGGESTIONS)].map(x => {
            return {
                searchText: ""
            }
        });
        const questionFavListFromStorage = getQuestionFavListFromStorage();
        if (questionFavListFromStorage !== null && questionFavListFromStorage.length > 0) {
            _questionFavList = [...questionFavListFromStorage, ..._questionFavList];
            _questionFavList.length = MAX_SUGGESTIONS;
        }
        
        set(() => ({
            questionFavList: _questionFavList
        }));
    },
    onTopicClick: (topicId) => {
        set((state) => {
            let _chatItems = [];
            for (let i = 0; i < state.topicHistoryList.length; i++) {
                for (let j = 0; j < state.topicHistoryList[i].topics.length; j++) {
                    if (state.topicHistoryList[i].topics[j].topicId === topicId)
                        _chatItems = state.topicHistoryList[i].topics[j].chatItems.map(x => {
                            return {
                                showMediaOptions: true,
                                ...x
                            }
                        });
                }
            }
            return {
                chatItems: _chatItems,
                selectedQuestion: null
            }
        });
    },
    addToQuestionFavList: (value) => {
        set((state) => {
            const index = state.questionFavList.findIndex(x => x && x.searchText === value);
            const _questionFavList = [
                index === -1 ? {
                    searchText: value
                } : state.questionFavList[index],
                ...state.questionFavList.filter((_, ind) => ind !== index)
            ];
            _questionFavList.length = MAX_SUGGESTIONS;

            return {
                questionFavList: _questionFavList
            }
        });
    },
    handleChatItemsUpdate: (value) => {
        set((state) => {
            if (value && value.length > 0) {
                if (state.selectedTopic === null) {
                    // If it is a new chat activation
                    let _topicHistoryList = [];
                    const newTopicObj = {
                        topicId: generateUUID(),
                        topic: value[0].message,
                        chatItems: value
                    };
                    if (state.topicHistoryList.length > 0) {
                        _topicHistoryList = state.topicHistoryList.map(x => {
                            if (x.period === "Today")
                                x.topics = [newTopicObj, ...x.topics];
                            return x;
                        });
                    }
                    else {
                        _topicHistoryList = [
                            {
                                period: "Today",
                                date: getCurrentDate(),
                                topics: [newTopicObj]
                            }
                        ];
                    }
                    return {
                        selectedTopic: newTopicObj.topicId,
                        topicHistoryList: _topicHistoryList,
                        chatItems: value
                    }
                }
                else {
                    // If it is old chat activation
                    let _topicHistoryList = [];
                    if (state.topicHistoryList &&
                        state.topicHistoryList[0] &&
                        state.topicHistoryList[0].topics &&
                        state.topicHistoryList[0].topics[0] &&
                        state.topicHistoryList[0].topics[0].topicId === state.selectedTopic
                    ) {
                        //Already prioritized
                        _topicHistoryList = [...state.topicHistoryList];
                        _topicHistoryList[0].topics[0].chatItems = value;
                    }
                    else {
                        let selectedTopicObj = null;
                        // Remove the selectedTopicObj from the topicHistory
                        _topicHistoryList = state.topicHistoryList.map(x => {
                            let topics = [];
                            for (let i = 0; i < x.topics.length; i++) {
                                if (x.topics[i].topicId === state.selectedTopic)
                                    selectedTopicObj = {
                                        ...x.topics[i],
                                        chatItems: value
                                    };
                                else
                                    topics.push(x.topics[i]);
                            }
                            return {
                                ...x,
                                topics
                            }
                        });
                        // Add it to the first
                        if (selectedTopicObj)
                            _topicHistoryList[0].topics = [selectedTopicObj, ..._topicHistoryList[0].topics];
                    }
                    return {
                        topicHistoryList: _topicHistoryList,
                        chatItems: value
                    }
                }
            }
            else {
                return {
                    selectedTopic: null,
                    chatItems: value
                }
            }
        });
    },
    getAllVoices: async () => {
        const apiResponse = await getAllVoicesApi();
        let _voiceList = [];
        let _voiceId = "";
        if(apiResponse?.status) {
            _voiceList = apiResponse.data?.map((voice, ind) => {
                if(ind === 0) {
                   // _voiceId = voice.voice_id;
                   _voiceId = "Danielle";
                }
                return voice;
            });
        }
        else {
            _voiceList = [];
        }
        set(() => ({
            voiceList: _voiceList,
            voiceId: _voiceId
        }));       
    },
    getAllAvatars: async () => {
        const apiResponse = await getAllAvatarsApi();
        let _avatarList = [];
        let _avatarId = "";
        if(apiResponse?.status) {
            _avatarList = apiResponse.data?.map((avatar, ind) => {
                if(ind === 0) {
                    //_avatarId = avatar.avatar_name;
                    _avatarId = "man-avatar1"
                }
                return avatar;
            });
        }
        else {
            _avatarList = [];
        }
        set(() => ({
            avatarList: _avatarList,
            avatarId: _avatarId
        }));
    },
    openAudioMediaOverlay: (type, message) => {
        let text = "";            
        if (type === SIMPLE)
            text = message;
        else if (type === COMPLEX)
            text = message.text;
        
        const blobUrl = getFromBlobUrlStore(AUDIO_OVERLAY_MODE, text);
        if (blobUrl) {
            if (blobUrl !== "...") {
                set(() => ({
                    mediaOverlayMode: AUDIO_OVERLAY_MODE,
                    audioUrl: blobUrl
                }));
            }
            else {
                set(() => ({
                    mediaOverlayMode: LOADING_OVERLAY_MODE
                }));
            }
        }
        else {
            get().textToAudioApi(true, text);
        }    
    },
    textToAudioApi: async (showOverlay, text) => {        
        pushToBlobUrlStore(AUDIO_OVERLAY_MODE, text, "...");
        showOverlay && set(() => ({ mediaOverlayMode: LOADING_OVERLAY_MODE }));
        const apiResponse = await getAudioUrlForText({
            llm_answer_text: text,
            voice_id: get().voiceId
        });
        if (apiResponse?.status) {
            const audioBlob = await apiResponse.data.blob();
            const audioUrl = URL.createObjectURL(audioBlob);
            pushToBlobUrlStore(AUDIO_OVERLAY_MODE, text, audioUrl);
            if (showOverlay || get().mediaOverlayMode === LOADING_OVERLAY_MODE) {
                set(() => ({ 
                    mediaOverlayMode: AUDIO_OVERLAY_MODE,  
                    audioUrl 
                }));
            }
        }
        else {
            pushToBlobUrlStore(AUDIO_OVERLAY_MODE, text, null);
            showOverlay && get().closeMediaOverlayContent();
        }
    },
    openVideoMediaOverlay: (type, message) => {
        let text = "";            
        if (type === SIMPLE)
            text = message;
        else if (type === COMPLEX)
            text = message.text;
        
        const blobUrl = getFromBlobUrlStore(VIDEO_OVERLAY_MODE, text);
        if (blobUrl) {
            if (blobUrl !== "...") {
                set(() => ({
                    mediaOverlayMode: VIDEO_OVERLAY_MODE,
                    videoUrl: blobUrl
                }));
            }
            else {
                set(() => ({
                    mediaOverlayMode: LOADING_OVERLAY_MODE
                }));
            }
        }
        else {
            get().textToVideoApi(true, text);
        }    
    },
    textToVideoApi: async (showOverlay, text) => {        
        pushToBlobUrlStore(VIDEO_OVERLAY_MODE, text, "...");
        showOverlay && set(() => ({ mediaOverlayMode: LOADING_OVERLAY_MODE }));
        const apiResponse = await getVideoUrlForText({
            llm_answer_text: text,
            voice_id: get().voiceId,
            avatar_name: get().avatarId
        });
        if (apiResponse?.status) {
            const videoBlob = await apiResponse.data.blob();
            const videoUrl = URL.createObjectURL(videoBlob);
            pushToBlobUrlStore(VIDEO_OVERLAY_MODE, text, videoUrl);
            if (showOverlay || get().mediaOverlayMode === LOADING_OVERLAY_MODE) {
                set(() => ({ 
                    mediaOverlayMode: VIDEO_OVERLAY_MODE,  
                    videoUrl 
                }));
            }
        }
        else {
            pushToBlobUrlStore(VIDEO_OVERLAY_MODE, text, null);
            showOverlay && get().closeMediaOverlayContent();
        }
    },
    closeMediaOverlayContent: () => {
        set(() => ({
            audioUrl: "",
            videoUrl: "",
            mediaOverlayMode: NO_OVERLAY_MODE
        }));
    },    
    handleBotError: (msg) => {
       get().insertBotResponse(COMPLEX, { text: msg ? msg : ERROR_BOT_RESPONSE }, true);
    },
    insertBotResponse: async (type, response, showMediaOptions = true) => {
        switch (type) {
            case SIMPLE:
                await timeout(0);
                get().handleChatItemsUpdate([...get().chatItems, {
                    message: "...",
                    uploadDoc: null,
                    type: SIMPLE,
                    isBot: true,
                    ts: getCurrentTs(),
                    showMediaOptions
                }]);
                break;
            case COMPLEX:
                set(() => ({ botToRespond: false}));
                get().handleChatItemsUpdate(get().chatItems.map((x, ind) => {
                    if (ind === get().chatItems.length - 1) {
                        return {
                            message: response,
                            uploadDoc: null,
                            type: COMPLEX,
                            isBot: true,
                            ts: getCurrentTs(),
                            showMediaOptions
                        }
                    }
                    else {
                        return x;
                    }
                }));
                break;
            default:
                break;
        }
    },
    onSearch: (uploadedFile) => {
        const searchedInput = get().searchText.trim();
        const chatItemToBeUpdated = {
            message: searchedInput,
            uploadDoc: uploadedFile && { name: uploadedFile.name, size: uploadedFile.size },
            type: SIMPLE,
            isBot: false,
            ts: getCurrentTs(),
            showMediaOptions: true
        };
        const chatItemsLoadingResponse = {
            message: "...",
            uploadDoc: null,
            type: SIMPLE,
            isBot: true,
            ts: getCurrentTs()
        }
        get().handleChatItemsUpdate([...get().chatItems, chatItemToBeUpdated, chatItemsLoadingResponse]);
        get().triggerApiCalls(searchedInput, uploadedFile);
    },
    triggerApiCalls: async (searchedInput, uploadedFile) => {
        set(() => ({ botToRespond: true }));
        if (uploadedFile) {
            const apiResponse = await getFilePathApi({ fileName: uploadedFile.name, fileContent: '' });
            if (apiResponse.status && apiResponse.data && apiResponse.data["url"] && apiResponse.data["url"]["url"] && apiResponse.data["url"]["fields"]) {
                const formData = new FormData();
                Object.entries(apiResponse.data["url"]["fields"]).forEach(function ([key, val]) {
                    formData.append(key, val);
                });
                formData.append("file", uploadedFile)
                const apiResponse1 = await uploadFileToS3Api(apiResponse.data["url"]["url"], formData);
                if (apiResponse1.status) {
                    get().triggerResponse(searchedInput, buildS3GetUrl(apiResponse.data["url"]["url"], uploadedFile.name));
                }
                else
                    get().handleBotError();
            }
            else
                get().handleBotError();
        }
        else
            get().triggerResponse(searchedInput, "");
    },
    triggerResponse: async (userQuestion, addHocDocumentPath) => {
        const apiResponse = await getResponseForQuestionApi({ userQuestion, ...(addHocDocumentPath && { addHocDocumentPath }) });
        try {
            const reader = apiResponse.body.pipeThrough(new TextDecoderStream()).getReader();
            let imagePresent = false;
            let nonImageData = "";
            let imageData = "";
            while (true) {
                const { value, done } = await reader.read();
                if (done) {
                    if (imagePresent) {
                        imageData = imageData.replace(new RegExp("'", 'g'), '"');
                    }
                    /* Insert Bot Response when streaming is done */
                    get().insertBotResponse(COMPLEX, {
                        text: nonImageData,
                        ...(imageData && { images: JSON.parse(imageData) })
                    }, true);
                    get().textToAudioApi(false, nonImageData);
                    get().textToVideoApi(false, nonImageData);
                    break;
                }
                const imageDataInd = value.indexOf("[{'type': 'image', '");
                if (imageDataInd === -1) {
                    if (imagePresent) {
                        imageData += value;
                    }
                    else {
                        nonImageData += value;
                    }
                }
                else {
                    imagePresent = true;
                    nonImageData += value.substring(0, imageDataInd);
                    imageData += value.substring(imageDataInd);
                }
                /* Insert Bot Response while streaming */
                get().insertBotResponse(COMPLEX, {
                    text: nonImageData,
                    images: []
                }, false);
            }
        }
        catch(err) {
            get().handleBotError();
        }
    },
    reset: () => {
        destroyAllStorage();
        set(() => ({
            ...initialState
        }));
    }
});

const useAppStore = create(appStore);

export default useAppStore;