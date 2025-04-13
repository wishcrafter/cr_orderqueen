from playwright.async_api import async_playwright, TimeoutError
import os
from dotenv import load_dotenv
import time
from urllib.parse import urlencode
import pandas as pd
from supabase import create_client
from datetime import datetime
import asyncio

# 수집할 매장 ID 리스트
TARGET_STORES = ['1001', '1003', '1004', '1005']

async def analyze_excel_structure(file_path: str) -> dict:
    """
    엑셀 파일의 구조를 분석
    Args:
        file_path: 엑셀 파일 경로
    Returns:
        dict: 파일 구조 정보
    """
    try:
        df = pd.read_excel(file_path, header=2)
        
        info = {
            'columns': list(df.columns),
            'dtypes': df.dtypes.to_dict(),
            'row_count': len(df),
            'sample_data': df.head(1).to_dict('records')[0] if not df.empty else None
        }
        
        print("\n=== 엑셀 파일 구조 분석 ===")
        print(f"컬럼 목록: {info['columns']}")
        print(f"데이터 타입: {info['dtypes']}")
        print(f"총 행 수: {info['row_count']}")
        print("\n샘플 데이터:")
        for key, value in info['sample_data'].items():
            print(f"  {key}: {value}")
            
        return info
    except Exception as e:
        print(f"파일 분석 중 오류 발생: {str(e)}")
        return None

async def get_supabase_table_info(table_name: str = 'sales') -> dict:
    """
    Supabase 테이블 구조 확인
    Args:
        table_name: 테이블 이름
    Returns:
        dict: 테이블 구조 정보
    """
    try:
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_KEY')
        
        if not supabase_url or not supabase_key:
            raise ValueError('Supabase 연결 정보가 없습니다.')
        
        supabase = create_client(supabase_url, supabase_key)
        
        result = await supabase.table(table_name).select("*").limit(1).execute()
        
        if result.data:
            sample_record = result.data[0]
            info = {
                'columns': list(sample_record.keys()),
                'sample_data': sample_record
            }
            
            print("\n=== Supabase 테이블 구조 ===")
            print(f"테이블명: {table_name}")
            print(f"컬럼 목록: {info['columns']}")
            print("\n샘플 데이터:")
            for key, value in info['sample_data'].items():
                print(f"  {key}: {value}")
                
            return info
        else:
            print(f"테이블 {table_name}에 데이터가 없습니다.")
            return None
            
    except Exception as e:
        print(f"테이블 정보 조회 중 오류 발생: {str(e)}")
        return None

async def upload_to_supabase(file_path: str, store_id: str) -> bool:
    """
    엑셀 파일을 읽어서 Supabase에 업로드
    Args:
        file_path: 엑셀 파일 경로
        store_id: 매장 ID
    Returns:
        bool: 업로드 성공 여부
    """
    try:
        print(f"\n=== Supabase 업로드 시작 ({store_id}) ===")
        print(f"파일 경로: {file_path}")
        
        df = pd.read_excel(file_path, header=2)
        print(f"엑셀 파일 읽기 완료: {len(df)} 행")
        
        df_processed = pd.DataFrame({
            'sales_date': df.iloc[:, 0],
            'store_id': store_id,
            'total_amount': df.iloc[:, 2],
            'transaction_count': df.iloc[:, 4],
            'cash_amount': df.iloc[:, 10],
            'card_amount': df.iloc[:, 11],
            'etc_amount': df.iloc[:, 13]
        })
        
        print("데이터 전처리 시작...")
        df_processed['sales_date'] = pd.to_datetime(df_processed['sales_date']).dt.strftime('%Y-%m-%d')
        df_processed['total_amount'] = pd.to_numeric(df_processed['total_amount'], errors='coerce')
        df_processed['transaction_count'] = pd.to_numeric(df_processed['transaction_count'], errors='coerce')
        df_processed['cash_amount'] = pd.to_numeric(df_processed['cash_amount'], errors='coerce')
        df_processed['card_amount'] = pd.to_numeric(df_processed['card_amount'], errors='coerce')
        df_processed['etc_amount'] = pd.to_numeric(df_processed['etc_amount'], errors='coerce')
        
        df_processed = df_processed.fillna(0)
        print("데이터 전처리 완료")
        
        print("\n=== 처리된 데이터 샘플 ===")
        print(df_processed.head())
        print(f"\n총 레코드 수: {len(df_processed)}")
        
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_KEY')
        
        print(f"\nSupabase URL: {supabase_url[:20] if supabase_url else 'None'}...")
        print(f"Supabase Key: {supabase_key[:10] if supabase_key else 'None'}...")
        
        if not supabase_url or not supabase_key:
            raise ValueError('Supabase 연결 정보가 없습니다.')
        
        print("\nSupabase 클라이언트 생성 시도...")
        try:
            supabase = create_client(supabase_url, supabase_key)
            print("Supabase 클라이언트 생성 성공")
        except Exception as e:
            print(f"Supabase 클라이언트 생성 실패: {str(e)}")
            if hasattr(e, '__dict__'):
                print(f"클라이언트 생성 에러 상세: {e.__dict__}")
            raise
        
        records = df_processed.to_dict('records')
        print(f"업로드할 레코드 수: {len(records)}")
        print("\n첫 번째 레코드 샘플:")
        print(records[0] if records else "레코드 없음")
        
        print("\nSupabase 테이블 업로드 시도...")
        try:
            print("1. 테이블 접근...")
            table = supabase.table('sales')
            print("2. Upsert 실행...")
            result = table.upsert(
                records,
                on_conflict='store_id,sales_date'
            ).execute()
            print("3. 실행 완료")
            print(f"\nSupabase 응답 데이터: {result.data if hasattr(result, 'data') else '없음'}")
            if hasattr(result, 'data') and result.data:
                print(f"업로드된 레코드 수: {len(result.data)}")
                print(f"\n{store_id} 매장 데이터 업로드 성공 (총 {len(result.data)}개 레코드)")
                return True
            else:
                print(f"\n{store_id} 매장 데이터 업로드 실패: 응답 데이터 없음")
                return False
        except Exception as e:
            print(f"\nSupabase 업로드 중 예외 발생:")
            print(f"예외 타입: {type(e)}")
            print(f"예외 메시지: {str(e)}")
            if hasattr(e, '__dict__'):
                print(f"예외 상세 정보: {e.__dict__}")
            raise
        
    except Exception as e:
        print(f"\n=== Supabase 업로드 실패 ===")
        print(f"매장 ID: {store_id}")
        print(f"에러 메시지: {str(e)}")
        print(f"에러 타입: {type(e)}")
        if hasattr(e, '__dict__'):
            print(f"에러 상세 정보: {e.__dict__}")
        return False

