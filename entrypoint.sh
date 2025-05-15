#!/bin/bash

echo "⏳ Waiting for PostgreSQL to be ready..."
export PGPASSWORD="ahmed2003"

# Wait until PostgreSQL is ready
until pg_isready -h db -p 5432 -U postgres; do
  echo "⌛ PostgreSQL is still loading..."
  sleep 2
done

echo "✅ PostgreSQL is ready!"

# Create flask_session directory with proper permissions
mkdir -p /app/flask_session
chmod 777 /app/flask_session

# Check if the database exists
DB_EXIST=$(psql -h db -U postgres -tAc "SELECT 1 FROM pg_database WHERE datname='eden'")

if [[ "$DB_EXIST" != "1" ]]; then
  echo "📌 Database 'eden' not found. Creating it..."
  psql -h db -U postgres -c "CREATE DATABASE eden;"
  echo "✅ Database 'eden' created successfully!"
fi

# Check if schema 'sensor_readings' exists
SCHEMA_EXIST=$(psql -h db -U postgres -d eden -tAc "SELECT 1 FROM information_schema.schemata WHERE schema_name='sensor_readings';")

if [[ "$SCHEMA_EXIST" == "1" ]]; then
  echo "⚠️ Schema 'sensor_readings' found. Skipping restore to preserve data."
else
  echo "📌 Schema 'sensor_readings' not found. Proceeding with backup restore..."
  
  # Create a temporary file for modified backup
  TMP_BACKUP="/tmp/eden_modified.backup"
  
  # Remove transaction_timeout setting from backup
  sed '/SET transaction_timeout/d' /app/eden.backup > "$TMP_BACKUP"
  
  # Restore from modified backup
  pg_restore --verbose --clean --if-exists --no-owner --no-privileges -h db -U postgres -d eden "$TMP_BACKUP"

  if [ $? -eq 0 ]; then
    echo "✅ Backup restored successfully!"
  else
    echo "⚠️ Backup restoration failed!"
  fi
  
  # Clean up
  rm -f "$TMP_BACKUP"
fi

# Start the application
exec python /app/global_analysis.py
