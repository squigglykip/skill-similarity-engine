# PowerShell script to fold a repository into a single .txt file for transfer
# Respects .gitignore patterns and handles both text and binary files

param(
    [string]$SourcePath = ".",
    [string]$OutputFile = "repo-folded.txt",
    [string]$GitIgnoreFile = ".gitignore"
)

# Function to check if a path matches gitignore patterns
function Test-GitIgnore {
    param([string]$Path, [string[]]$Patterns)
    
    $relativePath = $Path -replace [regex]::Escape($PWD.Path + "\"), ""
    $relativePath = $relativePath -replace "\\", "/"
    $fileName = Split-Path $relativePath -Leaf
    
    foreach ($pattern in $Patterns) {
        if ([string]::IsNullOrWhiteSpace($pattern) -or $pattern.StartsWith("#")) {
            continue
        }
        
        # Handle simple file extension patterns (*.ext)
        if ($pattern.StartsWith("*.")) {
            $extension = $pattern.Substring(1)
            if ($fileName.EndsWith($extension, [StringComparison]::OrdinalIgnoreCase)) {
                return $true
            }
        }
        # Handle directory patterns
        elseif ($pattern.EndsWith("/")) {
            $dirPattern = $pattern.TrimEnd("/")
            if ($relativePath.StartsWith("$dirPattern/") -or $relativePath -eq $dirPattern) {
                return $true
            }
        }
        # Handle specific file/path patterns
        else {
            $wildcardPattern = $pattern -replace "\*\*/", "*" -replace "/\*\*", "*" -replace "\*\*", "*"
            if ($relativePath -like $wildcardPattern -or $relativePath -like "*/$wildcardPattern" -or $relativePath -like "$wildcardPattern/*") {
                return $true
            }
        }
    }
    
    return $false
}

# Function to check if a file is binary
function Test-BinaryFile {
    param([string]$FilePath)
    
    try {
        $bytes = [System.IO.File]::ReadAllBytes($FilePath)
        if ($bytes.Length -eq 0) { return $false }
        
        # Check first 8KB for null bytes (common binary indicator)
        $checkLength = [Math]::Min(8192, $bytes.Length)
        for ($i = 0; $i -lt $checkLength; $i++) {
            if ($bytes[$i] -eq 0) { return $true }
        }
        
        return $false
    }
    catch {
        return $true  # If we can't read it, treat as binary
    }
}

Write-Host "Folding repository into $OutputFile..." -ForegroundColor Green
Write-Host "Source: $SourcePath" -ForegroundColor Cyan

# Read gitignore patterns
$gitIgnorePatterns = @()
if (Test-Path $GitIgnoreFile) {
    $gitIgnorePatterns = Get-Content $GitIgnoreFile | Where-Object { $_ -and -not $_.StartsWith("#") }
    Write-Host "Loaded $($gitIgnorePatterns.Count) gitignore patterns" -ForegroundColor Yellow
}

# Add common patterns to ignore
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
    # Data files
    "*.csv"
    "*.xlsx"
    "*.xls"
    "*.tsv"
    # Model and ML files  
    "*.joblib"
    "*.pkl"
    "*.pickle"
    "*.h5"
    "*.hdf5"
    "*.model"
    # Database files
    "*.sqlite"
    "*.sqlite3"
    "*.db"
    "*.mdb"
    # Large text files and exports
    "*.txt"
    # Exclude entire data directories
    "data/"
    "models/"
    "exports/"
    # Cache and compiled files
    "*.pyc"
    "__pycache__/"
    "*.pyo"
    "*.pyd"
    # Documentation builds
    "docs/_build/"
    "docs/*.html"
)

# Start building the output
$output = @()
$output += "=== FOLDED REPOSITORY ==="
$output += "Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
$output += "Source: $SourcePath"
$output += "=== BEGIN REPOSITORY DATA ==="

$fileCount = 0
$binaryCount = 0
$skippedCount = 0

# Get all files recursively
Get-ChildItem -Path $SourcePath -Recurse -File | ForEach-Object {
    $file = $_
    $relativePath = $file.FullName -replace [regex]::Escape((Resolve-Path $SourcePath).Path + "\"), ""
    
    # Check if file should be ignored
    if (Test-GitIgnore -Path $file.FullName -Patterns $gitIgnorePatterns) {
        $skippedCount++
        Write-Host "Skipping (gitignore): $relativePath" -ForegroundColor DarkGray
        return
    }
    
    # Check file size (skip very large files)
    if ($file.Length -gt 50MB) {
        $skippedCount++
        Write-Host "Skipping (too large): $relativePath" -ForegroundColor Yellow
        return
    }
    
    $fileCount++
    Write-Host "Processing: $relativePath" -ForegroundColor White
    
    # Add file header
    $output += ""
    $output += "=== FILE START ==="
    $output += "PATH: $relativePath"
    $output += "SIZE: $($file.Length)"
    $output += "MODIFIED: $($file.LastWriteTime.ToString('yyyy-MM-dd HH:mm:ss'))"
    
    # Determine if file is binary
    $isBinary = Test-BinaryFile -FilePath $file.FullName
    
    if ($isBinary) {
        $binaryCount++
        $output += "TYPE: BINARY"
        $output += "ENCODING: BASE64"
        $output += "=== CONTENT START ==="
        
        try {
            $bytes = [System.IO.File]::ReadAllBytes($file.FullName)
            $base64 = [System.Convert]::ToBase64String($bytes)
            $output += $base64
        }
        catch {
            $output += "ERROR: Could not read binary file: $($_.Exception.Message)"
        }
    }
    else {
        $output += "TYPE: TEXT"
        $output += "ENCODING: UTF8"
        $output += "=== CONTENT START ==="
        
        try {
            $content = Get-Content -Path $file.FullName -Raw -Encoding UTF8
            if ($content) {
                $output += $content
            }
        }
        catch {
            $output += "ERROR: Could not read text file: $($_.Exception.Message)"
        }
    }
    
    $output += "=== CONTENT END ==="
    $output += "=== FILE END ==="
}

$output += ""
$output += "=== END REPOSITORY DATA ==="
$output += "=== SUMMARY ==="
$output += "Total files processed: $fileCount"
$output += "Binary files: $binaryCount"
$output += "Text files: $($fileCount - $binaryCount)"
$output += "Skipped files: $skippedCount"
$output += "=== END FOLDED REPOSITORY ==="

# Write to output file
$output | Out-File -FilePath $OutputFile -Encoding UTF8

Write-Host "`nRepository folded successfully!" -ForegroundColor Green
Write-Host "Output file: $OutputFile" -ForegroundColor Cyan
Write-Host "File size: $([math]::Round((Get-Item $OutputFile).Length / 1MB, 2)) MB" -ForegroundColor Yellow
Write-Host "Files processed: $fileCount (Text: $($fileCount - $binaryCount), Binary: $binaryCount)" -ForegroundColor White
Write-Host "Files skipped: $skippedCount" -ForegroundColor Gray
