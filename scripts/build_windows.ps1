$ErrorActionPreference = 'Stop'

$projectRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$python = Join-Path $projectRoot 'backend\.venv\Scripts\python.exe'

Push-Location (Join-Path $projectRoot 'frontend')
try {
    npm run build
} finally {
    Pop-Location
}

Push-Location $projectRoot
try {
    & $python -m PyInstaller `
        --noconfirm `
        --clean `
        --onefile `
        --windowed `
        --name 'VoC-Insight' `
        --paths 'backend' `
        --add-data 'frontend\dist;frontend_dist' `
        --hidden-import 'uvicorn.logging' `
        --hidden-import 'uvicorn.loops.auto' `
        --hidden-import 'uvicorn.protocols.http.auto' `
        --hidden-import 'uvicorn.protocols.websockets.auto' `
        --hidden-import 'uvicorn.lifespan.on' `
        'launcher.py'
} finally {
    Pop-Location
}

New-Item -ItemType Directory -Path (Join-Path $projectRoot 'release') -Force | Out-Null
Copy-Item -LiteralPath (Join-Path $projectRoot 'dist\VoC-Insight.exe') -Destination (Join-Path $projectRoot 'release\VoC-Insight-Windows-x64.exe') -Force
Write-Output "Package ready: $projectRoot\release\VoC-Insight-Windows-x64.exe"

