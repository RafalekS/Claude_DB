# update_skills.ps1

# ── CONFIG ────────────────────────────────────────────────────────────────────
$SshKey     = "C:\Users\r_sta\.ssh\P16_id_rsa"
$RemoteUser = "pi"
$RemoteHost = "192.168.0.97"

# ── GENERIC FUNCTION ──────────────────────────────────────────────────────────
function Sync-File {
    param (
        [string]$Name,
        [string]$Source,
        [string[]]$Destinations,
        [string]$RemotePath
    )

    Write-Host "`nCopying $Name..." -ForegroundColor Cyan

    foreach ($dest in $Destinations) {
        $dir = Split-Path $dest -Parent
        if (-not (Test-Path $dir)) {
            New-Item -ItemType Directory -Path $dir -Force | Out-Null
        }

        Copy-Item -Path $Source -Destination $dest -Force
        Write-Host "  -> $dest"
    }

    if ($RemotePath) {
        scp -i $global:SshKey -o StrictHostKeyChecking=no `
            $Source "${global:RemoteUser}@${global:RemoteHost}:${RemotePath}"
    }
}

# ── SOURCES ───────────────────────────────────────────────────────────────────
$src1 = "C:\Users\r_sta\.claude\skills\coding\SKILL.md"
$src2 = "C:\Users\r_sta\.claude\skills\help_wiki\SKILL.md"
$src3 = "C:\Users\r_sta\.claude\commands\raf\overhaul.md"

# ── DESTINATIONS ──────────────────────────────────────────────────────────────

# coding
$dest1 = @(
    "C:\Scripts\Raspberry\picc\config\home\.claude\skills\coding\SKILL.md",
    "C:\Scripts\AI\Claude_DB\config\templates\skills\development\coding.md",
    "C:\Scripts\AI\autoclaude\reference\templates\skills\development\coding.md"
)

# help_wiki
$dest2 = @(
    "C:\Scripts\Raspberry\picc\config\home\.claude\skills\help_wiki\SKILL.md",
    "C:\Scripts\AI\Claude_DB\config\templates\skills\development\help_wiki.md",
    "C:\Scripts\AI\autoclaude\reference\templates\skills\development\help_wiki.md"
)

# overhaul
$dest3 = @(
    "C:\Scripts\Raspberry\picc\config\home\.claude\commands\raf\overhaul.md",
    "C:\Scripts\AI\Claude_DB\config\templates\commands\raf\overhaul.md",
    "C:\Scripts\AI\autoclaude\reference\templates\commands\raf\overhaul.md"
)

# ── EXECUTION MAP (THIS IS THE ONLY PLACE YOU TOUCH) ──────────────────────────
$jobs = @(
    @{
        name = "coding SKILL.md"
        src  = $src1
        dest = $dest1
        remote = "/home/pi/.claude/skills/coding/SKILL.md"
    },
    @{
        name = "help_wiki SKILL.md"
        src  = $src2
        dest = $dest2
        remote = "/home/pi/.claude/skills/help_wiki/SKILL.md"
    },
    @{
        name = "overhaul.md"
        src  = $src3
        dest = $dest3
        remote = "/home/pi/.claude/commands/overhaul.md"
    }
)

# ── RUN ───────────────────────────────────────────────────────────────────────
foreach ($job in $jobs) {
    Sync-File `
        -Name $job.name `
        -Source $job.src `
        -Destinations $job.dest `
        -RemotePath $job.remote
}

Write-Host "`nDone." -ForegroundColor Green