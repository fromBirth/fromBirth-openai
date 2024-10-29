import os
import asyncio
from fastapi import APIRouter, HTTPException
from openai import OpenAI
from pydantic import BaseModel
from typing import List
from dotenv import load_dotenv

# .env 파일에서 환경 변수 로드(윈도우 환경에서 실행)
load_dotenv()

router = APIRouter(prefix="/assistant", tags=["Assistant"])
metadata_assistant = {
    "name": "FromBirth Assistant API version 1",
    "description": "Version 1 AI API for FromBirth"
}

# OpenAI API 키 설정
API_KEY = os.getenv("OPENAI_API_KEY")
SURVEY_ASSISTANT_ID = os.getenv("OPENAI_SURVEY_ASSISTANT_ID")
ADVICE_ASSISTANT_ID = os.getenv("OPENAI_ADVICE_ASSISTANT_ID")
client = OpenAI(api_key=API_KEY)


# 요청 모델 정의 (여러 개의 일기를 받을 수 있도록 리스트 형태로 수정)
class DiaryRequest(BaseModel):
    diary_content: List[str]


# thread 생성 함수
async def create_thread():
    try:
        thread = client.beta.threads.create()
        return thread
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create thread: {str(e)}")


async def poll_run_async(run, thread):
    while run.status != "completed":
        run = client.beta.threads.runs.retrieve(
            thread_id=thread.id,
            run_id=run.id
        )
        await asyncio.sleep(0.5)  # 비동기 sleep
    return run


async def create_run_async(thread_id, assistant_id):
    run = client.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=assistant_id,
    )
    return run


async def delete_thread(thread_id):
    try:
        client.beta.threads.delete(thread_id=thread_id)
        print(f"Thread {thread_id} deleted.")
    except Exception as e:
        print(f"Failed to delete thread {thread_id}: {str(e)}")


async def process_diary(diary_content_list, assistant_id):
    try:
        # 새로운 thread 생성
        thread = await create_thread()

        # 모든 일기에 대해 사용자 메시지 생성
        for diary_content in diary_content_list:
            if not diary_content:
                raise HTTPException(status_code=400, detail="Diary content cannot be empty")

            # 사용자 메시지 생성
            client.beta.threads.messages.create(
                thread_id=thread.id,
                role="user",
                content=diary_content
            )

        # 비동기적으로 run 생성 및 상태 확인
        run = await create_run_async(thread.id, assistant_id)
        completed_run = await poll_run_async(run, thread)

        # 메시지 리스트에서 assistant의 모든 응답 찾기
        messages = client.beta.threads.messages.list(thread_id=thread.id)
        messages_list = list(messages)

        return thread, messages_list
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 질문 처리 엔드포인트 (일주일치 일기 분석 후 스레드 삭제)
@router.post(
    path="/analyze", summary="Analyze a diary"
)
async def analyze_diary(request: DiaryRequest):
    global value
    try:
        # 일기 처리 로직 함수 호출
        thread, messages_list = await process_diary(request.diary_content, SURVEY_ASSISTANT_ID)

        # 모든 assistant 메시지의 일치 항목 수 합산
        total_matches = 0
        for message in messages_list:
            if message.role == "assistant":
                if isinstance(message.content, list):
                    for block in message.content:
                        print(f"Block: {block}")  # 각 block의 실제 구조 출력

                        # block이 올바른 구조인지 확인 후 처리
                        if hasattr(block, 'text') and hasattr(block.text, 'value'):
                            value = block.text.value
                            try:
                                matches = int(value.strip())
                                total_matches += matches
                            except ValueError:
                                raise HTTPException(status_code=500, detail="Invalid response from assistant block")
                            

        # 스레드를 삭제하고 결과 반환
        await delete_thread(thread.id)
        return {"total_matches": total_matches}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 육아 조언에 대한 API 엔드 포인트
@router.post(
    path="/advice", summary="Assistant Advice"
)
async def give_advice(request: DiaryRequest):
    try:
        # 일기 처리 로직 함수 호출
        thread, messages_list = await process_diary(request.diary_content, ADVICE_ASSISTANT_ID)

        # 모든 assistant 메시지에서 text value 값만 추출
        advice_responses = []
        for message in messages_list:
            if message.role == "assistant" and isinstance(message.content, list):
                for block in message.content:
                    advice_responses.append(block.text.value)

        # 스레드를 삭제하고 결과 반환
        await delete_thread(thread.id)
        return {"advice_responses": advice_responses}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
