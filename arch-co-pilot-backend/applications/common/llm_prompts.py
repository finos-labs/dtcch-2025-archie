import json
import botocore
import asyncio
from common.utils import timeit


class LLMPrompts():
    def __init__(self, bedrock_runtime, config, model_id=None):
        """
        class to generate multimodal embedings 
        """
        self.bedrock_runtime = bedrock_runtime
        if model_id:
            self.model_id = model_id
        else:
            self.model_id = config['models']['primary_model']
       
    @timeit 
    def execute_image_prompt(self, base64_encoded_pngs, model_id):

        page_response_list = []
          
        for img_indx, base64_encd_png in enumerate(base64_encoded_pngs):
            prompt_detail = {} 
            img_base64 = base64_encd_png["img_base64"] 
            image_filename = base64_encoded_pngs[img_indx]["image_filename"]
            chunk_number = base64_encd_png['chunk_number']
            #print(f"execute_image_prompt image_filename  \n {image_filename}")

            response_format = """{"image_filename": "image_filename", "image_summary": "image_summary"}"""
     
            text_instructions =  """ 1. Create a summary of the image.\
                                 2. in JSON <response>{response_format}</response> "image_filename" is <image_filename>{image_filename}</image_filename>\
                                 2. return image_path and sumary in the folowing format <response>{response_format}</response>.\
                                 3. return a valid json dictionary not a string in format <response>{response_format}</response>.\
                                 4. response dict keys are "image_filename" , "image_summary".\
                                 5. make sure to enclose the dict keys in double quotes.\
                                 6. make sure to enclose dict values in double quotes.\
                                 7. do not include quotes in the image summary.
                            """
                            
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": img_base64}},
                        {"type": "text", "text": text_instructions}
                    ]
                }
            ]
    
            model_kwargs =  { 
                "max_tokens": 30000, "temperature": 0.1,
                "top_k": 250, "top_p": 1, "stop_sequences": ["\n\nHuman"],
            }
            
            body = {
                "anthropic_version": "bedrock-2023-05-31",
                "system": "You are a honest and helpful bot.Be consize",
                "messages": messages,
            }
            
            
            body.update(model_kwargs)
            # Invoke
            response = self.bedrock_runtime.invoke_model(
                modelId=model_id,
                body=json.dumps(body),
            )
            # Process and print the response
            response_prompt = json.loads(response.get("body").read())
            response_prompt = response_prompt["content"][0]["text"].replace('{','').replace('}','')
            response_prompt = response_prompt.replace('image_filename', '"image_filename"').replace('image_summary','"image_summary"').replace('""','"')
            response_prompt = response_prompt.replace('": ','": "').replace('\n','')  + '"' 
            response_prompt = response_prompt.replace('\n','').replace('""','"')
            response_prompt = '{' + response_prompt + '}'
            response_prompt = response_prompt.replace('<response>','').replace('</response>','')
            
            print(f"execute_image_prompt response_prompt \n {response_prompt} ")
            try:
                response_prompt = json.loads(response_prompt)
            except:
                response_prompt = response_prompt.replace('"image_summary": ', '"image_summary": "') 
                
                response_prompt = json.loads('{' + response_prompt + '"}')
                
            #print(f"execute_image_prompt response_prompt \n {response_prompt} ")
            
            prompt_detail['accumulated_text'] = response_prompt["image_summary"]
            prompt_detail['accumulated_images'] =  [{"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": img_base64}, "image_filename": image_filename}]
            prompt_detail['chunk_number'] = chunk_number

            page_response_list.append(prompt_detail)
            
            
            
            #print("****************haiku_prompt3********************")
            #print(response_prompt)
            #print("***********************haiku_prompt3*********************")
            
        return page_response_list
                
            
    @timeit 
    def execute_text_prompt(self, text_instructions, model_id=None):
        response_list = []
        if not model_id:
            model_id = self.model_id
        messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": text_instructions}
                    ]
                }
            ]
    
        model_kwargs =  { 
            "max_tokens": 30000, "temperature": 0.1,
            "top_k": 250, "top_p": 1, "stop_sequences": ["\n\nHuman"],
        }
        
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "system": "You are a honest and helpful bot.Be consize",
            "messages": messages,
        }
        
            
        body.update(model_kwargs)
        # Invoke
        response = self.bedrock_runtime.invoke_model(
            modelId=model_id,
            body=json.dumps(body),
        )
        # Process and print the response
        response_prompt = json.loads(response.get("body").read())
        response_prompt = response_prompt["content"][0]["text"].replace('{','').replace('}','')
        response_prompt = response_prompt.replace('<response>','').replace('</response>','')

        return  response_prompt

    @timeit 
    def llm_filter_image(self, img_base64, context, model_id=None):
        if not model_id:
            model_id = self.model_id

        response_format = """{"filter_image": "YES", "image_empty": "YES"}"""
    
        text_instructions =  """ 1. if image does not have visible words return <response>{"filter_image": "YES", "image_empty": "YES"}</responses>.\
                                2. input context is <context> {context} </context> \
                                3. If image is not relevant to input context return <response>{"filter_image": "YES", "image_empty": "NO"}</responses>.\
                                4. If image is a logo then return response <response>{"filter_image": "YES", "image_empty": "NO"}</responses>.\
                                5. Only return a valid json dictionary not a string in format <response>{response_format}</responses>.\
                                6. Do not return anything else but json response \
                                7. make sure to enclose the dict keys in double quotes.\
                                8. make sure to enclose dict values in double quotes.\
                                9. do not include quotes in the image summary.
                        """
                        
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": img_base64}},
                    {"type": "text", "text": text_instructions}
                ]
            }
        ]

        model_kwargs =  { 
            "max_tokens": 30000, "temperature": 0.1,
            "top_k": 250, "top_p": 1, "stop_sequences": ["\n\nHuman"],
        }
        
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "system": "You are a honest and helpful bot.Be consize",
            "messages": messages,
        }
        
        
        body.update(model_kwargs)
        # Invoke
        response = self.bedrock_runtime.invoke_model(
            modelId=model_id,
            body=json.dumps(body),
        )

        # Process and print the response
        response_prompt = json.loads(response.get("body").read())
        response_prompt = response_prompt["content"][0]["text"].replace('{','').replace('}','')
        response_prompt = response_prompt.replace('filter_image', '"filter_image"').replace('image_empty','"image_empty"').replace('""','"')
        response_prompt = response_prompt.replace('": ','": "').replace('\n','')  + '"' 

        response_prompt = response_prompt.replace('\n','').replace('""','"')
  
        response_prompt = '{' + response_prompt + '}'
        response_prompt = response_prompt.replace('<response>','').replace('</response>','')
        
        #print(f"execute_image_prompt response_prompt3 \n {response_prompt} ")
        try:
            response_prompt = json.loads(response_prompt)
        except:
            response_prompt = response_prompt.replace('"filter_image": ', '"filter_image": "').replace('"image_empty": ', '"image_empty": "').replace('""','"') 
           
            response_prompt = json.loads( response_prompt)
            
        #print(f"llm_filter_image response_prompt \n {response_prompt} ")

        return response_prompt

 

    

class AsyncBedrockLLMHandler:
    def __init__(self,bedrock_runtime, config):
        """
        Initialize the class with configuration.
        :param config: Dictionary containing models and other configurations.
        """
        self.config = config
        self.bedrock_runtime = bedrock_runtime

    async def invoke_bedrock_stream(self, model_id, body):
        """
        Asynchronously invoke the Bedrock model in streaming mode.
        :param model_id: ID of the model to invoke.
        :param body: Payload to send to the Bedrock API.
        :return: Async generator yielding responses.
        """
        def sync_invoke_model_stream():
            return self.bedrock_runtime.invoke_model_with_response_stream(
                modelId=model_id,
                contentType="application/json",
                body=body
            )

        response = await asyncio.to_thread(sync_invoke_model_stream)
        stream = response.get("body")
        print(f"sync_invoke_model_stream stream \n {stream}")

        # Return an async generator for the streaming response
        stream = response.get('body')
        if stream:
            for event in stream:
                chunk = event.get('chunk')
                if chunk:
                    message = json.loads(chunk.get("bytes").decode())
                    if message['type'] == "content_block_delta":
                        yield message['delta']['text'] or ""
                    elif message['type'] == "message_stop":
                        yield "\n"

                   