
$ErrorActionPreference = "SilentlyContinue"
Write-Host "Waiting for Docker to start..."
while ($true) {
    docker ps | Out-Null
    if ($?) {
        Write-Host "Docker is running!"
        exit 0
    }
    Write-Host -NoNewline "."
    Start-Sleep -Seconds 2
}
