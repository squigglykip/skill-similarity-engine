# PowerShell script to analyze file sizes in the repository
# Helps identify what's taking up space in the folded output

param(
    [string]$SourcePath = ".",
    [int]$TopCount = 20,
    [string]$GitIgnoreFile = ".gitignore"
)

# Function to check if a path matches gitignore patterns
function Test-GitIgnore {
    param([string]$Path, [string[]]$Patterns)
    
    $relativePath = $Path -replace [regex]::Escape($PWD.Path + "\"), ""
    $relativePath = $relativePath -replace "\\", "/"
    
    foreach ($pattern in $Patterns) {
        if ([string]::IsNullOrWhiteSpace($pattern) -or $pattern.StartsWith("#")) {
            continue
        }
        
        # Convert gitignore pattern to PowerShell wildcard
        $wildcardPattern = $pattern -replace "\*\*/", "*" -replace "/\*\*", "*" -replace "\*\*", "*"
        $wildcardPattern = $wildcardPattern -replace "\.", "\." -replace "\*", "*"
        
        # Check if path matches pattern
        if ($relativePath -like $wildcardPattern -or $relativePath -like "*/$wildcardPattern" -or $relativePath -like "$wildcardPattern/*") {
            return $true
        }
        
        # Handle directory patterns
        if ($pattern.EndsWith("/") -and $relativePath.StartsWith($pattern.TrimEnd("/"))) {
            return $true
        }
    }
    
    return $false
}

function Format-FileSize {
    param([long]$Size)
    
    if ($Size -gt 1GB) {
        return "{0:N2} GB" -f ($Size / 1GB)
    }
    elseif ($Size -gt 1MB) {
        return "{0:N2} MB" -f ($Size / 1MB)
    }
    elseif ($Size -gt 1KB) {
        return "{0:N2} KB" -f ($Size / 1KB)
    }
    else {
        return "$Size bytes"
    }
}

Write-Host "Analyzing file sizes in: $SourcePath" -ForegroundColor Green
Write-Host "=" * 60 -ForegroundColor Cyan

# Read gitignore patterns
$gitIgnorePatterns = @()
if (Test-Path $GitIgnoreFile) {
    $gitIgnorePatterns = Get-Content $GitIgnoreFile | Where-Object { $_ -and -not $_.StartsWith("#") }
}

# Add common patterns to ignore (same as fold script)
$gitIgnorePatterns += @(
    ".git/*"
    ".git/**"
    "*.tmp"
    "*.temp"
    "Thumbs.db"
    ".DS_Store"
    "repo-folded.txt"
    "fold-repo.ps1"
    "unfold-repo.ps1"
    "analyze-file-sizes.ps1"
    "*.csv"
    "*.xlsx"
    "*.xls"
    "*.joblib"
    "*.pkl"
    "*.pickle"
)

# Collect all files with their info
$allFiles = @()
$totalSize = 0
$includedSize = 0
$excludedSize = 0
$includedCount = 0
$excludedCount = 0

Get-ChildItem -Path $SourcePath -Recurse -File | ForEach-Object {
    $file = $_
    $relativePath = $file.FullName -replace [regex]::Escape((Resolve-Path $SourcePath).Path + "\"), ""
    
    $isIgnored = Test-GitIgnore -Path $file.FullName -Patterns $gitIgnorePatterns
    $totalSize += $file.Length
    
    $fileInfo = [PSCustomObject]@{
        Path = $relativePath
        Size = $file.Length
        SizeFormatted = Format-FileSize -Size $file.Length
        Extension = $file.Extension.ToLower()
        IsIgnored = $isIgnored
        LastModified = $file.LastWriteTime
    }
    
    $allFiles += $fileInfo
    
    if ($isIgnored) {
        $excludedSize += $file.Length
        $excludedCount++
    }
    else {
        $includedSize += $file.Length
        $includedCount++
    }
}

# Summary statistics
Write-Host "`nSUMMARY:" -ForegroundColor Yellow
Write-Host "Total files: $($allFiles.Count)" -ForegroundColor White
Write-Host "Total size: $(Format-FileSize -Size $totalSize)" -ForegroundColor White
Write-Host ""
Write-Host "Files to be INCLUDED:" -ForegroundColor Green
Write-Host "  Count: $includedCount"
Write-Host "  Size: $(Format-FileSize -Size $includedSize)"
Write-Host ""
Write-Host "Files to be EXCLUDED:" -ForegroundColor Red
Write-Host "  Count: $excludedCount"
Write-Host "  Size: $(Format-FileSize -Size $excludedSize)"
Write-Host ""

# Top largest files that WILL BE INCLUDED
Write-Host "TOP $TopCount LARGEST FILES (TO BE INCLUDED):" -ForegroundColor Yellow
Write-Host "=" * 60 -ForegroundColor Cyan
$includedFiles = $allFiles | Where-Object { -not $_.IsIgnored } | Sort-Object Size -Descending | Select-Object -First $TopCount
foreach ($file in $includedFiles) {
    Write-Host "$($file.SizeFormatted.PadLeft(10)) - $($file.Path)" -ForegroundColor White
}

# File type breakdown for included files
Write-Host "`nFILE TYPE BREAKDOWN (INCLUDED FILES):" -ForegroundColor Yellow
Write-Host "=" * 60 -ForegroundColor Cyan
$includedByType = $allFiles | Where-Object { -not $_.IsIgnored } | 
    Group-Object Extension | 
    Sort-Object { ($_.Group | Measure-Object Size -Sum).Sum } -Descending |
    Select-Object -First 15

foreach ($group in $includedByType) {
    $typeSize = ($group.Group | Measure-Object Size -Sum).Sum
    $typeCount = $group.Count
    $avgSize = if ($typeCount -gt 0) { $typeSize / $typeCount } else { 0 }
    
    $extension = if ($group.Name) { $group.Name } else { "(no extension)" }
    Write-Host "$(Format-FileSize -Size $typeSize).PadLeft(10) - $extension ($typeCount files, avg: $(Format-FileSize -Size $avgSize))" -ForegroundColor White
}

# Directories with most content (included)
Write-Host "`nLARGEST DIRECTORIES (INCLUDED CONTENT):" -ForegroundColor Yellow
Write-Host "=" * 60 -ForegroundColor Cyan
$dirSizes = $allFiles | Where-Object { -not $_.IsIgnored } | 
    ForEach-Object { 
        $dirPath = Split-Path $_.Path -Parent
        if (-not $dirPath) { $dirPath = "." }
        [PSCustomObject]@{ Directory = $dirPath; Size = $_.Size }
    } |
    Group-Object Directory |
    ForEach-Object {
        [PSCustomObject]@{
            Directory = $_.Name
            TotalSize = ($_.Group | Measure-Object Size -Sum).Sum
            FileCount = $_.Count
        }
    } |
    Sort-Object TotalSize -Descending |
    Select-Object -First 10

foreach ($dir in $dirSizes) {
    Write-Host "$(Format-FileSize -Size $dir.TotalSize).PadLeft(10) - $($dir.Directory) ($($dir.FileCount) files)" -ForegroundColor White
}

# Suggestions for further reduction
Write-Host "`nSUGGESTIONS FOR SIZE REDUCTION:" -ForegroundColor Magenta
Write-Host "=" * 60 -ForegroundColor Cyan

# Large individual files
$largeFiles = $allFiles | Where-Object { -not $_.IsIgnored -and $_.Size -gt 1MB } | Sort-Object Size -Descending
if ($largeFiles) {
    Write-Host "• Consider excluding these large files (>1MB):" -ForegroundColor Yellow
    $largeFiles | Select-Object -First 5 | ForEach-Object {
        Write-Host "  - $($_.Path) ($(Format-FileSize -Size $_.Size))" -ForegroundColor Gray
    }
}

# Suggest additional extensions to exclude
$heavyExtensions = $includedByType | Where-Object { ($_.Group | Measure-Object Size -Sum).Sum -gt 5MB } | Select-Object -First 3
if ($heavyExtensions) {
    Write-Host "• Consider excluding these file types:" -ForegroundColor Yellow
    foreach ($ext in $heavyExtensions) {
        $typeSize = ($ext.Group | Measure-Object Size -Sum).Sum
        $extension = if ($ext.Name) { $ext.Name } else { "(no extension)" }
        Write-Host "  - $extension files ($(Format-FileSize -Size $typeSize))" -ForegroundColor Gray
    }
}

Write-Host "`nEstimated folded file size: $(Format-FileSize -Size ($includedSize * 1.1))" -ForegroundColor Green
Write-Host "(+10% overhead for text formatting)" -ForegroundColor Gray
