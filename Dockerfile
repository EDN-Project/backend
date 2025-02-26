FROM python:latest

# تثبيت PostgreSQL Client
RUN apt-get update && apt-get install -y postgresql-client

# إنشاء مجلد للتطبيق
WORKDIR /app

# نسخ كود التطبيق وقاعدة البيانات
COPY . /app

# جعل `entrypoint.sh` قابلاً للتنفيذ
RUN chmod +x /app/entrypoint.sh

# تثبيت المتطلبات
RUN pip install --no-cache-dir -r /app/requirements.txt

# تشغيل السكريبت عند بدء التشغيل
ENTRYPOINT ["/bin/bash", "/app/entrypoint.sh"]