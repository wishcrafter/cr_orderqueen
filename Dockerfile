# Python 3.11 이미지 사용
FROM python:3.11-slim

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 의존성 설치 (Playwright 필요)
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    xvfb \
    && wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list' \
    && apt-get update \
    && apt-get install -y \
    google-chrome-stable \
    fonts-ipafont-gothic \
    fonts-wqy-zenhei \
    fonts-thai-tlwg \
    fonts-kacst \
    fonts-freefont-ttf \
    libxss1 \
    xauth \
    x11-utils \
    && rm -rf /var/lib/apt/lists/*

# 의존성 파일 복사 및 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Playwright 설치
RUN playwright install chromium
RUN playwright install-deps

# 애플리케이션 파일 복사
COPY . .

# 포트 설정
EXPOSE 8080

# xvfb 실행 스크립트 생성
RUN echo '#!/bin/bash\nxvfb-run --server-args="-screen 0 1280x800x24" uvicorn app:app --host 0.0.0.0 --port 8080' > /app/start.sh \
    && chmod +x /app/start.sh

# 실행 명령어
CMD ["/app/start.sh"] 