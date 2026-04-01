<#
.SYNOPSIS
    Automated Background USB Listener for Scrcpy
.DESCRIPTION
    This script listens for USB plug-in events via WMI. When a USB is connected,
    it verifies via ADB if an 'authorized' Android device is connected.
    If authorized, it launches Scrcpy with advanced power-saving parameters.
#>

$ErrorActionPreference = "Stop"

# Use the Scrcpy path relative to this script, matching your Python toolkit
$ScrcpyPath = Join-Path -Path $PSScriptRoot -ChildPath "scrcpy-win64-v3.3.4\scrcpy-win64-v3.3.4\scrcpy.exe"

# Make sure Scrcpy exists
if (-not (Test-Path $ScrcpyPath)) {
    Write-Host "[-] Could not find scrcpy.exe at $ScrcpyPath. Please verify the path!" -ForegroundColor Red
    # Fallback to checking PATH
    if (Get-Command "scrcpy.exe" -ErrorAction SilentlyContinue) {
        $ScrcpyPath = "scrcpy.exe"
    } else {
        Exit
    }
}

# The WMI query listens for Win32_DeviceChangeEvent where EventType = 2 (Device Arrival/Plugged-in)
$WmiQuery = "SELECT * FROM Win32_DeviceChangeEvent WHERE EventType = 2"
$Watcher = New-Object System.Management.ManagementEventWatcher
$Watcher.Query = New-Object System.Management.WqlEventQuery($WmiQuery)

Write-Host "================================================" -ForegroundColor Cyan
Write-Host " 🤖 AutoScrcpy USB WMI Listener Started" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "[*] Listening for USB connections in the background..." -ForegroundColor Gray

try {
    while ($true) {
        # This blocks until a USB device is plugged in
        $Event = $Watcher.WaitForNextEvent()
        
        Write-Host "`n[*] USB Event detected! Waiting 2 seconds to allow ADB to mount..." -ForegroundColor Yellow
        Start-Sleep -Seconds 2

        # Check if scrcpy is ALREADY running to prevent spamming multiple instances
        if (Get-Process "scrcpy" -ErrorAction SilentlyContinue) {
            Write-Host "[!] Scrcpy is already running. Skipping trigger." -ForegroundColor Yellow
            continue
        }

        # Query ADB for device status
        $AdbOutput = adb devices
        $IsAuthorized = $false

        foreach ($line in $AdbOutput) {
            # ADB returns formatted text like: "192.168.1.5:5555    device" or "TA1903423  unauthorized"
            if ($line -match "\bdevice\b") {
                $IsAuthorized = $true
                break
            }
        }

        if ($IsAuthorized) {
            Write-Host "[+] DEVICE CONNECTED AND AUTHORIZED!" -ForegroundColor Green
            Write-Host "[>] Launching Scrcpy with power-saving parameters..." -ForegroundColor Green
            
            # Application parameters
            $ScrcpyArgs = @(
                "--always-on-top",
                "--turn-screen-off",
                "--stay-awake",
                "--power-off-on-close"
            )

            # Start Scrcpy in the background hidden from the main terminal shell
            Start-Process -FilePath $ScrcpyPath -ArgumentList $ScrcpyArgs -WindowStyle Hidden
            
            # Debounce sleep to avoid duplicate WMI triggers from the same physical plug event
            Start-Sleep -Seconds 5
        } else {
            Write-Host "[-] USB CONNECTED BUT NOT AN AUTHORIZED ADB DEVICE." -ForegroundColor Red
        }
    }
}
finally {
    # Cleanup watcher if script exits
    $Watcher.Dispose()
}
