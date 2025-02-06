import { AUDIO_OVERLAY_MODE, VIDEO_OVERLAY_MODE } from "../constants/app";

let blobUrlStore = [];
export const pushToBlobUrlStore = (type, text, blobUrl) => {
    const ind = blobUrlStore.findIndex(x => x.text === text);
    if(ind === -1){
        blobUrlStore.push({
            text,
            AUDIO_OVERLAY_MODE: type === AUDIO_OVERLAY_MODE ? blobUrl: null,
            VIDEO_OVERLAY_MODE: type === VIDEO_OVERLAY_MODE ? blobUrl: null
        })
    }
    else {
        blobUrlStore[ind][type] = blobUrl;
    }
}
export const getFromBlobUrlStore = (type, text) => {
    const ind = blobUrlStore.findIndex(x => x.text === text);
    if(ind === -1) {
        return null;
    }
    else {
        return blobUrlStore[ind][type];
    }
}
export const resetBlobUrlStore = () => {
    blobUrlStore = [];
}