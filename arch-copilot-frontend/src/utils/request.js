import { getAllAvatarsApiUrl, getAllVoicesApiUrl, getAudioUrlForTextApiUrl, getFilePathApiUrl, getResponseForQuestionApiUrl, getResponseForTextToSpeechApiUrl, getVideoUrlForTextApiUrl, saveTopicApiUrl } from '../constants/request';
import { getSessionId, getUserId } from '../store/localStorage/session';

export const getFilePathApi = async (payload) => {
    return await fetch(
            getFilePathApiUrl,
            {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    userid: getUserId(),
                    sessionid: getSessionId(),
                    eventdatetime: new Date()                    
                },
                body: JSON.stringify(payload)
            }
        )
        .then(res => {
            if (res.ok)
                return res.json();
            else
                throw new Error(`Request failed - ${res.status}`);
        })
        .then(res => {
            return {
                status: true,
                data: res,
                errorMsg: null
            }
        })
        .catch((err) => {
            return {
                status: false,
                data: null,
                errorMsg: err
            }
        });
}
export const uploadFileToS3Api = async (url, payload) => {
    return await fetch(
            url,
            {
                method: 'POST',
                headers: {
                    // 'Content-Type': 'multipart/form-data'           
                },
                body: payload
            }
        )
        .then(res => {
            if (res.ok)
                return {
                    status: true,
                    data: res,
                    errorMsg: null
                }
            else
                throw new Error(`Request failed - ${res.status}`);
        })
        .catch((err) => {
            return {
                status: false,
                data: null,
                errorMsg: err
            }
        });
}
export const getAllVoicesApi = async () => {
    return await fetch(
            getAllVoicesApiUrl,
            {
                method: 'GET',
                headers: {
                    userid: getUserId(),
                    sessionid: getSessionId(),
                    eventdatetime: 'TestEventDateTime',
                    conversationtopic: 'TestConversationTopic',
                    "Content-Type": "application/json"      
                },
            }
        )
        .then(res => {
            if (res.ok)
                return res.json();
            else
                throw new Error(`Request failed - ${res.status}`);
        })
        .then(res => {
            return {
                status: true,
                data: res,
                errorMsg: null
            }
        })
        .catch((err) => {
            return {
                status: false,
                data: null,
                errorMsg: err
            }
        });
}
export const getAllAvatarsApi = async () => {
    return await fetch(
            getAllAvatarsApiUrl,
            {
                method: 'GET',
                headers: {
                    userid: getUserId(),
                    sessionid: getSessionId(),
                    eventdatetime: 'TestEventDateTime',
                    conversationtopic: 'TestConversationTopic',
                    "Content-Type": "application/json"      
                },
            }
        )
        .then(res => {
            if (res.ok)
                return res.json();
            else
                throw new Error(`Request failed - ${res.status}`);
        })
        .then(res => {
            return {
                status: true,
                data: res,
                errorMsg: null
            }
        })
        .catch((err) => {
            return {
                status: false,
                data: null,
                errorMsg: err
            }
        });
}
export const getAudioUrlForText = async (payload) => {
    return await fetch(
            getAudioUrlForTextApiUrl,
            {
                method: 'POST',
                headers: {
                    userid: getUserId(),
                    sessionid: getSessionId(),
                    eventdatetime: 'TestEventDateTime',
                    conversationtopic: 'TestConversationTopic',
                    "Content-Type": "text/plain"      
                },
                body: JSON.stringify(payload)
            }
        )
        .then(res => {
            if (res.ok)
                return {
                    status: true,
                    data: res,
                    errorMsg: null
                }
            else {
                return {
                    status: false,
                    data: null,
                    errorMsg: res.status
                }
            }                
        })
        .catch((err) => {
            return {
                status: false,
                data: null,
                errorMsg: err
            }
        });
}
export const getVideoUrlForText = async (payload) => {
    return await fetch(
            getVideoUrlForTextApiUrl,
            {
                method: 'POST',
                headers: {
                    userid: getUserId(),
                    sessionid: getSessionId(),
                    eventdatetime: 'TestEventDateTime',
                    conversationtopic: 'TestConversationTopic',
                    "Content-Type": "application/json"      
                },
                body: JSON.stringify(payload)
            }
        )
        .then(res => {
            if (res.ok)
                return {
                    status: true,
                    data: res,
                    errorMsg: null
                }
            else
                return {
                    status: false,
                    data: null,
                    errorMsg: res.status
                }
        })
        .catch((err) => {
            return {
                status: false,
                data: null,
                errorMsg: err
            }
        });
}
export const getResponseForQuestionApi = async (payload) => {
    return await fetch(
            getResponseForQuestionApiUrl,
            {
                method: 'POST',
                headers: {
                    userid: getUserId(),
                    sessionid: getSessionId(),
                    eventdatetime: 'TestEventDateTime',
                    conversationtopic: 'TestConversationTopic',
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(payload)
            }
        )
        .then(res => {
            if (res.ok)
                return res;
            else
                throw new Error(`Request failed - ${res.status}`);
        })
        .catch((err) => {
            console.log("err", err);
            return {
                status: false,
                data: null,
                errorMsg: err.message
            }
        });
}
export const getResponseForTextToSpeechApi = async(payload) => {
    return await fetch(
        getResponseForTextToSpeechApiUrl,
        {
            method: 'POST',
            headers: {
                userid: getUserId(),
                sessionid: getSessionId(),
                eventdatetime: 'TestEventDateTime',
                conversationtopic: 'TestConversationTopic',
                "Content-Type": "application/json"
            },
            body: JSON.stringify(payload)
        }
    )
    .then(res => {
        if (res.ok)
            return res;
        else
            throw new Error(`Request failed - ${res.status}`);
    })
    // .then(res => {
    //     return {
    //         status: true,
    //         data: res,
    //         errorMsg: null
    //     }
    // })
    .catch((err) => {
        console.log("err", err);
        return {
            status: false,
            data: null,
            errorMsg: err.message
        }
    });
}
export const saveTopicApi = async (payload) => {
    return await fetch(
            saveTopicApiUrl,
            {
                method: 'POST',
                headers: {
                    userid: getUserId(),
                    sessionid: getSessionId(),
                    eventdatetime: new Date(),
                    conversationtopic: 'TestConversationTopic',
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(payload)
            }
        )
        .then(res => {
            if (res.ok)
                return res.json();
            else
                throw new Error(`Request failed - ${res.status}`);
        })
        .then(res => {
            return {
                status: true,
                data: res,
                errorMsg: null
            }
        })
        .catch((err) => {
            return {
                status: false,
                data: null,
                errorMsg: err
            }
        });
}