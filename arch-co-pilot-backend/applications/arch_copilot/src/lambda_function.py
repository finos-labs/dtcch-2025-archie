import json
import yaml
import logging
from datetime import datetime
from botocore.exceptions import ClientError
import boto3
import pandas as pd
from fastapi.responses import StreamingResponse
import asyncio
from fastapi import FastAPI, APIRouter, Request, Header
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum
from pydantic import BaseModel
from typing import Dict, Any

from common.session_memory import SessionMemory
from common.utils import load_config
from src.process_event import ProcessEvent
from src.process_request import AsyncProcessRequest




logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

common_config = load_config("common/config.yaml")
app_config = load_config("./config.yaml")
config = {**common_config, **app_config}

print(f"config --- \n {config}")

s3_c = boto3.client('s3')
bedrock_runtime = boto3.client(service_name='bedrock-runtime')
rds_client = boto3.client('rds-data')
polly = boto3.client('polly')



app = FastAPI()
router_questionAnswer = APIRouter()

print(f"inside lambda")

   
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_methods=["*"],
    allow_headers=["*"],
)


  
#event = {"headers": {"conversationtopic": "abc", "eventdatetime": "abc", "sessionid": "abc", "userid": "abc"},  "body": '{"userQuestion": "what are the Benefits of active/active architecture in cluster linking"}'}



# POST endpoint
@router_questionAnswer.post("/questionAnswer")
async def stream_response(event: Request):
    headers = dict(event.headers)
    print(f"Headers: {headers}")
    body = await event.json()
    print(f"stream_response body \n {body}")
    event = {"headers": headers, "body": body}
    # for manual testing
    #event = body
    event_type = 'question_answer'
    print(f"event \n {event}")
    async_proc_request = AsyncProcessRequest(bedrock_runtime, rds_client, s3_c, polly, config, event, event_type)
    print("AsyncProcessRequest initialized ")

    async def response_generator():
        async for response in async_proc_request.process_request_stream():
            yield f" {response} \n\n"

    async for data in response_generator():
        print(data)

    return StreamingResponse(response_generator(), media_type="text/event-stream")

  
app.include_router(router_questionAnswer)

handler = Mangum(router_questionAnswer)


