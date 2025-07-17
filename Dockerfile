FROM python:3.11-slim

# Установка ffmpeg и зависимостей
RUN apt-get update && apt-get install -y ffmpeg libsndfile1 && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . /app

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

ENV PYTHONUNBUFFERED=1

CMD ["python", "-m", "ona.bot.main"]
