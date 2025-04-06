# OrderQueen Data Collector

OrderQueen 사이트에서 매출 데이터를 수집하고 Supabase에 저장하는 웹 애플리케이션입니다.

## 기능

- 지정된 기간의 매출 데이터 수집
- 수집된 데이터 Supabase 저장
- 편리한 웹 인터페이스
- 지난달, 최근 1주 등 빠른 날짜 선택

## 설치 방법

1. 저장소 클론
```bash
git clone [repository-url]
cd [repository-name]
```

2. 가상환경 생성 및 활성화
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. 의존성 설치
```bash
pip install -r requirements.txt
```

4. 환경 변수 설정
`.env` 파일을 생성하고 다음 내용을 입력:
```
OQ_ID=your_orderqueen_id
OQ_PASSWORD=your_orderqueen_password
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
```

## 실행 방법

```bash
python app.py
```

서버가 실행되면 `http://localhost:8000`으로 접속할 수 있습니다.

## 주의사항

- `.env` 파일에는 민감한 정보가 포함되어 있으므로 절대 깃허브에 커밋하지 마세요.
- 다운로드된 엑셀 파일은 자동으로 처리 후 삭제됩니다. 