async def download_daily_sales(start_date: str, end_date: str) -> list:
    """
    OrderQueen 일별매출 데이터 다운로드
    Args:
        start_date: 시작일자 (YYYY-MM-DD)
        end_date: 종료일자 (YYYY-MM-DD)
    Returns:
        list: 다운로드된 파일 경로 리스트
    """
    load_dotenv()
    user_id = os.getenv('OQ_ID')
    password = os.getenv('OQ_PASSWORD')
    
    if not user_id or not password:
        raise ValueError('.env 파일에 로그인 정보가 없습니다.')
    
    downloaded_files = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
        )
        context = await browser.new_context(
            accept_downloads=True,
            viewport={'width': 1920, 'height': 1080}
        )
        page = await context.new_page()
        
        try:
            print("로그인 중...")
            await page.goto('https://www.orderqueen.kr/backoffice_admin/login.itp')
            await page.wait_for_load_state('networkidle')
            
            # 로그인 폼이 완전히 로드될 때까지 대기
            await page.wait_for_selector('input[name="userId"]', timeout=60000)
            await page.wait_for_timeout(2000)  # 추가 대기
            
            id_input = await page.wait_for_selector('input[name="userId"]', timeout=60000)
            await id_input.fill(user_id)
            await page.wait_for_timeout(1000)  # 입력 후 대기
            
            pw_input = await page.wait_for_selector('input[name="pw"]', timeout=60000)
            await pw_input.fill(password)
            await page.wait_for_timeout(1000)  # 입력 후 대기
            
            login_button = await page.wait_for_selector('#btnLoginNew', timeout=60000)
            await login_button.click()
            
            # 로그인 후 페이지 로딩 대기
            await page.wait_for_load_state('networkidle', timeout=60000)
            await page.wait_for_timeout(5000)  # 로그인 후 추가 대기
            
            for store_id in TARGET_STORES:
                try:
                    print(f"\n{store_id} 매장 데이터 다운로드 중...")
                    
                    params = {
                        'currentPageNo': '1',
                        'recordCountPerPage': '15',
                        'pageSize': '15',
                        'schStoreNm': '',
                        'brandCd': 'yumice',
                        'schStoreNo': store_id,
                        'schSDate': start_date,
                        'schEDate': end_date
                    }
                    
                    download_url = f'https://www.orderqueen.kr/backoffice_admin/BSL01010_EXCEL.itp?{urlencode(params)}'
                    
                    async with page.expect_download(timeout=60000) as download_info:
                        await page.evaluate(f"window.location.href = '{download_url}'")
                        try:
                            download = await download_info.value
                            downloaded_path = await download.path()
                            # WindowsPath를 문자열로 변환
                            downloaded_path_str = str(downloaded_path)
                            downloaded_files.append((downloaded_path_str, store_id))
                            print(f"{store_id} 매장 다운로드 완료: {downloaded_path_str}")
                        except Exception as e:
                            print(f"{store_id} 매장 다운로드 실패: {str(e)}")
                            continue
                    
                    await page.wait_for_timeout(3000)
                    
                except Exception as e:
                    print(f"{store_id} 매장 처리 중 에러 발생: {str(e)}")
                    continue
            
            print("\n다운로드된 파일 처리 중...")
            for file_path, store_id in downloaded_files:
                try:
                    print(f"\n{store_id} 매장 데이터 Supabase 업로드 중...")
                    await upload_to_supabase(file_path, store_id)
                except Exception as e:
                    print(f"파일 처리 실패 ({store_id}): {str(e)}")
            
            # 파일 경로만 문자열 리스트로 반환
            return [str(path) for path, _ in downloaded_files]
                
        except Exception as e:
            print(f"에러 발생: {str(e)}")
            raise
            
        finally:
            print("\n브라우저를 종료합니다...")
            await page.wait_for_timeout(3000)
            await browser.close()

async def process_daily_sales(start_date: str, end_date: str) -> dict:
    """
    일별 매출 데이터를 처리하는 함수
    """
    try:
        file_paths = await download_daily_sales(start_date, end_date)
        return {
            "status": "success",
            "message": "데이터 처리가 완료되었습니다.",
            "files": file_paths
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

if __name__ == "__main__":
    async def main():
        result = await process_daily_sales(
            start_date="2024-03-30",
            end_date="2024-03-31"
        )
        print("\n실행 결과:", result)

    asyncio.run(main()) 
