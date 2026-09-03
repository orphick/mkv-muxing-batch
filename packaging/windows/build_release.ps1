param(
    [string]$Version = "2.7.5",
    [ValidateSet(5, 6)]
    [int]$QtMajor = 6,
    [string]$Python = ""
)

$ErrorActionPreference = "Stop"
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
if ([string]::IsNullOrWhiteSpace($Python)) {
    $Python = if ($QtMajor -eq 5) {
        ".\.venv-qt5\Scripts\python.exe"
    }
    else {
        ".\.venv\Scripts\python.exe"
    }
}
$directorySuffix = if ($QtMajor -eq 5) { "-qt5" } else { "" }
$applicationName = if ($QtMajor -eq 5) { "MKV Muxing Batch GUI Qt5" } else { "MKV Muxing Batch GUI" }
$buildDirectory = Join-Path $projectRoot "build$directorySuffix"
$distDirectory = Join-Path $projectRoot "dist$directorySuffix"
$releaseDirectory = Join-Path $projectRoot "release$directorySuffix"
$specFile = Join-Path $PSScriptRoot $(if ($QtMajor -eq 5) { "MkvMuxingBatchQt5.spec" } else { "MkvMuxingBatch.spec" })
$installerScript = Join-Path $PSScriptRoot $(if ($QtMajor -eq 5) { "InstallerQt5.iss" } else { "Installer.iss" })
$applicationDirectory = Join-Path $distDirectory $applicationName
$portableFile = Join-Path $releaseDirectory "MKV.Muxing.Batch.GUI.x64.v$Version.Qt$QtMajor.Windows.Portable.zip"
$installerFile = Join-Path $releaseDirectory "MKV.Muxing.Batch.GUI.x64.v$Version.Qt$QtMajor.Windows.Installer.exe"
$checksumsFile = Join-Path $releaseDirectory "SHA256SUMS.txt"
$runtimeVerifier = Join-Path $PSScriptRoot "verify_packaged_runtime.py"
$sourceVersion = [regex]::Match(
    (Get-Content -LiteralPath (Join-Path $projectRoot "packages\Startup\Version.py") -Raw),
    'Version\s*=\s*"([^"]+)"'
).Groups[1].Value
if ($sourceVersion -ne $Version) {
    throw "Source version '$sourceVersion' does not match requested release '$Version'"
}

foreach ($target in @($buildDirectory, $distDirectory, $releaseDirectory)) {
    $fullTarget = [System.IO.Path]::GetFullPath($target)
    if (-not $fullTarget.StartsWith($projectRoot + [System.IO.Path]::DirectorySeparatorChar)) {
        throw "Refusing to clean a build path outside the project: $fullTarget"
    }
    if (Test-Path -LiteralPath $fullTarget) {
        Remove-Item -LiteralPath $fullTarget -Recurse -Force
    }
}
New-Item -ItemType Directory -Path $releaseDirectory | Out-Null

