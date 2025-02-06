import { COMPLEX, SIMPLE } from "../constants/app";

export const generateUUID = () => Date.now();

export const timeout = (ms) => new Promise(resolve => setTimeout(resolve, ms));


export const buildS3GetUrl = (uploadUrl, fileName) => {
    return `s3://${uploadUrl.replace("https://", "").replace(".s3.amazonaws.com", "")}${fileName}`
}

export const getDate = (ts) => {
    const today = new Date(ts);
    return today.toLocaleDateString();
}

export const getDateWithTime = (ts) => {
    const today = new Date(ts);
    return today.toLocaleString().replace(",", "");
}

export const getCurrentTs = () => {
    return new Date().getTime();
}

export const getCurrentDate = () => {
    return getDate(getCurrentTs());
}

export const getPeriod = (dateInput) => {
    const dateToday = getCurrentDate();
    const dateYt = new Date();
    dateYt.setDate(dateYt.getDate() - 1);
    const dateYesterday = getDate(dateYt.getTime());
    if (dateInput === dateToday)
        return "Today";
    else if (dateInput === dateYesterday)
        return "Yesterday";
    else
        return dateInput;
}

export const copyToClipboard = (type, value) => {
    switch (type) {
        case SIMPLE:
            return navigator.clipboard.writeText(value)
        case COMPLEX:
            let textToBeCopied = "";
            textToBeCopied = value.text;
            return navigator.clipboard.writeText(textToBeCopied);
        default:
            return null;
    }
}   