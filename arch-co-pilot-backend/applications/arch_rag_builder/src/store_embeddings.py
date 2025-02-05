import json
import boto3
from common.utils import timeit
import uuid
import pandas as pd
from pandas.io.json._normalize import nested_to_record 
import datetime
from common.parse_docs import ParsePDFDocTextImages as PDFDocParserTI
from common.embbed_docs import MultimodalEmbeding
from common.llm_prompts import LLMPrompts
from common.doc_pgvector import DocPGVector
from prepare_semantic_search import PrepareSemanticSearch 




class StoreEmbeddings(DocPGVector):
    def __init__(self, s3_c,bedrock_runtime, rds_client, config, s3_pdf_path,s3_output_folder):
        """
        class to store embeddings
        """
        super().__init__(rds_client, config) 
        self.config = config
        self.s3_pdf_path = s3_pdf_path
        self.s3_output_folder = s3_output_folder
        self.pdf_parser_inst = PDFDocParserTI(s3_c, config, s3_pdf_path,s3_output_folder, bedrock_runtime)
        self.m_embbeding = MultimodalEmbeding(bedrock_runtime, config)
        self.llm_prompt = LLMPrompts(bedrock_runtime, config)
        self.semantic_search = PrepareSemanticSearch(bedrock_runtime, config)
        self.model_id = config['models']['primary_model']
        self.proces_pdf()
         
    def get_table_cols(self, table_type):
        table_dtls = {}
        table_dtls['doc_table'] = self.config[f'{table_type}_table']['name']
        table_dtls['df_cols'] = self.config[f'{table_type}_table']['df_cols']
        table_dtls['tbl_cols'] = self.config[f'{table_type}_table']['tbl_cols']
        return table_dtls

    
    @property
    def document_id(self):
        return self.pdf_parser_inst.document_id
        
    @property
    def document_name(self):
        return self.pdf_parser_inst.document_name
        
    @property
    def document_filename(self):
        return self.pdf_parser_inst.document_filename
    
    def proces_pdf(self):
        self.page_details, self.accumulated_chunks, self.doc_text  = self.pdf_parser_inst.process_pdf_pages()
        
    def pd_normalize(self, dict_doc,df_cols):
        #print(f"pd_normalize dict_doc \n {dict_doc[0].keys()}")
        doc_df = pd.json_normalize(dict_doc)
        return doc_df[df_cols]
    
    def pd_embed_doc(self, accumulated_chunks, embbeding_type,df_cols):
        chunk_embedings = self.m_embbeding.embbed_doc(accumulated_chunks, embbeding_type)

        return self.pd_normalize(chunk_embedings,df_cols)

        
    def set_common_cols(self,doc_df, tbl_cols):
        created_ts = str(datetime.datetime.now().isoformat())
        doc_df['document_category'] = self.pdf_parser_inst.document_category
        doc_df['document_source'] = self.pdf_parser_inst.document_source
        doc_df['document_id'] = self.pdf_parser_inst.document_id
        doc_df['document_name'] = self.pdf_parser_inst.document_name
        doc_df['document_filename'] = self.pdf_parser_inst.document_filename
        doc_df = doc_df[tbl_cols]
        return doc_df
        
        
    def insert_batch(self, doc_df, tabled_dtls, vector_column=None):
        size_embedd = doc_df.shape[0]
        batch_size = 100
        num_transactions = size_embedd // batch_size
        last_batch_size = size_embedd % batch_size
        if last_batch_size != 0:
            num_transactions = num_transactions + 1
        for indx in range(num_transactions):
            if indx == 0:
                start_indx = (batch_size * indx)
            else:
                start_indx = (batch_size * indx) + 1
            if last_batch_size != 0 and indx == (num_transactions - 1):
                end_indx  = (batch_size * indx) + last_batch_size
            else:
                end_indx = (batch_size * (indx + 1))
            print(f"start_indx is {start_indx}; end_indx is {end_indx}")
            doc_df0 = doc_df.loc[start_indx:end_indx]
            doc_df0 = self.set_common_cols(doc_df0, tabled_dtls['tbl_cols'])
            sql_parameter_sets = self.format_records(doc_df0, tabled_dtls['doc_table'])
            #print(f"sql_parameter_sets[0]\n {sql_parameter_sets[0]}")
            insrt_stmnt = self.format_insert_stmnt(tabled_dtls['doc_table'], tabled_dtls['tbl_cols'],vector_column=vector_column)
            records = self.batch_execute_statement(insrt_stmnt, sql_parameter_sets)
        return records
        
    def store_doc_details(self):
        category = self.pdf_parser_inst.document_category.replace('-docs','')
        tabled_dtls = self.get_table_cols('main_doc')
        
        response_summary = self.semantic_search.generate_doc_summary(self.doc_text)    
        #print(f"store_doc_details response_summary1 \n {response_summary}")
        doc_df = self.pd_normalize([response_summary], tabled_dtls['df_cols'])
        #print(f"store_doc_details response_summary2 \n {response_summary}")
        doc_df['data_classification'] = 4 
        doc_df['document_access_group'] = 'ALL'
        doc_df['document_owner'] = 'Kafka'
        doc_df['document_source_link'] = 'https://www.confluent.io/resources/'
        doc_df['document_source_storage'] = 'sharepoint'

        records = self.insert_batch(doc_df, tabled_dtls)

    def main_embedding(self):
        print(f"length of accumulated_chunks -> {len(self.accumulated_chunks)}")
        embbeding_type = 'image'
        tabled_dtls = self.get_table_cols('main_embedd')
        
        chunk_embedings_df = self.pd_embed_doc(self.accumulated_chunks, embbeding_type,tabled_dtls['df_cols'])
        chunk_embedings_df = chunk_embedings_df.loc[chunk_embedings_df.astype(str).drop_duplicates().index]
        #print(f" length of chunk_embedings 1 -> {chunk_embedings_df1.shape[0]}")

        """
        base64_encoded_pngs = self.pdf_parser_inst.pdf_to_base64_pngs()
        
        page_response_list = self.llm_prompt.execute_image_prompt(base64_encoded_pngs , self.model_id)
    
        embbeding_type = 'page'
        chunk_embedings_df2 = self.pd_embed_doc(page_response_list, embbeding_type, tabled_dtls['df_cols'])
        chunk_embedings_df2 = chunk_embedings_df2.loc[chunk_embedings_df2.astype(str).drop_duplicates().index]
        #print(f" length of chunk_embedings 2 -> {chunk_embedings_df2.shape[0]}")
        
        chunk_embedings_df = pd.concat([chunk_embedings_df1, chunk_embedings_df2]).reset_index(drop=True)
        #print(f" length of chunk_embedings after concat -> {chunk_embedings_df.shape}")
        """

        chunk_embedings_df = self.set_common_cols(chunk_embedings_df, tabled_dtls['tbl_cols'])
        sql_parameter_sets = self.format_records(chunk_embedings_df, tabled_dtls['doc_table'])
        #print(f"sql_parameter_sets[0]\n {sql_parameter_sets[0]}")
        
        insrt_stmnt = self.format_insert_stmnt(tabled_dtls['doc_table'], tabled_dtls['tbl_cols'],vector_column='multimodal_embedding') 
        records = self.batch_execute_statement(insrt_stmnt, sql_parameter_sets)
            
        #print(f"records \n {records}")
        return records
        
         
    def search_embedding(self):
        category = self.pdf_parser_inst.document_category.replace('-docs','')
        tabled_dtls = self.get_table_cols('search_embedd')
  
        print(f"search_embedding self.accumulated_chunks-> {self.accumulated_chunks[0].keys()}")
        print(f"search_embedding self.page_details -> {self.page_details[0].keys()}")

        #print(f"search_embedding self.page_details \n {self.page_details}")
        response_questions = self.semantic_search.generate_doc_page_questions(self.page_details, category)                    
        chunk_embedings = self.semantic_search.embedd_doc_questions(response_questions)    
        chunk_embedings_df = self.pd_normalize(chunk_embedings, tabled_dtls['df_cols'])
        records = self.insert_batch(chunk_embedings_df, tabled_dtls, vector_column='multimodal_embedding')
        
        response_questions = self.semantic_search.generate_doc_page_keypoints(self.page_details, category)
        chunk_embedings = self.semantic_search.embedd_doc_keypoints(response_questions)
        chunk_embedings_df = self.pd_normalize(chunk_embedings, tabled_dtls['df_cols'])
        records = self.insert_batch(chunk_embedings_df, tabled_dtls, vector_column='multimodal_embedding')
    
        response_questions = self.semantic_search.generate_doc_chunk_questions(self.accumulated_chunks, category)
        chunk_embedings = self.semantic_search.embedd_doc_questions(response_questions)    
        chunk_embedings_df = self.pd_normalize(chunk_embedings, tabled_dtls['df_cols'])
        records = self.insert_batch(chunk_embedings_df, tabled_dtls, vector_column='multimodal_embedding')

        response_questions = self.semantic_search.generate_doc_chunk_keypoints(self.accumulated_chunks, category)
        chunk_embedings = self.semantic_search.embedd_doc_keypoints(response_questions)
        chunk_embedings_df = self.pd_normalize(chunk_embedings, tabled_dtls['df_cols'])
        records = self.insert_batch(chunk_embedings_df, tabled_dtls, vector_column='multimodal_embedding')
      
        return records
        