FROM python:3.10-slim

# تثبيت FFmpeg وأدوات البناء الأساسية عشان المكتبات تتثبت بدون مشاكل
RUN apt-get update && apt-get install -y ffmpeg gcc g++ make

WORKDIR /app
COPY . /app

# تحديث أداة التثبيت pip أولاً
RUN pip install --upgrade pip setuptools wheel

# تثبيت مكتبات البايثون
RUN pip install --no-cache-dir -r requirements.txt

# أمر تشغيل البوت
CMD ["python", "main.py"]
