# Start portable MongoDB (user install, no Windows service required)
$mongod = "$env:USERPROFILE\mongodb-local\mongodb-win32-x86_64-windows-7.0.16\bin\mongod.exe"
$dataPath = "$env:USERPROFILE\mongodb-data"
$logPath = "$dataPath\mongod.log"

if (-not (Test-Path $mongod)) {
    Write-Error "mongod.exe not found at $mongod. Re-run the portable install first."
    exit 1
}

New-Item -ItemType Directory -Force -Path $dataPath | Out-Null
Write-Host "Starting MongoDB on mongodb://localhost:27017 ..."
Write-Host "Data: $dataPath"
Write-Host "Log:  $logPath"
& $mongod --dbpath $dataPath --logpath $logPath --bind_ip 127.0.0.1 --port 27017
