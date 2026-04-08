@echo off
echo ========================================
echo   Database Setup
echo ========================================
echo.
echo This will create the 'elearning' database and run migrations.
echo Make sure PostgreSQL is running first!
echo.

set PGPASSWORD=postgres
psql -U postgres -c "CREATE DATABASE elearning;" 2>nul
echo Database created (or already exists)

echo Running migrations...
psql -U postgres -d elearning -f backend\src\db\schema.sql

echo.
echo [OK] Database setup complete!
echo Now run start.bat to launch the platform.
pause
