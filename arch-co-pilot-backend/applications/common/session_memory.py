import json
import pandas as pd
from common.embbed_docs import MultimodalEmbeding
from common.pgvector_interface import PGVectorInterface
from common.llm_prompts import LLMPrompts
import re


class SessionMemory(PGVectorInterface):
    def __init__(self,bedrock_runtime, rds_client, config):
        super().__init__(rds_client, config) 
        self.m_embbeding = MultimodalEmbeding(bedrock_runtime, config)
        self.llm_prompt = LLMPrompts(bedrock_runtime, config)

    
    @property
    def session_memory_table(self):
        return  self.config['session_memory_table']['name']
        
    @session_memory_table.setter
    def session_memory_table(self, value):
        if not isinstance(value, str):
            raise ValueError("Name must be a string")
        self.session_memory_table = value
    @property
    def session_columns(self):
        return self.get_table_column_names(self.session_memory_table)
        
    @session_columns.setter
    def session_columns(self, value):
        if not isinstance(value, list):
            raise ValueError("Name must be a list")
        self.session_columns = value

    @property
    def session_length(self):
        return self.config['session_details']['session_length']
        
    @session_length.setter
    def session_length(self, value):
        if not isinstance(value, int):
            raise ValueError("Name must be an integer")
        self.session_length = value

    @property
    def max_images(self):
        return self.config['session_details']['max_images']
        
    @max_images.setter
    def max_images(self, value):
        if not isinstance(value, int):
            raise ValueError("Name must be an integer")
        self.max_images = value    

    @property
    def rag_response_hist_table(self):
        return  self.config['rag_response_hist_table']['name']
        
    @rag_response_hist_table.setter
    def rag_response_hist_table(self, value):
        if not isinstance(value, str):
            raise ValueError("Name must be a string")
        self.rag_response_hist_table = value

    def initialize_session(self):
        print(f"initialize_session")
        self.session_memory_df = pd.DataFrame(columns = self.session_columns)

    def get_similar_question_response(self, user_question,user_doc=None):
        user_question = self.m_embbeding.remove_stop_words(user_question)
        user_question_embedding = self.m_embbeding.get_titan_embedingd(user_question, None)
        return self.get_similar_question_response(user_question_embedding, user_doc=None)


    def get_user_session_memory(self, user_id, session_id, user_doc):
        sql_stmnt = f"""select user_id, session_id, user_question, llm_response_sumarization 
                    from {self.session_memory_table}
                    where user_id = '{user_id}' and session_id = '{session_id}'
                    and user_doc = '{user_doc}'
                    order by session_timestamp desc limit {self.session_length};
        """
        response = self.execute_statement(sql_stmnt) 
        return self.formatOutputJsonRecords(response)

    def get_user_session_images(self, user_id, session_id):
        sql_stmnt = f"""select user_id, session_id, user_question, response_images 
                    from {self.session_memory_table}
                    where user_id = '{user_id}' and session_id = '{session_id}'
                    order by session_timestamp desc limit {self.max_images};
        """
        response = self.execute_statement(sql_stmnt) 
        return self.formatOutputJsonRecords(response)


    def set_user_session_memory(self, user_id, session_id, llm_response):
        llm_response_sumarization = self.summarize_response(llm_response)


    def summarize_response(self, llm_response):
        prompt_instructions = f"""1. summarize this text. \
                                  2. The summary should not exceed 1 paragraph.\
                                  3. The summary should only be based on text context <context>{llm_response}</context> .\
                                  4. give a response based on context. 
                                  5. your response should only be the summary, nothing else.
                                  """
        response_prompt = self.llm_prompt.execute_text_prompt(prompt_instructions)
        response_prompt = re.sub(r'[\n\r\t]', ' ', response_prompt)
        return response_prompt


    def get_similar_question_response(self, similarity_vector, user_doc=None, min_threshold=0.9, top_n=1):
        doc_filter = "user_doc is null "
        if user_doc:
            doc_filter = "user_doc = '{user_doc}' "
        sql_stmnt = f"""select user_id, session_id, user_question, llm_response, response_images ,
            1 - (question_embedding <=> '{similarity_vector}') as cosine_similarity
            from {self.session_memory_table} 
            where {doc_filter}
            and (1 - (question_embedding <=> '{similarity_vector}')) > {min_threshold} 
            ORDER BY (1 - (question_embedding <=> '{similarity_vector}')) DESC LIMIT {top_n}"""
        response = self.execute_statement(sql_stmnt) 
        return self.formatOutputJsonRecords(response)
