#!/usr/bin/env pwsh
# Backup script for Claude_DB program files
# Creates timestamped tar.gz backup

$timestamp = Get-Date -Format "dd_MM_HH_mm"
$backupDir = "C:\Scripts\python\Claude_DB\backup"
$programDir = "C:\Scripts\python\Claude_DB"
$backupFile = "backup_$timestamp.tar.gz"
$backupPath = Join-Path $backupDir $backupFile

# Ensure backup directory exists
if (-not (Test-Path $backupDir)) {
    New-Item -ItemType Directory -Path $backupDir -Force | Out-Null
}

Write-Host "Creating backup: $backupFile" -ForegroundColor Cyan

# Files and directories to backup
$itemsToBackup = @(
    "src",
    "help",
	"config",
    "CLAUDE.md",
    "backup_program.ps1"
)

# Create temporary directory for staging
$tempDir = Join-Path $env:TEMP "claude_db_backup_temp"
if (Test-Path $tempDir) {
    Remove-Item $tempDir -Recurse -Force
}
New-Item -ItemType Directory -Path $tempDir -Force | Out-Null

# Copy items to temp directory
foreach ($item in $itemsToBackup) {
    $sourcePath = Join-Path $programDir $item
    if (Test-Path $sourcePath) {
        $destPath = Join-Path $tempDir $item
        if (Test-Path $sourcePath -PathType Container) {
            Copy-Item $sourcePath -Destination $destPath -Recurse -Force
        } else {
            Copy-Item $sourcePath -Destination $destPath -Force
        }
        Write-Host "  Copied: $item" -ForegroundColor Green
    } else {
        Write-Host "  Skipped (not found): $item" -ForegroundColor Yellow
    }
}

# Create tar.gz archive
try {
    Push-Location $tempDir

    # Use tar command (available in Windows 10+)
    tar -czf $backupPath *

    Pop-Location

    Write-Host "`nBackup created successfully!" -ForegroundColor Green
    Write-Host "Location: $backupPath" -ForegroundColor Cyan

    # Show file size
    $fileSize = (Get-Item $backupPath).Length / 1KB
    Write-Host "Size: $([math]::Round($fileSize, 2)) KB" -ForegroundColor Cyan

} catch {
    Write-Host "`nError creating backup: $_" -ForegroundColor Red
    exit 1
} finally {
    # Clean up temp directory
    if (Test-Path $tempDir) {
        Remove-Item $tempDir -Recurse -Force
    }
}

# List recent backups
Write-Host "`nRecent backups:" -ForegroundColor Cyan
Get-ChildItem $backupDir -Filter "backup_*.tar.gz" |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 5 |
    ForEach-Object {
        $size = [math]::Round($_.Length / 1KB, 2)
        Write-Host "  $($_.Name) - $size KB - $($_.LastWriteTime)" -ForegroundColor Gray
    }
