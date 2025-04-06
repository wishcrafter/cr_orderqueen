from fastapi import FastAPI, HTTPException, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from datetime import datetime
from dotenv import load_dotenv
from cr_orderqueen import process_daily_sales
import os
import logging
import traceback
from fastapi.middleware.cors import CORSMiddleware

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 환경변수 로드
load_dotenv()

app = FastAPI(title="OrderQueen Crawler API")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# HTML 템플릿 설정
templates = Jinja2Templates(directory="templates")

class CrawlRequest(BaseModel):
    start_date: str
    end_date: str

@app.get("/")
async def home(request: Request):
    """웹 인터페이스 홈페이지"""
    return templates.TemplateResponse(
        "index.html",
        {"request": request}
    )

@app.get("/api/health")
async def health_check():
    """API 상태 확인"""
    env_vars = {
        "OQ_ID": os.getenv('OQ_ID'),
        "OQ_PASSWORD": os.getenv('OQ_PASSWORD'),
        "SUPABASE_URL": os.getenv('SUPABASE_URL'),
        "SUPABASE_KEY": os.getenv('SUPABASE_KEY')
    }
    
    missing_vars = [key for key, value in env_vars.items() if not value]
    
    status = "healthy" if not missing_vars else "warning"
    
    return {
        "status": status,
        "timestamp": datetime.now().isoformat(),
        "env_check": {
            key: "설정됨" if value else "설정안됨" for key, value in env_vars.items()
        },
        "missing_env_vars": missing_vars if missing_vars else None
    }

@app.post("/api/crawl")
async def crawl_data(crawl_request: CrawlRequest):
    """데이터 수집 API 엔드포인트"""
    try:
        logger.info(f"크롤링 시작: {crawl_request.start_date} ~ {crawl_request.end_date}")
        
        # 날짜 형식 검증
        try:
            start = datetime.strptime(crawl_request.start_date, '%Y-%m-%d')
            end = datetime.strptime(crawl_request.end_date, '%Y-%m-%d')
            if start > end:
                raise ValueError("시작일이 종료일보다 늦을 수 없습니다.")
        except ValueError as e:
            logger.error(f"날짜 형식 오류: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))

        # 환경변수 검증
        env_vars = {
            "OQ_ID": os.getenv('OQ_ID'),
            "OQ_PASSWORD": os.getenv('OQ_PASSWORD'),
            "SUPABASE_URL": os.getenv('SUPABASE_URL'),
            "SUPABASE_KEY": os.getenv('SUPABASE_KEY')
        }
        
        missing_vars = [key for key, value in env_vars.items() if not value]
        if missing_vars:
            error_msg = f"필수 환경변수가 설정되지 않았습니다: {', '.join(missing_vars)}"
            logger.error(error_msg)
            raise HTTPException(status_code=400, detail=error_msg)

        # 크롤링 실행
        logger.info("process_daily_sales 함수 실행 시작")
        result = await process_daily_sales(
            start_date=crawl_request.start_date,
            end_date=crawl_request.end_date
        )
        logger.info(f"process_daily_sales 실행 결과: {result}")

        if result["status"] == "success":
            response_data = {
                "status": "success",
                "message": "데이터 수집 및 업로드 완료",
                "files_processed": len(result["files"]),
                "processed_files": result["files"]
            }
            logger.info(f"크롤링 성공: {response_data}")
            return JSONResponse(response_data)
        else:
            error_msg = f"크롤링 실패: {result['message']}"
            logger.error(error_msg)
            raise HTTPException(status_code=500, detail=error_msg)

    except Exception as e:
        error_msg = f"예외 발생: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        timeout_keep_alive=120,
        log_level="info"
    ) 