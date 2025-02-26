#!/bin/bash

# انتظار حتى تصبح قاعدة البيانات جاهزة
export PGPASSWORD="$POSTGRES_PASSWORD"
until pg_isready -h db -p 5432 -U $POSTGRES_USER; do
  echo "Waiting for database..."
  sleep 2
done

# التحقق من وجود قاعدة البيانات
if ! psql -h db -U $POSTGRES_USER -d $POSTGRES_DB -c "SELECT 1" &> /dev/null; then
  echo "Restoring database from backup..."
  pg_restore --verbose --clean --if-exists --no-owner --exit-on-error -h db -U $POSTGRES_USER -d $POSTGRES_DB /app/eden.backup
else
  echo "Database already exists, skipping restore."
fi

# تشغيل التطبيق
exec python /app/global_analysis.py