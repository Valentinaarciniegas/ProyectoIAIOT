# Enciende la VM (sin ventana), arranca la app Flask y verifica que todo responda.
$VBox = "C:\Program Files\Oracle\VirtualBox\VBoxManage.exe"
$VM   = "ubuntu-iot"

$corriendo = & $VBox list runningvms | Select-String $VM
if ($corriendo) {
    Write-Host "1) La VM ya estaba encendida." -ForegroundColor Cyan
} else {
    Write-Host "1) Encendiendo la VM..." -ForegroundColor Cyan
    & $VBox startvm $VM --type headless | Out-Null
}

Write-Host "2) Esperando a que Ubuntu arranque (SSH)..." -ForegroundColor Cyan
$ok = $false
for ($i = 0; $i -lt 30; $i++) {
    ssh -o BatchMode=yes -o ConnectTimeout=3 cocatrace "true" 2>$null
    if ($LASTEXITCODE -eq 0) { $ok = $true; break }
    Start-Sleep -Seconds 3
}
if (-not $ok) { Write-Host "La VM no respondio por SSH. Abrela en VirtualBox para ver que pasa." -ForegroundColor Red; exit 1 }

Write-Host "3) Revisando los servicios (arrancan solos con la VM)..." -ForegroundColor Cyan
for ($i = 0; $i -lt 10; $i++) {
    $estado = ssh -o BatchMode=yes cocatrace "systemctl is-active mongod cocatrace"
    if (-not ($estado -ne "active")) { break }
    Start-Sleep -Seconds 2
}
Write-Host "   mongod: $($estado[0])   cocatrace (app): $($estado[1])"

Write-Host "4) Verificando /health..." -ForegroundColor Cyan
curl.exe -s -m 5 http://127.0.0.1:5000/health
Write-Host ""

$ip = (Get-NetIPAddress -InterfaceAlias "Wi-Fi" -AddressFamily IPv4 -ErrorAction SilentlyContinue).IPAddress
Write-Host "5) IP de este PC en el WiFi: $ip" -ForegroundColor Cyan
if ($ip -ne "192.168.40.13") {
    Write-Host "   OJO: la IP cambio. El ESP32 apunta a 192.168.40.13; actualiza SERVER_URL en config.h." -ForegroundColor Yellow
}
Write-Host "Dashboard: http://127.0.0.1:5000/" -ForegroundColor Green
