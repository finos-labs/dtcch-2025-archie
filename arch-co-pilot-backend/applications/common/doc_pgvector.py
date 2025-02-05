
import boto3
import json
import pandas as pd
from common.utils import timeit
from common.pgvector_interface import PGVectorInterface


class DocPGVector(PGVectorInterface):
    def __init__(self, rds_client, config):
        """
        class to enteract with PGVector
        """
        super().__init__(rds_client, config) 

    @property
    def main_doc_table(self):
        return  self.config['main_doc_table']['name']
        
    @main_doc_table.setter
    def main_doc_table(self, value):
        if not isinstance(value, str):
            raise ValueError("Name must be a string")
        self.main_doc_table = value
        
    @property
    def main_embedding_table(self):
        return  self.config['main_embedd_table']['name']
        
    @main_embedding_table.setter
    def main_embedding_table(self, value):
        if not isinstance(value, str):
            raise ValueError("Name must be a string")
        self.main_embedding_table = value
        
    @property
    def search_embedding_table(self):
        return  self.config['search_embedd_table']['name']
        
    @search_embedding_table.setter
    def search_embedding_table(self, value):
        if not isinstance(value, str):
            raise ValueError("Name must be a string")
        self.search_embedding_table = value
    
    @property
    def embedding_tables(self):
        return  [self.main_embedding_table, self.search_embedding_table]
        
    @embedding_tables.setter
    def embedding_tables(self, value):
        if not isinstance(value, list):
            raise ValueError("Name must be a list")
        self.embedding_tables = value
        

    def get_doc_cosine_topn_similar_records(self, top_n, similarity_vector, min_threshold=0.8):
        sql_stmnt = f"""select topn_srch.document_id,topn_srch.chunk_number,topn_srch.embedding_type,
                topn_srch.cosine_similarity as similarity_score, 'cosine' as similarity_func,
                doc.document_source_link, doc.document_filename, topn_srch.text_description, main.image_base64, main.image_description from 
                (select document_id,chunk_number,embedding_type,cosine_similarity,text_description from 
                (select document_id,chunk_number,text_type as embedding_type,text_description ,
                1 - (multimodal_embedding <=> '{similarity_vector}') as cosine_similarity
                from {self.search_embedding_table} 
                where (1 - (multimodal_embedding <=> '{similarity_vector}')) > {min_threshold} 
                union all  
                select document_id,chunk_number,embedding_type, ' ' as text_description,
                1 - (multimodal_embedding <=> '{similarity_vector}')  as cosine_similarity
                from {self.main_embedding_table} 
                where (1 - (multimodal_embedding <=> '{similarity_vector}')) > {min_threshold} ) srch
                ORDER BY cosine_similarity DESC LIMIT { top_n}) topn_srch
                join (select document_id, document_source_link , document_filename from {self.main_doc_table} ) doc
                on topn_srch.document_id = doc.document_id
                join (select document_id,chunk_number,image_base64, image_description 
                from {self.main_embedding_table} where embedding_type = 'image' ) main
                on topn_srch.document_id = main.document_id
                and topn_srch.chunk_number = main.chunk_number
                order by topn_srch.cosine_similarity desc; """
        response = self.execute_statement(sql_stmnt) 
        return self.formatOutputJsonRecords(response)

    def get_doc_l2_topn_similar_records(self, top_n, similarity_vector, max_threshold=0.8):
        sql_stmnt = f"""select topn_srch.document_id,topn_srch.chunk_number,topn_srch.embedding_type,
                topn_srch.l2_similarity as similarity_score, 'l2' as similarity_func,
                doc.document_source_link, doc.document_filename, topn_srch.text_description, main.image_base64, main.image_description from 
                (select document_id,chunk_number,embedding_type,l2_similarity,text_description from 
                (select document_id,chunk_number,text_type as embedding_type,text_description ,
                (multimodal_embedding <-> '{similarity_vector}') as l2_similarity
                from {self.search_embedding_table} 
                where (multimodal_embedding <-> '{similarity_vector}') < {max_threshold}
                union all  
                select document_id,chunk_number,embedding_type, ' ' as text_description,
                (multimodal_embedding <-> '{similarity_vector}')  as l2_similarity
                from {self.main_embedding_table} 
                where (multimodal_embedding <-> '{similarity_vector}') < {max_threshold} ) srch
                ORDER BY l2_similarity asc LIMIT { top_n}) topn_srch
                join (select document_id, document_source_link , document_filename from {self.main_doc_table} ) doc
                on topn_srch.document_id = doc.document_id
                join (select document_id,chunk_number,image_base64, image_description 
                from {self.main_embedding_table} where embedding_type = 'image' ) main
                on topn_srch.document_id = main.document_id
                and topn_srch.chunk_number = main.chunk_number
                order by topn_srch.l2_similarity asc; """
        response = self.execute_statement(sql_stmnt) 
        return self.formatOutputJsonRecords(response)





