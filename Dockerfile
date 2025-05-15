FROM python:3.13-alpine

# تحديث apk وتثبيت الأدوات المطلوبة مع postgresql-client و bash و tzdata
RUN apk update && apk add --no-cache \
    bash \
    curl \
    gnupg \
    lsb-release \
    postgresql-client \
    tzdata

# ضبط المنطقة الزمنية لمصر
RUN cp /usr/share/zoneinfo/Africa/Cairo /etc/localtime && echo "Africa/Cairo" > /etc/timezone

# تعيين مجلد العمل
WORKDIR /app

# نسخ ملفات التطبيق
COPY . /app

# إعطاء صلاحيات التنفيذ للـ entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# تثبيت مكتبات بايثون المطلوبة
RUN pip install --no-cache-dir -r /app/requirements.txt

# تشغيل السكريبت عند بداية الكونتينر
ENTRYPOINT ["/bin/bash", "/app/entrypoint.sh"]
