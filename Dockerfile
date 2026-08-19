FROM python:3.9

# تثبيت برنامج معالجة الصوت FFmpeg
RUN apt-get update && apt-get install -y ffmpeg

WORKDIR /app
COPY . /app

# تحديث أداة التثبيت
RUN pip install --upgrade pip

# تثبيت مكتبات البايثون
RUN pip install --no-cache-dir -r requirements.txt

# أمر تشغيل البوت
CMD ["python", "main.py"]
