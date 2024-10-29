from fastapi import FastAPI, APIRouter
from mangum import Mangum
from api.assistantAI import router as assistant_router


# FastAPI 애플리케이션 인스턴스 생성
app = FastAPI()

# APIRouter 인스턴스 생성
api_router = APIRouter(prefix="/api")


@app.get("/healthcheck")
async def healthcheck():
    return {"message": "OK"}


# 각 라우터 등록
api_router.include_router(assistant_router)
app.include_router(api_router)

handler = Mangum(app)
