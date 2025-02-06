import { useEffect } from 'react';
import '../style/Homepage.css';
import SidePane from './SidePane';
import useAppStore from '../store/application/appStore';
import { setChatHistoryToStorage } from '../store/localStorage/chatHistory';
import { setQuestionFavListToStorage } from '../store/localStorage/favQuestions';
import MainPane from './MainPane';

function Homepage() {
    const topicHistoryList = useAppStore((state) => state.topicHistoryList);
    const questionFavList = useAppStore((state) => state.questionFavList);
    const selectedTopic = useAppStore((state) => state.selectedTopic);
    
    const syncTopicHistoryListFromStorage = useAppStore((state) => state.syncTopicHistoryListFromStorage);
    const syncQuestionFavListFromStorage = useAppStore((state) => state.syncQuestionFavListFromStorage);
    const onTopicClick = useAppStore((state) => state.onTopicClick);
    const getAllVoices = useAppStore((state) => state.getAllVoices);
    const getAllAvatars = useAppStore((state) => state.getAllAvatars);

    useEffect(() => {
        syncTopicHistoryListFromStorage();
        syncQuestionFavListFromStorage();
        getAllVoices();
        getAllAvatars();
    }, []);
    useEffect(() => {
        setChatHistoryToStorage(topicHistoryList);
    }, [topicHistoryList]);
    useEffect(() => {
        questionFavList.length > 0 && setQuestionFavListToStorage(questionFavList);
    }, [questionFavList]);
    useEffect(() => {
        if (selectedTopic !== null) {
            onTopicClick(selectedTopic);
        }
    }, [selectedTopic]);

    return (
        <div id="home-page-wrapper" className="full-vh">
            <SidePane />
            <MainPane />
        </div>
    )
}
export default Homepage;