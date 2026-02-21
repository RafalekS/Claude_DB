# Paths
$themesFile = "themes.json"
$schemesFile = "schemes.json"
$outputFile = "themes_new.json"

# Read files
$themesRaw = Get-Content $themesFile -Raw | ConvertFrom-Json
$schemesText = Get-Content $schemesFile -Raw

# Extract the main schemes array (tolerates extra text)
$schemesArrayText = [regex]::Match($schemesText, '\[\s*\{[\s\S]*\}\s*\]').Value
if (-not $schemesArrayText) {
    Write-Error "❌ Could not locate the schemes array inside schemes.json"
    exit 1
}

# Wrap extracted array into valid JSON
$schemesJson = "{ `"schemes`": $schemesArrayText }"
$schemes = $schemesJson | ConvertFrom-Json

# Define field rename mapping
$mapping = @{
    selectionBackground = "selection"
    cursorColor         = "cursor"
}

# Transform each scheme
$newThemes = @{}
foreach ($scheme in $schemes.schemes) {
    $name = $scheme.name
    $theme = [ordered]@{ name = $name }

    foreach ($prop in $scheme.PSObject.Properties) {
        if ($prop.Name -eq "name") { continue }
        $newKey = if ($mapping.ContainsKey($prop.Name)) { $mapping[$prop.Name] } else { $prop.Name }
        $theme[$newKey] = $prop.Value
    }

    $newThemes[$name] = $theme
}

# Sort themes alphabetically by name
$sortedThemes = $newThemes.GetEnumerator() | Sort-Object Name

# Convert sorted dictionary back into an ordered hash table
$orderedThemes = [ordered]@{}
foreach ($entry in $sortedThemes) {
    $orderedThemes[$entry.Name] = $entry.Value
}

# Save to JSON file
$orderedThemes | ConvertTo-Json -Depth 10 | Set-Content $outputFile -Encoding UTF8
Write-Host "✅ Created sorted themes file: $outputFile"
