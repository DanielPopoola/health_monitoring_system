@echo off
cd C:\Users\user\health_monitoring_system\backend
call venv\Scripts\activate.bat

start "Celery Worker" cmd /k celery -A core worker -l info -P threads --concurrency=4
start "Celery Beat" cmd /k celery -A core beat -l info