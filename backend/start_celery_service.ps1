# Set project directory and log path
$projectDir = "C:\Users\user\health_monitoring_system\backend"
$logDir = Join-Path $projectDir "logs"
$logFile = Join-Path $logDir ("celery_service_log_" + (Get-Date -Format "yyyy-MM-dd") + ".txt")

# Ensure log directory exists
if (!(Test-Path -Path $logDir)) {
    New-Item -Path $logDir -ItemType Directory | Out-Null
}

# Activate the virtual environment
$venvPath = Join-Path $projectDir "venv\Scripts\Activate.ps1"
. $venvPath

# Start transcript
Start-Transcript -Path "$logDir\startup_debug.txt" -Append
Write-Output "Task started at $(Get-Date -Format G)"

# Start Redis using Docker (attempt restart if container exists)
Write-Output "Starting Redis..."
# Kill any containers using port 6379
$portInUse = docker ps --format "{{.ID}} {{.Ports}}" | Select-String "0.0.0.0:6379"
if ($portInUse) {
    $containerId = ($portInUse -split " ")[0]
    Write-Output "Stopping conflicting container: $containerId"
    docker stop $containerId >> $logFile 2>&1
    docker rm $containerId >> $logFile 2>&1
}

# Remove previous conflicting redis container if it exists
$existingContainer = docker ps -a --filter "name=my-redis-server" --format "{{.ID}}"
if ($existingContainer) {
    Write-Output "Removing old container: $existingContainer"
    docker rm $existingContainer >> $logFile 2>&1
}

# Now run a fresh Redis container
Write-Output "Running fresh Redis container..."
docker run --name my-redis-server -p 6379:6379 -d redis >> $logFile 2>&1


Start-Sleep -Seconds 5

# Start Celery Worker
Start-Process -FilePath "powershell.exe" -ArgumentList "-NoProfile -WindowStyle Hidden -Command `"cd '$projectDir'; celery -A core worker -l info -P threads --concurrency=4 | Tee-Object -FilePath '$logFile' -Append`"" -WindowStyle Hidden

Start-Sleep -Seconds 10

# Start Celery Beat (direct log to file)
Start-Process -FilePath "powershell.exe" -ArgumentList "-NoProfile -WindowStyle Hidden -Command `"cd '$projectDir'; celery -A core beat -l info >> '$logFile' 2>&1`"" -WindowStyle Hidden

Start-Sleep -Seconds 3600 # Sleep for 1 hour

# Stop Celery Worker and Beat (Terminate processes)
Stop-Process -Name "celery" -Force

# Stop Redis container
docker stop my-redis-server


Write-Output "Task completed at $(Get-Date -Format G)"
Stop-Transcript
