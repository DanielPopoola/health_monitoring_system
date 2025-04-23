# Set project directory and log path
$projectDir = "C:\Users\user\health_monitoring_system\backend"
$logDir = Join-Path $projectDir "logs"
$logFile = Join-Path $logDir ("celery_service_log_" + (Get-Date -Format "yyyy-MM-dd") + ".txt")

# Ensure log directory exists
if (!(Test-Path -Path $logDir)) {
    New-Item -Path $logDir -ItemType Directory | Out-Null
}

# Start Celery Worker
Start-Process -FilePath "powershell.exe" -ArgumentList "-NoProfile -WindowStyle Hidden -Command `"cd '$projectDir'; celery -A core worker -l info -P threads --concurrency=4 >> '$logFile' 2>&1`"" -WindowStyle Hidden

Start-Sleep -Seconds 10

# Start Celery Beat
Start-Process -FilePath "powershell.exe" -ArgumentList "-NoProfile -WindowStyle Hidden -Command `"cd '$projectDir'; celery -A core beat -l info >> '$logFile' 2>&1`"" -WindowStyle Hidden
