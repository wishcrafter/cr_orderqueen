from fastapi import FastAPI, HTTPException, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from datetime import datetime
from dotenv import load_dotenv
from cr_orderqueen import process_daily_sales  # process_daily_sales 함수를 직접 import
import os

# 환경변수 로드
load_dotenv()

app = FastAPI(title="OrderQueen Crawler API")

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
    return {
        "status": "healthy", 
        "timestamp": datetime.now().isoformat(),
        "env_check": {
            "OQ_ID": "설정됨" if os.getenv('OQ_ID') else "설정안됨",
            "OQ_PASSWORD": "설정됨" if os.getenv('OQ_PASSWORD') else "설정안됨",
            "SUPABASE_URL": "설정됨" if os.getenv('SUPABASE_URL') else "설정안됨",
            "SUPABASE_KEY": "설정됨" if os.getenv('SUPABASE_KEY') else "설정안됨"
        }
    }

@app.post("/api/crawl")
async def crawl_data(crawl_request: CrawlRequest):
    """데이터 수집 API 엔드포인트"""
    try:
        # 날짜 형식 검증
        try:
            start = datetime.strptime(crawl_request.start_date, '%Y-%m-%d')
            end = datetime.strptime(crawl_request.end_date, '%Y-%m-%d')
            if start > end:
                raise ValueError("시작일이 종료일보다 늦을 수 없습니다.")
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        # 환경변수 검증
        if not os.getenv('OQ_ID') or not os.getenv('OQ_PASSWORD'):
            raise HTTPException(
                status_code=400,
                detail="OrderQueen 로그인 정보가 설정되지 않았습니다. (.env 파일을 확인해주세요)"
            )

        # 크롤링 실행 (비동기 함수 호출)
        result = await process_daily_sales(
            start_date=crawl_request.start_date,
            end_date=crawl_request.end_date
        )

        if result["status"] == "success":
            return JSONResponse({
                "status": "success",
                "message": "데이터 수집 및 업로드 완료",
                "files_processed": len(result["files"]),
                "processed_files": result["files"]
            })
        else:
            raise HTTPException(status_code=500, detail=result["message"])

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001) 