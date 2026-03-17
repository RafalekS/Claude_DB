# update_skills.ps1 - Copy SKILL.md and overhaul.md to all destinations

$SshKey     = "C:\Users\r_sta\.ssh\P16_id_rsa"
$RemoteUser = "pi"
$RemoteHost = "192.168.0.97"

# ── SKILL.md ──────────────────────────────────────────────────────────────────
$SkillSrc = "C:\Users\r_sta\.claude\skills\coding\SKILL.md"

$SkillDests = @(
    "C:\Scripts\Raspberry\picc\config\home\.claude\skills\coding\SKILL.md",
    "C:\Scripts\AI\Claude_DB\config\templates\skills\development\coding.md",
    "C:\Scripts\AI\autoclaude\reference\templates\skills\development\coding.md"
)

Write-Host "Copying SKILL.md..." -ForegroundColor Cyan

foreach ($dest in $SkillDests) {
    $dir = Split-Path $dest -Parent
    if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
    Copy-Item -Path $SkillSrc -Destination $dest -Force
    Write-Host "  -> $dest"
}

$RemoteSkillPath = "/home/pi/.claude/skills/coding/SKILL.md"
Write-Host "  -> scp ${RemoteUser}@${RemoteHost}:${RemoteSkillPath}"
scp -i $SshKey -o StrictHostKeyChecking=no $SkillSrc "${RemoteUser}@${RemoteHost}:${RemoteSkillPath}"

# ── overhaul.md ───────────────────────────────────────────────────────────────
$OverhaulSrc = "C:\Users\r_sta\.claude\commands\raf\overhaul.md"

$OverhaulDests = @(
    "C:\Scripts\Raspberry\picc\config\home\.claude\commands\raf\overhaul.md",
    "C:\Scripts\AI\Claude_DB\config\templates\commands\raf\overhaul.md",
    "C:\Scripts\AI\autoclaude\reference\templates\commands\raf\overhaul.md"
)

Write-Host "`nCopying overhaul.md..." -ForegroundColor Cyan

foreach ($dest in $OverhaulDests) {
    $dir = Split-Path $dest -Parent
    if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
    Copy-Item -Path $OverhaulSrc -Destination $dest -Force
    Write-Host "  -> $dest"
}

$RemoteOverhaulPath = "/home/pi/.claude/commands/overhaul.md"
Write-Host "  -> scp ${RemoteUser}@${RemoteHost}:${RemoteOverhaulPath}"
scp -i $SshKey -o StrictHostKeyChecking=no $OverhaulSrc "${RemoteUser}@${RemoteHost}:${RemoteOverhaulPath}"

Write-Host "`nDone." -ForegroundColor Green
