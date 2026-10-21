# Apaga la VM de forma ordenada (como presionar el boton de encendido).
# Ubuntu cierra MongoDB y la app correctamente antes de apagarse.
$VBox = "C:\Program Files\Oracle\VirtualBox\VBoxManage.exe"
$VM   = "ubuntu-iot"

if (-not (& $VBox list runningvms | Select-String $VM)) {
    Write-Host "La VM ya estaba apagada." -ForegroundColor Green
    exit 0
}

Write-Host "Apagando la VM de forma ordenada..." -ForegroundColor Cyan
& $VBox controlvm $VM acpipowerbutton

for ($i = 0; $i -lt 40; $i++) {
    Start-Sleep -Seconds 3
    if (-not (& $VBox list runningvms | Select-String $VM)) {
        Write-Host "VM apagada correctamente." -ForegroundColor Green
        exit 0
    }
}
Write-Host "La VM no se apago en 2 minutos. Revisala en VirtualBox (no la fuerces sin avisar)." -ForegroundColor Yellow
