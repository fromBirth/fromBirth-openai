import os
import re
from dotenv import load_dotenv
from openai import OpenAI

# .env 파일 로드
load_dotenv()

# 파일 경로 설정 (환경 변수에서 가져오기)
FILE_PATH = os.environ.get("FILE_PATH")
PROCESSED_FILE_PATH = "processed_diagnosis.txt"
SURVEY_ASSISTANT_ID = os.getenv("OPENAI_SURVEY_ASSISTANT_ID")
API_KEY = os.getenv("OPENAI_API_KEY")
VECTOR_STORE_ID = os.getenv("OPENAI_VECTOR_STORE_ID")
client = OpenAI(api_key=API_KEY)


# 전처리 함수 정의
def preprocess_text(text):
    # 특수 기호 제거, 소문자 변환, 공백 정리 등
    text = re.sub(r"[^가-힣\s]", "", text)  # 한글과 공백만 남기기
    text = re.sub(r"\s+", " ", text.strip())  # 다중 공백 제거 및 공백 정리
    return text


# 파일 읽기 및 전처리 수행
def process_file():
    with open(FILE_PATH, "r", encoding="utf-8") as infile, open(PROCESSED_FILE_PATH, "w", encoding="utf-8") as outfile:
        for line in infile:
            cleaned_line = preprocess_text(line)
            if cleaned_line:  # 전처리 결과가 빈 문자열이 아닐 때만 저장
                outfile.write(cleaned_line + "\n")

    # 환경 변수 업데이트 (업로드용 파일 경로를 전처리된 파일로 변경)
    os.environ["FILE_PATH"] = os.path.abspath(PROCESSED_FILE_PATH)
    return os.environ["FILE_PATH"]


def upload_file_to_vector_store(file_path):
    # 벡터 스토어 생성
    vector_store = client.beta.vector_stores.create(name="processed_survey_file")
    print(f"Survey Vector Store ID: {vector_store.id}")

    # 파일 업로드 준비
    with open(file_path, "rb") as file_stream:
        file_batch = client.beta.vector_stores.file_batches.upload_and_poll(
            vector_store_id=vector_store.id,
            files=[file_stream]
        )

    return vector_store.id


def update_assistant(vector_store_id):
    # 어시스턴트 업데이트
    survey_assistant = client.beta.assistants.update(
        assistant_id=SURVEY_ASSISTANT_ID,
        tool_resources={"file_search": {"vector_store_ids": [vector_store_id]}}
    )
    return survey_assistant


# 메인 로직
def main():
    try:
        # Step 1: 파일 전처리 수행
        processed_file_path = process_file()

        # Step 2: 벡터 스토어에 파일 업로드
        vector_store_id = upload_file_to_vector_store(processed_file_path)

        # Step 3: 어시스턴트 업데이트
        updated_assistant = update_assistant(vector_store_id)

        print(f"Assistant updated successfully. : {updated_assistant}")

    except Exception as e:
        print(f"Error: {str(e)}")


if __name__ == "__main__":
    main()
