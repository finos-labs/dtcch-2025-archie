import json
import yaml
import logging
from datetime import datetime
from botocore.exceptions import ClientError
import boto3
import pandas as pd
import asyncio
from fastapi.responses import StreamingResponse, FileResponse
from fastapi import FastAPI, APIRouter, Request, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any

from common.session_memory import SessionMemory
from common.utils import load_config
from src.process_event import ProcessEvent
from src.process_request import AsyncProcessRequest
from common.polly_interface import AsyncPolly




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


print(f"inside chat app")

   
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


router_qa = APIRouter()

# POST endpoint
@router_qa.post("/questionAnswer")
async def text_stream_response(event: Request):
    logger.info("inside question answer")
    headers = dict(event.headers)
    logger.info(f"Headers: {headers}")
    body = await event.json()
    logger.info(f"stream_response body \n {body}")
    event = {"headers": headers, "body": body}
    logger.info(f"event \n {event}")
 
    event_type = 'question_answer'
    async_proc_request = AsyncProcessRequest(bedrock_runtime, rds_client, s3_c, polly, config, event, event_type)
    logger.info("AsyncProcessRequest initialized ")

    async def response_generator():
        async for response in async_proc_request.process_request_stream():
            yield f"{response}"
    
    return StreamingResponse(response_generator(), media_type="text/event-stream")
    
  

app.include_router(router_qa)

router_asa = APIRouter()

@router_asa.post("/audioSynchAnswer")
async def audio_stream_response(event: Request):
    headers = dict(event.headers)
    body = await event.json()
    event = {"headers": headers, "body": body}
    event_type = 'audio_answer'

    async_proc_request = AsyncProcessRequest(bedrock_runtime, rds_client, s3_c, polly, config, event, event_type)
    logger.info("AsyncProcessRequest initialized ")


    llm_answer_text = body['llm_answer_text']
    voice_id = body['voice_id']

    logger.info(f"llm_answer_text \n {llm_answer_text}")
    logger.info(f"voice_id -> {voice_id}")
    
    async def response_generator():
        async for response in async_proc_request.audio_answer_stream(llm_answer_text, voice_id):
            yield f"{response}"
    
    return StreamingResponse(response_generator(), media_type="text/event-stream")
    
app.include_router(router_asa)


router_afa = APIRouter()

@router_afa.post("/audioFileAnswer")
async def audio_stream_response(event: Request):
    headers = dict(event.headers)
    body = await event.json()
    event = {"headers": headers, "body": body}
    event_type = 'audio_file_answer'

    async_proc_request = AsyncProcessRequest(bedrock_runtime, rds_client, s3_c, polly, config, event, event_type)
    logger.info("AsyncProcessRequest initialized ")

    llm_answer_text = body['llm_answer_text']
    voice_id = body['voice_id']

    logger.info(f"llm_answer_text \n {llm_answer_text}")
    logger.info(f"voice_id -> {voice_id}")
    
    async for response_path in async_proc_request.audio_answer_file():
        return FileResponse(response_path, media_type="audio/mpeg",filename=response_path.split('/')[0])

    
app.include_router(router_afa)


router_vfa = APIRouter()

@router_vfa.post("/videoFileAnswer")
async def video_stream_response(event: Request):
    headers = dict(event.headers)
    body = await event.json()
    event = {"headers": headers, "body": body}
    event_type = 'video_file_answer'

    async_proc_request = AsyncProcessRequest(bedrock_runtime, rds_client, s3_c, polly, config, event, event_type)
    logger.info("AsyncProcessRequest initialized ")

    llm_answer_text = body['llm_answer_text']
    voice_id = body['voice_id']
    avatar_name = body['avatar_name']

    logger.info(f"llm_answer_text \n {llm_answer_text}")
    logger.info(f"voice_id -> {voice_id}")
    logger.info(f"avatar_name -> {avatar_name}")
    
    async for video_response_path in async_proc_request.video_answer_file():
        return FileResponse(video_response_path, media_type="video/mp4", filename=video_response_path.split('/')[0])

    
app.include_router(router_vfa)

router_gpv = APIRouter()

@router_gpv.get("/pollyVoices")
async def get_polly_voices():
    """
    Endpoint to retrieve a list of Polly voices that support English.
    """
    # Describe all available voices
    apollyi = AsyncPolly(polly, config)
    return apollyi.get_poly_voices()
    

app.include_router(router_gpv)


router_gaa = APIRouter()

@router_gaa.get("/availableAvatars")
async def get_avatars():
    """
    Endpoint to retrieve a list of all avatars with images.
    """
    # Describe all available voices
    apollyi = AsyncPolly(polly, config)
    return apollyi.get_avatars()
    

app.include_router(router_gaa)

