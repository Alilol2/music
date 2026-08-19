FROM python:3.10-slim

# تثبيت FFmpeg المطلوب لتشغيل الصوتيات
RUN apt-get update && apt-get install -y ffmpeg

WORKDIR /app
COPY . /app

# تثبيت مكتبات البايثون
RUN pip install --no-cache-dir -r requirements.txt

# أمر تشغيل البوت
CMD ["python", "main.py"]
