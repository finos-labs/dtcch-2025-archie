import boto3
import json
import os
import logging
import uuid
from common.utils import timeit



logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class MultimodalEmbeding():
    def __init__(self, bedrock_runtime, config, model_id=None):
        """
        class to generate multimodal embedings 
        """
        self.bedrock_runtime = bedrock_runtime
        if model_id:
            self.model_id = model_id
        else:
            self.model_id = config['models']['embedd_model']
         
    @timeit    
    def embbed_doc(self, accumulated_chunks, embbeding_type):
        """
        method to run embbeding for all chunks
        ccumulated_chunks has required format 
        {'chunk_number': <>, 'accumulated_text': <>, 'accumulated_images': <>}
        chunk_number is integer and denotes chunk number
        acumulated text is the text to be sent to embbeding
        acumulated images, could be a list, we ned to embed each one
        """
        chunk_details = []
        for chunk_indx, chunk in enumerate(accumulated_chunks):
            text = chunk['accumulated_text']
            embedding_text = self.remove_stop_words(text)
            chunk_number = chunk['chunk_number']
            if chunk_number == 0:
                print(f"embbed_doc chunk_number == 0 accumulated_text\n {embedding_text}")
            if (len(text) == 0) or (len(embedding_text) == 0):
                continue
            image_indx = 0
            chunk_c = {}
            
            for image_indx, image_dict in enumerate(chunk['accumulated_images']):
                image_base64 = image_dict["source"]["data"]
                multi_modal_embbeding = self.get_titan_embedding(embedding_text, image_base64)
                chunk_c['embedding_type'] = embbeding_type
                chunk_c['image_description'] = text 
                chunk_c['chunk_number'] = chunk_number
                chunk_c['image_filename'] = image_dict['image_filename'] 
                chunk_c['embedding_id'] = str(uuid.uuid4())
                chunk_c['image_base64'] = image_base64
                chunk_c['multimodal_embedding'] = multi_modal_embbeding
                chunk_details.append(chunk_c)
                
            if image_indx == 0:
                multi_modal_embbeding = self.get_titan_embedding(embedding_text, None)
                chunk_c['embedding_type'] = embbeding_type
                chunk_c['image_description'] = text
                chunk_c['chunk_number'] = chunk_number
                chunk_c['image_filename'] = None
                chunk_c['embedding_id'] = str(uuid.uuid4())
                chunk_c['image_base64'] = None
                chunk_c['multimodal_embedding'] = multi_modal_embbeding
                chunk_details.append(chunk_c)
                
        return chunk_details
    
    def get_titan_embedding(self, text, image_base64):
        body = json.dumps(
            {
                "inputText": text,
                "inputImage": image_base64,
                "embeddingConfig": { 
                                     "outputEmbeddingLength": 1024
                                    }
            }
            )
        try:
            response = self.bedrock_runtime.invoke_model(
                            body=body,
                            modelId=self.model_id,
                            accept="application/json",
                            contentType="application/json"
                        )
            embeddings = json.loads(response.get("body").read())
            embeddings = embeddings['embedding']
        except Exception as e:
            embeddings = None
            logger.error(f"exception while encoding text={text}, exception={e}")
        
   
        return embeddings
        
       
    def remove_stop_words(self, text):
        # Define spaCy stop words in-memory
        spacy_stop_words = {
            'a', 'about', 'above', 'across', 'after', 'again', 'against', 'all', 'almost', 'alone', 
            'along', 'already', 'also', 'although', 'always', 'am', 'among', 'an', 'and', 'another', 
            'any', 'anybody', 'anyone', 'anything', 'anywhere', 'are', 'around', 'as', 'at', 'back', 
            'be', 'because', 'been', 'before', 'behind', 'being', 'below', 'beside', 'besides', 'between',
            'beyond', 'both', 'but', 'by', 'can', 'cannot', 'could', 'did', 'do', 'does', 'doing', 'done',
            'down', 'during', 'each', 'either', 'else', 'every', 'everybody', 'everyone', 'everything', 
            'everywhere', 'few', 'for', 'from', 'further', 'had', 'has', 'have', 'having', 'he', 'her', 
            'here', 'hers', 'herself', 'him', 'himself', 'his', 'how', 'i', 'if', 'in', 'into', 'is', 
            'it', 'its', 'itself', 'just', 'me', 'more', 'most', 'much', 'my', 'myself', 'no', 'nor', 
            'not', 'now', 'of', 'off', 'on', 'once', 'only', 'or', 'other', 'ought', 'our', 'ours', 
            'ourselves', 'out', 'over', 'own', 'same', 'she', 'should', 'so', 'some', 'such', 'than', 
            'that', 'the', 'their', 'theirs', 'them', 'themselves', 'then', 'there', 'these', 'they', 
            'this', 'those', 'through', 'to', 'too', 'under', 'until', 'up', 'very', 'was', 'we', 
            'were', 'what', 'when', 'where', 'which', 'while', 'who', 'whom', 'why', 'with', 'would', 
            'you', 'your', 'yours', 'yourself', 'yourselves'
        }


        return  ' '.join([word for word in text.lower().split() if word not in spacy_stop_words])

