import json
import boto3
import uuid
import pandas as pd
import datetime
import json 
import re
import itertools
from common.embbed_docs import MultimodalEmbeding
from common.llm_prompts import LLMPrompts
from common.utils import timeit
    
 
class PrepareSemanticSearch():
    def __init__(self, bedrock_runtime, config, model_id=None):
        """
        class to prepare details for embedding to get acurate semantic searches
        """
        self.bedrock_runtime = bedrock_runtime
        if model_id:
            self.model_id = model_id
        else:
            self.model_id = config['models']['primary_model']
        self.llm_prompt = LLMPrompts(bedrock_runtime, config)
        self.m_embbeding = MultimodalEmbeding(bedrock_runtime, config)
        
    
    def get_question_instructions(self, category, chunk_number, question_number ,keywords_number, context):
        keywords_list = []
        for i in range(keywords_number):
            keywords_list.append(f"key word{i + 1}")
            
        keywords_list = str(keywords_list).replace("'",'"')

        response_format_list = []
        for i in range(question_number):
            res_format = '{' + f'"chunk_number": chunk_number, "question_number": {i+1},' 
            res_format =  res_format + f'"question": "question {i+1} text", "answer": "answer {i+1}", "key_words": {keywords_list}' + '\}'
            response_format_list.append(res_format) 
         
        #response_format = f"""{str(response_format_list).replace("'{",'{').replace("\\\}'",'}')}"""
        response_format = f"""{str(response_format_list).replace("'{",'{').replace("}'",'}')}""" 
        print(f"get_question_instructions response_format {response_format}")


        prompt_instructions = f"""1. give me {question_number} questions/answers and key words about this page \n
                                      2. give me exactly {keywords_number} key words for each question/answer, first key word should be the {category} in this document \n
                                      2. chunk_number in the response json is {chunk_number} .\n
                                      2. The questions should only be based on text context <context>{context}</context> .\n
                                      3. RETURN a valid list of JSON records in the following format <response>{response_format}</response> \n
                                      3. the response should return a list of JSON records like in <response>{response_format}</response> .\n
                                      3. DO NOT INCLUDE double or single quotes in Answer.\n
                                      4. make sure to enclose keys and values of json in quote \n
                                      4. question number is an integer, question and answer are strings.
                                  """
        
        return prompt_instructions
        
    def get_keypoints_instructions(self, category, chunk_number ,keypoints_number, context):
        keypoints_list = []
        for i in range(keypoints_number):
            keypoints_list.append(f"key point{i + 1}")
            
        keypoints_list = str(keypoints_list).replace("'",'"')
        
        response_format = '{' + f'"chunk_number": chunk_number,  "key_points":  {keypoints_list}' + '}'
                   
        prompt_instructions = f"""1. give me {keypoints_number} key points in very short sentences about this document, include {category} key word in each point\n
                                      2. sentences should contain no more than 20 words\n
                                      3. The key points should only be based on text context <context>{context}</context>.\n
                                      3. chunk_number in the response json is {chunk_number} .\n
                                      4. RETURN a valid JSON in the following format <response>{response_format}</response> \n
                                      4. the response should return a JSON like in <response>{response_format}</response> .\n
                                      4. Key_points key is of type list of strings. \n
                                      4. Make sure to add quotes to key points in list of key_points .\n
                                      4. DO NOT INCLUDE double or single quotes in Answer.\n
                                      4. make sure to enclose keys and values of json in quote \n
                                      5. Do not repeat key points, give unique key points.
                                  """ 
        
        return prompt_instructions
    
        
    @timeit 
    def generate_doc_page_questions(self, doc_context, category):
        print(f"generate_doc_questions executing")
        page_format = """[{'page_indx': page_indx, 
                         'chunk_number': chunk_number, 
                         'page_text': page_text,
                         'num_pages': num_pages)}]"""
        responses = []                 
        for page in doc_context:
            if len(page['page_text']) < 10:
                continue
            prompt_instructions = self.get_question_instructions(category, page['chunk_number'], 3 ,5, page['page_text'])
            response_prompt = self.llm_prompt.execute_text_prompt(prompt_instructions)
            response_prompt = self.clean_list_prompt_response(response_prompt, 'chunk_number')
            
            #print(f"generate_doc_page_questions response_prompt \n {response_prompt}")
            responses.append(response_prompt)
        return responses
     
    
    def embedd_chunk(self, chunk_number,text_type,text):
        chunk_dtl = {} 
        chunk_dtl['chunk_number'] = int(chunk_number)
        chunk_dtl['text_type'] = text_type
        chunk_dtl['text_description'] = text
        chunk_dtl['embedding_type'] = 'text'
    
        chunk_dtl['embedding_id'] = str(uuid.uuid4())
        chunk_dtl['multimodal_embedding'] = self.m_embbeding.get_titan_embedding(self.m_embbeding.remove_stop_words(text), None)
        return chunk_dtl
    
    def embedd_question(self,response):
        chunk_dtls = []
        #print(f"embedd_questions response \n {response} ")
        chunk_dtl = self.embedd_chunk(response['chunk_number'],'question',response['question'])
        chunk_dtls.append(chunk_dtl)
        chunk_dtl = self.embedd_chunk(response['chunk_number'],'answer',response['answer'])
        chunk_dtls.append(chunk_dtl)
        text = ' '.join(response['key_words']).replace('-','')
        chunk_dtl = self.embedd_chunk(response['chunk_number'],'key_words',text)
        chunk_dtls.append(chunk_dtl)
            
        return chunk_dtls
        
        
    def flatten_list(self, mixed_list):
        if any(isinstance(i, list) for i in mixed_list):
            return list(itertools.chain(*mixed_list))
        else:
            return mixed_list

        
    def embedd_doc_questions(self,response_questions):
        chunk_dtls = []
        #print(f"embedd_doc_questions response_questions \n {response_questions} ")
        for responses in response_questions:
            #print(f"embedd_doc_questions responses \n {responses} ")
            if len(responses) > 1:
                try:
                    responses = json.loads(responses)
                    for response in responses:
                        #print(f"embedd_doc_questions response \n {response} ")
                        chunk_dtls.append(self.embedd_question(response))
                except:
                    continue
            else:
                chunk_dtls.append(self.embedd_question(responses))
            
        return self.flatten_list(chunk_dtls)
    
    def remove_extra_spaces_in_response(self, response_prompt):
        response_prompt = re.sub(r'\s*,\s*', ', ', response_prompt)  # Fix spacing after commas
        response_prompt = re.sub(r'\s*}\s*', '}', response_prompt)  # Remove spaces after closing curly braces
        response_prompt = re.sub(r'\s*{\s*', '{', response_prompt)  # Remove spaces after opening curly braces
        response_prompt = re.sub(r'\s*\[\s*', '[', response_prompt)  # Remove spaces after opening [ braces
        response_prompt = re.sub(r'\s*]\s*', ']', response_prompt)  # Remove spaces after closing ] braces
        response_prompt = response_prompt.replace("'","").replace('"chunk_number"', '{"chunk_number"').replace('"]','"]}').replace('{{','{').replace('}}','}').replace('\n','')
        response_prompt = response_prompt.replace('"question": ', '"question": "').replace(', "answer": ', '", "answer": "').replace(', "key_words"','", "key_words"')
        response_prompt = response_prompt.replace('""','"')
        return response_prompt
         
        
    def clean_list_prompt_response(self, response_prompt, start_keyword):
        response_prompt = self.remove_extra_spaces_in_response(response_prompt)
        response_prompt = response_prompt.replace(']]',']}]').replace('] ]',']}]')
        #print(f"clean_prompt_response response_prompt.find('[')  {type(response_prompt)} ; {response_prompt.find('[')} \n{response_prompt}")
        resp_start_pos0 = response_prompt.find('[')
        resp_start_pos1 = response_prompt.find('{')
        resp_start_pos2 = response_prompt.find(f'"{start_keyword}')
        if resp_start_pos1 < resp_start_pos0:
           response_prompt = '[' + response_prompt[resp_start_pos1:] 
        elif resp_start_pos2 < resp_start_pos1:
           response_prompt = '[{' + response_prompt[resp_start_pos2:]
        elif resp_start_pos0 != 0:
            response_prompt = response_prompt[resp_start_pos0:]
        else:
           response_prompt = response_prompt.strip()
           
        return response_prompt
        
    
    def clean_prompt_response(self, response_prompt, start_keyword):
        response_prompt = self.remove_extra_spaces_in_response(response_prompt)
        #print(f"clean_prompt_response response_prompt.find  {type(response_prompt)} ; {response_prompt.find('{')} \n{response_prompt}")
        resp_start_pos1 = response_prompt.strip().find('{')
        resp_start_pos2 = response_prompt.strip().find(f'"{start_keyword}')
        if resp_start_pos2 < resp_start_pos1:
           response_prompt = '{' + response_prompt[resp_start_pos2:]
        elif resp_start_pos1 != 0:
            response_prompt = response_prompt[resp_start_pos1:]
        else:
           response_prompt = response_prompt.strip()
           
        #print(f"clean_prompt_response response_prompt2  {type(response_prompt)} \n {response_prompt}")   
        return response_prompt
        
    @timeit 
    def generate_doc_page_keypoints(self, doc_context, category):
        page_format = """[{'page_indx': page_indx, 
                         'chunk_number': chunk_number, 
                         'page_text': page_text,
                         'num_pages': num_pages)}]"""
        responses = []
        for page in doc_context:
            if len(page['page_text']) < 10:
                continue
            #print(f"test of page \n {page['page_text']}")                 
            prompt_instructions = self.get_keypoints_instructions(category, page['chunk_number'] ,3, page['page_text'])
            response_prompt = self.llm_prompt.execute_text_prompt(prompt_instructions)
            response_prompt = self.clean_prompt_response(response_prompt, 'chunk_number')
            
            #print(f"generate_doc_page_keypoints response_prompt \n {response_prompt}")
            responses.append(response_prompt)
        return responses
            
    def embedd_doc_keypoints(self,response_questions):
        chunk_dtls = []

        #print(f"embedd_doc_keypoints response_questions \n {response_questions}")
        for response in response_questions:
            #print(f"embedd_doc_keypoints len(response) {len(response)} , responses \n {response} ")
            response = json.loads(response)
            #print(f"embedd_doc_keypoints type(response) \n {type(response)}")
            for key_point in response['key_points']:
                #print(f"embedd_doc_keypoints key_point \n {key_point} ")
                chunk_dtls.append(self.embedd_chunk(response['chunk_number'],'key_point',key_point))
                
        return self.flatten_list(chunk_dtls)
      
           
    @timeit 
    def generate_doc_chunk_questions(self, accumulated_chunks, category):
        chunk_format = """[{'chunk_number': chunk_number, 
                           'accumulated_text': accumulated_text, 
                           'accumulated_images': accumulated_images}]"""
        responses = []
        for chunk in accumulated_chunks:
            #print(f"test of chunk \n {chunk['accumulated_text']}")  
            #print(f"test of text chunk len {len(chunk['accumulated_text'])}")
            if len(chunk['accumulated_text']) < 10:
                continue 
            prompt_instructions = self.get_question_instructions(category, chunk['chunk_number'], 4 ,7,  chunk['accumulated_text'])
            response_prompt = self.llm_prompt.execute_text_prompt(prompt_instructions)
            response_prompt = self.clean_list_prompt_response(response_prompt, 'chunk_number')
            
            #print(f"generate_doc_chunk_questions response_prompt \n {response_prompt}")
            responses.append(response_prompt)
        return responses
          
    @timeit 
    def generate_doc_chunk_keypoints(self, accumulated_chunks, category):
        chunk_format = """[{'chunk_number': chunk_number, 
                           'accumulated_text': accumulated_text, 
                           'accumulated_images': accumulated_images}]"""
        responses = []
        for chunk in accumulated_chunks:
            if len(chunk['accumulated_text']) < 10:
                continue
            prompt_instructions = self.get_keypoints_instructions(category, chunk['chunk_number'], 4, chunk['accumulated_text'])
            response_prompt = self.llm_prompt.execute_text_prompt(prompt_instructions)
            #print(f"generate_doc_chunk_keypoints response_prompt \n {response_prompt}")
            response_prompt = self.clean_prompt_response(response_prompt, 'chunk_number')
            
            #print(f"generate_doc_chunk_keypoints response_prompt  {type(response_prompt)} \n {response_prompt}") 
            responses.append(response_prompt)

            #print(f"generate_doc_chunk_keypoints 1 response_prompt \n {response_prompt}")    
            
        return responses
            
    @timeit 
    def generate_doc_questions(self, doc_context, category):
        responses = []
        response_format = """ [{"category": "category","question_number": "question number", "question": "question text", "answer": "answer", "key_words": ["key word1","key word2","key word3", "key word4","key word5","key word6"]}]"""              
        size_doc = len(doc_context) / 3 
        for indx in range(3):
            start_indx = int(size_doc * indx) + 1
            end_indx = int(size_doc * (indx + 1)) + 1
            print(f" procesing question/answers for text from {start_indx} to {end_indx}")
            text_chunk = doc_context[start_indx:end_indx]
            prompt_instructions = f"""1. give me exactly 10 questions about this document. \
                                      3. give me exactly 5 key words for each question/answer.\
                                         first key word should be the {category} in this document \
                                      5. return a valid json in the folowing response format <response>{response_format}</response>.
                                      5. the category in the dictionary is {category}. \
                                      6. The questions and key words should only be based on text context <context>{text_chunk}</context> .\
                                      7. so you wil give me 50 keywords in total .\
                                      8. the question should not return "this text".
                                      9. give a response based on context. \
                                      10. in the response do not add anything else besides json. \
                                      11. make sure to enclose keys and values of json in quote \
                                      12. question number is an integer, question and answer are strings.
                                  """
            response_prompt = self.llm_prompt.execute_text_prompt(prompt_instructions)
            responses.append(response_prompt)
        return responses
        
    
    @timeit 
    def generate_doc_summary(self, doc_context):
        responses = ''
        size_doc = len(doc_context) / 3 
        for indx in range(3):
            start_indx = int(size_doc * indx) + 1
            end_indx = int(size_doc * (indx + 1)) + 1
            print(f" procesing question/answers for text from {start_indx} to {end_indx}")
            text_chunk = doc_context[start_indx:end_indx]
            prompt_instructions = f"""1. give me a brief summary about this document. \
                                      2. The summary should not exceed 3 paragraphs.\
                                      3. The summary should only be based on text context <context>{text_chunk}</context> .\
                                      4. give a response based on context. 
                                  """
            response_prompt = self.llm_prompt.execute_text_prompt(prompt_instructions)
            response_prompt = re.sub(r'[\n\r\t]', ' ', response_prompt)
            responses += responses + ' ' + response_prompt
        
        return {'doc_summarization': responses.strip()}
            
            
    def generate_doc_embeddings(self, doc_context, category):
        response_questions = self.generate_doc_page_questions(doc_context, category)
        chunk_dtls = self.embedd_doc_questions(response_questions)
        response_questions = self.generate_doc_page_keypoints(doc_context, category)
        chunk_dtls.append(self.embedd_doc_keypoints(response_questions))
        response_questions = self.generate_doc_chunk_questions(accumulated_chunks, category)
        chunk_dtls.append(self.embedd_doc_questions(response_questions))
        response_questions = self.generate_doc_chunk_keypoints(accumulated_chunks, category) 
        chunk_dtls.append(self.embedd_doc_keypoints(response_questions))
        
        return chunk_dtls
        