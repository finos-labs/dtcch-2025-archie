import json
import boto3
from botocore.exceptions import ClientError
import pandas as pd
from pandas.io.json._normalize import nested_to_record 
from datetime import datetime
from common.utils import timeit
from common.parse_docs import ParsePDFDocTextImages as PDFDocParserTI
from common.embbed_docs import MultimodalEmbeding
from common.llm_prompts import LLMPrompts, AsyncBedrockLLMHandler
from common.doc_pgvector import DocPGVector
from common.s3_interface import S3Interface
from common.polly_interface import AsyncPolly
from common.session_memory import SessionMemory
from src.process_event import ProcessEvent
from src.model_response import AsyncModelResponse
from contextlib import closing
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class AsyncProcessRequest(ProcessEvent):
    def __init__(self,bedrock_runtime, rds_client, s3_c, polly, config, event, event_type):
        super().__init__(config, event, event_type) 
        self.bedrock_runtime = bedrock_runtime
        self.rds_client = rds_client
        self.s3_c = s3_c
        self.polly = polly
        self.m_embbeding = MultimodalEmbeding(bedrock_runtime, config)
        self.llm_prompt = LLMPrompts(bedrock_runtime, config)
        self.doc_pgvctr = DocPGVector(rds_client, config)
        self.session_memory = SessionMemory(bedrock_runtime, rds_client, config)
        self.s3i = S3Interface(s3_c, config)
        self.apollyi = AsyncPolly(polly, config)
        logger.info(f"event_type {event_type}")
        if event_type in ('audio_file_answer', 'video_file_answer'):
            logger.info("event_type in ('audio_file_answer', 'video_file_answer')")
            self.apollyi.set_llm_answer_text(self.llm_answer_text)
            self.apollyi.set_voice_id(self.voice_id)
        if event_type == 'video_file_answer':
            self.apollyi.set_avatar_name(self.avatar_name)
        self.async_model_response = AsyncModelResponse(bedrock_runtime, config)
        self.primary_model = self.config['models']['primary_model']
        self.secondary_model = self.config['models']['secondary_model']



    async def process_request_stream(self):
        answer = ''
        embed_user_question = self.m_embbeding.remove_stop_words(self.user_question)
        embed_user_question = self.m_embbeding.get_titan_embedding(embed_user_question, None)
        try:
            run_answer = False
            if self.adhoc_document_path:
                print(f"runing session_memory.get_similar_question_response for doc")
                response_memory = self.session_memory.get_similar_question_response(embed_user_question, user_doc=self.adhoc_document_path)
            else:
                print(f"runing session_memory.get_similar_question_response for non doc")
                response_memory = self.session_memory.get_similar_question_response(embed_user_question)
            if response_memory:
                self.response_memory_df = pd.DataFrame(response_memory)
                print(f"response_memory_df handler 1 {self.response_memory_df.shape[0]}") 
                if self.response_memory_df.shape[0] > 0:
                    answer = self.response_memory_df[['user_id', 'session_id', 'llm_response', 'response_images']].to_dict('records') 
                    memory_user_id = answer[0]['user_id']
                    memory_session_id = answer[0]['session_id']
                
                    yield answer[0]['llm_response']
                    yield answer[0]['response_images']
            else:
                run_answer = True
                
            if run_answer: 
                async for response_part in self.execute_model_response_stream():
                    yield response_part

        except ClientError as e:
            yield self.format_response(400, str(e))
            return

      

        
    async def execute_model_response_stream(self):
        print(f"execute_model_response_stream")
        """
        Process the request and generate a response in streaming mode.
        """
        answer = ''
        accumulated_text_chunks = [{'chunk_number': 0, 'accumulated_text': ''} ,{'chunk_number': 0, 'accumulated_text': ''}]
        accumulated_image_chunks = {}
        accumulated_text_chunks, accumulated_image_chunks, accumulated_document_source_links, contexts_size, embed_question_vector = self.prepare_chunks()

        model_id = self.primary_model
        session_memory_df = pd.DataFrame(self.session_memory.get_user_session_memory(self.user_id, self.session_id, self.adhoc_document_path))

        if self.adhoc_document_path:
            async for response_part in self.async_model_response.process_user_question_context_stream(self.doc_text, 
                [], session_memory_df, model_id, self.user_question):
                answer = answer + ''.join(response_part)
                accumulated_image_chunk = None
                yield response_part
        else:
            if contexts_size > 0:
                accumulated_text_chunk = accumulated_text_chunks[0]['accumulated_text']
                accumulated_image_chunk = accumulated_image_chunks[0]['accumulated_images']
                print(f"context size {contexts_size}")
                async for response_part in self.async_model_response.process_user_question_context_stream(accumulated_text_chunk, 
                accumulated_image_chunk, session_memory_df, model_id, self.user_question):
                    answer = answer + ''.join(response_part)
                    yield response_part
                yield accumulated_image_chunk
            else:
                async for response_part in self.async_model_response.process_user_question_stream(session_memory_df, model_id, self.user_question):
                    answer = answer + ''.join(response_part)
                    accumulated_image_chunk = None
                    yield response_part

        # add session memory if 
        session_memory = {}
        session_memory['user_id'] = self.user_id
        session_memory['session_id'] = self.session_id
        session_memory['user_question'] = self.user_question
        session_memory['user_doc'] = self.adhoc_document_path
        session_memory['llm_response'] = answer
        session_memory['llm_response_sumarization'] = self.session_memory.summarize_response(answer)
        session_memory['response_images'] = str(accumulated_image_chunk)
        session_memory['response_doc_links'] = str(accumulated_document_source_links)
        session_memory['session_timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        session_memory['session_date'] = datetime.now().strftime("%Y-%m-%d")
        session_memory['question_embedding'] = str(embed_question_vector)
        session_memory_df = pd.DataFrame(session_memory, index=[0])
        columns = self.doc_pgvctr.get_table_column_names(self.session_memory.session_memory_table)
        session_memory_df = session_memory_df[columns]
        sql_parameter_sets = self.doc_pgvctr.format_records(session_memory_df, self.session_memory.session_memory_table)
        insrt_stmnt = self.doc_pgvctr.format_insert_stmnt(self.session_memory.session_memory_table, columns, vector_column='question_embedding') 
        records = self.doc_pgvctr.batch_execute_statement(insrt_stmnt, sql_parameter_sets)
    
        print(f"execute_model_response_stream answer is \n {answer}")

    def prepare_chunks(self):
        """
        Prepare accumulated text and image chunks based on the request.
        """
        contexts_size = 0
        user_question = self.m_embbeding.remove_stop_words(self.user_question)
        embed_question_vector = self.m_embbeding.get_titan_embedding(user_question, None)
        accumulated_document_source_links = ''
        accumulated_text_chunks = {}
        accumulated_image_chunks = {}
        llm_context = False

        if self.adhoc_document_path:
            doc_bucket , doc_key = self.s3i.parse_s3_uri(self.adhoc_document_path)
            s3_output_folder = 's3://' + doc_bucket + '/' + self.config['output_details']['output_key']
            self.pdf_parser_inst = PDFDocParserTI(self.s3_c, self.config, self.adhoc_document_path,s3_output_folder, self.bedrock_runtime, ui_input=True)
            page_details, accumulated_chunks, self.doc_text  = self.pdf_parser_inst.process_pdf_pages()
            llm_context = True
            
        else:
            print(f"caling get_question_context")
            accumulated_image_chunks = {}
            accumulated_chunks, contexts_size, embed_question_vector = self.get_question_context()
            print(f"contexts_size is -> {contexts_size}")
            if contexts_size > 0:
                llm_context = True
        if llm_context:
            accumulated_chunks_df = pd.DataFrame(accumulated_chunks) 
            if 'document_source_links' in accumulated_chunks_df.columns:
                accumulated_document_source_links = accumulated_chunks_df[['document_source_links']].to_dict('records')
            accumulated_text_chunks = accumulated_chunks_df[['chunk_number','accumulated_text']].to_dict('records') 
            accumulated_image_chunks = accumulated_chunks_df[['chunk_number','accumulated_images']].to_dict('records') 

        return accumulated_text_chunks, accumulated_image_chunks, accumulated_document_source_links, contexts_size, embed_question_vector


    def get_question_context(self):
        embed_question_vector = []
        contexts = ''
        print(f"user_question -> {self.user_question}")
        user_question = self.m_embbeding.remove_stop_words(self.user_question)
        embed_question_vector = self.m_embbeding.get_titan_embedding(user_question, None)

        contexts_dict = self.doc_pgvctr.get_doc_cosine_topn_similar_records(5, embed_question_vector, min_threshold=0.75)
        contexts_size = len(contexts_dict)
        print(f"context size -> {contexts_size}")

        if contexts_size > 0:
            #acumulate al responses into one context
            accumulated_chunks_df = pd.DataFrame(contexts_dict)
            accumulated_chunks_df['chunk_number'] = 1

            accumulated_chunks_df = accumulated_chunks_df[['chunk_number', 'image_description', 'image_base64', 'document_source_link']] 

    
            accumulated_chunks_df = accumulated_chunks_df.groupby("chunk_number").apply(
                            lambda group: pd.Series({
                            "accumulated_text": " ".join(group["image_description"]),  # Concatenate descriptions
                            "document_source_links": list(group["document_source_link"].unique()),  # Unique links
                            "accumulated_images": [
                            {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": image_base64}}
                            for image_base64 in set(row["image_base64"] for _, row in group.iterrows() if row["image_base64"] is not None)], 
                            })).reset_index()

                            

            accumulated_chunks = accumulated_chunks_df.to_dict('records') 
            #save context search in RAG
            columns = self.doc_pgvctr.get_table_column_names(self.session_memory.rag_response_hist_table)
            response_df = pd.DataFrame(contexts_dict)
            response_df['user_id'] = self.user_id
            response_df['session_id'] = self.session_id
            response_df['user_question'] = self.user_question
            response_df['response_timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
            response_df['response_date'] = datetime.now().strftime("%Y-%m-%d")
            response_df = response_df[columns]
            sql_parameter_sets = self.doc_pgvctr.format_records(response_df, self.session_memory.rag_response_hist_table)
            insrt_stmnt = self.doc_pgvctr.format_insert_stmnt(self.session_memory.rag_response_hist_table, columns) 
            records = self.doc_pgvctr.batch_execute_statement(insrt_stmnt, sql_parameter_sets)

        else:
            accumulated_chunks = [{'chunk_number': 0, 'accumulated_text': '', 'accumulated_images': {}}]

        return accumulated_chunks, contexts_size, embed_question_vector


    async def audio_answer_stream(self):
        async for audio_response in self.apollyi.generate_synch_polly_audio_stream():
            yield audio_response

    async def audio_answer_file(self):
        file_name = f"{self.user_id}_{self.session_id}"
        async for audio_file_response in self.apollyi.generate_polly_audio_file(file_name):
            yield audio_file_response

    async def video_answer_file(self):
        file_name = f"{self.user_id}_{self.session_id}"
        async for video_file_response in self.apollyi.generate_video(file_name):
            yield video_file_response

   