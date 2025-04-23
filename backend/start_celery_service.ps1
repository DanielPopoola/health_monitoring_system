# Set project directory and log path
$projectDir = "C:\Users\user\health_monitoring_system\backend"
$logDir = Join-Path $projectDir "logs"
$logFile = Join-Path $logDir ("celery_service_log_" + (Get-Date -Format "yyyy-MM-dd") + ".txt")

# Ensure log directory exists
if (!(Test-Path -Path $logDir)) {
    New-Item -Path $logDir -ItemType Directory | Out-Null
}

# Start Redis using Docker (only if not already running)
$redisStatus = docker ps --filter "name=my-redis" --filter "status=running" -q
if (-not $redisStatus) {
    # If container exists but stopped, start it. Otherwise, create it.
    $existingRedis = docker ps -a --filter "name=my-redis" -q
    if ($existingRedis) {
        docker start my-redis | Out-Null
    } else {
        docker run --name my-redis -p 6379:6379 -d redis | Out-Null
    }
}

# Wait a bit to ensure Redis is up
Start-Sleep -Seconds 10

# Start Celery Worker
Start-Process -FilePath "powershell.exe" -ArgumentList "-NoProfile -WindowStyle Hidden -Command `"cd '$projectDir'; celery -A core worker -l info -P threads --concurrency=4 >> '$logFile' 2>&1`"" -WindowStyle Hidden

Start-Sleep -Seconds 10

# Start Celery Beat
Start-Process -FilePath "powershell.exe" -ArgumentList "-NoProfile -WindowStyle Hidden -Command `"cd '$projectDir'; celery -A core beat -l info >> '$logFile' 2>&1`"" -WindowStyle Hidden
