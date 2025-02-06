import asyncio
import boto3
import json
import pandas as pd
from common.llm_prompts import LLMPrompts, AsyncBedrockLLMHandler



class AsyncModelResponse(AsyncBedrockLLMHandler):
    def __init__(self,bedrock_runtime, config):
        """
        Initialize the class with configuration.
        :param bedrock_runtime: bedrock client
        :param config: Dictionary containing models and other configurations.
        """
        super().__init__(bedrock_runtime, config)
        self.config = config
        self.bedrock_runtime = bedrock_runtime


    async def process_doc_question_stream(self, accumulated_text_chunks, accumulated_image_chunks, model_id, question):
        """
        Process document questions and return results in streaming mode.
        :param accumulated_text_chunks: Text chunks for context.
        :param accumulated_image_chunks: Image chunks associated with the text.
        :param model_id: Bedrock model ID.
        :param question: User question.
        :return: Async generator for streaming responses.
        """
        max_tokens = self.config['models']['max_tokens']

        for indx, accumulated_text in enumerate(accumulated_text_chunks):
            if indx == 0:
                continue  # Skip the first chunk

            context = accumulated_text['accumulated_text']
            chunk_number = accumulated_text['chunk_number']

            # Process images for the chunk
            if accumulated_image_chunks:
                accumulated_images_for_chunk = next(
                    item['accumulated_images']
                    for item in accumulated_image_chunks
                    if item['chunk_number'] == chunk_number
                )
                images_df = pd.DataFrame(accumulated_images_for_chunk)
                print(f"images_df columns {images_df.columns}")
                if images_df.shape[0] > 0:
                    print(f"images_df columns {images_df.columns}")
                    context = context + str(images_df[['image_filename']].to_dict('records'))
                    doc_images = images_df[['type', 'source']].to_dict('records') 
                else:
                    doc_images = images_df.to_dict('records')
            else:
                doc_images = []
            print(f"ize of doc_images {len(doc_images)}")

            return_image_format = """text_response_ended@[{"image_number": image_number, "image_path": "image path",
            "image_description": "description", "image_summary": "summary", "image_data": "base64 image data"}]"""

            # Construct the input for the LLM

            input_text = f"""
                        0.  Answer the question from the user {question} .\
                        1. Be consize and precise. Maximum 6 paragraphs are enough.\
                        2. To answer the user's question, Use the folowing context to answer {context}.\
                        Pay atention to text in document first, and then images.
                        3. If The context contains images, then the image path is included.\
                        image path is included in this format 'image_path': './extracted_images/page_4_block_2.png'\
                        4. if images/diagrams are included in context, please retun image number starting with 0 and image path which help answer the question in JSON format.\
                            to get the image path corect, correlate image number you recieve with image path .
                        5. when returning JSON of image paths, include description and sumary of image. return using format {return_image_format}\
                            Please return a valid json .
                        6. if the context contains images/diagrams,Include JSON with image paths after answerring the question.\
                        7. Answer the question first and then return {return_image_format}\
                        8. only include text_response_ended@ once. after text_response_ended@ return all images/diagram in {return_image_format}, \
                            do not include double quotes in your answer.
                        9. IN {return_image_format} FOR "image_data" key should be the image base64 data.\
                        9.If you do not know the anser, say I do not know\
                        """


            message = {"role": "user",
                 "content": [
                     *doc_images,
                    {"type": "text", "text": input_text}
                    ]}
        

            body = json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": max_tokens,
                "temperature": 0.0,
                "top_k": 250, 
                "top_p": 1, 
                "messages": [message]
            })

            # Stream the responses
            async for response_part in self.invoke_bedrock_stream(model_id, body):

                yield response_part



    async def process_text_question_stream(self, context, model_id, question):
        """
        Process document questions and return results in streaming mode.
        :param context: Text chunks for context.
        :param model_id: User question.
        :return: Async generator for streaming responses.
        """
        max_tokens = self.config['models']['max_tokens']

        # Construct the input for the LLM

        input_text = f"""
                    0.  Answer the question from the user {question} .\
                    1. Be consize and precise. Maximum 9 paragraphs are enough.\
                    2. To answer the user's question, Use the folowing context to answer {context}.\
                    Pay atention to text in document first, and then images.
                    3. If you do not know the anser, say I do not know\
                    """

        message = {"role": "user",
                "content": [
                {"type": "text", "text": input_text}
                ]}
    

        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "temperature": 0.0,
            "top_k": 250, 
            "top_p": 1, 
            "messages": [message]
        })

        # Stream the responses
        async for response_part in self.invoke_bedrock_stream(model_id, body):
            yield response_part


    async def process_user_question_context_stream(self, context, doc_images, session_memory_df, model_id, question):
        """
        Process document questions and return results in streaming mode.
        :param context: Text chunks for context.
        :param doc_images: Image chunks associated with the text.
        :param session_memory_df: session memory dataframe
        :param model_id: Bedrock model ID.
        :param question_type: Type of question.
        :return: Async generator for streaming responses.
        """
        max_tokens = self.config['models']['max_tokens']


        print(f"ize of doc_images {len(doc_images)}")
        #print(f" doc_images {doc_images[0].keys()}")
        print(f"context \n {context}")
        session_memory = {}
        # Construct the input for the LLM
        if len(session_memory_df) == 0:
            memory_instructions = ''
        else:
            session_memory = session_memory_df[["user_question","llm_response_sumarization"]].to_dict('records')
            memory_instructions = """3. Please take into consideration the conversation history <history>{sesion_memory}</history>\
                    4. The conversation history is in JSON format <history_format>{sesion_memory_format}</history_format>"""
            sesion_memory_format = """[{"user_question": "user_question","llm_response_sumarization": "llm_response_sumarization"}]"""

        #print(f"process_user_question_stream sesion_memory \n {session_memory}")
        input_text = f"""
                    0.  Answer the question from the user <question>{question}</question> .\
                    1. Be consize and precise. Maximum 9 paragraphs are enough.\
                    2. To answer the user's question, Use the folowing context to answer <context>{context}</context>.\
                    Pay atention to text in document first, and then images.
                    {memory_instructions}
                    5. If you do not know the anser, say I do not know\
                    """

        message = {"role": "user",
                "content": [
                    *doc_images,
                {"type": "text", "text": input_text}
                ]}
    

        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "temperature": 0.0,
            "top_k": 250, 
            "top_p": 1, 
            "messages": [message]
        })

        # Stream the responses
        async for response_part in self.invoke_bedrock_stream(model_id, body):
            yield response_part



    async def process_user_question_stream(self, session_memory_df, model_id, question):
        """
        Process document questions and return results in streaming mode.
        :param session_memory_df: session memory dataframe
        :param model_id: Bedrock model ID.
        :param question: user question
        :return: Async generator for streaming responses.
        """
        max_tokens = self.config['models']['max_tokens']

        session_memory = {}
        # Construct the input for the LLM
        if len(session_memory_df) == 0:
            memory_instructions = ''
        else:
            session_memory = session_memory_df[["user_question","llm_response_sumarization"]].to_dict('records')
            memory_instructions = """2. Please take into consideration the conversation history <history>{sesion_memory}</history>\\
                    3. The conversation history is in JSON format <history_format>{sesion_memory_format}</history_format>\
                    4. If the conversation history is not related to question, ignore it and answer question"""
            sesion_memory_format = """[{"user_question": "user_question","llm_response_sumarization": "llm_response_sumarization"}]"""

        print(f"process_user_question_stream sesion_memory \n {session_memory}")
        input_text = f"""
                    0.  Answer the question from the user <question>{question}</question> .\
                    1. Be consize and precise. Maximum 7 paragraphs are enough.\
                    {memory_instructions}
                    5. If you do not know the anser, say I do not know\
                    """

        message = {"role": "user",
                "content": [{"type": "text", "text": input_text}
                ]}

        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "temperature": 0.0,
            "top_k": 250, 
            "top_p": 1, 
            "messages": [message]
        })

        # Stream the responses
        async for response_part in self.invoke_bedrock_stream(model_id, body):
            yield response_part