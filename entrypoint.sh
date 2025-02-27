#!/bin/bash

echo "⏳ Waiting for PostgreSQL to be ready..."
export PGPASSWORD="ahmed2003"

# Wait until PostgreSQL is ready
until pg_isready -h eden-postgres -p 5432 -U postgres; do
  echo "⌛ PostgreSQL is still loading..."
  sleep 2
done

echo "✅ PostgreSQL is ready!"

# Check if the database exists
DB_EXIST=$(psql -h eden-postgres -U postgres -tAc "SELECT 1 FROM pg_database WHERE datname='eden'")

if [[ "$DB_EXIST" != "1" ]]; then
  echo "📌 Database 'eden' does not exist, creating it..."
  psql -h eden-postgres -U postgres -c "CREATE DATABASE eden;"
  echo "✅ Database 'eden' created successfully!"
  
  echo "📌 Restoring backup..."
  pg_restore --verbose --clean --if-exists --no-owner --exit-on-error -h eden-postgres -U postgres -d eden /app/eden.backup
  
  if [ $? -eq 0 ]; then
    echo "✅ Backup restored successfully!"
  else
    echo "⚠️ Backup restoration failed!"
  fi
else
  echo "✅ Database already exists, skipping restoration."
fi

# Start the application
exec python /app/global_analysis.py