Push-Location $projectRoot
try {
    $pythonExecutable = (Resolve-Path -LiteralPath $Python).Path
    $basePythonDirectory = & $pythonExecutable -c "import sys; print(sys.base_prefix)"
    if ($LASTEXITCODE -ne 0) {
        throw "Could not inspect the release Python interpreter"
    }

    # Native dependency discovery must not inherit DLL directories from Codex,
    # Poppler, media tools, or other software installed on the build machine.
    $originalPath = $env:PATH
    $originalPythonPath = $env:PYTHONPATH
    $originalQtPluginPath = $env:QT_PLUGIN_PATH
    $originalQtApi = $env:MKV_MUXING_BATCH_QT_API
    $cleanPathEntries = @(
        (Split-Path -Parent $pythonExecutable),
        $basePythonDirectory,
        (Join-Path $basePythonDirectory "Scripts"),
        (Join-Path $env:SystemRoot "System32"),
        $env:SystemRoot
    ) | Where-Object { $_ -and (Test-Path -LiteralPath $_) } | Select-Object -Unique
    try {
        $env:PATH = $cleanPathEntries -join [System.IO.Path]::PathSeparator
        Remove-Item Env:PYTHONPATH -ErrorAction SilentlyContinue
        Remove-Item Env:QT_PLUGIN_PATH -ErrorAction SilentlyContinue
        $env:MKV_MUXING_BATCH_QT_API = if ($QtMajor -eq 5) { "pyside2" } else { "pyside6" }
        & $pythonExecutable -m PyInstaller --noconfirm --clean --workpath $buildDirectory --distpath $distDirectory $specFile
        if ($LASTEXITCODE -ne 0) {
            throw "PyInstaller failed with exit code $LASTEXITCODE"
        }
    }
    finally {
        $env:PATH = $originalPath
        if ($null -eq $originalPythonPath) {
            Remove-Item Env:PYTHONPATH -ErrorAction SilentlyContinue
        }
        else {
            $env:PYTHONPATH = $originalPythonPath
        }
        if ($null -eq $originalQtPluginPath) {
            Remove-Item Env:QT_PLUGIN_PATH -ErrorAction SilentlyContinue
        }
        else {
            $env:QT_PLUGIN_PATH = $originalQtPluginPath
        }
        if ($null -eq $originalQtApi) {
            Remove-Item Env:MKV_MUXING_BATCH_QT_API -ErrorAction SilentlyContinue
        }
        else {
            $env:MKV_MUXING_BATCH_QT_API = $originalQtApi
        }
    }

    & $pythonExecutable $runtimeVerifier $applicationDirectory --qt-major $QtMajor
    if ($LASTEXITCODE -ne 0) {
        throw "Packaged Qt runtime verification failed"
    }

    $packagedExecutable = Join-Path $applicationDirectory "$applicationName.exe"
    $startupProcess = Start-Process -FilePath $packagedExecutable -PassThru
    try {
        $startupDeadline = [DateTime]::UtcNow.AddSeconds(15)
        $startupVerified = $false
        while ([DateTime]::UtcNow -lt $startupDeadline) {
            Start-Sleep -Milliseconds 250
            $startupProcess.Refresh()
            if ($startupProcess.HasExited) {
                throw "Packaged application exited during startup with code $($startupProcess.ExitCode)"
            }
            if ($startupProcess.MainWindowTitle -eq "Unhandled exception in script") {
                throw "Packaged application opened PyInstaller's unhandled-exception dialog"
            }
            if (
                $startupProcess.MainWindowTitle -eq "MKV Muxing Batch GUI v$Version" -and
                $startupProcess.Responding
            ) {
                $startupVerified = $true
                break
            }
        }
        if (-not $startupVerified) {
            throw "Packaged application did not open a responsive v$Version window within 15 seconds"
        }
        Write-Output "Packaged startup verification passed: MKV Muxing Batch GUI v$Version"

        $diagnosticsLog = Join-Path $env:APPDATA "MKV Muxing Batch GUI\diagnostics.log"
        $expectedQtBinding = if ($QtMajor -eq 5) { "PySide2" } else { "PySide6" }
        $diagnosticsDeadline = [DateTime]::UtcNow.AddSeconds(5)
        $diagnosticsVerified = $false
        while ([DateTime]::UtcNow -lt $diagnosticsDeadline) {
            Start-Sleep -Milliseconds 250
            if (Test-Path -LiteralPath $diagnosticsLog) {
                $diagnosticsText = Get-Content -LiteralPath $diagnosticsLog -Raw
                if (
                    $diagnosticsText.Contains("PID=$($startupProcess.Id) frozen=True") -and
                    $diagnosticsText.Contains("Qt binding=$expectedQtBinding") -and
                    $diagnosticsText.Contains("GUI watchdog started")
                ) {
                    $diagnosticsVerified = $true
                    break
                }
            }
        }
        if (-not $diagnosticsVerified) {
            throw "Packaged application did not initialize its diagnostic logger and GUI watchdog"
        }
        Write-Output "Packaged diagnostic logger verification passed: $diagnosticsLog"
    }
    finally {
        $startupProcess.Refresh()
        if (-not $startupProcess.HasExited) {
            Stop-Process -Id $startupProcess.Id -Force
        }
    }

    $innoCompilerCandidates = @(
        (Join-Path $env:LOCALAPPDATA "Programs\Inno Setup 6\ISCC.exe"),
        "C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        "C:\Program Files\Inno Setup 6\ISCC.exe"
    )
    $innoCompiler = $innoCompilerCandidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
    if (-not $innoCompiler) {
        throw "Inno Setup 6 was not found"
    }
    & $innoCompiler "/DMyAppVersion=$Version" $installerScript
    if ($LASTEXITCODE -ne 0) {
        throw "Inno Setup failed with exit code $LASTEXITCODE"
    }

    Compress-Archive -LiteralPath $applicationDirectory -DestinationPath $portableFile -CompressionLevel Optimal
    $checksumLines = foreach ($artifact in @($installerFile, $portableFile)) {
        $hash = (Get-FileHash -LiteralPath $artifact -Algorithm SHA256).Hash.ToLowerInvariant()
        "$hash  $([System.IO.Path]::GetFileName($artifact))"
    }
    [System.IO.File]::WriteAllLines($checksumsFile, $checksumLines)
}
finally {
    Pop-Location
}

Get-Item -LiteralPath $installerFile, $portableFile, $checksumsFile |
    Select-Object Name, Length, LastWriteTime
