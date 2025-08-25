# PowerShell script to unfold a repository from a single .txt file
# Recreates the original directory structure and file contents

param(
    [string]$InputFile = "repo-folded.txt",
    [string]$OutputPath = ".",
    [switch]$Force = $false
)

# Function to ensure directory exists
function Ensure-Directory {
    param([string]$Path)
    
    $dir = Split-Path -Path $Path -Parent
    if ($dir -and -not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
}

Write-Host "Unfolding repository from $InputFile..." -ForegroundColor Green
Write-Host "Output: $OutputPath" -ForegroundColor Cyan

# Check if input file exists
if (-not (Test-Path $InputFile)) {
    Write-Error "Input file '$InputFile' not found!"
    exit 1
}

# Check if output directory has content (safety check)
if ((Test-Path $OutputPath) -and (Get-ChildItem $OutputPath -Force).Count -gt 0 -and -not $Force) {
    Write-Warning "Output directory '$OutputPath' is not empty!"
    Write-Warning "Use -Force parameter to overwrite existing content."
    $response = Read-Host "Continue anyway? (y/N)"
    if ($response -ne "y" -and $response -ne "Y") {
        Write-Host "Operation cancelled." -ForegroundColor Yellow
        exit 0
    }
}

# Create output directory if it doesn't exist
if (-not (Test-Path $OutputPath)) {
    New-Item -ItemType Directory -Path $OutputPath -Force | Out-Null
}

# Read the folded file
Write-Host "Reading folded repository file..." -ForegroundColor Yellow
$content = Get-Content -Path $InputFile -Raw -Encoding UTF8

# Validate file format
if (-not $content.StartsWith("=== FOLDED REPOSITORY ===")) {
    Write-Error "Invalid file format! This doesn't appear to be a folded repository file."
    exit 1
}

# Split content into lines for processing
$lines = $content -split "`r?`n"

$currentState = "HEADER"
$currentFilePath = ""
$currentFileType = ""
$currentEncoding = ""
$currentContent = @()
$fileCount = 0
$errorCount = 0

Write-Host "Processing repository data..." -ForegroundColor Yellow

for ($i = 0; $i -lt $lines.Count; $i++) {
    $line = $lines[$i]
    
    switch ($currentState) {
        "HEADER" {
            if ($line -eq "=== BEGIN REPOSITORY DATA ===") {
                $currentState = "LOOKING_FOR_FILE"
                Write-Host "Found repository data section" -ForegroundColor Green
            }
            break
        }
        
        "LOOKING_FOR_FILE" {
            if ($line -eq "=== FILE START ===") {
                $currentState = "FILE_HEADER"
                $currentContent = @()
            }
            elseif ($line -eq "=== END REPOSITORY DATA ===") {
                $currentState = "COMPLETE"
                break
            }
            break
        }
        
        "FILE_HEADER" {
            if ($line.StartsWith("PATH: ")) {
                $currentFilePath = $line.Substring(6)
            }
            elseif ($line.StartsWith("TYPE: ")) {
                $currentFileType = $line.Substring(6)
            }
            elseif ($line.StartsWith("ENCODING: ")) {
                $currentEncoding = $line.Substring(10)
            }
            elseif ($line -eq "=== CONTENT START ===") {
                $currentState = "FILE_CONTENT"
                $currentContent = @()
            }
            break
        }
        
        "FILE_CONTENT" {
            if ($line -eq "=== CONTENT END ===") {
                # Process the file content
                try {
                    $fullPath = Join-Path $OutputPath $currentFilePath
                    Write-Host "Creating: $currentFilePath" -ForegroundColor White
                    
                    # Ensure directory exists
                    Ensure-Directory -Path $fullPath
                    
                    if ($currentFileType -eq "BINARY") {
                        # Handle binary file
                        if ($currentContent.Count -gt 0 -and -not $currentContent[0].StartsWith("ERROR:")) {
                            $base64Content = $currentContent -join ""
                            $bytes = [System.Convert]::FromBase64String($base64Content)
                            [System.IO.File]::WriteAllBytes($fullPath, $bytes)
                        }
                        else {
                            Write-Warning "Skipping binary file with error: $currentFilePath"
                            $errorCount++
                        }
                    }
                    else {
                        # Handle text file
                        if ($currentContent.Count -gt 0 -and -not $currentContent[0].StartsWith("ERROR:")) {
                            $textContent = $currentContent -join "`n"
                            [System.IO.File]::WriteAllText($fullPath, $textContent, [System.Text.Encoding]::UTF8)
                        }
                        else {
                            Write-Warning "Skipping text file with error: $currentFilePath"
                            $errorCount++
                        }
                    }
                    
                    $fileCount++
                }
                catch {
                    Write-Error "Failed to create file '$currentFilePath': $($_.Exception.Message)"
                    $errorCount++
                }
                
                $currentState = "FILE_FOOTER"
            }
            else {
                $currentContent += $line
            }
            break
        }
        
        "FILE_FOOTER" {
            if ($line -eq "=== FILE END ===") {
                $currentState = "LOOKING_FOR_FILE"
            }
            break
        }
    }
}

Write-Host "`nRepository unfolded successfully!" -ForegroundColor Green
Write-Host "Output directory: $OutputPath" -ForegroundColor Cyan
Write-Host "Files created: $fileCount" -ForegroundColor White

if ($errorCount -gt 0) {
    Write-Warning "Errors encountered: $errorCount"
    Write-Warning "Check the output above for details about failed files."
}

# Display summary from original fold file if available
$summaryStarted = $false
foreach ($line in $lines) {
    if ($line -eq "=== SUMMARY ===") {
        $summaryStarted = $true
        Write-Host "`nOriginal Summary:" -ForegroundColor Green
        continue
    }
    if ($summaryStarted) {
        if ($line -eq "=== END FOLDED REPOSITORY ===") {
            break
        }
        Write-Host $line -ForegroundColor Gray
    }
}
