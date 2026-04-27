$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot
Remove-Item -Recurse -Force build, dist, installer\output, installer\Output -ErrorAction SilentlyContinue
Remove-Item -Force *.spec -ErrorAction SilentlyContinue
Write-Host "Cleaned build output."
