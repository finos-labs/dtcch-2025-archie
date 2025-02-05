
import boto3
import json
import os
import logging
import yaml
import pandas as pd
from common.utils import timeit

 
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)



class PGVectorInterface():
    def __init__(self, rds_client, config):
        """
        class to enteract with PGVector
        """
        self.rds_client = rds_client
        self.config = config
        
        
    @property
    def db_cluster_arn(self):
        return self.config['db_details']['db_cluster_arn']
        
    @db_cluster_arn.setter
    def db_cluster_arn(self, value):
        if not isinstance(value, str):
            raise ValueError("Name must be a string")
        self.db_cluster_arn = value
        
    @property
    def db_secrets_arn(self):
        return self.config['db_details']['db_secrets_arn']
        
    @db_secrets_arn.setter
    def db_secrets_arn(self, value):
        if not isinstance(value, str):
            raise ValueError("Name must be a string")
        self.db_secrets_arn = value
        
    @property
    def db_name(self):
        return self.config['db_details']['db_name']
        
    @db_name.setter
    def db_name(self, value):
        if not isinstance(value, str):
            raise ValueError("Name must be a string")
        self.db_name = value
            
        
    @timeit     
    def execute_statement(self,sql_stmnt, sql_parameters=[]):
        try:
            response = self.rds_client.execute_statement(
                                        secretArn=self.db_secrets_arn,
                                        database=self.db_name,
                                        resourceArn=self.db_cluster_arn,
                                        formatRecordsAs="JSON",
                                        includeResultMetadata=True,
                                        sql=sql_stmnt,
                                        parameters=sql_parameters
                                    )
        except Exception as e:
            logger.error(e)
            raise 
            
        return response
    
    @timeit    
    def batch_execute_statement(self,sql_stmnt, sql_parameter_sets):
        print(f"transaction size {len(sql_parameter_sets)}")
        try:
            transaction = self.rds_client.begin_transaction(
                        secretArn=self.db_secrets_arn,
                        resourceArn=self.db_cluster_arn,
                        database=self.db_name)
                        
            transaction_id = transaction['transactionId']
            print(f"batch_execute_statement transaction_id {transaction_id}")
                        
            parameters = {
                        'secretArn': self.db_secrets_arn,
                        'database': self.db_name,
                        'resourceArn': self.db_cluster_arn,
                        'transactionId': transaction_id,
                        'sql': sql_stmnt,
                        'parameterSets': sql_parameter_sets
                    }
            response = self.rds_client.batch_execute_statement(**parameters)
        except Exception as e:
            print(f'Error: {e}')
            transaction_response = self.rds_client.rollback_transaction(
                        secretArn=self.db_secrets_arn,
                        resourceArn=self.db_cluster_arn,
                        transactionId=transaction_id)
            raise
        else:
            transaction_response = self.rds_client.commit_transaction(
                        secretArn=self.db_secrets_arn,
                        resourceArn=self.db_cluster_arn,
                        transactionId=transaction_id)
            print(f'Number of records updated: {len(response["updateResults"])}')
            
        print(f'Transaction Status: {transaction_response["transactionStatus"]}')
                
        return response
        
    def get_unique_key(self, table):
        unq_stmnt = """select i.relname as index_name, a.attname as column_name,  ix.indisunique ,t.relname as table_name 
            from pg_class t, pg_class i, pg_index ix, pg_attribute a, pg_namespace n
            where t.oid = ix.indrelid and i.oid = ix.indexrelid and a.attrelid = t.oid
            and a.attnum = ANY(ix.indkey) and n.oid=t.relnamespace and t.relkind = 'r'
            and t.relname = 'doc_details' 
            and ix.indisunique is TRUE """
        response = self.formatOutputJsonRecords(self.execute_statement(unq_stmnt))         
        return response[0]['column_name']
        
    def get_foreign_keys(self, tables):
        filter_str = "'" + "', '".join(tables) +  "'"

        fk_stmnt = f"""SELECT  t.relname as table_name, rt.relname as referenced_table_name,
                        c.conname AS constraint, a.attname AS fk_column
                        FROM pg_catalog.pg_constraint c
                        CROSS JOIN LATERAL unnest(c.conkey) WITH ORDINALITY AS x(attnum, n)
                        JOIN pg_catalog.pg_attribute a
                        ON a.attnum = x.attnum AND a.attrelid = c.conrelid
                        join pg_class t 
                        on t.oid = c.conrelid
                        join pg_class rt 
                        on rt.oid = c.confrelid
                        WHERE c.contype = 'f' and c.conrelid::regclass in ({filter_str})
                        GROUP BY t.relname , c.conname, rt.relname ,a.attname ;"""

        #print(fk_stmnt)
        response = self.formatOutputJsonRecords(self.execute_statement(fk_stmnt))
        return response
    
    
    @timeit    
    def records_exists(self, table_name, search_column, search_value):
        exist_stmnt = f"""select {search_column} from {table_name} where {search_column} = '{search_value}' limit 1; """ 
        record_exist = len(self.formatOutputJsonRecords(self.execute_statement(exist_stmnt)))
        
        if record_exist == 0:
            return False
        else:
            return True
    
    @timeit 
    def delete_table_records(self,table_name,search_column, search_value):
        del_stmnt = f"""delete from {table_name} where {search_column} = '{search_value}'; """
        print(f"delete_table_records del_stmnt \n {del_stmnt}")
        return self.execute_statement(del_stmnt)
        
    @timeit 
    def delete_related_tables_records(self, main_table, delete_tables,search_column, search_value):
        responses = []
        delete_tables.append(main_table)
        uk_column = self.get_unique_key(main_table)
        if uk_column != search_column:
            search_values = self.formatOutputJsonRecords(self.execute_statement(f"""select 
                              {uk_column} from {main_table} where {search_column} = '{search_value}'"""))
        if search_values:
            for search_value in search_values:
                for table_name in delete_tables:
                    response = self.delete_table_records(table_name, uk_column, search_value[f'{uk_column}'])
                    responses.append(response)
        return responses


    def get_column_data_type(self,pg_schema_df,column_name):
        return pg_schema_df[pg_schema_df['column_name'].str.lower() == column_name.lower()]['data_type'].iloc[0]
    
    def map_row_to_rds_format(self,table_name, row):
        pg_schema = self.get_table_columns(table_name)
        pg_schema_df = pd.DataFrame(pg_schema, columns=['column_name' , 'data_type'])
        pg_to_rds_data_api_map = {
            "serial": {"type": "intValue"},
            "bigserial": {"type": "bigIntValue"},
            "smallint": {"type": "longValue"},
            "integer": {"type": "longValue"},
            "bigint": {"type": "longValue"},
            "decimal": {"type": "stringValue", "typeHint": "DECIMAL"},
            "numeric": {"type": "stringValue", "typeHint": "DECIMAL"},
            "real": {"type": "doubleValue"},
            "character varying": {"type": "stringValue"},
            "varchar": {"type": "stringValue"},
            "character": {"type": "stringValue"},
            "char": {"type": "stringValue"},
            "text": {"type": "stringValue"},
            "bytea": {"type": "blobValue"},
            "timestamp": {"type": "stringValue", "typeHint": "TIMESTAMP"},
            "timestamp with time zone": {"type": "stringValue", "typeHint": "TIMESTAMP"},
            "timestamp without time zone": {"type": "stringValue", "typeHint": "TIMESTAMP"},
            "date": {"type": "stringValue", "typeHint": "DATE"},
            "time": {"type": "stringValue", "typeHint": "TIME"},
            "time with time zone": {"type": "stringValue", "typeHint": "TIME"},
            "time without time zone": {"type": "stringValue", "typeHint": "TIME"},
            "interval": {"type": "stringValue"},
            "boolean": {"type": "bitValue"},
            "json": {"type": "stringValue", "typeHint": "JSON"},
            "jsonb": {"type": "stringValue", "typeHint": "JSON"},
            "uuid": {"type": "stringValue", "typeHint": "UUID"},
            "xml": {"type": "stringValue"},
            "inet": {"type": "stringValue"}
        }       
     
        row_data = []
        for col, value in row.items():
            pg_type = self.get_column_data_type(pg_schema_df,col)
            rds_mapping = pg_to_rds_data_api_map.get(pg_type, {"type": "stringValue"})
            if pg_type == 'USER-DEFINED' or pg_type == 'decimal' or pg_type == 'numeric':
                value = str(value)
            if value == None:
                field_data = {"name": col, "value": {"isNull": True}}
            else:
                field_data = {"name": col, "value": {rds_mapping["type"]: value}}
            if "typeHint" in rds_mapping:
                field_data["typeHint"] = rds_mapping["typeHint"]
            #print(f"map_row_to_rds_format field_data --> {field_data} ")
            row_data.append(field_data)
        return row_data
        
    def format_records(self,table_df, table_name):
        sql_parameter_sets = table_df.apply(lambda row: self.map_row_to_rds_format(table_name,row), axis=1).tolist()
        #print(f"sql_parameter_sets[0]\n {sql_parameter_sets[0]}")
        return sql_parameter_sets
        
    def formatOutputJsonRecords(self,records):
        return json.loads(records['formattedRecords'])
        
    def get_table_columns(self, table_name):
        sql_stmnt = f"SELECT table_catalog as db_name,table_schema,table_name , column_name , ordinal_position, data_type ,\
                      column_default, is_nullable  FROM information_schema.columns where table_name = '{table_name}'\
                      order by ordinal_position;"
        response = self.formatOutputJsonRecords(self.execute_statement(sql_stmnt))
        #print(f"get_table_columns response \n {response}")
        return response

    def get_table_column_names(self, table_name):
        return [item["column_name"] for item in self.get_table_columns(table_name)]
        
    def format_insert_stmnt(self, table_name, table_columns, vector_column=None):
        values_columns = f""":{table_columns[0]},:{',:'.join(table_columns[1:-1])}"""
        if vector_column:
            values_columns = values_columns + f",vector(:{vector_column})" 
        else:
            values_columns = values_columns + ",:" + table_columns[-1]
        def_columns = f"""{str(table_columns).replace("[","").replace("]","").replace("'","")} """
        insert_stmnt = f"insert into {table_name} ({def_columns}) values ({values_columns})"

        return insert_stmnt
     