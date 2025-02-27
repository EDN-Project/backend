FROM python:latest

# تثبيت الأدوات المطلوبة وإضافة مستودع PostgreSQL الرسمي
RUN apt-get update && apt-get install -y curl gnupg lsb-release
RUN curl -fsSL https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add -
RUN echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list
RUN apt-get update && apt-get install -y postgresql-client-17

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
