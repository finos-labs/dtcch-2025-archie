export const APP_NAME = "Archie CoPilot";
export const APP_MENU = [
    {
        "label": "Architecture Dashboards",
        "type": "dropdown",
        "sub": [
            {
                "label": "ARB",
                "type": "link",
                "link": "https://dtcc.sharepoint.com/sites/ITARB/Pages/1/index.aspx"
            },
            {
                "label": "Architecture Drift",
                "type": "link",
                "link": "https://app.powerbi.com/groups/c531f077-8c90-04c64-a949-746787b21802/reports/be716fbe-7346-498a-a506-2ee70b47e04c"
            },
            {
                "label": "Architecture Asset Inventory",
                "type": "link",
                "link": "https://app.powerbi.com/groups/c531f077-8c90-04c64-a949-746787b21802/reports/9aba3340-07c6-4c44-8b90-39fe8a5d3490"
            },
            {
                "label": "Business Capability",
                "type": "link",
                "link": "https://app.powerbi.com/groups/c531f077-8c90-04c64-a949-746787b21802/reports/42c63165-1d5a-46c9-974d-619961151c96"
            }
        ]        
    },
    {
        "label": "COE Resources",
        "type": "dropdown",
        "sub": [
            {
                "label": "Quality Control",
                "type": "dropdown",
                "sub": [
                    {
                        "label": "Sharepoint",
                        "type": "link",
                        "link": "https://dtcc.sharepoint.com/sites/ITARB/Pages/1/index.aspx"
                    },
                    {
                        "label": "PowerBI",
                        "type": "link",
                        "link": "https://app.powerbi.com/groups/c531f077-8c90-04c64-a949-746787b21802/reports/be716fbe-7346-498a-a506-2ee70b47e04c"
                    }
                ]
               
            },
            {
                "label": "Web App standards",
                "type": "dropdown",
                "sub": [
                    {
                        "label": "Sharepoint2",
                        "type": "link",
                        "link": "https://dtcc.sharepoint.com/sites/ITARB/Pages/1/index.aspx"
                    },
                    {
                        "label": "PowerBI2",
                        "type": "link",
                        "link": "https://app.powerbi.com/groups/c531f077-8c90-04c64-a949-746787b21802/reports/be716fbe-7346-498a-a506-2ee70b47e04c"
                    }
                ]
               
            }
        ]
    }
];
export const FAVORITE_TOPIC = "TOPICS";
export const FAVORITE_QUESTION = "QUESTIONS";


export const SIMPLE = "simple";
export const COMPLEX = "complex";

export const MAX_SUGGESTIONS = 25;
export const MAX_SUGGESTIONS_PER_PAGE = 5;
export const MAX_RETRY_ATTEMPTS = 2;
export const RETRY_INTERVAL = 10 * 1000; //10s

export const NO_OVERLAY_MODE = "NO_OVERLAY_MODE";
export const LOADING_OVERLAY_MODE = "LOADING_OVERLAY_MODE";
export const AUDIO_OVERLAY_MODE = "AUDIO_OVERLAY_MODE";
export const VIDEO_OVERLAY_MODE = "VIDEO_OVERLAY_MODE";

export const ERROR_BOT_RESPONSE = `Oops Something went wrong.`;

export const MALE_GENDER = 'Male';
export const FEMALE_GENDER = 'Female';