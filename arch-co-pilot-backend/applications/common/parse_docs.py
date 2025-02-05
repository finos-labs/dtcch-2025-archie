import json
import logging
import base64
from botocore.exceptions import ClientError
from urllib.parse import urlparse
import pymupdf
import os
from PIL import Image, ImageShow
from typing import List, Dict, Any
import io
import pandas as pd

import re
import uuid
import pypdfium2 as pdfium
from functools import wraps
from common.utils import timeit
from common.llm_prompts import LLMPrompts

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)




class ParsePDFDocTextImages():
    def __init__(self, s3_c, config, s3_pdf_path,s3_output_folder,bedrock_runtime,):
        """
        clas to parse text and images from pdf docs
        """
        self.s3_c = s3_c
        self.config = config
        self.s3_pdf_path = s3_pdf_path
        self.s3_output_folder = s3_output_folder
        self.bedrock_runtime = bedrock_runtime
        self.chunk_size = self.config['chunk_dtls']['chunk_size']
        self.chunk_overlap_percent = self.config['chunk_dtls']['chunk_overlap_percent']
        self.doc = self.download_pdf_from_s3()
        self.document_id = str(uuid.uuid4())

 
    @property
    def doc_details(self):
        return self.s3_pdf_path.replace('s3://','').split('/')
        
    @doc_details.setter
    def doc_details(self, value):
        if not isinstance(value, dict):
            raise ValueError("Name must be a dictionary")
        self.doc_details = value
        
    @property
    def document_category(self):
        return self.doc_details[2]
        
    @document_category.setter
    def document_category(self, value):
        if not isinstance(value, str):
            raise ValueError("Name must be a string")
        self.document_category = value
        
    @property
    def document_source(self):
        return self.doc_details[3]
        
    @document_source.setter
    def document_source(self, value):
        if not isinstance(value, str):
            raise ValueError("Name must be a string")
        self.document_source = value
        
    @property
    def document_name(self):
        return self.doc_details[4]
        
    @document_name.setter
    def document_name(self, value):
        if not isinstance(value, str):
            raise ValueError("Name must be a string")
        self.document_name = value
        
    @property
    def document_filename(self):
        return self.doc_details[5]
        
    @document_filename.setter
    def document_filename(self, value):
        if not isinstance(value, str):
            raise ValueError("Name must be a string")
        self.document_filename = value
    
        
    def parse_s3_uri(self, s3_uri):
        parsed_url = urlparse(s3_uri)
        bucket_name = parsed_url.netloc  # Extract bucket name from URI
        object_key = parsed_url.path.lstrip('/') 
        
        return bucket_name, object_key

    
    def download_pdf_from_s3(self):
        """Downloads a PDF file from an S3 bucket."""
        bucket_name ,object_key = self.parse_s3_uri(self.s3_pdf_path)
        s3_response = self.s3_c.get_object(Bucket=bucket_name, Key=object_key)
        pdf_content = s3_response['Body'].read()
        pdf_stream = io.BytesIO(pdf_content)  # Create an in-memory stream for the PDF content
        pdf_document = pymupdf.open(stream=pdf_stream, filetype="pdf")
    
        return pdf_document
    
    def save_image_to_s3(self, block_img, image_filename):
        """
        Saves an image from the given block bytes to a specific S3 location.
    
        :param block_img: Image bytes from the block.
        """
        # Parse the S3 URI
        s3_bucket, s3_key_prefix = self.parse_s3_uri(self.s3_output_folder)
        
        # Full path (key) for the image in the S3 bucket
        s3_key = f"{s3_key_prefix}{image_filename}"

    
        # Convert the image to bytes for uploading
        image_buffer = io.BytesIO()
        block_img.save(image_buffer, format="PNG")
        image_buffer.seek(0)  # Go to the start of the BytesIO buffer
    
        # Upload the image to S3
        try:
            self.s3_c.upload_fileobj(image_buffer, s3_bucket, s3_key)
        except Exception as e:
            print(f"Failed to upload image to S3: {e}")
    
    
        
        
    def get_block_details(self, page_indx, block):
        block_number = block['number']
        if block['type'] == 0:
            block_type = "text"
        elif block['type'] == 1:
            block_type = "image"
        else:
            block_type = "unknown"
    
        text = []
        if "lines" in block.keys():
            text = block["lines"]
        bbox = block["bbox"]  # Bounding box of the block
        bbox_list = list(bbox)
        
        page_block = str(page_indx) + '_' + str(block_number)
    
        block_details = {'block_number': block_number, 'block_type': block_type,'text': text,
                         'x0':bbox_list[0], 'x1': bbox_list[2], 
                         'y0': bbox_list[1], 'y1': bbox_list[3],
                         'page_indx': page_indx, 'page_block': page_block}
        return block_details
        
    
    def get_block_images(self, chunk_number,block, block_details, accumulated_images, block_text):
        block_img_bytes = block['image'] 
        block_img = Image.open(io.BytesIO(block_img_bytes)) #.putalpha(0)
    
        # Display the image
        #block_img.show()
        
         # Generate a filename for the image
        image_filename = f"chunk_{chunk_number + 1}_page_{block_details['page_indx'] + 1}_block_{block_details['block_number']}.png"
        image_path = os.path.join(self.s3_output_folder, image_filename)
        #print(f"get_block_images image_path\n {image_path}")
        
        content_image = base64.b64encode(block_img_bytes).decode('utf8')
        filter_image = self.filter_images({'x0': block_details['x0'], 'x1': block_details['x1'],
                                      'y0': block_details['y0'], 'y1': block_details['y1']})

        if not filter_image:    
            llm_prompt = LLMPrompts(self.bedrock_runtime, self.config)     
            response = llm_prompt.llm_filter_image(content_image, block_text)   
            if response['filter_image'] == "YES":
                filter_image = True

        img_indx = 0
        if not filter_image:
            img_indx = 1
            # Save the image to the output folder
            self.save_image_to_s3(block_img, image_filename)
            
            accumulated_images.append({"type": "image", "source": {"type": "base64",
                                        "media_type": "image/jpeg", "data": content_image},
                                      "image_filename": image_filename})
                                    
        del block_img
        del content_image
    
        return accumulated_images, img_indx
    
    def filter_images(self, bbox_coordinates: dict) -> bool:
        # this indicates logos
        if bbox_coordinates['y0'] < 1 and bbox_coordinates['x1'] - bbox_coordinates['x0'] < 400:
            return True
        return False
        
    def get_chunk_overlap(self, text, overlap_type=None):
        match overlap_type:
            case "word" | "sentence":
                if overlap_type == 'word':
                    delimtr = ' '
                else:
                    delimtr = '.'
                words_text = text.split(delimtr)
                text_size = len(words_text)

                overlap_words_size = text_size - (text_size * self.chunk_overlap_percent) // 100 
                overlap_text = ' '.join(words_text[overlap_words_size:])
            case _:
                text_size = len(text)
                overlap_size = text_size - (text_size * self.chunk_overlap_percent) // 100
                overlap_text = text[overlap_size:]

        return  overlap_text.strip()
 
                
    @timeit
    def process_pdf_pages(self):
        num_pages = self.doc.page_count
        print(f"doc num_pages--> {num_pages}")
        chunk_number = 0
        page_details = []
        accumulated_chunks = []
        accumulated_text = ""
        accumulated_images = []
        image_indx = 0
        img_indx = 0
        
        doc_text = ''

    
        for page_indx, page in enumerate(self.doc):
            #for a specific chunk size coresponding to number of pages, acumulate text and acompanying images
            prev_accumulated_text = accumulated_text
            overlap_accumulated_text = self.get_chunk_overlap(prev_accumulated_text, overlap_type='word')
            
            if (page_indx % self.chunk_size == 0) or (num_pages == page_indx + 1): 
                chunk_number = page_indx // self.chunk_size
                accumulated_text = prev_accumulated_text + ' ' + accumulated_text
                accumulated_chunks.append({'chunk_number': chunk_number, 'accumulated_text': accumulated_text.strip(), 'accumulated_images': accumulated_images})
                doc_text += ' ' + accumulated_text.strip() 
                #print(f"process_pdf_pages chunk_number: {chunk_number}; accumulated_text  \n {accumulated_text.strip()}")

                accumulated_text = ''
                accumulated_images = []
           
            page_text = ''    
                
            text_data = page.get_text("dict")
            # Loop through the blocks of text
            if "blocks" in text_data.keys():
                for block in text_data["blocks"]:
                    block_details = self.get_block_details(page_indx, block)
                    block_text = ''   
                    
                    for line in block_details['text']:
                        for line_indx, span in enumerate(line['spans']):
                            span_bbox_list = list(span['bbox'])
                            page_text += ' ' + span['text'].strip().replace("'","").replace('"','')
                            accumulated_text = accumulated_text.strip() + ' ' + span['text'].strip().replace("'","").replace('"','')
                                     
                    if "image" in block:
                        accumulated_images, img_indx = self.get_block_images(chunk_number, block, block_details, accumulated_images, page_details)
                        image_indx = image_indx + img_indx
          
            page_details.append({'page_indx': page_indx + 1, 
                                 'chunk_number': chunk_number + 1, 
                                 'page_text': page_text.strip(),
                                 'num_pages': num_pages})
            #print(f"process_pdf_pages page_details --> page_indx {page_indx + 1}; chunk_number {chunk_number + 1};page_details \n {page_details[page_indx]}")
        return page_details, accumulated_chunks, doc_text       
         
                
    def process_pdf_page(self, page_indx, page):
        accumulated_text = ''
        accumulated_images = []
        page_details = []
        chunk_number = page_indx // self.chunk_size
        print(f"process_pdf_page page_indx {page_indx}")
    
        text_data = page.get_text("dict")
        if "blocks" in text_data.keys():
            for block in text_data["blocks"]:
                block_details = self.get_block_details(page_indx, block)
                block_text = []
                for line in block_details['text']:
                    for line_indx, span in enumerate(line['spans']):
                        span_bbox_list = list(span['bbox'])
                        accumulated_text += ' ' + span['text'].replace("'","").replace('"','')
                        block_text += ' ' + span['text'].replace("'","").replace('"','')
                        
                page_details.append({'page_block': block_details['page_block'], 'page_indx': page_indx + 1, 
                                     'block_number': block_details['block_number'],
                                     'chunk_number': chunk_number, 
                                     'block_text': block_text.strip(),
                                     'block_type': block_details['block_type'], 'num_pages': num_pages})
                
                if "image" in block:
                    accumulated_images, page_details, img_indx = self.get_block_images(chunk_number, block, block_details, accumulated_images, block_text)
    
        return page_details, {'chunk_number': chunk_number, 'accumulated_text': accumulated_text, 'accumulated_images': accumulated_images}

    def proces_pdf(self):
        self.page_details, self.accumulated_chunks, self.doc_text  = self.pdf_parser_inst.process_pdf_pages()
    
    @timeit
    def pdf_to_base64_pngs(self, quality=75, max_size=(1024, 1024)):
    # Open the PDF file
        num_pages = self.doc.page_count
        print(f"doc num_pages--> {num_pages}")

        base64_encoded_pngs = []
        image_filename_list = []
        zoom = 4
        #matrix = pymupdf.Matrix(300/72, 300/72)
        matrix = pymupdf.Matrix(zoom, zoom)
    
        # Iterate through each page of the PDF
        for page_num, page in enumerate(self.doc):
            # Load the page

            chunk_number = (page_num // self.chunk_size) + 1
            # Render the page as a PNG image
            pix = page.get_pixmap(matrix=matrix)
    
            # Convert the pixmap to a PIL Image
            image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            
            # Resize the image if it exceeds the maximum size
            if image.size[0] > max_size[0] or image.size[1] > max_size[1]:
                image.thumbnail(max_size, Image.Resampling.LANCZOS)
    
            # Save image to a bytes buffer
            buffered = io.BytesIO()
            image.save(buffered, format="PNG")
            
            image_filename = f"page_{page_num + 1}_image_{uuid.uuid4().hex}.png"
            image_path = os.path.join(self.s3_output_folder, image_filename)
 
            # Convert image to base64 string
            img_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
            base64_encoded_pngs.append({"chunk_number": chunk_number, "img_base64": img_base64, "image_filename": image_filename})
            
            del pix 
            del image 

        return base64_encoded_pngs
    
        