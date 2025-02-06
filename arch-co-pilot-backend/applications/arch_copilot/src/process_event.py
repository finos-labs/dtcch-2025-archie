import json


 
class ProcessEvent():
    def __init__(self,config, event, event_type):
        self.config = config
        self.event = event
        self.event_type = event_type
        self.validate_event_format()


    @property
    def headers(self):
        return self.event.get('headers', {})
        
    @headers.setter
    def headers(self, value):
        if not isinstance(value, dict):
            raise ValueError("Name must be a dictionary")
        self.headers = value

    @property
    def session_id(self):
        return self.headers.get('sessionid', {})
        
    @session_id.setter
    def session_id(self, value):
        if not isinstance(value, str):
            raise ValueError("Name must be a string")
        self.session_id = value

    @property
    def user_id(self):
        return self.headers.get('userid', {})
        
    @user_id.setter
    def user_id(self, value):
        if not isinstance(value, str):
            raise ValueError("Name must be a string")
        self.user_id = value

    @property
    def body(self):
        body = self.event.get('body')
        if isinstance(body, dict):
            return body
        else:
            return json.loads(self.event.get('body'))
        
    @body.setter
    def body(self, value):
        if not isinstance(value, dict):
            raise ValueError("Name must be a dictionary")
        self.body = value

    @property
    def user_question(self):
        try:
            return self.body['userQuestion']
        except (json.JSONDecodeError, KeyError) as e:
            return response(400, {"error": f"missing user question in body: {str(e)}"},self.body)
        
    @user_question.setter
    def user_question(self, value):
        if not isinstance(value, str):
            raise ValueError("Name must be a string")
        self.user_question = value
        
    @property
    def llm_answer_text(self):
        if self.event_type == 'audio_file_answer' or self.event_type == 'video_file_answer':
            return self.body['llm_answer_text']
        else:
            return None
        
    @llm_answer_text.setter
    def llm_answer_text(self, value):
        if not isinstance(value, str):
            raise ValueError("llm_answer_text must be a string")
        self.llm_answer_text = value

    @property
    def voice_id(self):
        if self.event_type == 'audio_file_answer' or self.event_type == 'video_file_answer':
            return self.body['voice_id']
        else:
            return None
        
    @voice_id.setter
    def voice_id(self, value):
        if not isinstance(value, str):
            raise ValueError("voice_id must be a string")
        self.voice_id = value


    @property
    def avatar_name(self):
        if self.event_type == 'video_file_answer':
            return self.body['avatar_name']
        else:
            return None
        
    @avatar_name.setter
    def avatar_name(self, value):
        if not isinstance(value, str):
            raise ValueError("avatar_name must be a string")
        self.avatar_name = value

    @property
    def adhoc_document_path(self):
        return self.body.get('addHocDocumentPath', None)
        
    @adhoc_document_path.setter
    def adhoc_document_path(self, value):
        if not isinstance(value, str):
            raise ValueError("Name must be a string")
        self.adhoc_document_path = value

    def format_response(self, status_code, message):
        return {
                'statusCode': status_code,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type, eventDatetime, sessionId, userId, conversationTopic'
                },
                'body': json.dumps({
                    'message': message,
                    'event': self.event
                })
            }

    def validate_event_header(self):
        # Define the required headers
        required_headers = self.config['event_details']['required_headers']
        missing_headers = []

        if 'headers' not in self.event or self.headers == {}:
            return self.format_response(400, f'Missing headers')

        if self.headers:
            missing_headers = [header for header in required_headers if header not in self.headers]

        if missing_headers:
            return self.format_response(400, f'Missing headers: {", ".join(missing_headers)}')
        
        return False

    def validate_event_body(self):
        # Check if request body is present
        if 'body' not in self.event or self.body is None:
            return self.format_response(400, 'Request body is missing')

        if self.event_type == 'question_answer':
            if 'userQuestion' not in self.body or self.user_question is None:
                return self.format_response(400, f'Missing user question')

        if self.event_type == 'audio_file_answer' or self.event_type == 'video_file_answer':
            if 'llm_answer_text' not in self.body or self.llm_answer_text is None:
                return self.format_response(400, f'Missing llm answer text')
            if 'voice_id' not in self.body or self.voice_id is None:
                return self.format_response(400, f'Missing voice_id')

        if self.event_type == 'audio_file_answer':
            if 'avatar_name' not in self.body or self.avatar_name is None:
                return self.format_response(400, f'Missing avatar name')
            
        return False

    def validate_event_format(self):
    
        event_invalid = self.validate_event_header()
        if event_invalid:
            return event_invalid

        event_invalid = self.validate_event_body()
        if event_invalid:
            return event_invalid

        return False
        
